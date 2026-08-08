"""Stable CLI for the Docker release target runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .errors import ReleaseError
from .runner import ReleaseRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-docker-release")
    subparsers = parser.add_subparsers(dest="command", required=True)
    artifact = subparsers.add_parser("verify-artifact")
    artifact.add_argument("--release-root", required=True, type=Path)
    artifact.add_argument("--release-id", required=True)
    for command in (
        "verify-target",
        "stage",
        "migrate",
        "activate",
        "verify",
        "deploy",
        "status",
        "rollback",
    ):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--profile", required=True, type=Path)
        command_parser.add_argument("--release-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = ReleaseRuntime()
    try:
        operation = getattr(runtime, args.command.replace("-", "_"))
        if args.command == "verify-artifact":
            result = operation(args.release_root, args.release_id)
        else:
            result = operation(args.profile, args.release_id)
    except ReleaseError as exc:
        print(
            json.dumps(
                {"ok": False, "error_code": exc.code, "message": exc.safe_message},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") is True else 3


if __name__ == "__main__":
    raise SystemExit(main())
