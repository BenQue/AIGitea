"""Allowlisted read-only inventory probes with no raw-output persistence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from .contract import (
    INVENTORY_VERSION,
    ROLE_TOOL_NAMES,
    ROLE_UNIT_NAMES,
    ROLES,
    CompanyDeliveryError,
    contains_sensitive_text,
    load_inventory,
)


Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]
Reader = Callable[[Path], str]
Clock = Callable[[], str]

SAFE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
OS_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")

TOOL_COMMANDS: dict[str, tuple[str, ...]] = {
    "act-runner": ("act_runner", "--version"),
    "docker-compose": ("docker", "compose", "version", "--short"),
    "docker-engine": ("docker", "version", "--format", "{{.Server.Version}}"),
    "git": ("git", "--version"),
    "gitea": ("gitea", "--version"),
    "nginx": ("nginx", "-v"),
    "postgresql-client": ("psql", "--version"),
    "python": ("python3", "--version"),
}

TOOL_VERSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "act-runner": re.compile(r"act_runner version v?([0-9]+\.[0-9]+\.[0-9]+)"),
    "docker-compose": re.compile(r"(?:Docker Compose version v?)?([0-9]+\.[0-9]+\.[0-9]+)"),
    "docker-engine": re.compile(r"([0-9]+\.[0-9]+\.[0-9]+)"),
    "git": re.compile(r"git version ([0-9]+\.[0-9]+\.[0-9]+)(?: \([A-Za-z0-9 ._-]+\))?"),
    "gitea": re.compile(r"Gitea version ([0-9]+\.[0-9]+\.[0-9]+)(?: built with [^\r\n]+)?"),
    "nginx": re.compile(r"nginx version: nginx/([0-9]+\.[0-9]+\.[0-9]+)(?: \([^\r\n]+\))?"),
    "postgresql-client": re.compile(r"psql \(PostgreSQL\) ([0-9]+\.[0-9]+(?:\.[0-9]+)?)(?: \([^\r\n]+\))?"),
    "python": re.compile(r"Python ([0-9]+\.[0-9]+\.[0-9]+)"),
}
OPTIONAL_SCM_TOOL_UNITS = {
    "act-runner": "act_runner.service",
    "gitea": "gitea.service",
}

ENABLED_STATES = {"enabled", "disabled", "masked", "static", "indirect"}
ACTIVE_STATES = {"active", "inactive", "failed", "activating", "deactivating", "maintenance"}


def collect_inventory(
    role: str,
    output: Path | str,
    *,
    runner: Runner | None = None,
    read_text: Reader | None = None,
    now: Clock | None = None,
) -> dict[str, object]:
    if role not in ROLES:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "role is outside the company delivery allowlist")
    output_path = Path(output)
    _require_new_protected_output(output_path)
    invoke = runner or _run
    read = read_text or _read_text
    clock = now or _utc_now
    pending: list[str] = []

    hostname = _probe(invoke, ["hostname"])
    hostname_sha = _fingerprint(hostname.stdout) if hostname.returncode == 0 else None
    if hostname_sha is None:
        pending.append("HOSTNAME_FINGERPRINT_UNAVAILABLE")

    try:
        machine_id = read(Path("/etc/machine-id"))
    except (OSError, KeyError):
        machine_id = ""
    machine_sha = _fingerprint(machine_id)
    if machine_sha is None:
        pending.append("MACHINE_ID_FINGERPRINT_UNAVAILABLE")

    try:
        os_release = _parse_os_release(read(Path("/etc/os-release")))
    except (OSError, KeyError):
        os_release = ("unknown", "unknown")
    if "unknown" in os_release:
        pending.append("OS_IDENTITY_UNAVAILABLE")

    kernel = _safe_version(_probe(invoke, ["uname", "-r"]).stdout)
    if kernel == "unknown":
        pending.append("KERNEL_VERSION_UNAVAILABLE")

    architecture = _architecture(_probe(invoke, ["uname", "-m"]).stdout)
    if architecture != "amd64":
        pending.append("ARCHITECTURE_UNSUPPORTED")

    cpu_count = _nonnegative_output(_probe(invoke, ["getconf", "_NPROCESSORS_ONLN"]))
    if cpu_count == 0:
        pending.append("CPU_COUNT_UNAVAILABLE")
    try:
        memory_bytes = _memory_bytes(read(Path("/proc/meminfo")))
    except (OSError, KeyError):
        memory_bytes = 0
    if memory_bytes == 0:
        pending.append("MEMORY_SIZE_UNAVAILABLE")
    root_free_bytes = _root_free_bytes(_probe(invoke, ["df", "-Pk", "/"]))
    if root_free_bytes == 0:
        pending.append("ROOT_FREE_SPACE_UNAVAILABLE")

    tools: list[dict[str, object]] = []
    for name in ROLE_TOOL_NAMES[role]:
        probe = _probe(invoke, list(TOOL_COMMANDS[name]))
        raw = (probe.stdout or "") + "\n" + (probe.stderr or "")
        if probe.missing:
            tools.append({"name": name, "status": "NOT RUN", "version": None, "reason": "command-missing"})
            pending.append("TOOL_PROBE_MISSING_" + name.upper().replace("-", "_"))
        elif probe.returncode != 0:
            tools.append({"name": name, "status": "BLOCKED", "version": None, "reason": "probe-failed"})
            pending.append("TOOL_PROBE_FAILED_" + name.upper().replace("-", "_"))
        elif contains_sensitive_text(raw):
            tools.append(
                {"name": name, "status": "BLOCKED", "version": None, "reason": "sensitive-output-rejected"}
            )
            pending.append("TOOL_OUTPUT_REJECTED_" + name.upper().replace("-", "_"))
        else:
            version = _tool_version(name, raw)
            if version is None:
                tools.append(
                    {"name": name, "status": "BLOCKED", "version": None, "reason": "version-output-unrecognized"}
                )
                pending.append("TOOL_VERSION_UNRECOGNIZED_" + name.upper().replace("-", "_"))
            else:
                tools.append({"name": name, "status": "PASS", "version": version, "reason": None})

    units: list[dict[str, str]] = []
    for unit in ROLE_UNIT_NAMES[role]:
        enabled = _unit_state(_probe(invoke, ["systemctl", "is-enabled", unit]), ENABLED_STATES)
        active = _unit_state(_probe(invoke, ["systemctl", "is-active", unit]), ACTIVE_STATES)
        units.append({"name": unit, "enabled": enabled, "active": active})
        if "unknown" in {enabled, active}:
            pending.append("UNIT_STATE_UNKNOWN_" + re.sub(r"[^A-Za-z0-9]", "_", unit).upper())
        if unit.endswith(".timer") and (enabled, active) not in {
            ("disabled", "inactive"),
            ("not-found", "not-found"),
        }:
            pending.append("SYNC_TIMER_MUST_REMAIN_DISABLED")

    if role == "scm-ci":
        tools_by_name = {str(item["name"]): item for item in tools}
        unit_states = {item["name"]: (item["enabled"], item["active"]) for item in units}
        for name, unit in OPTIONAL_SCM_TOOL_UNITS.items():
            tool = tools_by_name[name]
            unit_absent = unit_states[unit] == ("not-found", "not-found")
            if (
                tool["status"] == "NOT RUN"
                and tool["reason"] == "command-missing"
                and unit_absent
            ):
                tool["status"] = "ABSENT"
                tool["reason"] = "confirmed-not-installed"
                pending.remove("TOOL_PROBE_MISSING_" + name.upper().replace("-", "_"))
            elif tool["status"] == "PASS" and unit_absent:
                pending.append("TOOL_UNIT_STATE_CONFLICT_" + name.upper().replace("-", "_"))

    value: dict[str, object] = {
        "contract_version": INVENTORY_VERSION,
        "collector_version": _collector_version(),
        "collected_at": clock(),
        "role": role,
        "scope": "company-candidate",
        "outcome": "BLOCKED" if pending else "PASS",
        "host": {
            "hostname_sha256": hostname_sha,
            "machine_id_sha256": machine_sha,
            "os_id": os_release[0],
            "os_version": os_release[1],
            "kernel_version": kernel,
            "architecture": architecture,
            "cpu_count": cpu_count,
            "memory_bytes": memory_bytes,
            "root_free_bytes": root_free_bytes,
        },
        "tools": tools,
        "units": units,
        "pending": sorted(set(pending)),
    }
    _write_new_json(output_path, value)
    return load_inventory(output_path)


class _Probe:
    def __init__(self, returncode: int, stdout: str, stderr: str, *, missing: bool = False) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.missing = missing


def _probe(runner: Runner, argv: list[str]) -> _Probe:
    try:
        result = runner(argv)
    except subprocess.TimeoutExpired:
        return _Probe(124, "", "")
    except (FileNotFoundError, PermissionError, OSError):
        return _Probe(127, "", "", missing=True)
    return _Probe(int(result.returncode), str(result.stdout or ""), str(result.stderr or ""))


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
    }
    return subprocess.run(
        argv,
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
        env=environment,
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collector_version() -> str:
    source = Path(__file__).resolve()
    candidates = (
        source.parents[2] / "VERSION",
        source.parents[3] / "company-delivery/VERSION",
    )
    value = ""
    for version_path in candidates:
        try:
            value = version_path.read_text(encoding="ascii").strip()
            break
        except OSError:
            continue
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) is None:
        raise CompanyDeliveryError("RUNTIME_INVALID", "operator VERSION is invalid")
    return value


def _tool_version(name: str, value: str) -> str | None:
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        return None
    match = TOOL_VERSION_PATTERNS[name].fullmatch(normalized)
    if match is None:
        return None
    version = match.group(1)
    if name == "postgresql-client" and version.count(".") == 1:
        return version + ".0"
    return version


def _fingerprint(value: str) -> str | None:
    normalized = value.strip()
    if not normalized or len(normalized.encode("utf-8")) > 1024:
        return None
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _parse_os_release(value: str) -> tuple[str, str]:
    fields: dict[str, str] = {}
    for line in value.splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if key not in {"ID", "VERSION_ID"}:
            continue
        normalized = raw.strip().strip('"').strip("'")
        fields[key] = normalized
    os_id = fields.get("ID", "unknown")
    version = fields.get("VERSION_ID", "unknown")
    if OS_ID.fullmatch(os_id) is None:
        os_id = "unknown"
    if SAFE_VERSION.fullmatch(version) is None:
        version = "unknown"
    return os_id, version


def _safe_version(value: str) -> str:
    normalized = value.strip()
    if contains_sensitive_text(normalized) or SAFE_VERSION.fullmatch(normalized) is None:
        return "unknown"
    return normalized


def _architecture(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"x86_64", "amd64"}:
        return "amd64"
    if normalized in {"aarch64", "arm64"}:
        return "arm64"
    return "unknown"


def _nonnegative_output(probe: _Probe) -> int:
    value = probe.stdout.strip()
    if probe.returncode != 0 or re.fullmatch(r"[0-9]+", value) is None:
        return 0
    return int(value)


def _memory_bytes(value: str) -> int:
    for line in value.splitlines():
        match = re.fullmatch(r"MemTotal:\s+([0-9]+)\s+kB", line.strip())
        if match:
            return int(match.group(1)) * 1024
    return 0


def _root_free_bytes(probe: _Probe) -> int:
    if probe.returncode != 0:
        return 0
    lines = [line for line in probe.stdout.splitlines() if line.strip()]
    if len(lines) != 2:
        return 0
    fields = lines[1].split()
    if len(fields) < 4 or re.fullmatch(r"[0-9]+", fields[3]) is None:
        return 0
    return int(fields[3]) * 1024


def _unit_state(probe: _Probe, allowed: set[str]) -> str:
    value = probe.stdout.strip()
    if value in allowed:
        return value
    if probe.returncode == 4:
        return "not-found"
    return "unknown"


def _require_new_protected_output(path: Path) -> None:
    if not path.is_absolute():
        raise CompanyDeliveryError("UNSAFE_PATH", "inventory output path must be absolute")
    parent = path.parent
    try:
        parent_metadata = parent.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", "inventory output parent is unavailable") from exc
    if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "inventory output parent must be a non-symlink directory")
    if stat.S_IMODE(parent_metadata.st_mode) != 0o700:
        raise CompanyDeliveryError("UNSAFE_MODE", "inventory output parent mode must be 0700")
    if os.path.lexists(path):
        raise CompanyDeliveryError("UNSAFE_PATH", "inventory output must be a new file")


def _write_new_json(path: Path, value: object) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        try:
            path.unlink()
        except OSError:
            pass
        raise CompanyDeliveryError("OUTPUT_FAILED", "inventory output could not be written safely") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
