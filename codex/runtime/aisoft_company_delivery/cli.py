"""Stable machine-readable CLI for company delivery operator contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bundle import build_bundle, verify_bundle
from .collector import collect_inventory
from .contract import CompanyDeliveryError, load_evidence, load_inventory


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
    collect.add_argument("--mode", choices=("preflight", "post-install"))
    collect.add_argument("--legacy-gitea-http-port", type=_port)

    bundle = subparsers.add_parser("build-bundle")
    bundle.add_argument("--repository-root", required=True, type=Path)
    bundle.add_argument("--source-sha", required=True)
    bundle.add_argument("--release-root", required=True, type=Path)
    bundle.add_argument("--release-id", required=True)
    bundle.add_argument("--output-directory", required=True, type=Path)
    bundle.add_argument("--created-at", required=True)
    bundle.add_argument(
        "--source-transport",
        required=True,
        choices=("approved-bundle", "allowlisted-github-ref"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build-bundle":
            value = build_bundle(
                repository_root=args.repository_root,
                source_sha=args.source_sha,
                release_root=args.release_root,
                release_id=args.release_id,
                output_directory=args.output_directory,
                created_at=args.created_at,
                source_transport=args.source_transport,
            )
        elif args.command == "collect-inventory":
            value = collect_inventory(
                args.role,
                args.output,
                mode=args.mode,
                legacy_gitea_http_port=args.legacy_gitea_http_port,
            )
        elif args.command == "verify-inventory":
            value = load_inventory(args.input)
        elif args.command == "verify-evidence":
            value = load_evidence(args.input)
        else:
            value = verify_bundle(args.manifest, args.bundle_root)
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
    output = {"contract_version": value["contract_version"], "ok": True}
    if args.command == "build-bundle":
        output.update(
            {
                "archive_name": value["archive_name"],
                "archive_sha256": value["archive_sha256"],
                "bundle_name": value["bundle_name"],
                "release_id": value["release_id"],
                "source_sha": value["source_sha"],
            }
        )
    elif args.command == "verify-handoff":
        output.update(
            {
                "docker_calls": value["docker_calls"],
                "release_id": value["release_id"],
                "target_facts": value["target_facts"],
            }
        )
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


def _port(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise argparse.ArgumentTypeError("port must be a decimal number")
    parsed = int(value, 10)
    if not 1 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
