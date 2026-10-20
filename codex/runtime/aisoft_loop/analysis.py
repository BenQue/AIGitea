"""Validated analyzer output and deterministic routing for the session tools."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Mapping

from aisoft_change_name import ChangeNameError, validate_slug

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


def analyze_route(
    issue: Mapping[str, object],
    result: AnalysisResult,
    *,
    change_control: str = "production",
) -> Route:
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
    route = result.classification.route(change_control=change_control)
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


def route_labels(result: AnalysisResult, route: Route) -> set[str]:
    labels = {f"type/{result.classification.change_type}", route.lifecycle_label}
    if route.complexity_label:
        labels.add(route.complexity_label)
    return labels


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
