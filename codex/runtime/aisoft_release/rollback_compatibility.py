"""Fail-closed proof that the old image may use this database revision."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from .contract import DIGEST, GIT_SHA, HOSTNAME, IDENTIFIER, COMPOSE_PROJECT, REPOSITORY, SHA256_HEX, ReleaseFiles, TargetProfile
from .errors import RollbackBlocked

EVIDENCE_VERSION = "docker-migration-rollback-compatibility/v1"
MAX_EVIDENCE_BYTES = 256 * 1024
MAX_RECORDS = 128
TARGET_FIELDS = ("profile_id", "environment", "expected_hostname", "compose_project", "source_repository")
UTC_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)$")
RECORD_FIELDS = set(TARGET_FIELDS) | {
    "candidate_release", "rollback_release", "candidate_manifest_sha256",
    "rollback_manifest_sha256", "candidate_migration_identity", "rollback_migration_identity",
    "database_migration_identity", "database_state_sha256", "verified_at", "expires_at",
    "evidence_id", "result",
}


def require_rollback_compatible(
    profile: TargetProfile, candidate: ReleaseFiles, rollback: ReleaseFiles,
    state: Mapping[str, object], *, now: datetime | None = None,
) -> None:
    revision = state["database_revision"]
    migrations = state["migrations"]
    if revision["status"] == "uncertain" or any(
        record["status"] in {"started", "failed"} for record in migrations.values()
    ):
        raise RollbackBlocked("rollback blocked by unresolved database migration")
    candidate_identity = candidate.manifest.migration.identity if candidate.manifest.migration else None
    rollback_identity = rollback.manifest.migration.identity if rollback.manifest.migration else None
    receipt = migrations.get(candidate_identity)
    if (
        revision["status"] == "known" and candidate_identity is not None
        and candidate_identity == rollback_identity == revision["migration_identity"]
        and isinstance(receipt, Mapping) and receipt["status"] == "completed"
    ):
        return
    if profile.rollback_compatibility_file is None:
        raise RollbackBlocked("rollback requires exact trusted database compatibility evidence")
    try:
        envelope = _read_evidence(profile)
        if not isinstance(envelope, dict) or set(envelope) != {"contract_version", "records"}:
            raise ValueError
        if envelope["contract_version"] != EVIDENCE_VERSION:
            raise ValueError
        records = envelope["records"]
        if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
            raise ValueError
        expected = {
            **target_namespace(profile),
            "candidate_release": candidate.manifest.release_id,
            "rollback_release": rollback.manifest.release_id,
            "candidate_manifest_sha256": _manifest_sha256(candidate),
            "rollback_manifest_sha256": _manifest_sha256(rollback),
            "candidate_migration_identity": candidate_identity,
            "rollback_migration_identity": rollback_identity,
            "database_state_sha256": database_state_sha256(profile, state),
        }
        clock = now or datetime.now(timezone.utc)
        if clock.tzinfo is None:
            raise ValueError
        matches = []
        for record in records:
            _validate_record(record)
            if all(record[key] == value for key, value in expected.items()):
                matches.append(record)
        if len(matches) != 1:
            raise ValueError
        record = matches[0]
        if revision["status"] == "known" and record["database_migration_identity"] != revision["migration_identity"]:
            raise ValueError
        if not _utc(record["verified_at"]) <= clock < _utc(record["expires_at"]):
            raise ValueError
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise RollbackBlocked("rollback compatibility evidence is invalid, stale or ambiguous") from exc


def target_namespace(profile: TargetProfile) -> dict[str, object]:
    return {key: getattr(profile, key) for key in TARGET_FIELDS}


def database_state_sha256(profile: TargetProfile, state: Mapping[str, object]) -> str:
    """No container pointers, last_result or environment content enter this proof."""
    encoded = json.dumps({"target": target_namespace(profile),
                          "database_revision": state["database_revision"],
                          "migrations": state["migrations"]},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _manifest_sha256(files: ReleaseFiles) -> str:
    return hashlib.sha256(files.manifest_path.read_bytes()).hexdigest()


def _utc(value: str) -> datetime:
    if not UTC_TIMESTAMP.fullmatch(value):
        raise ValueError
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_record(record: object) -> None:
    if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
        raise ValueError
    patterns = {"profile_id": IDENTIFIER, "expected_hostname": HOSTNAME,
                "compose_project": COMPOSE_PROJECT, "source_repository": REPOSITORY,
                "candidate_release": GIT_SHA, "rollback_release": GIT_SHA,
                "candidate_manifest_sha256": SHA256_HEX, "rollback_manifest_sha256": SHA256_HEX,
                "database_state_sha256": SHA256_HEX, "evidence_id": IDENTIFIER}
    for key, pattern in patterns.items():
        if not isinstance(record[key], str) or not pattern.fullmatch(record[key]):
            raise ValueError
    for key in ("candidate_migration_identity", "rollback_migration_identity", "database_migration_identity"):
        value = record[key]
        if value is not None and (not isinstance(value, str) or not DIGEST.fullmatch(value)):
            raise ValueError
    if record["environment"] not in {"test", "production"} or record["result"] != "compatible":
        raise ValueError
    for key in ("verified_at", "expires_at"):
        if not isinstance(record[key], str):
            raise ValueError
    if _utc(record["verified_at"]) >= _utc(record["expires_at"]):
        raise ValueError


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _read_evidence(profile: TargetProfile) -> object:
    """Traverse pinned directory descriptors; validate the opened inode before reading."""
    path = profile.rollback_compatibility_file
    assert path is not None
    owner = profile.owner_uid
    if owner is None:
        raise ValueError
    directory_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    file_fd = None
    try:
        for part in path.parent.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
            info = os.fstat(directory_fd)
            # Root-owned sticky system temp ancestors are safe traversal anchors;
            # the operator parent below must still be private and owned.
            if info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX):
                raise ValueError
        parent_info = os.fstat(directory_fd)
        if parent_info.st_mode & 0o022 or parent_info.st_uid not in {0, owner}:
            raise ValueError
        file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) not in {0o400, 0o600}:
            raise ValueError
        if before.st_uid not in {0, owner} or before.st_size > MAX_EVIDENCE_BYTES:
            raise ValueError
        chunks = []
        size = 0
        while True:
            chunk = os.read(file_fd, min(65536, MAX_EVIDENCE_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_EVIDENCE_BYTES:
                raise ValueError
        after = os.fstat(file_fd)
        named = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ) or (named.st_dev, named.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError
        parent_now = path.parent.stat()
        if (parent_now.st_dev, parent_now.st_ino) != (parent_info.st_dev, parent_info.st_ino):
            raise ValueError
        return json.loads(b"".join(chunks).decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)
