"""Atomic local state, global lock, and bounded retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping, Optional


class StateError(ValueError):
    """State is invalid or unsafe to persist."""


class LockUnavailable(RuntimeError):
    """Another controller already owns the single active-Issue lock."""


class TerminalState(str, Enum):
    CONTINUE = "CONTINUE"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    NEEDS_HUMAN_DECISION = "NEEDS_HUMAN_DECISION"
    BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
    FAILED_LIMIT = "FAILED_LIMIT"


SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:auth|authorization|token|password|secret|credential)(?:$|[_-])",
    re.IGNORECASE,
)


class StateStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def load(self, issue_number: int) -> dict[str, object]:
        target = self._target(issue_number)
        if not target.exists():
            return {}
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateError(f"state file is unreadable or corrupt: {target}") from exc
        if not isinstance(value, dict):
            raise StateError("state root must be a JSON object")
        _reject_sensitive(value)
        return value

    def save(self, issue_number: int, state: Mapping[str, object]) -> None:
        target = self._target(issue_number)
        if not isinstance(state, Mapping):
            raise StateError("state root must be a mapping")
        serializable = dict(state)
        _reject_sensitive(serializable)
        try:
            encoded = json.dumps(
                serializable,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"
        except (TypeError, ValueError) as exc:
            raise StateError("state must contain JSON-serializable values") from exc

        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(target.parent, 0o700)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{issue_number}.", suffix=".tmp", dir=target.parent
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb", closefd=True) as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            os.chmod(target, 0o600)
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    def _target(self, issue_number: int) -> Path:
        if not isinstance(issue_number, int) or issue_number <= 0:
            raise StateError("issue number must be a positive integer")
        return self.root / "issues" / f"{issue_number}.json"


class GlobalLock:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._fd: Optional[int] = None

    def acquire(self) -> "GlobalLock":
        if self._fd is not None:
            raise StateError("lock is already held by this object")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise LockUnavailable("another Development Loop is active") from exc
        self._fd = fd
        return self

    def release(self) -> None:
        if self._fd is None:
            return
        fd = self._fd
        self._fd = None
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def __enter__(self) -> "GlobalLock":
        return self.acquire()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


@dataclass
class LoopBudget:
    max_rounds: int = 8
    max_same_root: int = 3
    rounds: int = 0
    last_root_cause: str = ""
    consecutive_same_root: int = 0

    def __post_init__(self) -> None:
        if self.max_rounds <= 0 or self.max_same_root <= 0:
            raise StateError("Loop limits must be positive")
        if self.rounds < 0 or self.consecutive_same_root < 0:
            raise StateError("Loop counters must not be negative")
        if self.rounds > self.max_rounds:
            raise StateError("round counter exceeds configured maximum")

    def start_round(self) -> Optional[TerminalState]:
        if self.rounds >= self.max_rounds:
            return TerminalState.FAILED_LIMIT
        self.rounds += 1
        return None

    def record_failure(self, root_cause: str) -> Optional[TerminalState]:
        normalized = root_cause.strip()
        if not normalized:
            raise StateError("root cause must not be empty")
        if normalized == self.last_root_cause:
            self.consecutive_same_root += 1
        else:
            self.last_root_cause = normalized
            self.consecutive_same_root = 1
        if self.consecutive_same_root >= self.max_same_root:
            return TerminalState.FAILED_LIMIT
        return None

    def clear_failure(self) -> None:
        self.last_root_cause = ""
        self.consecutive_same_root = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "max_rounds": self.max_rounds,
            "max_same_root": self.max_same_root,
            "rounds": self.rounds,
            "last_root_cause": self.last_root_cause,
            "consecutive_same_root": self.consecutive_same_root,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "LoopBudget":
        try:
            return cls(
                max_rounds=int(value.get("max_rounds", 8)),
                max_same_root=int(value.get("max_same_root", 3)),
                rounds=int(value.get("rounds", 0)),
                last_root_cause=str(value.get("last_root_cause", "")),
                consecutive_same_root=int(value.get("consecutive_same_root", 0)),
            )
        except (TypeError, ValueError) as exc:
            raise StateError("invalid serialized Loop budget") from exc


def default_state_root() -> Path:
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state) / "aisoft-loop"
    return Path.home() / ".local" / "state" / "aisoft-loop"


def _reject_sensitive(value: object, path: str = "state") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if SENSITIVE_KEY.search(key_text):
                raise StateError(f"sensitive key is forbidden in persisted state: {path}.{key_text}")
            _reject_sensitive(nested, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive(nested, f"{path}[{index}]")
