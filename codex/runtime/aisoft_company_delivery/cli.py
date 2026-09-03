"""Stable machine-readable CLI for company delivery operator contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bundle import build_bundle, verify_bundle
from .collector import collect_inventory, sync_timer_unit_from_handoff
from .contract import (
    CompanyDeliveryError,
    load_evidence,
    load_inventory,
    verify_gitea_transition,
    verify_legacy_health,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-company-delivery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("verify-inventory")
    inventory.add_argument("--input", required=True, type=Path)

    transition = subparsers.add_parser("verify-gitea-transition")
    transition.add_argument("--input", required=True, type=Path)
    transition.add_argument("--scm-inventory", required=True, type=Path)
    transition.add_argument("--appserver-inventory", required=True, type=Path)
    transition.add_argument("--handoff-manifest", required=True, type=Path)
    transition.add_argument("--postgresql-package-manifest", required=True, type=Path)

    legacy = subparsers.add_parser("verify-legacy-health")
    legacy.add_argument("--transition", required=True, type=Path)
    legacy.add_argument("--post-inventory", required=True, type=Path)

    evidence = subparsers.add_parser("verify-evidence")
    evidence.add_argument("--input", required=True, type=Path)

    handoff = subparsers.add_parser("verify-handoff")
    handoff.add_argument("--manifest", required=True, type=Path)
    handoff.add_argument("--bundle-root", required=True, type=Path)

    collect = subparsers.add_parser("collect-inventory")
    collect.add_argument("--role", required=True, choices=("scm-ci", "appserver-prod"))
    collect.add_argument("--output", required=True, type=Path)
    collect.add_argument("--mode", choices=("preflight", "post-install"))
    # scm-ci only: the sync timer unit is read from the verified handoff
    # manifest, never typed by hand and never defaulted by the runtime.
    collect.add_argument("--handoff-manifest", type=Path)

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
    bundle.add_argument("--compatibility-matrix", required=True, type=Path)
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
                compatibility_matrix=args.compatibility_matrix,
            )
        elif args.command == "collect-inventory":
            sync_timer_unit = None
            if args.handoff_manifest is not None:
                if args.role != "scm-ci":
                    raise CompanyDeliveryError(
                        "INVALID_ARGUMENT", "appserver inventory does not accept SCM-only options"
                    )
                sync_timer_unit = sync_timer_unit_from_handoff(args.handoff_manifest)
            value = collect_inventory(
                args.role,
                args.output,
                mode=args.mode,
                sync_timer_unit=sync_timer_unit,
            )
        elif args.command == "verify-inventory":
            value = load_inventory(args.input)
        elif args.command == "verify-gitea-transition":
            value = verify_gitea_transition(
                args.input,
                args.scm_inventory,
                args.appserver_inventory,
                args.handoff_manifest,
                args.postgresql_package_manifest,
            )
        elif args.command == "verify-legacy-health":
            value = verify_legacy_health(args.transition, args.post_inventory)
        elif args.command == "verify-evidence":
            value = load_evidence(args.input)
        elif args.command == "verify-handoff":
            value = verify_bundle(args.manifest, args.bundle_root)
        else:
            raise CompanyDeliveryError("INVALID_ARGUMENT", "command is outside the operator allowlist")
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
    elif args.command == "verify-gitea-transition":
        output.update({"decision": value["decision"], "outcome": value["outcome"]})
    elif args.command == "verify-legacy-health":
        output.update(
            {
                "decision": value["decision"],
                "legacy_invariant": value["legacy_invariant"],
                "stages_30_40": value["stages_30_40"],
            }
        )
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
