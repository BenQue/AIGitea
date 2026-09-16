"""Single-writer ownership for change worktrees (#298).

Shared by the loop CLI (which claims a worktree and scans for foreign rewrites)
and the host access broker (which refuses `git.push.change` when the caller is
not the owner). It lives at the top level for the same reason
`aisoft_change_name` does: the two packages ship through different installers,
so neither can import the other, and each installer copies this one file into
its own runtime directory.

The marker lives in the worktree's **git dir**, not in the working tree. Any
file inside the working tree would show up in `git status --porcelain`, and
`git.push.change` reads that before it reads anything here — the marker would
make every push fail as `WORKTREE_DIRTY` instead of being read at all.

This is a cooperative guardrail, not a security boundary. Two agents on one
machine run as one user: whatever B can read, B can also rewrite. The goal is
to turn an *accidental* cross-worktree rewrite into an event that stops, not to
defend against an agent that means to forge ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping, Optional

from aisoft_change_name import ChangeName, ChangeNameError

SCHEMA_VERSION = 1
MARKER_NAME = "aisoft-owner.json"
# Deliberately an environment variable and not a broker argument: `arguments` is
# an exact set (broker.py compares sets for equality), so adding one to an
# existing operation fails every existing caller at once (06 pitfall 26).
SESSION_ENV = "AISOFT_SESSION_ID"

CODE_UNCLAIMED = "WORKTREE_UNCLAIMED"
CODE_CLAIM_INVALID = "WORKTREE_CLAIM_INVALID"
CODE_OWNER_MISMATCH = "WORKTREE_OWNER_MISMATCH"

# Session ids come from agent harnesses (uuids, slugs, numeric ids). Bounded and
# printable so a marker can never smuggle control characters into an error
# message or a scan report.
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

MARKER_KEYS = frozenset(
    {
        "schema_version",
        "issue",
        "branch",
        "session",
        "worktree",
        "created",
        "last_push_head",
        "last_push_at",
    }
)

CLAIM_HINT = (
    "claim it with: PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli "
    "claim-worktree --branch <change/N-slug> --session <session id>"
)


class WorktreeOwnerError(Exception):
    """A typed refusal. `code` is what the broker reports to its caller."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OwnerMarker:
    issue: int
    branch: str
    session: str
    worktree: str
    created: str
    last_push_head: Optional[str]
    last_push_at: Optional[str]

    def as_json(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "issue": self.issue,
            "branch": self.branch,
            "session": self.session,
            "worktree": self.worktree,
            "created": self.created,
            "last_push_head": self.last_push_head,
            "last_push_at": self.last_push_at,
        }


def marker_path(git_dir: str | Path) -> Path:
    return Path(git_dir) / MARKER_NAME


def caller_session(environ: Optional[Mapping[str, str]] = None) -> str:
    """The calling session's identity, or an empty string when it is absent."""
    source = os.environ if environ is None else environ
    return (source.get(SESSION_ENV) or "").strip()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _invalid(detail: str) -> WorktreeOwnerError:
    return WorktreeOwnerError(CODE_CLAIM_INVALID, f"worktree ownership marker is invalid: {detail}")


def _validated(raw: object) -> OwnerMarker:
    if not isinstance(raw, dict):
        raise _invalid("top level value is not an object")
    keys = set(raw)
    if keys != MARKER_KEYS:
        missing = sorted(MARKER_KEYS - keys)
        unknown = sorted(keys - MARKER_KEYS)
        raise _invalid(f"exact key set required; missing={missing} unknown={unknown}")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise _invalid(f"unsupported schema_version {raw['schema_version']!r}")

    branch = raw["branch"]
    if not isinstance(branch, str) or not branch:
        raise _invalid("branch must be a non-empty string")
    try:
        name = ChangeName.parse_branch(branch)
    except ChangeNameError as exc:
        raise _invalid(f"branch is not a change branch: {exc}") from exc

    issue = raw["issue"]
    # `isinstance(True, int)` is True in Python, so booleans are excluded first.
    if isinstance(issue, bool) or not isinstance(issue, int):
        raise _invalid("issue must be an integer")
    if issue != name.issue_number:
        raise _invalid(f"issue {issue} does not match branch {branch}")

    session = raw["session"]
    if not isinstance(session, str) or SESSION_RE.fullmatch(session) is None:
        raise _invalid("session must be a bounded printable identifier")

    worktree = raw["worktree"]
    if not isinstance(worktree, str) or not os.path.isabs(worktree):
        raise _invalid("worktree must be an absolute path")

    created = raw["created"]
    if not isinstance(created, str) or not created.strip():
        raise _invalid("created must be a non-empty string")

    head = raw["last_push_head"]
    at = raw["last_push_at"]
    if head is not None and (not isinstance(head, str) or COMMIT_SHA_RE.fullmatch(head) is None):
        raise _invalid("last_push_head must be null or a 40 character lowercase sha")
    if at is not None and (not isinstance(at, str) or not at.strip()):
        raise _invalid("last_push_at must be null or a non-empty string")
    if (head is None) != (at is None):
        raise _invalid("last_push_head and last_push_at must be set together")

    return OwnerMarker(
        issue=issue,
        branch=branch,
        session=session,
        worktree=worktree,
        created=created,
        last_push_head=head,
        last_push_at=at,
    )


def read_marker(git_dir: str | Path) -> OwnerMarker:
    """Read and validate the marker. Missing and malformed are different codes:
    the first is a worktree nobody claimed, the second is a claim that cannot be
    trusted, and conflating them would send the reader to the wrong fix."""
    path = marker_path(git_dir)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise WorktreeOwnerError(
            CODE_UNCLAIMED,
            f"change worktree has no ownership marker at {path}; {CLAIM_HINT}",
        ) from exc
    except OSError as exc:
        raise _invalid(f"cannot read {path}: {exc}") from exc
    try:
        raw = json.loads(text)
    except ValueError as exc:
        raise _invalid(f"{path} is not valid JSON: {exc}") from exc
    return _validated(raw)


def write_marker(git_dir: str | Path, marker: OwnerMarker) -> Path:
    """Replace the marker atomically so a crash mid-write cannot leave a file
    that reads as `WORKTREE_CLAIM_INVALID` forever."""
    path = marker_path(git_dir)
    payload = json.dumps(marker.as_json(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, prefix=f".{MARKER_NAME}.", delete=False
    )
    try:
        with handle:
            handle.write(payload)
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
    return path


def claim(
    git_dir: str | Path,
    *,
    branch: str,
    session: str,
    worktree: str | Path,
    takeover: bool = False,
    now: Optional[str] = None,
) -> tuple[OwnerMarker, str]:
    """Bind this worktree to one session. Idempotent for the same owner.

    Returns the marker and one of `created` / `updated` / `no-op` / `taken-over`.
    A different session is refused unless `takeover` is explicit: a hand-off is
    a decision, and a silent one is exactly the event this Issue is about.
    """
    try:
        name = ChangeName.parse_branch(branch)
    except ChangeNameError as exc:
        raise WorktreeOwnerError(CODE_CLAIM_INVALID, f"not a change branch: {exc}") from exc
    if SESSION_RE.fullmatch(session or "") is None:
        raise WorktreeOwnerError(
            CODE_CLAIM_INVALID, "session must be a bounded printable identifier"
        )
    resolved = os.path.realpath(str(worktree))

    existing: Optional[OwnerMarker] = None
    discarded_invalid = False
    try:
        existing = read_marker(git_dir)
    except WorktreeOwnerError as exc:
        if exc.code == CODE_CLAIM_INVALID:
            # An unreadable marker is not a free pass: overwriting it silently
            # would hide whatever corrupted it. It takes the same explicit
            # hand-off flag as claiming over another live session.
            if not takeover:
                raise
            discarded_invalid = True
        elif exc.code != CODE_UNCLAIMED:
            raise

    if existing is None:
        marker = OwnerMarker(
            issue=name.issue_number,
            branch=branch,
            session=session,
            worktree=resolved,
            created=now or _now(),
            last_push_head=None,
            last_push_at=None,
        )
        write_marker(git_dir, marker)
        return marker, "taken-over" if discarded_invalid else "created"

    same_owner = existing.session == session and existing.branch == branch
    if not same_owner and not takeover:
        raise WorktreeOwnerError(
            CODE_OWNER_MISMATCH,
            f"worktree is already claimed by session {existing.session} for {existing.branch}; "
            "pass --takeover only when that session handed it back",
        )
    marker = OwnerMarker(
        issue=name.issue_number,
        branch=branch,
        session=session,
        worktree=resolved,
        created=existing.created,
        # The push ledger is a fact about the remote, not about the owner, so a
        # hand-off carries it across instead of resetting it to null.
        last_push_head=existing.last_push_head,
        last_push_at=existing.last_push_at,
    )
    if marker == existing:
        return marker, "no-op"
    write_marker(git_dir, marker)
    return marker, "updated" if same_owner else "taken-over"


def authorize_push(
    git_dir: str | Path, *, branch: str, session: str
) -> OwnerMarker:
    """Refuse unless the caller is this worktree's single writer.

    The three failure codes are distinct and none of them reuses
    `WORKTREE_DIRTY`, which describes an unrelated condition and would send the
    reader looking at their working tree instead of at who owns it.
    """
    marker = read_marker(git_dir)
    if marker.branch != branch:
        raise WorktreeOwnerError(
            CODE_OWNER_MISMATCH,
            f"worktree is claimed for {marker.branch}, not {branch}",
        )
    if not session:
        raise WorktreeOwnerError(
            CODE_OWNER_MISMATCH,
            f"{SESSION_ENV} is not set; this worktree is owned by session "
            f"{marker.session} and the owning session must identify itself on every push",
        )
    if session != marker.session:
        raise WorktreeOwnerError(
            CODE_OWNER_MISMATCH,
            f"worktree is owned by session {marker.session}, not {session}; "
            "the owning session pushes its own branch, another session notifies or hands back",
        )
    return marker


def record_push(
    git_dir: str | Path, *, head: str, now: Optional[str] = None
) -> OwnerMarker:
    """Record a push that already succeeded. Never called on a failed push: a
    sha written here is read back as `the remote has this`, and recording one
    that never landed would make the scan report a clean worktree that is not."""
    if COMMIT_SHA_RE.fullmatch(head or "") is None:
        raise _invalid("pushed head must be a 40 character lowercase sha")
    existing = read_marker(git_dir)
    marker = OwnerMarker(
        issue=existing.issue,
        branch=existing.branch,
        session=existing.session,
        worktree=existing.worktree,
        created=existing.created,
        last_push_head=head,
        last_push_at=now or _now(),
    )
    write_marker(git_dir, marker)
    return marker
