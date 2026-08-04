"""Docker/Compose subprocess adapter with fixed argv and non-disclosing failures."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Mapping, Sequence

from .compatibility import (
    CompatibilityDecision,
    DockerCapability,
    require_supported,
)
from .errors import DeploymentError


MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_METADATA_OUTPUT_BYTES = 64 * 1024


class DockerAdapter:
    """Only fixed Docker operations used by the release state machine."""

    def __init__(
        self,
        executable: str = "docker",
        *,
        compatibility_path: Path | str | None = None,
    ) -> None:
        self.executable = executable
        self.compatibility_path = compatibility_path

    def assert_runtime_compatible(self) -> CompatibilityDecision:
        return require_supported(self.detect_capability(), self.compatibility_path)

    def detect_capability(self) -> DockerCapability:
        server = self._json_object(
            [
                self.executable,
                "version",
                "--format",
                "{{json .Server}}",
            ],
            None,
            "Docker server version detection",
            max_output_bytes=MAX_METADATA_OUTPUT_BYTES,
        )
        engine_version = _exact_version(server.get("Version"), "Docker Engine")
        os_name = server.get("Os")
        architecture = server.get("Arch")
        if os_name != "linux" or architecture != "amd64":
            raise DeploymentError("Docker server must report exact linux/amd64")
        compose_raw = self._run(
            [self.executable, "compose", "version", "--short"],
            None,
            "Docker Compose version detection",
            max_output_bytes=MAX_METADATA_OUTPUT_BYTES,
        ).strip()
        compose_version = _exact_version(compose_raw.removeprefix("v"), "Docker Compose")
        driver_raw = self._run(
            [self.executable, "info", "--format", "{{.Driver}}"],
            None,
            "Docker image driver detection",
            max_output_bytes=MAX_METADATA_OUTPUT_BYTES,
        ).strip()
        driver_status = self._json_value(
            [
                self.executable,
                "info",
                "--format",
                "{{json .DriverStatus}}",
            ],
            None,
            "Docker image-store detection",
            max_output_bytes=MAX_METADATA_OUTPUT_BYTES,
        )
        image_store = _normalize_image_store(driver_raw, driver_status)
        return DockerCapability(
            engine_version=engine_version,
            compose_version=compose_version,
            os=str(os_name),
            architecture=str(architecture),
            image_store=image_store,
        )

    def compose_config(self, compose_path: Path, project: str) -> Mapping[str, object]:
        args = self._compose_base(compose_path, project) + [
            "config",
            "--format",
            "json",
            "--no-interpolate",
            "--no-env-resolution",
        ]
        return self._json_object(args, compose_path.parent, "compose config validation")

    def pull_image(self, reference: str) -> None:
        self._run(
            [self.executable, "image", "pull", reference],
            None,
            "immutable image pull",
        )

    def tag_image(self, source_reference: str, target_reference: str) -> None:
        self._run(
            [self.executable, "image", "tag", source_reference, target_reference],
            None,
            "release-scoped image tag",
        )

    def save_images(self, references: Sequence[str], archive_path: Path) -> None:
        if not references:
            raise DeploymentError("offline image save requires at least one reference")
        if archive_path.exists() or archive_path.is_symlink():
            raise DeploymentError("offline image save refuses to overwrite an archive path")
        if not archive_path.parent.is_dir() or archive_path.parent.is_symlink():
            raise DeploymentError("offline image save parent directory is invalid")
        self._run(
            [
                self.executable,
                "image",
                "save",
                "--output",
                str(archive_path),
                *references,
            ],
            archive_path.parent,
            "offline image save",
        )

    def load_archive(self, archive_path: Path) -> None:
        self._run(
            [self.executable, "image", "load", "--input", str(archive_path)],
            archive_path.parent,
            "offline image load",
        )

    def inspect_image(self, reference: str) -> Mapping[str, object]:
        return self._json_object(
            [
                self.executable,
                "image",
                "inspect",
                "--format",
                "{{json .}}",
                reference,
            ],
            None,
            "image identity inspection",
        )

    def run_migration(
        self,
        compose_path: Path,
        project: str,
        env_file: Path,
        service: str,
    ) -> None:
        args = self._compose_base(compose_path, project, env_file) + [
            "run",
            "--rm",
            "--no-deps",
            "--pull",
            "never",
            service,
        ]
        self._run(args, compose_path.parent, "migration service")

    def compose_up(
        self,
        compose_path: Path,
        project: str,
        env_file: Path,
        wait_timeout_seconds: int,
    ) -> None:
        args = self._compose_base(compose_path, project, env_file) + [
            "up",
            "--detach",
            "--wait",
            "--wait-timeout",
            str(wait_timeout_seconds),
            "--pull",
            "never",
            "--no-build",
            "--remove-orphans",
        ]
        self._run(args, compose_path.parent, "compose up wait")

    def container_ids(
        self,
        compose_path: Path,
        project: str,
        env_file: Path,
        service: str,
    ) -> tuple[str, ...]:
        args = self._compose_base(compose_path, project, env_file) + [
            "ps",
            "--quiet",
            service,
        ]
        raw = self._run(args, compose_path.parent, "compose container lookup")
        identifiers = tuple(line.strip() for line in raw.splitlines() if line.strip())
        for identifier in identifiers:
            if not identifier.isalnum() or len(identifier) > 128:
                raise DeploymentError("compose returned an invalid container identifier")
        return identifiers

    def inspect_container(self, container_id: str) -> Mapping[str, object]:
        return self._json_object(
            [
                self.executable,
                "container",
                "inspect",
                "--format",
                "{{json .}}",
                container_id,
            ],
            None,
            "container identity inspection",
        )

    def _compose_base(
        self, compose_path: Path, project: str, env_file: Path | None = None
    ) -> list[str]:
        args = [
            self.executable,
            "compose",
            "--project-name",
            project,
            "--file",
            str(compose_path),
        ]
        if env_file is not None:
            args.extend(["--env-file", str(env_file)])
        return args

    def _json_object(
        self,
        args: Sequence[str],
        cwd: Path | None,
        operation: str,
        *,
        max_output_bytes: int = MAX_OUTPUT_BYTES,
    ) -> Mapping[str, object]:
        value = self._json_value(
            args,
            cwd,
            operation,
            max_output_bytes=max_output_bytes,
        )
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], Mapping):
            value = value[0]
        if not isinstance(value, Mapping):
            raise DeploymentError(f"{operation} did not return a JSON object")
        return value

    def _json_value(
        self,
        args: Sequence[str],
        cwd: Path | None,
        operation: str,
        *,
        max_output_bytes: int = MAX_OUTPUT_BYTES,
    ) -> object:
        raw = self._run(args, cwd, operation, max_output_bytes=max_output_bytes)
        try:
            value = json.loads(raw, object_pairs_hook=_unique_object)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DeploymentError(f"{operation} returned invalid JSON") from exc
        return value

    def _run(
        self,
        args: Sequence[str],
        cwd: Path | None,
        operation: str,
        *,
        max_output_bytes: int = MAX_OUTPUT_BYTES,
    ) -> str:
        if not args or any(not isinstance(item, str) or "\x00" in item for item in args):
            raise DeploymentError("Docker adapter received invalid fixed arguments")
        try:
            completed = subprocess.run(
                list(args),
                cwd=cwd,
                env=_docker_environment(),
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                shell=False,
            )
        except OSError as exc:
            raise DeploymentError(f"{operation} could not start") from exc
        if (
            len(completed.stdout) > max_output_bytes
            or len(completed.stderr) > max_output_bytes
        ):
            raise DeploymentError(f"{operation} exceeded the bounded output limit")
        if completed.returncode != 0:
            # Docker/Compose can echo interpolated values in errors. Never include
            # stdout, stderr or the full argv in a caller-visible exception.
            raise DeploymentError(
                f"{operation} failed with exit code {completed.returncode}"
            )
        try:
            return completed.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DeploymentError(f"{operation} returned non-UTF-8 output") from exc


def _docker_environment() -> dict[str, str]:
    allowed = {
        "DOCKER_CONFIG",
        "DOCKER_CONTEXT",
        "DOCKER_HOST",
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TMPDIR",
        "XDG_RUNTIME_DIR",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _exact_version(value: object, product: str) -> str:
    if not isinstance(value, str):
        raise DeploymentError(f"{product} version output is missing")
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise DeploymentError(f"{product} version output is not exact major.minor.patch")
    return value


def _normalize_image_store(driver: str, status: object) -> str:
    if status is None:
        entries: list[object] = []
    elif isinstance(status, list):
        entries = status
    else:
        raise DeploymentError("Docker DriverStatus output is invalid")
    driver_types: list[str] = []
    for entry in entries:
        if (
            not isinstance(entry, list)
            or len(entry) != 2
            or not all(isinstance(item, str) for item in entry)
        ):
            raise DeploymentError("Docker DriverStatus output is invalid")
        if entry[0] == "driver-type":
            driver_types.append(entry[1])
    if driver_types == ["io.containerd.snapshotter.v1"] and driver == "overlayfs":
        return "containerd"
    if not driver_types and driver == "overlay2":
        return "classic"
    raise DeploymentError("Docker image store is unknown, ambiguous, or conflicting")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result
