"""Strict stdlib-only contracts for portable company delivery evidence."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping


INVENTORY_VERSION = "company-delivery-inventory/v1"
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


def load_inventory(path: Path | str, *, require_protected: bool = True) -> dict[str, object]:
    value = _load_object(path, "inventory", require_protected=require_protected)
    _reject_sensitive(value)
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
    _const(value, "contract_version", INVENTORY_VERSION, "inventory")
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
