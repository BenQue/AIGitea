"""Stable machine-readable CLI for company delivery operator contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .collector import collect_inventory
from .contract import CompanyDeliveryError, load_evidence, load_handoff, load_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-company-delivery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("verify-inventory")
    inventory.add_argument("--input", required=True, type=Path)

    evidence = subparsers.add_parser("verify-evidence")
    evidence.add_argument("--input", required=True, type=Path)

    handoff = subparsers.add_parser("verify-handoff")
    handoff.add_argument("--manifest", required=True, type=Path)
    handoff.add_argument("--bundle-root", required=True, type=Path)

    collect = subparsers.add_parser("collect-inventory")
    collect.add_argument("--role", required=True, choices=("scm-ci", "appserver-prod"))
    collect.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "collect-inventory":
            value = collect_inventory(args.role, args.output)
        elif args.command == "verify-inventory":
            value = load_inventory(args.input)
        elif args.command == "verify-evidence":
            value = load_evidence(args.input)
        else:
            value = load_handoff(args.manifest, bundle_root=args.bundle_root)
    except CompanyDeliveryError as exc:
        print(
            json.dumps(
                {"error_code": exc.code, "message": exc.safe_message, "ok": False},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(
            {"contract_version": value["contract_version"], "ok": True},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
