"""Restricted parser and deterministic routing for analyzer classifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ClassificationError(ValueError):
    """Raised when analyzer output does not satisfy the fixed contract."""


FULL_FIELDS = (
    "change_type",
    "requested_complexity",
    "assessed_complexity",
    "effective_complexity",
    "contract_effect",
    "reason",
    "risk_flags",
    "required_docs",
    "confidence",
    "override_reason",
)
UNCLEAR_FIELDS = tuple(name for name in FULL_FIELDS if name != "effective_complexity")
LIST_FIELDS = frozenset({"risk_flags", "required_docs"})
DOCUMENT_ROLES = ("summary", "spec", "plan", "verification")
LEGACY_DOCUMENTS = (
    "00-summary.md",
    "01-spec.md",
    "02-plan.md",
    "03-verification.md",
)
ALLOWED_DOCS = frozenset(DOCUMENT_ROLES + LEGACY_DOCUMENTS)

# The closed type taxonomy, without the label prefix. contract.TYPE_LABELS is
# derived from this so the analyzer contract and the label projector can never
# drift apart, and test_contract.py pins both to the canonical manifest (#108).
CHANGE_TYPES = frozenset(
    {
        "bugfix",
        "feature",
        "docs",
        "test",
        "refactor",
        "maintenance",
        "platform",
        "security",
        "reliability",
        "data",
    }
)
# Types that mean "complex" by their own definition, independent of any
# risk_flags the analyzer may or may not have emitted.
FORCED_COMPLEX_TYPES = frozenset({"feature", "platform", "security", "data"})
FORCED_COMPLEX_RISKS = frozenset(
    {
        "functional-change",
        "schema-change",
        "data-migration",
        "external-contract",
        "authentication",
        "authorization",
        "security",
        "shared-core",
        "cross-module",
        "cross-service",
        "ci-integration",
        "ci-change",
        "artifact",
        "deployment",
        "deployment-boundary",
        "rollback",
        "agent-governance",
        "platform-governance",
    }
)


@dataclass(frozen=True)
class Route:
    effective_complexity: Optional[str]
    lifecycle_label: str
    complexity_label: Optional[str]
    required_docs: tuple[str, ...]
    override_reason: str = ""


@dataclass(frozen=True)
class Classification:
    change_type: str
    requested_complexity: str
    assessed_complexity: str
    effective_complexity: Optional[str]
    contract_effect: str
    reason: str
    risk_flags: tuple[str, ...]
    required_docs: tuple[str, ...]
    confidence: str
    override_reason: str

    @classmethod
    def from_yaml(cls, text: str) -> "Classification":
        values, order = _parse_restricted_yaml(text)
        assessed = _require_scalar(values, "assessed_complexity")
        contract_effect = _require_scalar(values, "contract_effect")
        effective = values.get("effective_complexity")
        if assessed == "needs-human-decision" or contract_effect == "unclear":
            if effective is not None:
                raise ClassificationError(
                    "needs-human-decision and unclear results must omit effective_complexity"
                )
        elif effective is None:
            raise ClassificationError("safe classification requires effective_complexity")

        expected_order = (
            UNCLEAR_FIELDS
            if assessed == "needs-human-decision" or contract_effect == "unclear"
            else FULL_FIELDS
        )
        if tuple(order) != expected_order:
            raise ClassificationError(
                "fields must use the canonical order; "
                f"expected {expected_order}, got {tuple(order)}"
            )

        classification = cls(
            change_type=_require_scalar(values, "change_type"),
            requested_complexity=_require_scalar(values, "requested_complexity"),
            assessed_complexity=assessed,
            effective_complexity=_optional_scalar(effective),
            contract_effect=contract_effect,
            reason=_require_scalar(values, "reason"),
            risk_flags=_require_list(values, "risk_flags"),
            required_docs=_require_list(values, "required_docs"),
            confidence=_require_scalar(values, "confidence"),
            override_reason=_require_scalar(values, "override_reason", allow_empty=True),
        )
        classification.validate()
        return classification

    def validate(self) -> None:
        _enum(
            "change_type",
            self.change_type,
            CHANGE_TYPES,
        )
        _enum("requested_complexity", self.requested_complexity, {"auto", "small", "complex"})
        _enum(
            "assessed_complexity",
            self.assessed_complexity,
            {"small", "complex", "needs-human-decision"},
        )
        if self.effective_complexity is not None:
            _enum("effective_complexity", self.effective_complexity, {"small", "complex"})
        _enum(
            "contract_effect",
            self.contract_effect,
            {"restore", "unchanged", "add", "change", "unclear"},
        )
        _enum("confidence", self.confidence, {"high", "medium", "low"})
        if not self.reason.strip():
            raise ClassificationError("reason must not be empty")
        if not self.required_docs or self.required_docs[0] not in {
            "summary",
            "00-summary.md",
        }:
            raise ClassificationError("required_docs must start with summary")
        unknown_docs = set(self.required_docs) - ALLOWED_DOCS
        if unknown_docs:
            raise ClassificationError(f"unsupported required_docs: {sorted(unknown_docs)}")
        styles = {
            "role" if name in DOCUMENT_ROLES else "legacy" for name in self.required_docs
        }
        if len(styles) != 1:
            raise ClassificationError("required_docs must not mix document roles and legacy filenames")
        if len(set(self.risk_flags)) != len(self.risk_flags):
            raise ClassificationError("risk_flags must not contain duplicates")
        if len(set(self.required_docs)) != len(self.required_docs):
            raise ClassificationError("required_docs must not contain duplicates")

    def route(self, *, change_control: str = "production") -> Route:
        if change_control not in {"development", "production"}:
            raise ClassificationError(f"unsupported change_control: {change_control!r}")
        role_based = self.required_docs[0] == "summary"
        unresolved_docs = ("summary",) if role_based else ("00-summary.md",)
        # development 阶段的强制 complex 去掉 spec/plan：它们的内容在交互开发中
        # 已即时产生并执行，而 summary（改了什么、如何判级）是事后唯一可查的证据。
        # verification 不在此处决定——它沿用下方与 production 完全相同的条件
        # （analyzer 是否要求）。#163 之前它还兼答「该变更要部署，终态是 deployed
        # 而非 completed」；那半边语义已经移出去了：现在由 governance manifest 的
        # deployment_lifecycle 回答，因为那是仓库属性而不是单次变更的属性
        # （见 mark-completed-issues.sh 与 03 §11）。这里只剩「欠不欠验证记录」，
        # change_control 不改变它。缺省 production，保持既有四份行为。
        if change_control == "development":
            complex_docs = ("summary",) if role_based else ("00-summary.md",)
        else:
            complex_docs = (
                ("summary", "spec", "plan")
                if role_based
                else ("00-summary.md", "01-spec.md", "02-plan.md")
            )
        if self.required_docs[-1] in {"verification", "03-verification.md"}:
            complex_docs += (self.required_docs[-1],)
        if (
            self.assessed_complexity == "needs-human-decision"
            or self.contract_effect == "unclear"
            or self.confidence == "low"
        ):
            return Route(None, "awaiting-triage", None, unresolved_docs)

        forced_reasons: list[str] = []
        if self.requested_complexity == "complex":
            forced_reasons.append("explicit complexity/complex request")
        # security and data join feature/platform because AGENTS.md already
        # forces complex for 认证/权限/安全 and schema/数据迁移, and those two
        # types mean exactly that by definition. The equivalent risk_flags
        # (security, schema-change, data-migration) also force complex, but a
        # flag is analyzer input that can be omitted; the type label cannot be.
        # reliability is deliberately absent: an availability fix is often a
        # pure restore of existing behavior, so it routes on contract_effect
        # like maintenance does.
        if self.change_type in FORCED_COMPLEX_TYPES:
            forced_reasons.append(f"type/{self.change_type}")
        if self.contract_effect in {"add", "change"}:
            forced_reasons.append(f"contract_effect={self.contract_effect}")
        forced_risks = sorted(set(self.risk_flags) & FORCED_COMPLEX_RISKS)
        forced_reasons.extend(forced_risks)
        if self.assessed_complexity == "complex" or self.effective_complexity == "complex":
            forced_reasons.append("AI assessed complex")

        if forced_reasons:
            override = self.override_reason
            if self.requested_complexity == "small" or self.effective_complexity == "small":
                override = "forced complex: " + ", ".join(dict.fromkeys(forced_reasons))
            return Route(
                "complex",
                "spec-drafting",
                "complexity/complex",
                complex_docs,
                override,
            )

        if self.assessed_complexity != "small" or self.effective_complexity != "small":
            raise ClassificationError("non-unclear classification cannot be routed safely")
        return Route(
            "small",
            "approved",
            "complexity/small",
            unresolved_docs,
            self.override_reason,
        )


def _parse_restricted_yaml(text: str) -> tuple[dict[str, object], list[str]]:
    values: dict[str, object] = {}
    order: list[str] = []
    active_list: Optional[str] = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        if "\t" in raw_line:
            raise ClassificationError(f"tabs are forbidden at line {line_number}")
        if raw_line.startswith("  - "):
            if active_list is None:
                raise ClassificationError(f"list item without list field at line {line_number}")
            item = _parse_scalar(raw_line[4:].strip(), line_number)
            if not item:
                raise ClassificationError(f"empty list item at line {line_number}")
            assert isinstance(values[active_list], list)
            values[active_list].append(item)
            continue
        if raw_line[0].isspace() or ":" not in raw_line:
            raise ClassificationError(f"unsupported YAML syntax at line {line_number}")

        name, raw_value = raw_line.split(":", 1)
        if name not in FULL_FIELDS:
            raise ClassificationError(f"unknown field {name!r} at line {line_number}")
        if name in values:
            raise ClassificationError(f"duplicate field {name!r} at line {line_number}")
        order.append(name)
        active_list = None
        value_text = raw_value.strip()
        if name in LIST_FIELDS:
            if value_text == "[]":
                values[name] = []
            elif value_text == "":
                values[name] = []
                active_list = name
            else:
                raise ClassificationError(f"{name} must be [] or a block list")
        else:
            if value_text == "":
                raise ClassificationError(f"{name} must be a scalar")
            values[name] = _parse_scalar(value_text, line_number)

    missing = set(UNCLEAR_FIELDS) - set(values)
    if missing:
        raise ClassificationError(f"missing required fields: {sorted(missing)}")
    return values, order


def _parse_scalar(value: str, line_number: int) -> str:
    if any(marker in value for marker in ("&", "*", "!", "{", "}", "[", "]")):
        raise ClassificationError(f"unsafe YAML scalar at line {line_number}")
    if value.startswith(("'", '"')):
        if len(value) < 2 or value[-1] != value[0]:
            raise ClassificationError(f"unterminated quoted scalar at line {line_number}")
        value = value[1:-1]
    return value


def _require_scalar(values: dict[str, object], name: str, *, allow_empty: bool = False) -> str:
    value = values.get(name)
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ClassificationError(f"{name} must be a scalar")
    return value


def _optional_scalar(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ClassificationError("effective_complexity must be a scalar")
    return value


def _require_list(values: dict[str, object], name: str) -> tuple[str, ...]:
    value = values.get(name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ClassificationError(f"{name} must be a list")
    return tuple(value)


def _enum(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ClassificationError(f"invalid {name}: {value!r}")
