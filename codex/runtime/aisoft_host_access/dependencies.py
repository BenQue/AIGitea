"""Credential-free dependency identity and terminal rules shared by both gates."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from .contract import AccessContract, ProjectContract

Dependency = int | str
QUALIFIED = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]{0,63})/([A-Za-z0-9][A-Za-z0-9._-]{0,63})#([1-9][0-9]{0,17})")


class DependencyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def parse_reference(value: object) -> Dependency:
    if isinstance(value, str) and QUALIFIED.fullmatch(value):
        return value
    # Preserve numeric scalars accepted by the old restricted YAML reader.
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        number = 0
    if isinstance(value, bool) or number <= 0:
        raise DependencyError("DEPENDENCY_FORMAT_INVALID", "depends_on requires positive local Issue numbers or owner/repo#N")
    return number


def identity(reference: Dependency, source: tuple[str, str]) -> tuple[str, str, int]:
    reference = parse_reference(reference)
    if isinstance(reference, int):
        return (*source, reference)
    match = QUALIFIED.fullmatch(reference)
    assert match is not None
    return (match[1], match[2], int(match[3]))


def display(reference: Dependency) -> str:
    return f"#{reference}" if isinstance(reference, int) else reference


def parse_dependencies(
    values: object, issue_number: int, source: tuple[str, str] | None = None,
) -> tuple[Dependency, ...]:
    if values is None or values == "":
        return ()
    if not isinstance(values, list):
        raise DependencyError("DEPENDENCY_FORMAT_INVALID", "depends_on must be a list of positive Issue numbers or owner/repo#N")
    result: list[Dependency] = []
    seen: set[object] = set()
    for value in values:
        ref = parse_reference(value)
        key = identity(ref, source) if source is not None else ref
        is_self = key == (*source, issue_number) if source is not None else ref == issue_number
        if is_self:
            raise DependencyError("DEPENDENCY_SELF", "depends_on must not reference its own Issue")
        if key in seen:
            raise DependencyError("DEPENDENCY_DUPLICATE", "depends_on contains duplicate Issue references")
        seen.add(key)
        result.append(ref)
    return tuple(result)


def resolve_target(
    contract: AccessContract, source: ProjectContract, reference: Dependency,
) -> tuple[ProjectContract, int, str]:
    owner, repository, number = identity(reference, (contract.governance.owner, source.repository))
    target = next((p for p in contract.projects if p.repository == repository), None)
    if owner != contract.governance.owner or target is None:
        raise DependencyError("DEPENDENCY_TARGET_DENIED", "dependency repository is not canonical and governed")
    if target.project_id != source.project_id and target.project_id not in source.dependency_read_targets:
        raise DependencyError("DEPENDENCY_TARGET_DENIED", "dependency source-to-target edge is not authorized")
    return target, number, f"{owner}/{repository}#{number}"


def project_issue(value: object, expected: tuple[str, str, int]) -> dict[str, object]:
    """Reject mismatched/PR/malformed responses, then discard unneeded content."""
    owner, repository, number = expected
    if not isinstance(value, Mapping):
        raise DependencyError("DEPENDENCY_RESPONSE_INVALID", "dependency response must be an Issue object")
    repo = value.get("repository")
    if (
        value.get("number") != number or isinstance(value.get("number"), bool)
        or not isinstance(repo, Mapping) or repo.get("full_name") != f"{owner}/{repository}"
        or value.get("pull_request") is not None or value.get("state") not in ("open", "closed")
        or not isinstance(value.get("labels"), list)
    ):
        raise DependencyError("DEPENDENCY_RESPONSE_INVALID", "dependency Issue identity or state is invalid")
    labels: list[str] = []
    for item in value["labels"]:
        name = item.get("name") if isinstance(item, Mapping) else item
        if not isinstance(name, str) or not name:
            raise DependencyError("DEPENDENCY_RESPONSE_INVALID", "dependency labels are invalid")
        labels.append(name)
    return {"repository": f"{owner}/{repository}", "number": number,
            "reference": f"{owner}/{repository}#{number}", "state": value["state"], "labels": labels}


def is_terminal(issue: Mapping[str, object]) -> bool:
    labels = issue.get("labels", [])
    if not isinstance(labels, list):
        return False
    names = {name for item in labels
             if isinstance(name := item.get("name") if isinstance(item, Mapping) else item, str)}
    return issue.get("state") == "closed" and bool(names & {"completed", "deployed"})
