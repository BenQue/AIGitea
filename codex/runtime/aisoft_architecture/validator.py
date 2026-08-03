"""Semantic validation for catalogs, profiles and project declarations."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from .errors import fail
from .schema import validate_schema

REVISION_RE = re.compile(r"^\d{4}\.\d{2}\.\d+$")
EXACT_VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z._+-]*(?:@[0-9A-Za-z._+-]+)?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ISSUE_RE = re.compile(r"^(?:https://[^\s]+/issues/[1-9][0-9]*|#[1-9][0-9]*)$")
ALLOWED_STATES = {"preferred", "supported", "sunset", "prohibited"}


def _as_date(value: str, path: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        fail("DATE_INVALID", "日期必须为有效的 YYYY-MM-DD。", path)


def _as_optional_date(value: str | None, path: str) -> date | None:
    if value is None:
        return None
    return _as_date(value, path)


def _component_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, component in enumerate(catalog["components"]):
        component_id = component["id"]
        if component_id in result:
            fail("CATALOG_COMPONENT_DUPLICATE", "Catalog component ID 重复。", f"$.components[{index}].id")
        result[component_id] = component
    return result


def validate_catalog(catalog: dict[str, Any], schema: dict[str, Any], today: date) -> dict[str, dict[str, Any]]:
    validate_schema(catalog, schema)
    if not REVISION_RE.fullmatch(catalog["revision"]):
        fail("CATALOG_REVISION_INVALID", "Catalog revision 必须为 YYYY.MM.N。", "$.revision")
    if _as_date(catalog["published_at"], "$.published_at") > today:
        fail("CATALOG_FROM_FUTURE", "Catalog published_at 不得晚于校验日期。", "$.published_at")
    if _as_date(catalog["review_by"], "$.review_by") < today:
        fail("CATALOG_REVIEW_OVERDUE", "Catalog 已超过 review_by。", "$.review_by")
    components = _component_map(catalog)
    for index, component in enumerate(catalog["components"]):
        base = f"$.components[{index}]"
        if component["state"] not in ALLOWED_STATES:
            fail("COMPONENT_STATE_UNKNOWN", "Component state 未知。", f"{base}.state")
        if not EXACT_VERSION_RE.fullmatch(component["version"]):
            fail("VERSION_NOT_EXACT", "Component version 必须是精确 pin。", f"{base}.version")
        if any(marker in component["version"].lower() for marker in ("latest", "^", "~", "*", ">", "<")):
            fail("VERSION_NOT_EXACT", "禁止 latest 或 semver range。", f"{base}.version")
        pin = component["pin"]
        if any(marker in pin["value"].lower() for marker in ("latest", "^", "~", "*", ">", "<")):
            fail("PIN_NOT_IMMUTABLE", "Pin value 不得使用 latest 或 range。", f"{base}.pin.value")
        if pin["strategy"] == "oci-digest" and not DIGEST_RE.fullmatch(pin["value"]):
            fail("OCI_DIGEST_REQUIRED", "OCI identity 必须包含 sha256 digest。", f"{base}.pin.value")
        lifecycle = component["lifecycle"]
        released = _as_optional_date(lifecycle["released_at"], f"{base}.lifecycle.released_at")
        support_end = _as_optional_date(lifecycle["support_end"], f"{base}.lifecycle.support_end")
        eol = _as_optional_date(lifecycle["eol"], f"{base}.lifecycle.eol")
        migrate_by = _as_optional_date(lifecycle["migrate_by"], f"{base}.lifecycle.migrate_by")
        if support_end is not None and released is not None and support_end < released:
            fail("LIFECYCLE_DATE_ORDER", "Lifecycle 日期顺序无效。", f"{base}.lifecycle")
        if eol is not None and support_end is not None and eol < support_end:
            fail("LIFECYCLE_DATE_ORDER", "Lifecycle 日期顺序无效。", f"{base}.lifecycle")
        if migrate_by is not None and eol is not None and migrate_by > eol:
            fail("MIGRATION_AFTER_EOL", "migrate_by 不得晚于 EOL。", f"{base}.lifecycle.migrate_by")
        if component["state"] == "sunset" and (eol is None or migrate_by is None):
            fail("SUNSET_DATES_REQUIRED", "Sunset component 必须声明 migrate_by 和 EOL。", f"{base}.lifecycle")
        provenance = component["provenance"]
        if not provenance["source_url"].startswith("https://"):
            fail("SOURCE_NOT_OFFICIAL_HTTPS", "Source 必须是 HTTPS upstream/official URL。", f"{base}.provenance.source_url")
        retrieved = _as_date(provenance["retrieved_at"], f"{base}.provenance.retrieved_at")
        review_by = _as_date(provenance["review_by"], f"{base}.provenance.review_by")
        if retrieved > today:
            fail("SOURCE_FROM_FUTURE", "Source retrieved_at 不得晚于校验日期。", f"{base}.provenance.retrieved_at")
        if review_by < today:
            fail("SOURCE_REVIEW_OVERDUE", "Official source 已超过 review_by。", f"{base}.provenance.review_by")
        if review_by < retrieved:
            fail("SOURCE_REVIEW_ORDER", "Source review_by 不得早于 retrieved_at。", f"{base}.provenance.review_by")
    return components


def validate_profile(
    profile: dict[str, Any],
    schema: dict[str, Any],
    catalog: dict[str, Any],
    components: dict[str, dict[str, Any]],
) -> None:
    validate_schema(profile, schema)
    if profile["catalog_revision"] != catalog["revision"]:
        fail("PROFILE_CATALOG_MISMATCH", "Profile catalog_revision 与 Catalog 不一致。", "$.catalog_revision")
    seen: set[str] = set()
    for index, requirement in enumerate(profile["required_components"]):
        component_id = requirement["component_id"]
        if component_id in seen:
            fail("PROFILE_COMPONENT_DUPLICATE", "Profile component 重复。", f"$.required_components[{index}]")
        seen.add(component_id)
        if component_id not in components:
            fail("PROFILE_COMPONENT_UNKNOWN", "Profile 引用了未知 component。", f"$.required_components[{index}].component_id")
        if components[component_id]["state"] not in requirement["allowed_states"]:
            fail("PROFILE_COMPONENT_STATE", "Profile 不允许该 component state。", f"$.required_components[{index}].allowed_states")


def _validate_exception(exception: dict[str, Any], today: date, path: str) -> None:
    if _as_date(exception["expires_at"], f"{path}.expires_at") <= today:
        fail("EXCEPTION_EXPIRED", "Architecture exception 已到期。", f"{path}.expires_at")
    if not ISSUE_RE.fullmatch(exception["migration_issue"]):
        fail("EXCEPTION_MIGRATION_ISSUE_INVALID", "Exception 必须引用 migration Issue。", f"{path}.migration_issue")


def validate_project(
    project: dict[str, Any],
    project_schema: dict[str, Any],
    profile: dict[str, Any],
    catalog: dict[str, Any],
    components: dict[str, dict[str, Any]],
    today: date,
) -> None:
    validate_schema(project, project_schema)
    if project["catalog_revision"] != catalog["revision"]:
        fail("PROJECT_CATALOG_MISMATCH", "Project catalog_revision 与 Catalog 不一致。", "$.catalog_revision")
    if project["profile_id"] != profile["profile_id"] or project["profile_version"] != profile["version"]:
        fail("PROJECT_PROFILE_MISMATCH", "Project profile identity 与所选 Profile 不一致。", "$.profile_id")
    if project["delivery_contract"] not in profile["delivery_contracts"]:
        fail("DELIVERY_CONTRACT_INCOMPATIBLE", "Delivery contract 不被 Profile 允许。", "$.delivery_contract")
    declared: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(project["components"]):
        component_id = item["component_id"]
        path = f"$.components[{index}]"
        if component_id in declared:
            fail("PROJECT_COMPONENT_DUPLICATE", "Project component 重复。", f"{path}.component_id")
        if component_id not in components:
            fail("PROJECT_COMPONENT_UNKNOWN", "Project 声明了未知 component。", f"{path}.component_id")
        component = components[component_id]
        if item["version"] != component["version"]:
            fail("PROJECT_VERSION_DRIFT", "Project version 与 pinned Catalog 不一致。", f"{path}.version")
        if component["pin"]["strategy"] == "oci-digest":
            if item.get("digest") != component["pin"]["value"] or not DIGEST_RE.fullmatch(item.get("digest", "")):
                fail("OCI_DIGEST_REQUIRED", "OCI component 必须声明 Catalog 中的不可变 digest。", f"{path}.digest")
        elif "digest" in item:
            fail("OCI_DIGEST_UNEXPECTED", "非 OCI component 不得声明 digest。", f"{path}.digest")
        state = component["state"]
        if state == "prohibited":
            fail("COMPONENT_PROHIBITED", "Project 使用了 prohibited component。", f"{path}.component_id")
        component_eol = _as_optional_date(component["lifecycle"]["eol"], f"{path}.lifecycle.eol")
        if component_eol is not None and component_eol <= today:
            fail("COMPONENT_EOL", "Project component 已到 EOL。", f"{path}.component_id")
        if state == "sunset" and not item.get("migration_issue"):
            fail("SUNSET_MIGRATION_REQUIRED", "Sunset component 必须引用 migration Issue。", f"{path}.migration_issue")
        if item.get("migration_issue") and not ISSUE_RE.fullmatch(item["migration_issue"]):
            fail("MIGRATION_ISSUE_INVALID", "migration_issue 格式无效。", f"{path}.migration_issue")
        declared[component_id] = item
    for requirement in profile["required_components"]:
        if requirement["component_id"] not in declared:
            fail("PROFILE_COMPONENT_MISSING", "Project 缺少 Profile 必需 component。", "$.components")
    exception_components: set[str] = set()
    for index, exception in enumerate(project["exceptions"]):
        _validate_exception(exception, today, f"$.exceptions[{index}]")
        component_id = exception["component_id"]
        if component_id not in declared:
            fail("EXCEPTION_COMPONENT_UNKNOWN", "Exception component 未在 Project 中声明。", f"$.exceptions[{index}].component_id")
        if component_id in exception_components:
            fail("EXCEPTION_COMPONENT_DUPLICATE", "同一 component 不得有多个有效 exception。", f"$.exceptions[{index}]")
        exception_components.add(component_id)
