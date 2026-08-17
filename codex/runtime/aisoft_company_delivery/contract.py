"""Strict stdlib-only contracts for portable company delivery evidence."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping


INVENTORY_V1_VERSION = "company-delivery-inventory/v1"
INVENTORY_V2_VERSION = "company-delivery-inventory/v2"
# Current operator bytes produce v2. The v1 loader remains only so archived
# 1.0.1 evidence can be inspected; transition receipts only bind v2 identities.
INVENTORY_VERSION = INVENTORY_V2_VERSION
TRANSITION_VERSION = "company-delivery-gitea-transition/v1"
HANDOFF_VERSION = "company-delivery-handoff/v1"
EVIDENCE_VERSION = "company-delivery-evidence/v1"
RELEASE_VERSION = "docker-release/v2"

GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA256_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
FACT_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
MAX_JSON_BYTES = 2 * 1024 * 1024

OUTCOMES = {"PASS", "FAIL", "BLOCKED", "NOT RUN"}
ROLES = {"scm-ci", "appserver-prod"}
ROLE_TOOL_NAMES = {
    "scm-ci": ("act-runner", "docker-compose", "docker-engine", "git", "gitea", "python"),
    "appserver-prod": ("docker-compose", "docker-engine", "nginx", "postgresql-client", "python"),
}
ROLE_UNIT_NAMES = {
    "scm-ci": (
        "act_runner.service",
        "aisoft-inbound-sync@newemaint.timer",
        "docker.service",
        "gitea.service",
    ),
    "appserver-prod": ("docker.service", "nginx.service", "postgresql.service"),
}
STAGES = {"00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "110"}
SCOPES = {"local-fake", "company-scm-ci", "company-appserver-prod", "company-cross-host"}
STAGE_SCOPES = {
    "00": {"local-fake", "company-scm-ci"},
    "10": {"company-scm-ci", "company-appserver-prod"},
    "20": {"company-cross-host"},
    "30": {"company-scm-ci", "company-appserver-prod", "company-cross-host"},
    "40": {"company-scm-ci", "company-appserver-prod", "company-cross-host"},
    "50": {"company-scm-ci"},
    "60": {"company-scm-ci"},
    "70": {"company-scm-ci"},
    "80": {"company-scm-ci"},
    "90": {"company-appserver-prod"},
    "100": {"company-appserver-prod"},
    "110": {"company-scm-ci", "company-appserver-prod", "company-cross-host"},
}
TOOL_NAMES = {name for names in ROLE_TOOL_NAMES.values() for name in names}
TOOL_REASONS = {
    "command-missing",
    "confirmed-not-installed",
    "probe-failed",
    "sensitive-output-rejected",
    "version-output-unrecognized",
}
UNIT_NAMES = {name for names in ROLE_UNIT_NAMES.values() for name in names}
ENABLED_STATES = {"enabled", "disabled", "masked", "static", "indirect", "not-found", "unknown"}
ACTIVE_STATES = {
    "active",
    "inactive",
    "failed",
    "activating",
    "deactivating",
    "maintenance",
    "not-found",
    "unknown",
}

FIXED_GITEA_TARGET = {
    "gitea_version": "1.26.4",
    "gitea_artifact": "gitea-1.26.4-linux-amd64",
    "gitea_sha256": "0faa36d151918f8f7d6e0f3ae67597d1c338583d695add146ac393109d0fc44a",
    "postgresql_version": "18.4",
    "postgresql_provenance_artifact": "postgresql-18.4.tar.bz2",
    "postgresql_provenance_sha256": "81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094",
    "linux_user": "aisoft-gitea",
    "linux_group": "aisoft-gitea",
    "gitea_unit": "aisoft-gitea.service",
    "gitea_binary": "/opt/aisoft/gitea/1.26.4/gitea",
    "gitea_config": "/etc/aisoft/gitea/app.ini",
    "gitea_data": "/var/lib/aisoft-gitea",
    "gitea_log": "/var/log/aisoft-gitea",
    "postgresql_cluster": "aisoft-gitea",
    "postgresql_unit": "postgresql@18-aisoft-gitea.service",
    "postgresql_data": "/var/lib/postgresql/18/aisoft-gitea",
    "postgresql_database": "aisoft_gitea",
    "postgresql_role": "aisoft_gitea",
    "gitea_http": "127.0.0.1:3000",
    "postgresql_listen": "127.0.0.1:55432",
}

SCM_RESOURCE_KEYS = {
    "gitea_binary",
    "gitea_config",
    "gitea_data",
    "gitea_log",
    "postgresql_data",
}
SCM_AUTOMATION = {
    "gitea_ssh": "disabled",
    "runner": "disabled-inactive",
    "sync_timer": "disabled-inactive",
    "actions_auto_deploy": "disabled-inactive",
    "production_gate": "disabled-inactive",
    "dns_tls": "NOT RUN",
    "reverse_proxy": "NOT RUN",
    "repository_import": "NOT RUN",
}

SENSITIVE_KEYS = {
    "authorization",
    "connection_string",
    "credential",
    "database_url",
    "password",
    "private_key",
    "secret",
    "ssh_key",
    "token",
}
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)authorization\s*:\s*(?:bearer|token)\s+\S+"),
    re.compile(r"(?i)(?:password|passwd|pwd|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql|mongodb)://[^/\s:@]+:[^@\s]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
)


class CompanyDeliveryError(RuntimeError):
    """Machine-classifiable error whose text never contains rejected input."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.safe_message = message
        super().__init__(message)


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contains_sensitive_text(value: str) -> bool:
    """Return only a boolean; callers must never echo the rejected value."""

    return any(pattern.search(value) is not None for pattern in SENSITIVE_VALUE_PATTERNS)


def legacy_baseline_sha256(legacy: Mapping[str, object]) -> str:
    """Return the one canonical, no-raw legacy identity used by pre/post gates."""

    canonical = {
        key: legacy.get(key)
        for key in (
            "publish_port_sha256",
            "presence",
            "container_id_sha256",
            "health",
            "version",
        )
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_inventory(path: Path | str, *, require_protected: bool = True) -> dict[str, object]:
    value = _load_object(path, "inventory", require_protected=require_protected)
    _reject_sensitive(value)
    version = value.get("contract_version")
    if version == INVENTORY_V1_VERSION:
        return _load_inventory_v1(value)
    if version == INVENTORY_V2_VERSION:
        return _load_inventory_v2(value)
    raise CompanyDeliveryError("INVALID_CONTRACT", "inventory contract version is unsupported")


def _load_inventory_v1(value: dict[str, object]) -> dict[str, object]:
    _exact_keys(
        value,
        {
            "contract_version",
            "collector_version",
            "collected_at",
            "role",
            "scope",
            "outcome",
            "host",
            "tools",
            "units",
            "pending",
        },
        "inventory",
    )
    _const(value, "contract_version", INVENTORY_V1_VERSION, "inventory")
    _matching(value, "collector_version", SEMVER, "inventory")
    _timestamp(value, "collected_at", "inventory")
    role = _enum(value, "role", ROLES, "inventory")
    _const(value, "scope", "company-candidate", "inventory")
    outcome = _enum(value, "outcome", OUTCOMES, "inventory")

    host = _object(value, "host", "inventory")
    _exact_keys(
        host,
        {
            "hostname_sha256",
            "machine_id_sha256",
            "os_id",
            "os_version",
            "kernel_version",
            "architecture",
            "cpu_count",
            "memory_bytes",
            "root_free_bytes",
        },
        "inventory.host",
    )
    for key in ("hostname_sha256", "machine_id_sha256"):
        if host[key] is not None:
            _matching(host, key, SHA256_ID, "inventory.host")
    _matching(host, "os_id", re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$"), "inventory.host")
    _matching(host, "os_version", SAFE_VERSION, "inventory.host")
    _matching(host, "kernel_version", SAFE_VERSION, "inventory.host")
    _enum(host, "architecture", {"amd64", "arm64", "unknown"}, "inventory.host")
    for key in ("cpu_count", "memory_bytes", "root_free_bytes"):
        _nonnegative_integer(host, key, "inventory.host")

    tools = _array(value, "tools", "inventory")
    seen_tools: set[str] = set()
    tool_statuses: dict[str, str] = {}
    for index, item in enumerate(tools):
        label = f"inventory.tools[{index}]"
        tool = _mapping(item, label)
        _exact_keys(tool, {"name", "status", "version", "reason"}, label)
        name = _enum(tool, "name", TOOL_NAMES, label)
        if name in seen_tools:
            raise CompanyDeliveryError("INVALID_CONTRACT", "inventory contains a duplicate tool")
        seen_tools.add(name)
        status_value = _enum(tool, "status", {"PASS", "ABSENT", "BLOCKED", "NOT RUN"}, label)
        tool_statuses[name] = status_value
        version = tool["version"]
        reason = tool["reason"]
        if status_value == "PASS":
            if not isinstance(version, str) or SEMVER.fullmatch(version) is None or reason is not None:
                raise CompanyDeliveryError("INVALID_CONTRACT", "passing tool evidence requires semver and no reason")
        elif status_value == "ABSENT":
            if version is not None or reason != "confirmed-not-installed":
                raise CompanyDeliveryError(
                    "INVALID_CONTRACT", "absent tool evidence requires the fixed confirmed reason"
                )
        elif version is not None or reason not in TOOL_REASONS - {"confirmed-not-installed"}:
            raise CompanyDeliveryError("INVALID_CONTRACT", "non-passing tool evidence requires one fixed reason")

    units = _array(value, "units", "inventory")
    seen_units: set[str] = set()
    unit_states: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(units):
        label = f"inventory.units[{index}]"
        unit = _mapping(item, label)
        _exact_keys(unit, {"name", "enabled", "active"}, label)
        name = _enum(unit, "name", UNIT_NAMES, label)
        if name in seen_units:
            raise CompanyDeliveryError("INVALID_CONTRACT", "inventory contains a duplicate unit")
        seen_units.add(name)
        enabled = _enum(unit, "enabled", ENABLED_STATES, label)
        active = _enum(unit, "active", ACTIVE_STATES, label)
        unit_states[name] = (enabled, active)

    pending = _array(value, "pending", "inventory")
    for item in pending:
        if not isinstance(item, str) or FACT_CODE.fullmatch(item) is None:
            raise CompanyDeliveryError("INVALID_CONTRACT", "inventory pending codes are invalid")
    if len(pending) != len(set(pending)):
        raise CompanyDeliveryError("INVALID_CONTRACT", "inventory pending codes must be unique")
    expected_tools = set(ROLE_TOOL_NAMES[role])
    expected_units = set(ROLE_UNIT_NAMES[role])
    if outcome == "NOT RUN":
        if tools or units or not pending:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "NOT RUN inventory cannot claim tool or unit observations"
            )
        return value
    if seen_tools != expected_tools or seen_units != expected_units:
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "inventory must contain every role-specific tool and unit exactly once"
        )
    if outcome == "BLOCKED" and not pending:
        raise CompanyDeliveryError("INVALID_CONTRACT", "BLOCKED inventory requires pending reason codes")
    for tool_name, status in tool_statuses.items():
        if status != "ABSENT":
            continue
        unit_name = {
            "act-runner": "act_runner.service",
            "gitea": "gitea.service",
        }.get(tool_name)
        if role != "scm-ci" or unit_name is None or unit_states[unit_name] != ("not-found", "not-found"):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "ABSENT tool evidence requires a confirmed scm-ci unit absence"
            )
    if outcome == "PASS":
        complete_host = (
            host["hostname_sha256"] is not None
            and host["machine_id_sha256"] is not None
            and host["os_id"] != "unknown"
            and host["os_version"] != "unknown"
            and host["kernel_version"] != "unknown"
            and host["architecture"] == "amd64"
            and all(int(host[key]) > 0 for key in ("cpu_count", "memory_bytes", "root_free_bytes"))
        )
        known_units = all("unknown" not in states for states in unit_states.values())
        optional_absence_consistent = role != "scm-ci" or all(
            (tool_statuses[tool_name] == "ABSENT")
            == (unit_states[unit_name] == ("not-found", "not-found"))
            for tool_name, unit_name in {
                "act-runner": "act_runner.service",
                "gitea": "gitea.service",
            }.items()
        )
        timer_safe = unit_states.get(
            "aisoft-inbound-sync@newemaint.timer", ("disabled", "inactive")
        ) in {("disabled", "inactive"), ("not-found", "not-found")}
        if (
            pending
            or not complete_host
            or not known_units
            or not optional_absence_consistent
            or not timer_safe
            or any(status not in {"PASS", "ABSENT"} for status in tool_statuses.values())
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "PASS inventory requires complete passing facts and no pending codes"
            )
    return value


def _load_inventory_v2(value: dict[str, object]) -> dict[str, object]:
    _exact_keys(
        value,
        {
            "contract_version",
            "collector_version",
            "collected_at",
            "role",
            "scope",
            "outcome",
            "mode",
            "host",
            "tools",
            "units",
            "scm",
            "pending",
        },
        "inventory",
    )
    _const(value, "contract_version", INVENTORY_V2_VERSION, "inventory")

    common = {
        key: item
        for key, item in value.items()
        if key not in {"mode", "scm"}
    }
    common["contract_version"] = INVENTORY_V1_VERSION
    _load_inventory_v1(common)

    role = _enum(value, "role", ROLES, "inventory")
    outcome = _enum(value, "outcome", OUTCOMES, "inventory")
    if role == "appserver-prod":
        if value["mode"] is not None or value["scm"] is not None:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "appserver inventory must not contain SCM probe facts"
            )
        return value

    mode = _enum(value, "mode", {"preflight", "post-install"}, "inventory")
    scm = _mapping(value["scm"], "inventory.scm")
    _exact_keys(scm, {"probe_profile", "legacy", "candidate", "automation"}, "inventory.scm")
    _const(
        scm,
        "probe_profile",
        "greenfield-parallel-replacement-v1",
        "inventory.scm",
    )
    legacy = _validate_scm_legacy(_object(scm, "legacy", "inventory.scm"))
    candidate = _validate_scm_candidate(_object(scm, "candidate", "inventory.scm"))
    automation = _validate_scm_automation(_object(scm, "automation", "inventory.scm"))

    if legacy["health"] == "healthy":
        if legacy["baseline_sha256"] != legacy_baseline_sha256(legacy):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "healthy legacy facts require the canonical baseline fingerprint"
            )
    elif legacy["baseline_sha256"] is not None:
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "non-healthy legacy facts cannot claim a baseline fingerprint"
        )

    if outcome != "PASS":
        return value

    if (
        legacy["presence"] != "present"
        or legacy["health"] != "healthy"
        or legacy["version"] is None
        or legacy["container_id_sha256"] is None
        or legacy["publish_port_sha256"] is None
        or legacy["baseline_sha256"] is None
        or legacy["reason"] is not None
    ):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "PASS SCM inventory requires a healthy fingerprinted legacy instance"
        )
    if automation != SCM_AUTOMATION:
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "PASS SCM inventory requires every automation entry disabled"
        )

    ports = candidate["ports"]
    resources = candidate["resources"]
    services = candidate["services"]
    if mode == "preflight":
        if set(ports.values()) != {"free"}:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "preflight PASS requires both candidate ports free"
            )
        if any(state not in {"absent", "expected-empty"} for state in resources.values()):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "preflight PASS requires candidate resources absent or empty"
            )
        if any(
            state != {"enabled": "not-found", "active": "not-found"}
            for state in services.values()
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "preflight PASS requires candidate services absent"
            )
    else:
        if set(ports.values()) != {"occupied"}:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "post-install PASS requires both candidate ports occupied"
            )
        if set(resources.values()) != {"occupied"}:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "post-install PASS requires candidate resources occupied"
            )
        if any(
            state != {"enabled": "enabled", "active": "active"}
            for state in services.values()
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "post-install PASS requires candidate services enabled and active"
            )
    return value


def _validate_scm_legacy(value: Mapping[str, object]) -> Mapping[str, object]:
    _exact_keys(
        value,
        {
            "publish_port_sha256",
            "presence",
            "container_id_sha256",
            "health",
            "version",
            "baseline_sha256",
            "reason",
        },
        "inventory.scm.legacy",
    )
    for key in ("publish_port_sha256", "container_id_sha256", "baseline_sha256"):
        if value[key] is not None:
            _matching(value, key, SHA256_ID, "inventory.scm.legacy")
    presence = _enum(
        value,
        "presence",
        {"present", "absent", "ambiguous", "unknown"},
        "inventory.scm.legacy",
    )
    health = _enum(
        value,
        "health",
        {"healthy", "unhealthy", "not-run", "unknown"},
        "inventory.scm.legacy",
    )
    if value["version"] is not None:
        _matching(value, "version", SEMVER, "inventory.scm.legacy")
    reason = value["reason"]
    allowed_reasons = {
        "confirmed-absent",
        "multiple-containers",
        "malformed-container-id",
        "docker-probe-failed",
        "health-probe-failed",
        "version-unrecognized",
        "sensitive-output-rejected",
        "not-run",
    }
    if reason is not None and (not isinstance(reason, str) or reason not in allowed_reasons):
        raise CompanyDeliveryError("INVALID_CONTRACT", "legacy probe reason is outside the allowlist")
    if presence == "absent" and (
        value["container_id_sha256"] is not None
        or health != "not-run"
        or value["version"] is not None
        or value["baseline_sha256"] is not None
        or reason != "confirmed-absent"
    ):
        raise CompanyDeliveryError("INVALID_CONTRACT", "absent legacy facts are inconsistent")
    if presence == "present" and value["container_id_sha256"] is None:
        raise CompanyDeliveryError("INVALID_CONTRACT", "present legacy facts require a container fingerprint")
    if health == "healthy" and (presence != "present" or value["version"] is None):
        raise CompanyDeliveryError("INVALID_CONTRACT", "healthy legacy facts require present semver evidence")
    return value


def _validate_scm_candidate(value: Mapping[str, object]) -> dict[str, dict[str, object]]:
    _exact_keys(value, {"ports", "resources", "services"}, "inventory.scm.candidate")
    ports = _object(value, "ports", "inventory.scm.candidate")
    _exact_keys(ports, {"gitea_http", "postgresql"}, "inventory.scm.candidate.ports")
    for key in ports:
        _enum(ports, key, {"free", "occupied", "unknown"}, "inventory.scm.candidate.ports")

    resources = _object(value, "resources", "inventory.scm.candidate")
    _exact_keys(resources, SCM_RESOURCE_KEYS, "inventory.scm.candidate.resources")
    for key in resources:
        _enum(
            resources,
            key,
            {"absent", "expected-empty", "occupied", "unsafe", "unknown"},
            "inventory.scm.candidate.resources",
        )

    services = _object(value, "services", "inventory.scm.candidate")
    _exact_keys(services, {"gitea", "postgresql"}, "inventory.scm.candidate.services")
    parsed_services: dict[str, dict[str, str]] = {}
    for key in services:
        service = _mapping(services[key], f"inventory.scm.candidate.services.{key}")
        _exact_keys(service, {"enabled", "active"}, f"inventory.scm.candidate.services.{key}")
        parsed_services[key] = {
            "enabled": _enum(
                service,
                "enabled",
                ENABLED_STATES,
                f"inventory.scm.candidate.services.{key}",
            ),
            "active": _enum(
                service,
                "active",
                ACTIVE_STATES,
                f"inventory.scm.candidate.services.{key}",
            ),
        }
    return {
        "ports": dict(ports),
        "resources": dict(resources),
        "services": parsed_services,
    }


def _validate_scm_automation(value: Mapping[str, object]) -> dict[str, str]:
    _exact_keys(value, set(SCM_AUTOMATION), "inventory.scm.automation")
    parsed: dict[str, str] = {}
    for key, required in SCM_AUTOMATION.items():
        parsed[key] = _enum(
            value,
            key,
            {required, "unknown", "NOT RUN"},
            "inventory.scm.automation",
        )
    return parsed


def load_gitea_transition(
    path: Path | str,
    *,
    require_protected: bool = True,
) -> dict[str, object]:
    value = _load_object(path, "Gitea transition", require_protected=require_protected)
    _reject_sensitive(value)
    _exact_keys(
        value,
        {
            "contract_version",
            "operator_version",
            "recorded_at",
            "source_git_sha",
            "reviewer_decision_id",
            "decision",
            "outcome",
            "inventories",
            "public_name_sha256",
            "legacy_baseline_sha256",
            "target",
            "prerequisites",
            "automation",
            "stages",
            "pending",
        },
        "Gitea transition",
    )
    _const(value, "contract_version", TRANSITION_VERSION, "Gitea transition")
    _const(value, "operator_version", "1.1.0", "Gitea transition")
    _timestamp(value, "recorded_at", "Gitea transition")
    _matching(value, "source_git_sha", GIT_SHA, "Gitea transition")
    _matching(value, "reviewer_decision_id", SAFE_ID, "Gitea transition")
    decision = _enum(
        value,
        "decision",
        {"greenfield-parallel-replacement", "controlled-upgrade-candidate", "BLOCKED"},
        "Gitea transition",
    )
    outcome = _enum(value, "outcome", {"PASS", "BLOCKED"}, "Gitea transition")

    inventories = _object(value, "inventories", "Gitea transition")
    _exact_keys(
        inventories,
        {"scm_ci_sha256", "appserver_prod_sha256"},
        "Gitea transition.inventories",
    )
    for key in inventories:
        _matching(inventories, key, SHA256, "Gitea transition.inventories")
    _matching(value, "public_name_sha256", SHA256_ID, "Gitea transition")
    if value["legacy_baseline_sha256"] is not None:
        _matching(value, "legacy_baseline_sha256", SHA256_ID, "Gitea transition")

    target = _object(value, "target", "Gitea transition")
    _exact_keys(target, set(FIXED_GITEA_TARGET), "Gitea transition.target")
    if dict(target) != FIXED_GITEA_TARGET:
        raise CompanyDeliveryError("INVALID_CONTRACT", "Gitea target identity has drifted")

    prerequisites = _object(value, "prerequisites", "Gitea transition")
    _exact_keys(
        prerequisites,
        {"legacy_backup_required", "isolated_restore_required", "stage50_prerequisite"},
        "Gitea transition.prerequisites",
    )
    backup_required = _boolean(
        prerequisites, "legacy_backup_required", "Gitea transition.prerequisites"
    )
    restore_required = _boolean(
        prerequisites, "isolated_restore_required", "Gitea transition.prerequisites"
    )
    stage50_prerequisite = _enum(
        prerequisites,
        "stage50_prerequisite",
        {"legacy-pre-post-equality", "stage-30-40-pass", "not-authorized"},
        "Gitea transition.prerequisites",
    )
    automation = _object(value, "automation", "Gitea transition")
    _exact_keys(automation, set(SCM_AUTOMATION), "Gitea transition.automation")
    if dict(automation) != SCM_AUTOMATION:
        raise CompanyDeliveryError("INVALID_CONTRACT", "transition automation gates must stay disabled")

    stages = _object(value, "stages", "Gitea transition")
    stage_keys = {"00", "10-scm-ci", "10-appserver-prod", "20", "30", "40", "50"}
    _exact_keys(stages, stage_keys, "Gitea transition.stages")
    for key in stages:
        _enum(stages, key, OUTCOMES, "Gitea transition.stages")
    pending = _array(value, "pending", "Gitea transition")
    if any(not isinstance(item, str) or FACT_CODE.fullmatch(item) is None for item in pending):
        raise CompanyDeliveryError("INVALID_CONTRACT", "transition pending codes are invalid")
    if len(pending) != len(set(pending)):
        raise CompanyDeliveryError("INVALID_CONTRACT", "transition pending codes must be unique")

    stage20_pass = {
        "00": "PASS",
        "10-scm-ci": "PASS",
        "10-appserver-prod": "PASS",
        "20": "PASS",
        "30": "NOT RUN",
        "40": "NOT RUN",
        "50": "NOT RUN",
    }
    if decision == "greenfield-parallel-replacement":
        if (
            outcome != "PASS"
            or dict(stages) != stage20_pass
            or value["legacy_baseline_sha256"] is None
            or pending
            or backup_required
            or restore_required
            or stage50_prerequisite != "legacy-pre-post-equality"
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "greenfield transition prerequisites or stage map are invalid"
            )
    elif decision == "controlled-upgrade-candidate":
        if (
            outcome != "PASS"
            or dict(stages) != stage20_pass
            or pending
            or not backup_required
            or not restore_required
            or stage50_prerequisite != "stage-30-40-pass"
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "controlled upgrade must retain backup and restore prerequisites"
            )
    elif (
        outcome != "BLOCKED"
        or not pending
        or stages["20"] != "BLOCKED"
        or any(stages[key] != "NOT RUN" for key in ("30", "40", "50"))
        or backup_required
        or restore_required
        or stage50_prerequisite != "not-authorized"
    ):
        raise CompanyDeliveryError("INVALID_CONTRACT", "blocked transition facts are inconsistent")
    return value


def verify_gitea_transition(
    transition_path: Path | str,
    scm_inventory_path: Path | str,
    appserver_inventory_path: Path | str,
) -> dict[str, object]:
    transition = load_gitea_transition(transition_path)
    if transition["outcome"] != "PASS":
        raise CompanyDeliveryError("TRANSITION_BLOCKED", "Gitea transition is not approved to continue")
    inventories = _object(transition, "inventories", "Gitea transition")
    scm_inventory, scm_sha256 = _load_stable_inventory(
        scm_inventory_path,
        "scm-ci inventory",
        expected_sha256=_string(inventories, "scm_ci_sha256", "Gitea transition.inventories"),
    )
    appserver_inventory, appserver_sha256 = _load_stable_inventory(
        appserver_inventory_path,
        "appserver-prod inventory",
        expected_sha256=_string(
            inventories,
            "appserver_prod_sha256",
            "Gitea transition.inventories",
        ),
    )
    if (
        scm_inventory["contract_version"] != INVENTORY_V2_VERSION
        or scm_inventory["role"] != "scm-ci"
        or scm_inventory["outcome"] != "PASS"
        or scm_inventory["mode"] != "preflight"
        or not isinstance(scm_inventory["scm"], Mapping)
    ):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "transition requires a passing scm-ci preflight inventory v2"
        )
    if (
        appserver_inventory["contract_version"] != INVENTORY_V2_VERSION
        or appserver_inventory["role"] != "appserver-prod"
        or appserver_inventory["outcome"] != "PASS"
        or appserver_inventory["mode"] is not None
        or appserver_inventory["scm"] is not None
    ):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "transition requires a passing appserver-prod inventory v2"
        )
    legacy = _object(
        _mapping(scm_inventory["scm"], "inventory.scm"),
        "legacy",
        "inventory.scm",
    )
    if legacy["baseline_sha256"] != transition["legacy_baseline_sha256"]:
        raise CompanyDeliveryError(
            "CHECKSUM_MISMATCH", "transition legacy baseline does not match the scm-ci inventory"
        )
    return {
        "contract_version": TRANSITION_VERSION,
        "decision": transition["decision"],
        "outcome": "PASS",
        "legacy_baseline_sha256": transition["legacy_baseline_sha256"],
        "scm_inventory_sha256": scm_sha256,
        "appserver_inventory_sha256": appserver_sha256,
    }


def verify_legacy_health(
    transition_path: Path | str,
    post_inventory_path: Path | str,
) -> dict[str, object]:
    transition = load_gitea_transition(transition_path)
    if (
        transition["decision"] != "greenfield-parallel-replacement"
        or transition["outcome"] != "PASS"
    ):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "legacy equality is only a greenfield Stage 50 prerequisite"
        )
    post_inventory, post_sha256 = _load_stable_inventory(
        post_inventory_path,
        "post-install scm-ci inventory",
    )
    if (
        post_inventory["contract_version"] != INVENTORY_V2_VERSION
        or post_inventory["role"] != "scm-ci"
        or post_inventory["outcome"] != "PASS"
        or post_inventory["mode"] != "post-install"
        or not isinstance(post_inventory["scm"], Mapping)
    ):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "legacy equality requires a passing post-install scm-ci inventory v2"
        )
    legacy = _object(
        _mapping(post_inventory["scm"], "inventory.scm"),
        "legacy",
        "inventory.scm",
    )
    if (
        legacy["presence"] != "present"
        or legacy["health"] != "healthy"
        or legacy["version"] is None
        or legacy["baseline_sha256"] != transition["legacy_baseline_sha256"]
    ):
        raise CompanyDeliveryError(
            "LEGACY_INVARIANT_FAILED", "legacy Gitea pre/post health identity has changed"
        )
    return {
        "contract_version": TRANSITION_VERSION,
        "decision": "greenfield-parallel-replacement",
        "legacy_invariant": "PASS",
        "post_inventory_sha256": post_sha256,
        "stages_30_40": "NOT RUN",
    }


def _load_stable_inventory(
    path: Path | str,
    label: str,
    *,
    expected_sha256: str | None = None,
) -> tuple[dict[str, object], str]:
    source = Path(path)
    before = _protected_file_sha256(source, label)
    value = load_inventory(source)
    after = _protected_file_sha256(source, label)
    if before != after:
        raise CompanyDeliveryError("CHECKSUM_MISMATCH", f"{label} changed during verification")
    if expected_sha256 is not None and after != expected_sha256:
        raise CompanyDeliveryError("CHECKSUM_MISMATCH", f"{label} checksum does not match the transition")
    return value, after


def _protected_file_sha256(path: Path, label: str) -> str:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", f"{label} is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", f"{label} must be a regular non-symlink file")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise CompanyDeliveryError("UNSAFE_MODE", f"{label} mode must be 0600")
    try:
        return sha256_file(path)
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", f"{label} is unavailable") from exc


def load_evidence(path: Path | str, *, require_protected: bool = True) -> dict[str, object]:
    value = _load_object(path, "evidence", require_protected=require_protected)
    _reject_sensitive(value)
    _exact_keys(
        value,
        {
            "contract_version",
            "evidence_id",
            "stage",
            "scope",
            "recorded_at",
            "operator_version",
            "source_git_sha",
            "release_id",
            "outcome",
            "observed",
            "changed",
            "verified",
            "pending",
        },
        "evidence",
    )
    _const(value, "contract_version", EVIDENCE_VERSION, "evidence")
    _matching(value, "evidence_id", SAFE_ID, "evidence")
    stage = _enum(value, "stage", STAGES, "evidence")
    scope = _enum(value, "scope", SCOPES, "evidence")
    if scope not in STAGE_SCOPES[stage]:
        raise CompanyDeliveryError("INVALID_CONTRACT", "evidence stage and scope are incompatible")
    _timestamp(value, "recorded_at", "evidence")
    _matching(value, "operator_version", SEMVER, "evidence")
    _matching(value, "source_git_sha", GIT_SHA, "evidence")
    if value["release_id"] is not None:
        _matching(value, "release_id", GIT_SHA, "evidence")
    outcome = _enum(value, "outcome", OUTCOMES, "evidence")
    section_statuses: dict[str, list[str]] = {}
    for section in ("observed", "changed", "verified", "pending"):
        facts = _array(value, section, "evidence")
        statuses: list[str] = []
        for index, item in enumerate(facts):
            statuses.append(
                _validate_fact(
                    _mapping(item, f"evidence.{section}[{index}]"),
                    f"evidence.{section}[{index}]",
                )
            )
        section_statuses[section] = statuses
    _validate_evidence_outcome(outcome, section_statuses)
    return value


def load_handoff(
    path: Path | str,
    *,
    bundle_root: Path | str | None,
    verify_payloads: bool = True,
    require_protected: bool = True,
) -> dict[str, object]:
    value = _load_object(path, "handoff manifest", require_protected=require_protected)
    _reject_sensitive(value)
    _exact_keys(
        value,
        {"contract_version", "operator_version", "created_at", "source", "release", "compatibility", "payloads"},
        "handoff manifest",
    )
    _const(value, "contract_version", HANDOFF_VERSION, "handoff manifest")
    _matching(value, "operator_version", SEMVER, "handoff manifest")
    _timestamp(value, "created_at", "handoff manifest")

    source = _object(value, "source", "handoff manifest")
    _exact_keys(source, {"repository", "git_sha", "transport"}, "handoff.source")
    _matching(source, "repository", REPOSITORY, "handoff.source")
    _matching(source, "git_sha", GIT_SHA, "handoff.source")
    _enum(source, "transport", {"approved-bundle", "allowlisted-github-ref"}, "handoff.source")

    release = _object(value, "release", "handoff manifest")
    _exact_keys(
        release,
        {"contract_version", "release_id", "manifest_path", "manifest_sha256", "platform", "transport"},
        "handoff.release",
    )
    _const(release, "contract_version", RELEASE_VERSION, "handoff.release")
    _matching(release, "release_id", GIT_SHA, "handoff.release")
    _relative_path(_string(release, "manifest_path", "handoff.release"))
    _matching(release, "manifest_sha256", SHA256, "handoff.release")
    _const(release, "platform", "linux/amd64", "handoff.release")
    _const(release, "transport", "offline-bundle", "handoff.release")

    compatibility = _object(value, "compatibility", "handoff manifest")
    _exact_keys(compatibility, {"matrix_path", "matrix_sha256", "required_roles"}, "handoff.compatibility")
    _relative_path(_string(compatibility, "matrix_path", "handoff.compatibility"))
    _matching(compatibility, "matrix_sha256", SHA256, "handoff.compatibility")
    roles = _array(compatibility, "required_roles", "handoff.compatibility")
    if roles != ["scm-ci", "appserver-prod"]:
        raise CompanyDeliveryError("INVALID_CONTRACT", "handoff required role sequence is invalid")

    payloads = _array(value, "payloads", "handoff manifest")
    if not payloads:
        raise CompanyDeliveryError("INVALID_CONTRACT", "handoff payloads must not be empty")
    parsed: list[tuple[str, str, int, str]] = []
    for index, item in enumerate(payloads):
        label = f"handoff.payloads[{index}]"
        payload = _mapping(item, label)
        _exact_keys(payload, {"path", "sha256", "size_bytes", "mode"}, label)
        relative = _relative_path(_string(payload, "path", label))
        digest = _matching(payload, "sha256", SHA256, label)
        size = _nonnegative_integer(payload, "size_bytes", label)
        mode = _enum(payload, "mode", {"0600", "0644", "0755"}, label)
        parsed.append((relative, digest, size, mode))
    paths = [item[0] for item in parsed]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise CompanyDeliveryError("INVALID_CONTRACT", "handoff payload paths must be unique and sorted")

    if verify_payloads:
        if bundle_root is None:
            raise CompanyDeliveryError("INVALID_CONTRACT", "handoff payload verification requires a bundle root")
        root = Path(bundle_root)
        manifest_path = Path(path)
        try:
            if manifest_path.resolve() != (root.resolve() / "handoff-manifest.json"):
                raise CompanyDeliveryError("UNSAFE_PATH", "handoff manifest must use the fixed bundle path")
        except OSError as exc:
            raise CompanyDeliveryError("UNSAFE_PATH", "handoff manifest path is unavailable") from exc
        _verify_payloads(root, parsed)
        by_path = {relative: digest for relative, digest, _size, _mode in parsed}
        if by_path.get(str(release["manifest_path"])) != release["manifest_sha256"]:
            raise CompanyDeliveryError("CHECKSUM_MISMATCH", "release manifest identity does not match payloads")
        if by_path.get(str(compatibility["matrix_path"])) != compatibility["matrix_sha256"]:
            raise CompanyDeliveryError("CHECKSUM_MISMATCH", "compatibility identity does not match payloads")
        _verify_checksum_manifest(root, manifest_path, parsed)
    return value


def _validate_fact(value: Mapping[str, object], label: str) -> str:
    _exact_keys(value, {"code", "status", "detail", "artifacts"}, label)
    _matching(value, "code", FACT_CODE, label)
    status_value = _enum(value, "status", OUTCOMES, label)
    detail = _string(value, "detail", label)
    if not detail or len(detail.encode("utf-8")) > 512 or "\n" in detail or "\r" in detail:
        raise CompanyDeliveryError("INVALID_CONTRACT", "evidence detail must be one bounded line")
    artifacts = _array(value, "artifacts", label)
    for artifact in artifacts:
        if not isinstance(artifact, str):
            raise CompanyDeliveryError("INVALID_CONTRACT", "evidence artifact reference must be a string")
        _relative_path(artifact)
    if len(artifacts) != len(set(artifacts)):
        raise CompanyDeliveryError("INVALID_CONTRACT", "evidence artifact references must be unique")
    return status_value


def _validate_evidence_outcome(outcome: str, sections: Mapping[str, list[str]]) -> None:
    observed = sections["observed"]
    changed = sections["changed"]
    verified = sections["verified"]
    pending = sections["pending"]
    completed = observed + changed + verified

    if any(status != "PASS" for status in changed):
        raise CompanyDeliveryError("INVALID_CONTRACT", "changed evidence facts must be PASS")
    if outcome == "PASS":
        if pending or not completed or any(status != "PASS" for status in completed):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "PASS evidence requires only completed PASS facts and no pending facts"
            )
        return
    if outcome == "FAIL":
        if (
            any(status not in {"PASS", "FAIL"} for status in completed)
            or "FAIL" not in completed
            or any(status not in {"BLOCKED", "NOT RUN"} for status in pending)
        ):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "FAIL evidence requires a completed FAIL fact and bounded pending states"
            )
        return
    if outcome == "BLOCKED":
        if any(status != "PASS" for status in completed):
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "BLOCKED evidence must keep completed facts at PASS"
            )
        if not pending or any(status not in {"BLOCKED", "NOT RUN"} for status in pending) or "BLOCKED" not in pending:
            raise CompanyDeliveryError(
                "INVALID_CONTRACT", "BLOCKED evidence requires at least one pending BLOCKED fact"
            )
        return
    if completed or not pending or any(status != "NOT RUN" for status in pending):
        raise CompanyDeliveryError(
            "INVALID_CONTRACT", "NOT RUN evidence requires only pending NOT RUN facts"
        )


def _verify_payloads(root: Path, payloads: list[tuple[str, str, int, str]]) -> None:
    try:
        metadata = root.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", "bundle root is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "bundle root must be a non-symlink directory")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise CompanyDeliveryError("UNSAFE_MODE", "bundle root mode must be 0700")
    resolved_root = root.resolve()
    for relative, expected_sha, expected_size, expected_mode in payloads:
        target = root / relative
        current = target.parent
        while current != root:
            try:
                parent_metadata = current.lstat()
            except OSError as exc:
                raise CompanyDeliveryError("PAYLOAD_MISSING", "handoff payload parent is missing") from exc
            if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
                raise CompanyDeliveryError(
                    "UNSAFE_PATH", "handoff payload parent must be a non-symlink directory"
                )
            if stat.S_IMODE(parent_metadata.st_mode) != 0o700:
                raise CompanyDeliveryError("UNSAFE_MODE", "handoff payload parent mode must be 0700")
            current = current.parent
        try:
            target_metadata = target.lstat()
        except OSError as exc:
            raise CompanyDeliveryError("PAYLOAD_MISSING", "handoff payload is missing") from exc
        if stat.S_ISLNK(target_metadata.st_mode) or not stat.S_ISREG(target_metadata.st_mode):
            raise CompanyDeliveryError("UNSAFE_PATH", "handoff payload must be a regular non-symlink file")
        try:
            target.resolve().relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            raise CompanyDeliveryError("UNSAFE_PATH", "handoff payload escapes bundle root") from exc
        if target_metadata.st_size != expected_size:
            raise CompanyDeliveryError("CHECKSUM_MISMATCH", "handoff payload size does not match")
        actual_mode = f"{stat.S_IMODE(target_metadata.st_mode):04o}"
        if actual_mode != expected_mode:
            raise CompanyDeliveryError("UNSAFE_MODE", "handoff payload mode does not match")
        if sha256_file(target) != expected_sha:
            raise CompanyDeliveryError("CHECKSUM_MISMATCH", "handoff payload checksum does not match")


def _verify_checksum_manifest(
    root: Path,
    manifest_path: Path,
    payloads: list[tuple[str, str, int, str]],
) -> None:
    checksum_path = root / "SHA256SUMS"
    try:
        metadata = checksum_path.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("PAYLOAD_MISSING", "SHA256SUMS is missing") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "SHA256SUMS must be a regular non-symlink file")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise CompanyDeliveryError("UNSAFE_MODE", "SHA256SUMS mode must be 0600")
    if metadata.st_size > MAX_JSON_BYTES:
        raise CompanyDeliveryError("INVALID_CONTRACT", "SHA256SUMS exceeds the size limit")
    try:
        lines = checksum_path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CompanyDeliveryError("INVALID_CONTRACT", "SHA256SUMS must be bounded ASCII") from exc
    parsed: list[tuple[str, str]] = []
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._@/-]+)", line)
        if match is None:
            raise CompanyDeliveryError("INVALID_CONTRACT", "SHA256SUMS contains an invalid line")
        relative = _relative_path(match.group(2))
        if relative == "SHA256SUMS":
            raise CompanyDeliveryError("INVALID_CONTRACT", "SHA256SUMS must not hash itself")
        parsed.append((relative, match.group(1)))
    expected = {relative: digest for relative, digest, _size, _mode in payloads}
    expected["handoff-manifest.json"] = sha256_file(manifest_path)
    actual = dict(parsed)
    if len(actual) != len(parsed) or [item[0] for item in parsed] != sorted(actual):
        raise CompanyDeliveryError("INVALID_CONTRACT", "SHA256SUMS paths must be unique and sorted")
    if actual != expected:
        raise CompanyDeliveryError("CHECKSUM_MISMATCH", "SHA256SUMS does not match the handoff inventory")
    for relative, digest in parsed:
        if sha256_file(root / relative) != digest:
            raise CompanyDeliveryError("CHECKSUM_MISMATCH", "SHA256SUMS payload checksum does not match")


def _load_object(path: Path | str, label: str, *, require_protected: bool) -> dict[str, object]:
    source = Path(path)
    try:
        metadata = source.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", f"{label} is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", f"{label} must be a regular non-symlink file")
    if require_protected and stat.S_IMODE(metadata.st_mode) != 0o600:
        raise CompanyDeliveryError("UNSAFE_MODE", f"{label} mode must be 0600")
    if metadata.st_size > MAX_JSON_BYTES:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label} exceeds the size limit")
    try:
        text = source.read_text(encoding="utf-8")
        value = json.loads(text, object_pairs_hook=_no_duplicates)
    except CompanyDeliveryError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompanyDeliveryError("INVALID_JSON", f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label} must be a JSON object")
    return value


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise CompanyDeliveryError("INVALID_JSON", "JSON contains a duplicate key")
        value[key] = item
    return value


def _reject_sensitive(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS:
                raise CompanyDeliveryError("SENSITIVE_CONTENT", "document contains a forbidden sensitive field")
            _reject_sensitive(item)
    elif isinstance(value, list):
        for item in value:
            _reject_sensitive(item)
    elif isinstance(value, str):
        if contains_sensitive_text(value):
            raise CompanyDeliveryError("SENSITIVE_CONTENT", "document contains forbidden sensitive content")


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label} fields do not match the strict contract")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label} must be an object")
    return value


def _object(value: Mapping[str, object], key: str, label: str) -> Mapping[str, object]:
    return _mapping(value.get(key), f"{label}.{key}")


def _array(value: Mapping[str, object], key: str, label: str) -> list[object]:
    item = value.get(key)
    if not isinstance(item, list):
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be an array")
    return item


def _string(value: Mapping[str, object], key: str, label: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be a string")
    return item


def _matching(value: Mapping[str, object], key: str, pattern: re.Pattern[str], label: str) -> str:
    item = _string(value, key, label)
    if pattern.fullmatch(item) is None:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} has an invalid format")
    return item


def _enum(value: Mapping[str, object], key: str, allowed: set[str], label: str) -> str:
    item = _string(value, key, label)
    if item not in allowed:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} is outside the allowlist")
    return item


def _const(value: Mapping[str, object], key: str, expected: str, label: str) -> None:
    if _string(value, key, label) != expected:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} has the wrong contract value")


def _timestamp(value: Mapping[str, object], key: str, label: str) -> str:
    item = _string(value, key, label)
    try:
        parsed = datetime.strptime(item, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be canonical UTC") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != item:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be canonical UTC")
    return item


def _nonnegative_integer(value: Mapping[str, object], key: str, label: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int) or item < 0:
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be a non-negative integer")
    return item


def _boolean(value: Mapping[str, object], key: str, label: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise CompanyDeliveryError("INVALID_CONTRACT", f"{label}.{key} must be a boolean")
    return item


def _relative_path(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise CompanyDeliveryError("UNSAFE_PATH", "path is not a safe POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CompanyDeliveryError("UNSAFE_PATH", "path is not a safe POSIX relative path")
    if str(path) != value or len(value.encode("utf-8")) > 512:
        raise CompanyDeliveryError("UNSAFE_PATH", "path is not canonical or exceeds the limit")
    if re.fullmatch(r"[A-Za-z0-9._@/-]+", value) is None:
        raise CompanyDeliveryError("UNSAFE_PATH", "path contains unsupported characters")
    return value
