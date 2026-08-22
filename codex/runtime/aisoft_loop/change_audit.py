"""Read-only sweep that turns the change document front matter contract into a gate.

`resolve-documents` is the only sanctioned way to find a change's documents, and
it parses the front matter of *every* mapped document — so one spec that does not
start with front matter makes the whole change unresolvable. Until #142 nothing
asserted that anywhere, and changes in that state were merged into `main`.

This module answers two questions about a checkout, offline and deterministically:

- change-documents: does `resolve_documents` succeed for every change directory?
- change-pr-url: does every summary whose lifecycle says a PR exists carry one?
"""

from __future__ import annotations

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


@dataclass(frozen=True)
class CheckResult:
    name: str
    problems: tuple[str, ...]

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
    directories = _change_directories(root)

    for name, directory in directories:
        if name is None:
            document_problems.append(f"{directory.name}: 目录名不是合法的 change 名元组")
            continue
        problems = _document_problems(repo_path, directory, name.issue_number)
        document_problems.extend(f"{directory.name}/{problem}" for problem in problems)
        if problems:
            # The pr_url judgement needs a parsed summary; reporting the same
            # broken document twice under two check names would read as two
            # independent defects.
            continue
        problem = _pr_url_problem(repo_path, name.issue_number)
        if problem is not None:
            pr_url_problems.append(f"{directory.name}: {problem}")

    return AuditReport(
        checks=(
            CheckResult(CHECK_DOCUMENTS, tuple(document_problems)),
            CheckResult(CHECK_PR_URL, tuple(pr_url_problems)),
        ),
        change_count=len(directories),
    )


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
