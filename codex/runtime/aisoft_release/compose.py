"""Security validation for the normalized Docker Compose JSON model."""

from __future__ import annotations

import re
from typing import Mapping

from .contract import ReleaseManifest
from .errors import ContractError
from .security import (
    is_external_environment_reference,
    reject_sensitive_compose_fields,
)


RELEASE_LABEL = "com.aisoft.release.id"
SERVICE_LABEL = "com.aisoft.release.service"
DOCKER_SOCKET_PATHS = {"/var/run/docker.sock", "/run/docker.sock"}
NUMERIC_USER = re.compile(r"^[1-9][0-9]*(?::[1-9][0-9]*)?$")
MEMORY_LIMIT = re.compile(r"^[1-9][0-9]*(?:[kKmMgG][bB]?)?$")
LOG_SIZE = re.compile(r"^[1-9][0-9]*(?:[kKmMgG][bB]?)$")


def validate_compose_model(
    model: Mapping[str, object], manifest: ReleaseManifest
) -> None:
    reject_sensitive_compose_fields(model)
    services = model.get("services")
    if not isinstance(services, Mapping) or not services:
        raise ContractError("Compose model must contain services")
    expected = {item.service for item in manifest.images}
    actual = set(services)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        detail = []
        if missing:
            detail.append("missing=" + ",".join(missing))
        if unknown:
            detail.append("unknown=" + ",".join(unknown))
        raise ContractError("Compose services do not match manifest: " + " ".join(detail))

    networks = model.get("networks")
    if not isinstance(networks, Mapping) or len(networks) < 2:
        raise ContractError("Compose model requires at least two explicit networks")
    internal_networks = {
        str(name)
        for name, config in networks.items()
        if isinstance(config, Mapping) and config.get("internal") is True
    }
    if not internal_networks:
        raise ContractError("Compose model requires at least one internal network")
    secrets = model.get("secrets")
    if secrets is not None and secrets != {}:
        raise ContractError("Compose secrets are forbidden; use the protected target env file")

    runtime = set(manifest.runtime_services)
    for service_name in sorted(actual):
        config = services.get(service_name)
        if not isinstance(config, Mapping):
            raise ContractError(f"Compose service {service_name} must be an object")
        image = manifest.image_for(service_name)
        build = config.get("build")
        if build is not None and build is not False:
            raise ContractError(f"Compose service {service_name} must not define build")
        if config.get("image") != image.runtime_reference:
            raise ContractError(
                f"Compose service {service_name} image must match manifest runtime reference"
            )
        privileged = config.get("privileged")
        if privileged is not None and privileged is not False:
            raise ContractError(f"Compose service {service_name} must not be privileged")
        _require_non_root(config, service_name)
        if config.get("read_only") is not True:
            raise ContractError(f"Compose service {service_name} requires read_only rootfs")
        _require_cap_drop(config, service_name)
        _require_no_new_privileges(config, service_name)
        _reject_host_namespaces(config, service_name)
        _reject_docker_socket(config, service_name)
        _require_explicit_writable_storage(config, service_name)
        _validate_environment(config, service_name)
        _validate_ports(config, service_name)
        _require_resources(config, service_name)
        _require_logging(config, service_name)
        service_networks = _service_networks(config, service_name)
        if "default" in service_networks:
            raise ContractError(f"Compose service {service_name} must not use default network")
        if not service_networks & internal_networks:
            raise ContractError(
                f"Compose service {service_name} must attach to an internal network"
            )
        labels = _labels(config.get("labels"), service_name)
        if labels.get(RELEASE_LABEL) != manifest.release_id:
            raise ContractError(
                f"Compose service {service_name} release label does not match manifest"
            )
        if labels.get(SERVICE_LABEL) != service_name:
            raise ContractError(
                f"Compose service {service_name} service label does not match manifest"
            )
        if service_name in runtime:
            _require_healthcheck(config, service_name)


def _require_non_root(config: Mapping[str, object], service: str) -> None:
    user = config.get("user")
    if isinstance(user, bool) or user is None:
        raise ContractError(f"Compose service {service} requires an explicit non-root user")
    text = str(user).strip()
    if not NUMERIC_USER.fullmatch(text):
        raise ContractError(
            f"Compose service {service} must use an explicit positive numeric UID/GID"
        )


def _require_cap_drop(config: Mapping[str, object], service: str) -> None:
    value = config.get("cap_drop")
    if not isinstance(value, list) or "ALL" not in {str(item).upper() for item in value}:
        raise ContractError(f"Compose service {service} requires cap_drop ALL")


def _require_no_new_privileges(config: Mapping[str, object], service: str) -> None:
    value = config.get("security_opt")
    if not isinstance(value, list):
        raise ContractError(f"Compose service {service} requires no-new-privileges")
    normalized = {str(item).lower().replace("=", ":") for item in value}
    if not any(item in {"no-new-privileges", "no-new-privileges:true"} for item in normalized):
        raise ContractError(f"Compose service {service} requires no-new-privileges")


def _reject_host_namespaces(config: Mapping[str, object], service: str) -> None:
    for field in ("ipc", "network_mode", "pid"):
        value = config.get(field)
        if value is not None:
            raise ContractError(f"Compose service {service} must not override {field}")


def _reject_docker_socket(config: Mapping[str, object], service: str) -> None:
    volumes = config.get("volumes", [])
    if not isinstance(volumes, list):
        raise ContractError(f"Compose service {service} volumes must be an array")
    for volume in volumes:
        values: list[str] = []
        if isinstance(volume, str):
            values.extend(volume.split(":"))
            source = volume.split(":", 1)[0]
            if source.startswith(("/", ".")):
                raise ContractError(
                    f"Compose service {service} must not use host bind mounts"
                )
        elif isinstance(volume, Mapping):
            values.extend(
                str(volume.get(field) or "") for field in ("source", "target")
            )
            if volume.get("type") == "bind":
                raise ContractError(
                    f"Compose service {service} must not use host bind mounts"
                )
        else:
            raise ContractError(f"Compose service {service} has an invalid volume")
        if any("$" in item for item in values):
            raise ContractError(f"Compose service {service} volume paths must be literal")
        if any(item in DOCKER_SOCKET_PATHS for item in values):
            raise ContractError(f"Compose service {service} must not mount Docker socket")


def _require_explicit_writable_storage(config: Mapping[str, object], service: str) -> None:
    tmpfs = config.get("tmpfs", [])
    volumes = config.get("volumes", [])
    if not isinstance(tmpfs, list) or not isinstance(volumes, list):
        raise ContractError(f"Compose service {service} writable storage is invalid")
    if not tmpfs and not volumes:
        raise ContractError(
            f"Compose service {service} requires explicit tmpfs or named writable volume"
        )
    if any("$" in str(item) for item in tmpfs):
        raise ContractError(f"Compose service {service} tmpfs paths must be literal")


def _validate_environment(config: Mapping[str, object], service: str) -> None:
    env_files = config.get("env_file")
    if env_files is not None and env_files != []:
        raise ContractError(
            f"Compose service {service} must use only the protected target env file"
        )
    environment = config.get("environment", {})
    if not isinstance(environment, Mapping):
        raise ContractError(f"Compose service {service} environment must be an object")
    for key, value in environment.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ContractError(f"Compose service {service} has an invalid environment key")
        if value is not None and not is_external_environment_reference(value):
            raise ContractError(
                f"Compose service {service} environment values must be external references"
            )


def _validate_ports(config: Mapping[str, object], service: str) -> None:
    ports = config.get("ports", [])
    if not isinstance(ports, list):
        raise ContractError(f"Compose service {service} ports must be an array")
    for port in ports:
        if isinstance(port, Mapping):
            published = port.get("published")
            if published in {None, "", 0, "0"}:
                continue
            host_ip = str(port.get("host_ip") or "")
            if host_ip not in {"127.0.0.1", "::1"}:
                raise ContractError(
                    f"Compose service {service} may publish only on loopback"
                )
        elif isinstance(port, str):
            if ":" not in port:
                continue
            if not (port.startswith("127.0.0.1:") or port.startswith("[::1]:")):
                raise ContractError(
                    f"Compose service {service} may publish only on loopback"
                )
        else:
            raise ContractError(f"Compose service {service} has an invalid port mapping")


def _require_resources(config: Mapping[str, object], service: str) -> None:
    deploy = config.get("deploy")
    if not isinstance(deploy, Mapping):
        raise ContractError(f"Compose service {service} requires deploy resource limits")
    resources = deploy.get("resources")
    limits = resources.get("limits") if isinstance(resources, Mapping) else None
    if not isinstance(limits, Mapping):
        raise ContractError(f"Compose service {service} requires resource limits")
    cpus = limits.get("cpus")
    memory = limits.get("memory")
    try:
        valid_cpus = not isinstance(cpus, bool) and float(str(cpus)) > 0
    except (TypeError, ValueError):
        valid_cpus = False
    valid_memory = not isinstance(memory, bool) and bool(
        MEMORY_LIMIT.fullmatch(str(memory))
    )
    if not valid_cpus or not valid_memory:
        raise ContractError(f"Compose service {service} requires CPU and memory limits")


def _require_logging(config: Mapping[str, object], service: str) -> None:
    logging = config.get("logging")
    if not isinstance(logging, Mapping) or logging.get("driver") not in {"json-file", "local"}:
        raise ContractError(f"Compose service {service} requires bounded local logging")
    options = logging.get("options")
    if not isinstance(options, Mapping):
        raise ContractError(f"Compose service {service} requires log rotation limits")
    max_size = options.get("max-size")
    max_file = options.get("max-file")
    if (
        not isinstance(max_size, str)
        or not LOG_SIZE.fullmatch(max_size)
        or not str(max_file).isdigit()
        or int(str(max_file)) <= 0
    ):
        raise ContractError(f"Compose service {service} requires log rotation limits")


def _service_networks(config: Mapping[str, object], service: str) -> set[str]:
    value = config.get("networks")
    if isinstance(value, Mapping):
        result = {str(item) for item in value}
    elif isinstance(value, list):
        result = {str(item) for item in value}
    else:
        result = set()
    if not result:
        raise ContractError(f"Compose service {service} requires explicit networks")
    return result


def _labels(value: object, service: str) -> dict[str, str]:
    if isinstance(value, Mapping):
        return {str(key): str(item) for key, item in value.items()}
    if isinstance(value, list):
        result: dict[str, str] = {}
        for item in value:
            text = str(item)
            if "=" not in text:
                raise ContractError(f"Compose service {service} has an invalid label")
            key, nested = text.split("=", 1)
            if key in result:
                raise ContractError(f"Compose service {service} has duplicate labels")
            result[key] = nested
        return result
    raise ContractError(f"Compose service {service} requires release labels")


def _require_healthcheck(config: Mapping[str, object], service: str) -> None:
    healthcheck = config.get("healthcheck")
    if not isinstance(healthcheck, Mapping) or healthcheck.get("disable") is True:
        raise ContractError(f"runtime service {service} requires an enabled healthcheck")
    test = healthcheck.get("test")
    if not isinstance(test, list) or len(test) < 2:
        raise ContractError(f"runtime service {service} requires a healthcheck test")
