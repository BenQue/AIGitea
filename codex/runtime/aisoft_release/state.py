"""Private atomic deployment state and a per-target process lock."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Mapping

from .contract import DIGEST, GIT_SHA, IDENTIFIER
from .errors import StateError


STATE_VERSION = "docker-release-state/v1"
SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:auth|authorization|token|password|secret|credential|"
    r"connection[_-]?string|certificate|ssh[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)


class StateStore:
    def __init__(self, root: Path, profile_id: str) -> None:
        self.root = root
        self.profile_id = profile_id
        self.path = root / "state.json"

    def empty(self) -> dict[str, object]:
        return {
            "contract_version": STATE_VERSION,
            "profile_id": self.profile_id,
            "current_release": None,
            "previous_release": None,
            "migrations": {},
            "last_result": "never-deployed",
        }

    def load(self) -> dict[str, object]:
        if not self.path.exists():
            return self.empty()
        _require_private_regular(self.path, "deployment state")
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateError("deployment state is unreadable or corrupt") from exc
        if not isinstance(value, dict):
            raise StateError("deployment state root must be an object")
        self._validate(value)
        return value

    def save(self, state: Mapping[str, object]) -> None:
        value = dict(state)
        self._validate(value)
        _reject_sensitive(value)
        try:
            encoded = (
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise StateError("deployment state is not JSON serializable") from exc
        _ensure_private_directory(self.root)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".state.", suffix=".tmp", dir=self.root
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
            directory_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    def _validate(self, value: Mapping[str, object]) -> None:
        expected = {
            "contract_version",
            "profile_id",
            "current_release",
            "previous_release",
            "migrations",
            "last_result",
        }
        if set(value) != expected:
            raise StateError("deployment state fields do not match state contract")
        if value.get("contract_version") != STATE_VERSION:
            raise StateError("deployment state contract_version is unsupported")
        if value.get("profile_id") != self.profile_id:
            raise StateError("deployment state profile_id does not match target")
        for field in ("current_release", "previous_release"):
            release = value.get(field)
            if release is not None and (
                not isinstance(release, str) or not GIT_SHA.fullmatch(release)
            ):
                raise StateError(f"deployment state {field} is invalid")
        migrations = value.get("migrations")
        if not isinstance(migrations, Mapping):
            raise StateError("deployment state migrations must be an object")
        for identity, record in migrations.items():
            if not isinstance(identity, str) or not DIGEST.fullmatch(identity):
                raise StateError("deployment state migration identity is invalid")
            if not isinstance(record, Mapping) or set(record) != {"status", "release_id"}:
                raise StateError("deployment state migration record is invalid")
            if record.get("status") not in {"started", "completed", "failed"}:
                raise StateError("deployment state migration status is invalid")
            release = record.get("release_id")
            if not isinstance(release, str) or not GIT_SHA.fullmatch(release):
                raise StateError("deployment state migration release_id is invalid")
        result = value.get("last_result")
        if not isinstance(result, str) or not IDENTIFIER.fullmatch(result):
            raise StateError("deployment state last_result is invalid")
        _reject_sensitive(value)


class DeploymentLock:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / "deploy.lock"
        self.descriptor: int | None = None

    def __enter__(self) -> "DeploymentLock":
        _ensure_private_directory(self.root)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(descriptor)
            raise StateError("another release operation owns the target lock") from exc
        self.descriptor = descriptor
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.descriptor is None:
            return
        descriptor = self.descriptor
        self.descriptor = None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _ensure_private_directory(path: Path) -> None:
    if path.exists():
        try:
            info = path.lstat()
        except OSError as exc:
            raise StateError("state root is unavailable") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise StateError("state root must be a regular directory")
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise StateError("state root mode must be 0700")
        return
    try:
        path.mkdir(parents=True, mode=0o700)
        os.chmod(path, 0o700)
    except OSError as exc:
        raise StateError("state root could not be created") from exc


def _require_private_regular(path: Path, context: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise StateError(f"{context} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise StateError(f"{context} must be a regular file")
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise StateError(f"{context} mode must be 0600")


def _reject_sensitive(value: object, path: str = "state") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            text = str(key)
            if SENSITIVE_KEY.search(text):
                raise StateError(f"sensitive field is forbidden in state: {path}.{text}")
            _reject_sensitive(nested, f"{path}.{text}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive(nested, f"{path}[{index}]")
