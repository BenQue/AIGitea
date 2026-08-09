#!/usr/bin/env python3
"""Issue #65 real-E2E driver for the existing public release lifecycle seam."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from aisoft_release.docker import DockerAdapter
from aisoft_release.errors import ReleaseError
from aisoft_release.runner import ReleaseRuntime


PHASES = (
    "verify-artifact",
    "verify-target",
    "stage",
    "migrate",
    "activate",
    "status",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docker-release-v2-lifecycle-driver")
    parser.add_argument("action", choices=PHASES)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--compatibility-matrix", required=True, type=Path)
    parser.add_argument("--docker", required=True)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--new-process-group", action="store_true")
    parser.add_argument("--process-group-ready-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.new_process_group:
        os.setpgrp()
        if args.process_group_ready_file is None:
            return _usage_error("--new-process-group requires --process-group-ready-file")
        _write_process_group_ready(args.process_group_ready_file)
    elif args.process_group_ready_file is not None:
        return _usage_error("--process-group-ready-file requires --new-process-group")
    if args.action == "verify-artifact":
        if args.release_root is None or args.profile is not None:
            return _usage_error("verify-artifact requires only --release-root")
    elif args.profile is None or args.release_root is not None:
        return _usage_error(f"{args.action} requires only --profile")

    runtime = ReleaseRuntime(
        DockerAdapter(
            args.docker,
            compatibility_path=args.compatibility_matrix,
        ),
        hostname=args.hostname,
    )
    try:
        operation = getattr(runtime, args.action.replace("-", "_"))
        target = args.release_root if args.action == "verify-artifact" else args.profile
        result = operation(target, args.release_id)
    except ReleaseError as exc:
        print(
            json.dumps(
                _release_error_payload(exc),
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") is True else 3


def _usage_error(message: str) -> int:
    print(json.dumps({"ok": False, "message": message}, sort_keys=True), file=sys.stderr)
    return 2


def _release_error_payload(exc: ReleaseError) -> dict[str, object]:
    """Keep one safe typed cause for the Issue #65 failure evidence."""

    payload: dict[str, object] = {
        "ok": False,
        "error_code": exc.code,
        "message": exc.safe_message,
    }
    cause = exc.__cause__
    if isinstance(cause, ReleaseError):
        payload["cause"] = {
            "error_code": cause.code,
            "message": cause.safe_message,
        }
    return payload


def _write_process_group_ready(path: Path) -> None:
    payload = json.dumps(
        {"pid": os.getpid(), "pgid": os.getpgrp()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
