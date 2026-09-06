"""Bounded public CLI. Errors never echo supplied JSON or process output."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .bundle import build, verify
from .contract import (ACTIONS, BootstrapError, canonical, digest, load, read_regular,
                       require, write_new)
from .workflow import adoption_plan, operation_request, readback


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="aisoft-platform-bootstrap")
    sub = root.add_subparsers(dest="command", required=True)
    builder = sub.add_parser("build-bundle")
    builder.add_argument("--repository-root", type=Path, required=True)
    builder.add_argument("--approval", type=Path, required=True)
    builder.add_argument("--output-directory", type=Path, required=True)
    inventory = sub.add_parser("verify-inventory")
    inventory.add_argument("--input", type=Path, required=True)
    commands = [sub.add_parser(name) for name in ("verify-handoff", "adoption-plan", "apply", "rollback")]
    for command in commands:
        command.add_argument("--handoff", type=Path, required=True)
        command.add_argument("--archive", type=Path, required=True)
        command.add_argument("--expected-handoff-sha256", required=True)
    for command in commands[1:]:
        command.add_argument("--inventory", type=Path, required=True)
        command.add_argument("--target", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    for command in commands[2:]:
        command.add_argument("--expected-plan-sha256", required=True)
        command.add_argument("--action", choices=ACTIONS, required=True)
        command.add_argument("--dry-run", action="store_true")
    reader = sub.add_parser("readback")
    reader.add_argument("--request", type=Path, required=True)
    reader.add_argument("--expected-request-sha256", required=True)
    reader.add_argument("--observation", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build-bundle":
            result = build(args.repository_root, args.approval, args.output_directory)
        elif args.command == "verify-inventory":
            value = load(args.input, "inventory")
            result = {"status": "PASS", "validation_scope": "schema-only",
                      "inventory_sha256": digest(canonical(value)), "target_facts": "NOT_READ"}
        elif args.command == "readback":
            request_bytes = read_regular(args.request)
            require(digest(request_bytes) == args.expected_request_sha256, "CHECKSUM_MISMATCH")
            result = readback(load(args.request, "request"), load(args.observation, "observation"))
        else:
            manifest = verify(args.handoff, args.archive, args.expected_handoff_sha256)
            if args.command == "verify-handoff":
                result = {"status": "PASS", "source_sha": manifest["source_sha"],
                          "target_facts": "NOT_READ", "execution": "NOT RUN"}
            else:
                plan = adoption_plan(manifest, args.expected_handoff_sha256,
                                     load(args.inventory, "inventory"), load(args.target, "target"))
                if args.command == "adoption-plan":
                    result = plan
                else:
                    require(digest(canonical(plan)) == args.expected_plan_sha256, "STALE_PLAN")
                    result = operation_request(plan, args.action, args.command, dry_run=args.dry_run)
                write_new(args.output, canonical(result))
        sys.stdout.buffer.write(canonical(result))
        return 0 if result["status"] in ("PASS", "PLANNED", "DRY_RUN") else 2
    except (BootstrapError, OSError, RuntimeError) as exc:
        code = exc.code if isinstance(exc, BootstrapError) else "LOCAL_IO_ERROR"
        sys.stderr.buffer.write(canonical({"status": "BLOCKED", "code": code, "execution": "NOT RUN"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
