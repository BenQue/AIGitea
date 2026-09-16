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

from aisoft_worktree_owner import CODE_CLAIM_INVALID, WorktreeOwnerError


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
