"""Bounded publishers used by Matt to-spec and to-tickets adapters."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Mapping

from .contract import (
    ContractError,
    PR_BEARING_STATUSES,
    parse_front_matter,
    resolve_change_name,
    resolve_documents,
    resolve_summary,
)


def publish_spec(
    repo: Path | str,
    issue: Mapping[str, object],
    body: str,
) -> Path:
    """Publish a spec to the exact path declared by one open Issue summary."""
    return _publish(repo, issue, "spec", body)


def publish_plan(
    repo: Path | str,
    issue: Mapping[str, object],
    graph: str,
) -> Path:
    """Publish a ticket plan to the exact path declared by one open Issue summary."""
    if not _has_ticket_graph(graph):
        raise ContractError("plan must contain a valid Ticket graph table")
    return _publish(repo, issue, "plan", graph)


def backfill_pr_url(
    repo: Path | str,
    issue_number: int,
    pr_url: str,
) -> tuple[Path, bool]:
    """Write one change's pull request URL into its summary front matter.

    pr_url is the only front matter field that cannot be known when the document
    is created — the PR does not exist until the branch has been pushed — so it
    is the one field that needs a writer of its own (#142). It lives in the
    summary only: no code reads pr_url from a spec, plan or verification, so a
    copy there is a duplicate with no consumer (spec §2).

    Returns the summary path and whether the file changed. Re-running with the
    value already in place writes nothing at all, so a repeated backfill leaves
    no diff; a *different* non-empty value is refused rather than overwritten,
    because one change has exactly one PR and a second value means the premise
    behind that rule has broken somewhere the caller cannot see.
    """
    repo_path = Path(repo).resolve()
    summary_path, summary = resolve_summary(repo_path, issue_number)
    expected_prefix = _pull_url_prefix(summary, issue_number)
    if not isinstance(pr_url, str) or not re.fullmatch(
        rf"{re.escape(expected_prefix)}[1-9][0-9]*", pr_url
    ):
        raise ContractError(
            f"pr_url must be {expected_prefix}<number>, derived from the summary gitea_url"
        )

    text = summary_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    # Bounded to the front matter block. A bare "pr_url:" inside the prose — this
    # very change's own documents contain several — must not be rewritten.
    end = _front_matter_end(lines)
    index = _front_matter_field(lines, end, "pr_url")
    if index is None:
        raise ContractError("summary front matter does not declare pr_url")
    # The value is taken from the parsed front matter, not by splitting the raw
    # line a second time. contract._safe_scalar strips matching quotes, so
    # `pr_url: ''` is empty to every reader in this runtime — the audit, the
    # prefix check, the Controller. Re-parsing here was a second, weaker rule
    # that kept the quotes, and it reported that spelling as a *different*
    # pr_url: a report of a second pull request that never existed (#186). The
    # raw line is still needed, but only to know which line to replace.
    declared = summary.get("pr_url")
    current = declared.strip() if isinstance(declared, str) else ""
    if current and current != pr_url:
        raise ContractError(
            f"summary already declares a different pr_url: {current}"
        )

    changed = current != pr_url
    if changed:
        lines[index] = _replaced(lines[index], "pr_url", pr_url)
    # The same fact, recorded in two fields: "this change now has a PR". Writing
    # them together is what makes the audit satisfiable at every point in time —
    # a summary that claims pr-open before the PR exists is simply false, and a
    # gate that reads it would fail every change's first CI run (spec §4.1).
    status_index = _front_matter_field(lines, end, "status")
    if status_index is not None:
        status = lines[status_index].split(":", 1)[1].strip()
        if status not in PR_BEARING_STATUSES:
            lines[status_index] = _replaced(lines[status_index], "status", "pr-open")
            changed = True
    if changed:
        _atomic_write(summary_path, "".join(lines))
    return summary_path, changed


def _replaced(line: str, name: str, value: str) -> str:
    terminator = "\n" if line.endswith("\n") else ""
    return f"{name}: {value}{terminator}"


def backfill_pr_number(
    repo: Path | str,
    issue_number: int,
    pr_number: int,
) -> tuple[Path, bool]:
    """Backfill by pull request number, deriving the URL from the summary itself.

    The Controller reaches this with a number straight out of create_pr, not a
    URL (#146). The URL is built from the summary's own gitea_url rather than
    from the response's html_url on purpose: on this platform the API renders
    html_url against one base (gitea-ci.orb.local:3000) while the runner sees
    another (localhost:3000), and feeding that difference to the strict prefix
    check would escalate a healthy Loop over pure cosmetics.
    """
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number <= 0:
        raise ContractError("pull request number must be a positive integer")
    repo_path = Path(repo).resolve()
    _, summary = resolve_summary(repo_path, issue_number)
    prefix = _pull_url_prefix(summary, issue_number)
    return backfill_pr_url(repo_path, issue_number, f"{prefix}{pr_number}")


def _pull_url_prefix(summary: Mapping[str, object], issue_number: int) -> str:
    """Derive the only pull request URL prefix this summary can legitimately carry.

    Checked against the summary's own gitea_url rather than against a configured
    base: it makes the check offline and makes a URL from another repository, or
    from another Issue, impossible to write without also having lied in the
    summary itself.
    """
    gitea_url = summary.get("gitea_url")
    if not isinstance(gitea_url, str) or not gitea_url:
        raise ContractError("summary front matter must declare gitea_url")
    match = re.fullmatch(r"(https?://\S+?)/issues/([1-9][0-9]*)", gitea_url)
    if not match or int(match.group(2)) != issue_number:
        raise ContractError(
            f"summary gitea_url must be the issues/{issue_number} URL of this Issue"
        )
    return f"{match.group(1)}/pulls/"


def _front_matter_end(lines: list[str]) -> int:
    if not lines or lines[0].rstrip("\n") != "---":
        raise ContractError("document must start with YAML front matter")
    for index in range(1, len(lines)):
        if lines[index].rstrip("\n") == "---":
            return index
    raise ContractError("document front matter is not closed")


def _front_matter_field(lines: list[str], end: int, name: str) -> int | None:
    for index in range(1, end):
        if lines[index].split(":", 1)[0] == name:
            return index
    return None


def _atomic_write(destination: Path, body: str) -> None:
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}-write-",
        dir=destination.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _publish(
    repo: Path | str,
    issue: Mapping[str, object],
    role: str,
    body: str,
) -> Path:
    repo_path = Path(repo).resolve()
    number = issue.get("number")
    if not isinstance(number, int) or number <= 0 or issue.get("state") != "open":
        raise ContractError("publisher requires an existing open Gitea Issue")
    change_name = resolve_change_name(repo_path, number)
    branch = change_name.branch
    current = _git_branch(repo_path)
    if current != branch:
        raise ContractError(f"current branch must be {branch}, got {current or 'detached'}")

    documents = resolve_documents(repo_path, number)
    name = documents.get(role)
    if not name:
        raise ContractError(f"documents mapping does not declare {role}")
    directory = repo_path / "docs" / "changes" / change_name.directory_name
    destination = directory / name
    if directory.is_symlink() or destination.is_symlink():
        raise ContractError("change document paths must not be symlinks")
    if destination.parent.resolve() != directory.resolve():
        raise ContractError("change document path escapes its Issue directory")

    front_matter = parse_front_matter(body)
    if str(front_matter.get("issue")) != str(number):
        raise ContractError(f"{role} front matter issue must be {number}")
    if front_matter.get("branch") != branch:
        raise ContractError(f"{role} front matter branch must be {branch}")
    created = front_matter.get("created")
    match = re.fullmatch(
        rf"{role}-[a-z0-9]+(?:-[a-z0-9]+){{1,3}}-(\d{{6}})\.md",
        name,
    )
    if match and (
        not isinstance(created, str)
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", created)
        or created[2:4] + created[5:7] + created[8:10] != match.group(1)
    ):
        raise ContractError(f"{role} created date must match its immutable filename")

    _atomic_write(destination, body)
    return destination


def _git_branch(repo: Path) -> str:
    result = subprocess.run(
        ("git", "branch", "--show-current"),
        cwd=repo,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ContractError("publisher repository is not an accessible Git checkout")
    return result.stdout.strip()


def _has_ticket_graph(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines[:-2]):
        cells = _cells(line)
        headers = [cell.lower().replace("_", " ") for cell in cells]
        if not {"ticket", "blocked by", "status"}.issubset(headers):
            continue
        separators = _cells(lines[index + 1])
        if not separators or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            continue
        ticket_index = headers.index("ticket")
        for row in lines[index + 2 :]:
            values = _cells(row)
            if not values:
                break
            if ticket_index < len(values) and re.fullmatch(
                r"T\d{2,}", values[ticket_index], re.IGNORECASE
            ):
                return True
    return False


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]
