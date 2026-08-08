"""Bounded publishers used by Matt to-spec and to-tickets adapters."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Mapping

from .contract import ContractError, parse_front_matter, resolve_documents


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
    branch = f"change/{number}"
    current = _git_branch(repo_path)
    if current != branch:
        raise ContractError(f"current branch must be {branch}, got {current or 'detached'}")

    documents = resolve_documents(repo_path, number)
    name = documents.get(role)
    if not name:
        raise ContractError(f"documents mapping does not declare {role}")
    directory = repo_path / "docs" / "changes" / str(number)
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

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{role}-publish-",
        dir=directory,
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
