"""Pure routine-auto eligibility and persistent submit authorization contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .classification import FORCED_COMPLEX_RISKS


MANUAL_ONLY_RISKS = frozenset(FORCED_COMPLEX_RISKS) | {
    "major",
    "phase-completion",
    "milestone-completion",
    "health-check",
    "backup",
}
MERGE_POLICIES = frozenset({"manual", "routine-auto"})


@dataclass(frozen=True)
class RoutineEligibility:
    eligible: bool
    reasons: tuple[str, ...]


def evaluate_routine_eligibility(
    *,
    issue_number: int,
    effective_complexity: str,
    contract_effect: str,
    local_scope: bool,
    reversible: bool,
    risk_flags: Iterable[str],
    major: bool,
    phase_or_milestone_completion: bool,
    repository_classification: str,
    repository_opt_in: bool,
    required_contexts: Iterable[str],
) -> RoutineEligibility:
    """Return every fail-closed reason without reading state or external services."""
    contexts = tuple(required_contexts)
    risks = frozenset(risk_flags)
    reasons: list[str] = []
    if issue_number == 208:
        reasons.append("ISSUE_208_MANUAL_ONLY")
    if effective_complexity != "small":
        reasons.append("COMPLEXITY_NOT_SMALL")
    if contract_effect not in {"restore", "unchanged"}:
        reasons.append("CONTRACT_EFFECT_NOT_ROUTINE")
    if not local_scope:
        reasons.append("SCOPE_NOT_LOCAL")
    if not reversible:
        reasons.append("CHANGE_NOT_REVERSIBLE")
    if major:
        reasons.append("MAJOR_CHANGE")
    if phase_or_milestone_completion:
        reasons.append("PHASE_OR_MILESTONE_COMPLETION")
    if risks & MANUAL_ONLY_RISKS:
        reasons.append("FORCED_RISK")
    if repository_classification != "internal-application":
        reasons.append("REPOSITORY_CLASSIFICATION_INELIGIBLE")
    if not repository_opt_in:
        reasons.append("REPOSITORY_NOT_OPTED_IN")
    if not contexts or any(not isinstance(item, str) or not item for item in contexts):
        reasons.append("REQUIRED_CONTEXTS_EMPTY")
    return RoutineEligibility(not reasons, tuple(reasons))


def authorization_marker(issue_number: int, branch: str, policy: str) -> str:
    if policy not in MERGE_POLICIES:
        raise ValueError("merge policy must be manual or routine-auto")
    return (
        "AISoft-Submit-Authorization: "
        f"issue={issue_number}; branch={branch}; policy={policy}"
    )
