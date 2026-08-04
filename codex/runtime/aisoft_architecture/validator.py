"""Semantic validation for catalogs, profiles and project declarations."""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urlsplit

from .errors import fail
from .schema import validate_schema

REVISION_RE = re.compile(r"^\d{4}\.\d{2}\.\d+$")
EXACT_VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z._+-]*(?:@[0-9A-Za-z._+-]+)?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ISSUE_RE = re.compile(r"^(?:https://[^\s]+/issues/[1-9][0-9]*|#[1-9][0-9]*)$")
ABSOLUTE_ISSUE_PATH_RE = re.compile(r"^/.+/issues/[1-9][0-9]*$")
ALLOWED_STATES = {"preferred", "supported", "sunset", "prohibited"}
MAX_EXCEPTION_DAYS = 180


def _as_date(value: str, path: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        fail("DATE_INVALID", "日期必须为有效的 YYYY-MM-DD。", path)


def _as_optional_date(value: str | None, path: str) -> date | None:
    if value is None:
        return None
    return _as_date(value, path)


def _is_absolute_issue_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.hostname
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and ABSOLUTE_ISSUE_PATH_RE.fullmatch(parsed.path)
    )


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
    preferred_ids: set[str] = set()
    for index, requirement in enumerate(profile["required_components"]):
        component_id = requirement["component_id"]
        if component_id in preferred_ids:
            fail("PROFILE_COMPONENT_DUPLICATE", "Profile component 重复。", f"$.required_components[{index}]")
        preferred_ids.add(component_id)
        if component_id not in components:
            fail("PROFILE_COMPONENT_UNKNOWN", "Profile 引用了未知 component。", f"$.required_components[{index}].component_id")
        if (
            components[component_id]["state"] != "preferred"
            or requirement["allowed_states"] != ["preferred"]
        ):
            fail("PROFILE_COMPONENT_STATE", "Profile 不允许该 component state。", f"$.required_components[{index}].allowed_states")
    transition_ids: set[str] = set()
    for index, requirement in enumerate(profile["required_components"]):
        preferred_id = requirement["component_id"]
        preferred = components[preferred_id]
        for transition_index, transition in enumerate(requirement.get("transitions", [])):
            path = f"$.required_components[{index}].transitions[{transition_index}]"
            transition_id = transition["component_id"]
            if transition_id in preferred_ids:
                fail(
                    "PROFILE_TRANSITION_CONFLICT",
                    "Transition component 不得同时作为 preferred slot component。",
                    f"{path}.component_id",
                )
            if transition_id in transition_ids:
                fail(
                    "PROFILE_TRANSITION_DUPLICATE",
                    "Transition component 在 Profile 中重复。",
                    f"{path}.component_id",
                )
            transition_ids.add(transition_id)
            if transition_id not in components:
                fail(
                    "PROFILE_TRANSITION_UNKNOWN",
                    "Profile transition 引用了未知 component。",
                    f"{path}.component_id",
                )
            candidate = components[transition_id]
            if candidate["category"] != preferred["category"]:
                fail(
                    "PROFILE_TRANSITION_CATEGORY",
                    "Transition component 必须与 preferred component 同 category。",
                    f"{path}.component_id",
                )
            if (
                candidate["state"] not in {"supported", "sunset"}
                or candidate["state"] not in transition["allowed_states"]
            ):
                fail(
                    "PROFILE_TRANSITION_STATE",
                    "Profile transition 不允许该 component state。",
                    f"{path}.allowed_states",
                )


def _validate_exception(
    exception: dict[str, Any],
    component: dict[str, Any],
    today: date,
    path: str,
) -> None:
    created_at = _as_date(exception["created_at"], f"{path}.created_at")
    expires_at = _as_date(exception["expires_at"], f"{path}.expires_at")
    if expires_at <= today:
        fail("EXCEPTION_EXPIRED", "Architecture exception 已到期。", f"{path}.expires_at")
    if created_at > today:
        fail("EXCEPTION_FROM_FUTURE", "Architecture exception created_at 不得晚于校验日期。", f"{path}.created_at")
    if expires_at <= created_at:
        fail("EXCEPTION_DATE_ORDER", "Architecture exception expires_at 必须晚于 created_at。", f"{path}.expires_at")
    if (expires_at - created_at).days > MAX_EXCEPTION_DAYS:
        fail(
            "EXCEPTION_DURATION_EXCEEDED",
            "Architecture exception 有效期不得超过 180 天。",
            f"{path}.expires_at",
        )
    migrate_by = _as_optional_date(
        component["lifecycle"]["migrate_by"], f"{path}.component.migrate_by"
    )
    if migrate_by is not None and expires_at > migrate_by:
        fail(
            "EXCEPTION_AFTER_MIGRATE_BY",
            "Architecture exception 不得晚于 component migrate_by。",
            f"{path}.expires_at",
        )
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
    exception_ids: set[str] = set()
    exception_components: set[str] = set()
    exceptions_by_component: dict[str, dict[str, Any]] = {}
    for index, exception in enumerate(project["exceptions"]):
        path = f"$.exceptions[{index}]"
        component_id = exception["component_id"]
        if component_id not in declared:
            fail("EXCEPTION_COMPONENT_UNKNOWN", "Exception component 未在 Project 中声明。", f"$.exceptions[{index}].component_id")
        if exception["id"] in exception_ids:
            fail("EXCEPTION_ID_DUPLICATE", "Architecture exception ID 重复。", f"{path}.id")
        exception_ids.add(exception["id"])
        if component_id in exception_components:
            fail("EXCEPTION_COMPONENT_DUPLICATE", "同一 component 不得有多个有效 exception。", f"$.exceptions[{index}]")
        exception_components.add(component_id)
        _validate_exception(exception, components[component_id], today, path)
        exceptions_by_component[component_id] = exception

    selected_transitions: set[str] = set()
    for requirement in profile["required_components"]:
        preferred_id = requirement["component_id"]
        transition_ids = [
            transition["component_id"]
            for transition in requirement.get("transitions", [])
        ]
        selected = [
            component_id
            for component_id in [preferred_id, *transition_ids]
            if component_id in declared
        ]
        if not selected:
            fail("PROFILE_COMPONENT_MISSING", "Project 缺少 Profile 必需 component。", "$.components")
        if len(selected) > 1:
            fail(
                "PROFILE_COMPONENT_AMBIGUOUS",
                "Project 为同一 Profile slot 声明了多个 component。",
                "$.components",
            )
        selected_id = selected[0]
        if selected_id == preferred_id:
            continue
        selected_transitions.add(selected_id)
        migration_issue = declared[selected_id].get("migration_issue")
        if not migration_issue:
            fail(
                "TRANSITION_MIGRATION_REQUIRED",
                "Transition component 必须引用独立 migration Issue。",
                "$.components",
            )
        if not _is_absolute_issue_url(migration_issue):
            fail(
                "TRANSITION_MIGRATION_ISSUE_INVALID",
                "Transition migration Issue 必须是绝对 HTTPS Issue URL。",
                "$.components",
            )
        exception = exceptions_by_component.get(selected_id)
        if exception is None:
            fail(
                "TRANSITION_EXCEPTION_REQUIRED",
                "Transition component 必须有且只有一个有效 exception。",
                "$.exceptions",
            )
        if exception["migration_issue"] != migration_issue:
            fail(
                "TRANSITION_EXCEPTION_MIGRATION_MISMATCH",
                "Transition component 与 exception 必须引用同一 migration Issue。",
                "$.exceptions",
            )

    for component_id, exception in exceptions_by_component.items():
        if component_id in selected_transitions:
            continue
        if components[component_id]["state"] == "sunset":
            if declared[component_id].get("migration_issue") != exception["migration_issue"]:
                fail(
                    "EXCEPTION_MIGRATION_MISMATCH",
                    "Sunset component 与 exception 必须引用同一 migration Issue。",
                    "$.exceptions",
                )
            continue
        fail(
            "EXCEPTION_NOT_REQUIRED",
            "Preferred/supported non-transition component 不得携带 architecture exception。",
            "$.exceptions",
        )

    for component_id, item in declared.items():
        if (
            components[component_id]["state"] == "sunset"
            and component_id not in exceptions_by_component
        ):
            fail(
                "SUNSET_EXCEPTION_REQUIRED",
                "Sunset component 必须有有效 architecture exception。",
                "$.exceptions",
            )
