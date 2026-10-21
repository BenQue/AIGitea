"""Read-only sweep that turns the change document front matter contract into a gate.

`resolve-documents` is the only sanctioned way to find a change's documents, and
it parses the front matter of *every* mapped document — so one spec that does not
start with front matter makes the whole change unresolvable. Until #142 nothing
asserted that anywhere, and changes in that state were merged into `main`.

This module answers two questions about a checkout, offline and deterministically:

- change-documents: does `resolve_documents` succeed for every change directory?
- change-pr-url: does every summary whose lifecycle says a PR exists carry one?

A project with history registers it instead of rewriting it (R12, #409): the
usage lock may declare `legacy_changes_before: N`, and problems in a directory
numbered below N are reported as LEGACY registrations, not gaps.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from aisoft_change_name import ChangeName, ChangeNameError

from .contract import (
    ContractError,
    LEGACY_DOCUMENTS,
    NEW_DOCUMENT_RE,
    PR_BEARING_STATUSES,
    parse_front_matter,
    resolve_documents,
    resolve_summary,
)


CHECK_DOCUMENTS = "change-documents"
CHECK_PR_URL = "change-pr-url"
USAGE_LOCK = Path(".aisoft") / "platform-usage.lock.json"
LEGACY_KEY = "legacy_changes_before"
# A directory name that is not a readable tuple still carries its Issue number
# when it starts with one: `13`, zero-padded `0001-board-fixes`.
NUMBERED_DIRECTORY_RE = re.compile(r"^([0-9]+)(?:-|$)")


@dataclass(frozen=True)
class CheckResult:
    name: str
    problems: tuple[str, ...]
    legacy: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class AuditReport:
    checks: tuple[CheckResult, ...]
    change_count: int

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)


def audit_change_documents(repo: Path | str) -> AuditReport:
    """Audit every change directory in one checkout without writing anything."""
    repo_path = Path(repo).resolve()
    root = repo_path / "docs" / "changes"
    document_problems: list[str] = []
    pr_url_problems: list[str] = []
    document_legacy: list[str] = []
    pr_url_legacy: list[str] = []
    directories = _change_directories(root)
    legacy_before, threshold_problem = _legacy_threshold(repo_path)
    if threshold_problem is not None:
        document_problems.append(threshold_problem)

    for name, directory in directories:
        is_legacy = legacy_before is not None and _is_legacy(name, directory, legacy_before)
        documents = document_legacy if is_legacy else document_problems
        pr_urls = pr_url_legacy if is_legacy else pr_url_problems
        if name is None:
            documents.append(f"{directory.name}: 目录名不是合法的 change 名元组")
            continue
        problems = _document_problems(repo_path, directory, name.issue_number)
        documents.extend(f"{directory.name}/{problem}" for problem in problems)
        if problems:
            # The pr_url judgement needs a parsed summary; reporting the same
            # broken document twice under two check names would read as two
            # independent defects.
            continue
        problem = _pr_url_problem(repo_path, name.issue_number)
        if problem is not None:
            pr_urls.append(f"{directory.name}: {problem}")

    return AuditReport(
        checks=(
            CheckResult(CHECK_DOCUMENTS, tuple(document_problems), tuple(document_legacy)),
            CheckResult(CHECK_PR_URL, tuple(pr_url_problems), tuple(pr_url_legacy)),
        ),
        change_count=len(directories),
    )


def _legacy_threshold(repo: Path) -> tuple[int | None, str | None]:
    """Read the optional threshold; the lock's own shape is platform-pin's job.

    A declared but malformed threshold is a gap: silently ignoring it would turn
    every registration back into a gap without saying why, and silently
    accepting `true` or "57" would register more than the project meant.
    """
    try:
        lock = json.loads((repo / USAGE_LOCK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    if not isinstance(lock, dict) or LEGACY_KEY not in lock:
        return None, None
    value = lock[LEGACY_KEY]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None, f"{USAGE_LOCK}: {LEGACY_KEY} 必须是正整数"
    return value, None


def _is_legacy(name: ChangeName | None, directory: Path, legacy_before: int) -> bool:
    if name is not None:
        return name.issue_number < legacy_before
    match = NUMBERED_DIRECTORY_RE.match(directory.name)
    return match is not None and int(match.group(1)) < legacy_before


def _change_directories(root: Path) -> list[tuple[ChangeName | None, Path]]:
    if not root.is_dir():
        return []
    found: list[tuple[ChangeName | None, Path]] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        try:
            found.append((ChangeName.parse_directory(path.name), path))
        except ChangeNameError:
            found.append((None, path))
    return found


def _document_problems(repo: Path, directory: Path, number: int) -> list[str]:
    """Name the offending file, not just the failure.

    `parse_front_matter` is generic and its errors carry no file name, so
    `resolve_documents` reports "document must start with YAML front matter"
    without saying which document. The acceptance criteria require the change and
    the file, so each candidate document is checked in its own right first and the
    structural error is only reported when no single file is at fault.
    """
    problems: list[str] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or not _is_change_document(path.name):
            continue
        try:
            parse_front_matter(path.read_text(encoding="utf-8"))
        except ContractError as exc:
            problems.append(f"{path.name}: {exc}")
        except (OSError, UnicodeError) as exc:
            problems.append(f"{path.name}: 无法读取（{exc}）")
    if problems:
        return problems
    try:
        resolve_documents(repo, number)
    except ContractError as exc:
        return [f"resolve-documents 失败：{exc}"]
    return []


def _pr_url_problem(repo: Path, number: int) -> str | None:
    try:
        summary_path, summary = resolve_summary(repo, number)
    except ContractError as exc:  # pragma: no cover - guarded by the caller
        return f"resolve-documents 失败：{exc}"
    status = summary.get("status")
    if not isinstance(status, str) or status not in PR_BEARING_STATUSES:
        return None
    pr_url = summary.get("pr_url")
    if isinstance(pr_url, str) and pr_url.strip():
        return None
    return f"{summary_path.name}: status 为 {status} 但 pr_url 为空"


def _is_change_document(name: str) -> bool:
    return bool(NEW_DOCUMENT_RE.fullmatch(name)) or name in set(LEGACY_DOCUMENTS.values())
