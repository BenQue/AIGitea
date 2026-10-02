"""Deterministic architecture lock generation and drift validation."""

from __future__ import annotations

from datetime import date
from typing import Any

from .errors import fail
from .jsonio import sha256_value
from .schema import validate_schema
from .validator import validate_catalog, validate_profile, validate_project


LOCK_SCHEMA_FILENAMES = {
    "1.0": "architecture-lock-v1.schema.json",
    "2.0": "architecture-lock-v2.schema.json",
}
PROFILE_CHECKSUM_CONTRACT = "profile-machine-v1"


def lock_schema_filename(schema_version: Any) -> str:
    """Resolve only known formats; never use untrusted input as a path."""
    if not isinstance(schema_version, str) or schema_version not in LOCK_SCHEMA_FILENAMES:
        fail("LOCK_SCHEMA_VERSION_UNSUPPORTED", "不支持该 lock schema_version。", "$.schema_version")
    return LOCK_SCHEMA_FILENAMES[schema_version]


def _profile_checksum(profile: dict[str, Any], schema_version: str) -> str:
    if schema_version == "1.0":
        return sha256_value(profile)
    machine_profile = {
        key: value for key, value in profile.items()
        if key not in {"description", "compatibility_rules"}
    }
    return sha256_value({"hash_contract": PROFILE_CHECKSUM_CONTRACT, "profile": machine_profile})


def build_lock(
    catalog: dict[str, Any],
    catalog_schema: dict[str, Any],
    profile: dict[str, Any],
    profile_schema: dict[str, Any],
    project: dict[str, Any],
    project_schema: dict[str, Any],
    today: date,
    *,
    schema_version: str = "2.0",
) -> dict[str, Any]:
    # V1 is retained for the strict legacy reader and compatibility tests only.
    schema_filename = lock_schema_filename(schema_version)
    components = validate_catalog(catalog, catalog_schema, today)
    validate_profile(profile, profile_schema, catalog, components)
    validate_project(project, project_schema, profile, catalog, components, today)
    exceptions_by_component = {
        exception["component_id"]: exception for exception in project["exceptions"]
    }
    resolved = []
    for declared in sorted(project["components"], key=lambda item: item["component_id"]):
        component = components[declared["component_id"]]
        as_built = bool(declared.get("as_built"))
        item: dict[str, Any] = {
            "component_id": component["id"],
            "version": declared["version"] if as_built else component["version"],
            "state": component["state"],
            "source_url": component["provenance"]["source_url"],
        }
        if "digest" in declared:
            item["digest"] = declared["digest"]
        if "migration_issue" in declared:
            item["migration_issue"] = declared["migration_issue"]
        exception = exceptions_by_component.get(declared["component_id"])
        if exception is not None:
            item["exception_id"] = exception["id"]
            item["exception_expires_at"] = exception["expires_at"]
        resolved.append(item)
    lock: dict[str, Any] = {
        "$schema": f"./architecture/schemas/{schema_filename}",
        "schema_version": schema_version,
        "project_id": project["project_id"],
        "profile_id": profile["profile_id"],
        "profile_version": profile["version"],
        "catalog_revision": catalog["revision"],
        "delivery_contract": project["delivery_contract"],
        "resolved_components": resolved,
        "exception_ids": sorted(exception["id"] for exception in project["exceptions"]),
        "source_checksums": {
            "catalog_sha256": sha256_value(catalog),
            "profile_sha256": _profile_checksum(profile, schema_version),
            "declaration_sha256": sha256_value(project),
        },
    }
    if schema_version == "2.0":
        lock["profile_checksum_contract"] = PROFILE_CHECKSUM_CONTRACT
    lock["lock_sha256"] = sha256_value(lock)
    return lock


def validate_lock(lock: dict[str, Any], lock_schema: dict[str, Any], expected: dict[str, Any]) -> None:
    validate_schema(lock, lock_schema)
    actual_hash = lock.get("lock_sha256")
    payload = dict(lock)
    payload.pop("lock_sha256", None)
    if actual_hash != sha256_value(payload):
        fail("LOCK_CHECKSUM_TAMPERED", "architecture.lock.json checksum 无效。", "$.lock_sha256")
    if lock != expected:
        fail("LOCK_DRIFT", "architecture.lock.json 与当前输入不一致。", "$", "重新运行 lock 并提交 canonical 输出。")
