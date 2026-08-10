"""Validated analyzer output, deterministic routing, and summary rendering."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Mapping

from aisoft_change_name import ChangeName, ChangeNameError, validate_slug

from .classification import Classification, ClassificationError, Route


class AnalysisError(ValueError):
    """Analyzer result or Issue routing inputs are incomplete or inconsistent."""


@dataclass(frozen=True)
class AnalysisResult:
    classification: Classification
    document_slug: str
    problem_summary: str
    impact: str
    approach: str
    risks: tuple[str, ...]
    evidence: tuple[str, ...]
    missing_acceptance_criteria: tuple[str, ...]

    @classmethod
    def from_json(cls, text: str) -> "AnalysisResult":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AnalysisError("analyzer output is not valid JSON") from exc
        expected = {
            "classification",
            "document_slug",
            "problem_summary",
            "impact",
            "approach",
            "risks",
            "evidence",
            "missing_acceptance_criteria",
        }
        if not isinstance(raw, dict) or set(raw) != expected:
            raise AnalysisError("analyzer output must use the exact result schema")
        for field in ("classification", "document_slug", "problem_summary", "impact", "approach"):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise AnalysisError(f"analyzer field {field} must be a non-empty string")
        document_slug = raw["document_slug"].strip()
        try:
            validate_slug(document_slug)
        except ChangeNameError as exc:
            raise AnalysisError(
                "analyzer field document_slug must use 2-4 lowercase kebab-case words and at most 32 characters"
            ) from exc
        for field in ("risks", "evidence", "missing_acceptance_criteria"):
            value = raw[field]
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                raise AnalysisError(f"analyzer field {field} must be a string array")
        if not raw["evidence"]:
            raise AnalysisError("analyzer evidence must not be empty")
        try:
            classification = Classification.from_yaml(raw["classification"])
        except ClassificationError as exc:
            raise AnalysisError(f"invalid analyzer classification: {exc}") from exc
        return cls(
            classification=classification,
            document_slug=document_slug,
            problem_summary=raw["problem_summary"].strip(),
            impact=raw["impact"].strip(),
            approach=raw["approach"].strip(),
            risks=tuple(item.strip() for item in raw["risks"]),
            evidence=tuple(item.strip() for item in raw["evidence"]),
            missing_acceptance_criteria=tuple(
                item.strip() for item in raw["missing_acceptance_criteria"]
            ),
        )


def analyze_route(issue: Mapping[str, object], result: AnalysisResult) -> Route:
    labels = _label_names(issue.get("labels"))
    requested_labels = labels & {"complexity/small", "complexity/complex"}
    if len(requested_labels) > 1:
        raise AnalysisError("Issue cannot request both complexity labels")
    requested = "auto"
    if requested_labels:
        requested = next(iter(requested_labels)).split("/", 1)[1]
    if result.classification.requested_complexity != requested:
        raise AnalysisError(
            "classification requested_complexity does not match the Issue declaration"
        )
    route = result.classification.route()
    if route.effective_complexity == "small" and not _has_acceptance_criteria(
        str(issue.get("body") or "")
    ):
        return Route(
            "small",
            "awaiting-triage",
            "complexity/small",
            route.required_docs,
            route.override_reason,
        )
    return route


def render_summary(
    issue: Mapping[str, object],
    result: AnalysisResult,
    route: Route,
    gitea_url: str,
    owner: str,
    repo: str,
    *,
    date: str,
) -> str:
    number = issue.get("number")
    if not isinstance(number, int) or number <= 0:
        raise AnalysisError("Issue number must be a positive integer")
    classification_lines = _normalized_classification(result.classification, route)
    document_lines = ["documents:"]
    for role in route.required_docs:
        if role not in {"summary", "spec", "plan", "verification"}:
            raise AnalysisError("new analyzer output must use semantic required_docs roles")
        document_lines.append(
            f"  {role}: {document_filename(role, result.document_slug, date)}"
        )
    front_matter = [
        "---",
        f"issue: {number}",
        f"gitea_url: {gitea_url.rstrip('/')}/{owner}/{repo}/issues/{number}",
        *classification_lines,
        *document_lines,
        f"status: {route.lifecycle_label}",
        f"branch: {ChangeName.new(number, result.document_slug).branch}",
        "pr_url:",
        f"created: {date}",
        f"updated: {date}",
        "---",
    ]
    risks = _bullets(result.risks, empty="- 无已识别风险。")
    evidence = _bullets(result.evidence)
    missing = _bullets(
        result.missing_acceptance_criteria,
        empty="- 无；如后续发现缺失则回到 awaiting-triage。",
    )
    classification_block = "\n".join(classification_lines)
    body = f"""

## 问题/需求总结

{result.problem_summary}

## 影响范围

{result.impact}

## 初步方案与建议

{result.approach}

## 风险

{risks}

## AI 判级

```yaml
{classification_block}
```

### 判级证据

{evidence}

### 缺失的 acceptance criteria 或决策

{missing}
"""
    return "\n".join(front_matter) + body


def document_filename(role: str, slug: str, created: str) -> str:
    if role not in {"summary", "spec", "plan", "verification"}:
        raise AnalysisError(f"unsupported document role: {role}")
    try:
        validate_slug(slug)
    except ChangeNameError as exc:
        raise AnalysisError("document_slug violates the short kebab-case contract")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", created):
        raise AnalysisError("document creation date must use YYYY-MM-DD")
    compact_date = created[2:4] + created[5:7] + created[8:10]
    name = f"{role}-{slug}-{compact_date}.md"
    if len(name) > 64:
        raise AnalysisError("document basename exceeds 64 characters")
    return name


def summary_filename(result: AnalysisResult, created: str) -> str:
    return document_filename("summary", result.document_slug, created)


def route_labels(result: AnalysisResult, route: Route) -> set[str]:
    labels = {f"type/{result.classification.change_type}", route.lifecycle_label}
    if route.complexity_label:
        labels.add(route.complexity_label)
    return labels


def _normalized_classification(
    classification: Classification, route: Route
) -> list[str]:
    output = [
        f"change_type: {classification.change_type}",
        f"requested_complexity: {classification.requested_complexity}",
        f"assessed_complexity: {classification.assessed_complexity}",
    ]
    if route.effective_complexity is not None:
        output.append(f"effective_complexity: {route.effective_complexity}")
    output.extend(
        (
            f"contract_effect: {classification.contract_effect}",
            f"reason: {classification.reason}",
            *_list_lines("risk_flags", classification.risk_flags),
            *_list_lines("required_docs", route.required_docs),
            f"confidence: {classification.confidence}",
            "override_reason: "
            + _quoted_empty(route.override_reason or classification.override_reason),
        )
    )
    return output


def _list_lines(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        return (f"{name}: []",)
    return (f"{name}:", *(f"  - {value}" for value in values))


def _quoted_empty(value: str) -> str:
    return value if value else "''"


def _bullets(values: tuple[str, ...], *, empty: str = "") -> str:
    if not values:
        return empty
    return "\n".join(f"- {value}" for value in values)


def _label_names(raw_labels: object) -> set[str]:
    if not isinstance(raw_labels, list):
        return set()
    names: set[str] = set()
    for item in raw_labels:
        if isinstance(item, str):
            names.add(item)
        elif isinstance(item, Mapping) and isinstance(item.get("name"), str):
            names.add(str(item["name"]))
    return names


def _has_acceptance_criteria(text: str) -> bool:
    match = re.search(
        r"^##\s+(?:Acceptance criteria|验收标准|验收条件)\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return False
    return bool(re.search(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?\S", match.group(1), re.MULTILINE))
