"""Local Git facts about change worktrees (#298).

Read-only helpers on top of `aisoft_worktree_owner`: resolving a worktree's git
dir, reading its branch, and enumerating every change worktree of one checkout.
Everything here shells out to `git` with an argv list — never a shell string.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Optional, Sequence

from aisoft_worktree_owner import (
    CODE_CLAIM_INVALID, CODE_UNCLAIMED, WorktreeOwnerError, read_marker,
)


class WorktreeError(Exception):
    pass


def _git(argv: Sequence[str], *, cwd: Path | str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *argv],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        # A missing or unreadable cwd fails inside Popen, before git ever runs.
        # Callers scan a list of worktree paths that may have been removed, so
        # this has to arrive as the same typed error as a git failure.
        raise WorktreeError(f"cannot run git in {cwd}: {exc}") from exc


def _git_ok(argv: Sequence[str], *, cwd: Path | str) -> str:
    result = _git(argv, cwd=cwd)
    if result.returncode != 0:
        raise WorktreeError(
            f"git {' '.join(argv)} failed in {cwd}: {result.stderr.strip() or result.returncode}"
        )
    return result.stdout.strip()


def resolve_git_dir(worktree: Path | str) -> Path:
    """The worktree's own git dir.

    `--absolute-git-dir` matters: a linked worktree's `.git` is a *file*, and
    plain `--git-dir` can answer with a relative path, so joining `.git` by hand
    or trusting the raw answer both land outside the per-worktree directory this
    marker has to live in.
    """
    return Path(_git_ok(["rev-parse", "--absolute-git-dir"], cwd=worktree))


def current_branch(worktree: Path | str) -> str:
    """The checked-out branch, or an empty string when HEAD is detached."""
    return _git_ok(["branch", "--show-current"], cwd=worktree)


def head_sha(worktree: Path | str) -> str:
    return _git_ok(["rev-parse", "HEAD"], cwd=worktree)


def is_ancestor(worktree: Path | str, ancestor: str, descendant: str) -> bool:
    """Whether `ancestor` is reachable from `descendant`.

    A missing object answers False rather than raising: a recorded push head
    that this repository no longer contains cannot be shown to be in HEAD's
    history, and treating "cannot prove it" as "fine" is the wrong default here.
    """
    return _git(
        ["merge-base", "--is-ancestor", ancestor, descendant], cwd=worktree
    ).returncode == 0


def require_branch(worktree: Path | str, branch: str) -> None:
    """Refuse to claim a worktree for a branch it is not standing on."""
    current = current_branch(worktree)
    if current != branch:
        raise WorktreeOwnerError(
            CODE_CLAIM_INVALID,
            f"worktree {worktree} is on {current or 'a detached HEAD'}, not {branch}",
        )


@dataclass(frozen=True)
class ScanEntry:
    worktree: str
    branch: str
    head: str
    last_push_head: Optional[str]
    session: Optional[str]
    reason: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.reason not in GAP_REASONS


# `ahead` and `unpushed` are listed but never fail the scan. Having unpushed
# local commits is the normal state for most of a change's life; if that were a
# GAP this command would be red for the whole implementation phase and readers
# would learn to ignore it — which destroys exactly the one signal it exists to
# give.
GAP_REASONS = frozenset({"rewritten", "unclaimed", "claim-invalid"})


def list_change_worktrees(checkout: Path | str) -> list[tuple[str, str]]:
    """Every linked worktree of `checkout` that is standing on a change branch.

    Parsed from `git worktree list --porcelain`: records are blank-line
    separated, and a record without a `branch` line is a detached HEAD, which
    cannot be a change worktree.
    """
    porcelain = _git_ok(["worktree", "list", "--porcelain"], cwd=checkout)
    found: list[tuple[str, str]] = []
    path: Optional[str] = None
    for line in porcelain.splitlines() + [""]:
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ")
        elif line.startswith("branch refs/heads/"):
            branch = line.removeprefix("branch refs/heads/")
            if path is not None and branch.startswith("change/"):
                found.append((path, branch))
        elif not line:
            path = None
    return found


def scan_change_worktrees(checkout: Path | str) -> list[ScanEntry]:
    """Read-only sweep of every change worktree of one checkout (#298).

    Writes nothing: no marker is created or repaired, no fetch, no push. It
    answers one question per worktree — is HEAD still what the last broker push
    put on the remote, and if not, why.
    """
    entries: list[ScanEntry] = []
    for path, branch in list_change_worktrees(checkout):
        try:
            git_dir = resolve_git_dir(path)
            head = head_sha(path)
        except WorktreeError as exc:
            entries.append(ScanEntry(
                worktree=str(path), branch=branch, head="", last_push_head=None,
                session=None, reason="claim-invalid", detail=str(exc),
            ))
            continue
        try:
            marker = read_marker(git_dir)
        except WorktreeOwnerError as exc:
            reason = "unclaimed" if exc.code == CODE_UNCLAIMED else "claim-invalid"
            entries.append(ScanEntry(
                worktree=str(path), branch=branch, head=head, last_push_head=None,
                session=None, reason=reason, detail=str(exc),
            ))
            continue
        if marker.branch != branch:
            entries.append(ScanEntry(
                worktree=str(path), branch=branch, head=head,
                last_push_head=marker.last_push_head, session=marker.session,
                reason="claim-invalid",
                detail=f"marker claims {marker.branch}, worktree is on {branch}",
            ))
            continue
        if marker.last_push_head is None:
            reason, detail = "unpushed", "never pushed through the broker"
        elif marker.last_push_head == head:
            reason, detail = "clean", "HEAD is exactly what the last push landed"
        elif is_ancestor(path, marker.last_push_head, head):
            ahead = _git_ok(
                ["rev-list", "--count", f"{marker.last_push_head}..{head}"], cwd=path
            )
            reason, detail = "ahead", f"{ahead} local commit(s) on top of the last push"
        else:
            reason = "rewritten"
            detail = (
                "HEAD is not a descendant of the last push; the branch was rewritten "
                "since it landed"
            )
        entries.append(ScanEntry(
            worktree=str(path), branch=branch, head=head,
            last_push_head=marker.last_push_head, session=marker.session,
            reason=reason, detail=detail,
        ))
    return entries
