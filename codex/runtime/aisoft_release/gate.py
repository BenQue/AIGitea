"""Root-owned fixed-action gate for independently authorized lifecycle phases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Mapping, Sequence

from .contract import GIT_SHA, IDENTIFIER
from .errors import GateError


GATE_VERSION = "docker-release-command-gate/v1"
GATE_ROOT = Path("/etc/aisoft-docker-release/action-grants")
CLI_PATH = Path("/usr/local/bin/aisoft-docker-release")
ALLOWED_ACTIONS = {
    "verify-target",
    "stage",
    "migrate",
    "activate",
    "status",
    "rollback",
}
SAFE_ENV = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
}


def run_gate(
    action: str,
    target_id: str,
    release_id: str,
    *,
    gate_root: Path = GATE_ROOT,
    cli_path: Path = CLI_PATH,
    enforce_root_owner: bool = True,
) -> int:
    if action not in ALLOWED_ACTIONS:
        raise GateError("action is not allowed by the fixed lifecycle gate")
    if not IDENTIFIER.fullmatch(target_id):
        raise GateError("target_id is invalid")
    if not GIT_SHA.fullmatch(release_id):
        raise GateError("release_id must be a lowercase 40-character Git SHA")
    if enforce_root_owner and os.geteuid() != 0:
        raise GateError("fixed lifecycle gate must run as root")
    _require_directory(gate_root, "action grant root", enforce_root_owner)
    action_root = gate_root / action
    _require_directory(action_root, "action grant directory", enforce_root_owner)
    grant_path = action_root / f"{target_id}.json"
    _require_protected(grant_path, "action grant", enforce_root_owner)
    grant = _load_grant(grant_path)
    if grant["action"] != action or grant["target_id"] != target_id:
        raise GateError("action grant identity does not match invocation")
    profile = Path(str(grant["profile"]))
    audit_log = Path(str(grant["audit_log"]))
    if not profile.is_absolute() or not audit_log.is_absolute():
        raise GateError("action grant profile and audit_log must be absolute paths")
    command = [
        str(cli_path),
        action,
        "--profile",
        str(profile),
        "--release-id",
        release_id,
    ]
    common = {
        "action": action,
        "target_id": target_id,
        "release_id": release_id,
    }
    _append_audit(
        audit_log,
        {**common, "event": "started"},
        enforce_root_owner=enforce_root_owner,
    )
    try:
        completed = subprocess.run(command, shell=False, check=False, env=SAFE_ENV)
    except OSError as exc:
        _append_audit(
            audit_log,
            {**common, "event": "completed", "exit_code": 127},
            enforce_root_owner=enforce_root_owner,
        )
        raise GateError("fixed lifecycle command could not be executed") from exc
    _append_audit(
        audit_log,
        {**common, "event": "completed", "exit_code": completed.returncode},
        enforce_root_owner=enforce_root_owner,
    )
    return completed.returncode


def _load_grant(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, GateError) as exc:
        raise GateError("action grant is unreadable or invalid") from exc
    required = {"contract_version", "action", "target_id", "profile", "audit_log"}
    if not isinstance(value, Mapping) or set(value) != required:
        raise GateError("action grant fields do not match gate contract")
    if value.get("contract_version") != GATE_VERSION:
        raise GateError("action grant contract_version is unsupported")
    if value.get("action") not in ALLOWED_ACTIONS:
        raise GateError("action grant action is not allowed")
    for key in ("target_id", "profile", "audit_log"):
        if not isinstance(value.get(key), str):
            raise GateError(f"action grant {key} must be a string")
    return value


def _append_audit(
    path: Path,
    record: Mapping[str, object],
    *,
    enforce_root_owner: bool,
) -> None:
    parent = path.parent
    _require_directory(parent, "audit directory", enforce_root_owner)
    if path.exists():
        _require_protected(path, "audit log", enforce_root_owner, exact_mode=0o600)
    value = {
        **record,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    encoded = (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require_directory(path: Path, context: str, enforce_root_owner: bool) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise GateError(f"{context} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise GateError(f"{context} must be a regular directory")
    if stat.S_IMODE(info.st_mode) & 0o022:
        raise GateError(f"{context} must not be group/world writable")
    if enforce_root_owner and info.st_uid != 0:
        raise GateError(f"{context} must be root-owned")


def _require_protected(
    path: Path,
    context: str,
    enforce_root_owner: bool,
    *,
    exact_mode: int | None = None,
) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise GateError(f"{context} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise GateError(f"{context} must be a regular file")
    mode = stat.S_IMODE(info.st_mode)
    if exact_mode is not None and mode != exact_mode:
        raise GateError(f"{context} mode is invalid")
    if exact_mode is None and mode not in {0o400, 0o600}:
        raise GateError(f"{context} mode must be 0400 or 0600")
    if enforce_root_owner and info.st_uid != 0:
        raise GateError(f"{context} must be root-owned")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GateError("action grant contains a duplicate JSON field")
        result[key] = value
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-docker-release-gate")
    parser.add_argument("action", choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("target_id")
    parser.add_argument("release_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_gate(args.action, args.target_id, args.release_id)
    except GateError as exc:
        print(
            json.dumps(
                {"ok": False, "error_code": exc.code, "message": exc.safe_message},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
