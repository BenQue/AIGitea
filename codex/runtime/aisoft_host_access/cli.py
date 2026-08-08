from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .broker import BrokerError, HostAccessBroker, credential_from_protocol
from .contract import AccessContractError, load_access_contract
from .profiles import ProfileMigrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-host-access")
    parser.add_argument("--access-manifest", required=True)
    parser.add_argument("--governance-manifest", required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate")

    broker = commands.add_parser("broker")
    broker.add_argument("--project", required=True)
    broker.add_argument("--operation", required=True)
    broker.add_argument("--number", type=int)
    broker.add_argument("--state", choices=("open", "closed", "all"))
    broker.add_argument("--branch")

    profile = commands.add_parser("profile")
    profile.add_argument("--project", required=True)
    profile.add_argument("--action", required=True,
                         choices=("plan", "apply", "read-back", "rollback"))

    spec = commands.add_parser("profile-spec")
    spec.add_argument("--profile-name", required=True)

    consume = commands.add_parser("profile-consume-check")
    consume.add_argument("--profile-name", required=True)

    credential = commands.add_parser("credential-helper")
    credential.add_argument("action", nargs="?", default="get")
    return parser


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        contract = load_access_contract(args.access_manifest, args.governance_manifest)
        if args.command == "validate":
            _json({
                "status": "PASS",
                "contract_version": contract.raw["contract_version"],
                "project_count": len(contract.projects),
                "operation_count": len(contract.operations),
                "merge_operation_count": 0,
            })
            return 0
        if args.command == "broker":
            value = HostAccessBroker(contract).execute(
                args.project,
                args.operation,
                number=args.number,
                state=args.state,
                branch=args.branch,
            )
            _json(value)
            return 0
        if args.command == "profile":
            try:
                project = contract.project(args.project)
            except AccessContractError as exc:
                raise BrokerError("TARGET_DENIED", "project is not in the migration manifest") from exc
            if project.vm_profile is None:
                raise BrokerError("TARGET_DENIED", "project has no approved VM profile migration")
            migrator = ProfileMigrator(
                contract, home=contract.raw["vm_profile_policy"]["runtime_home"]
            )
            method = getattr(migrator, args.action.replace("-", "_"))
            _json(method(args.project))
            return 0
        if args.command == "profile-spec":
            project = contract.project_for_profile(args.profile_name)
            assert project.vm_profile is not None
            policy = contract.raw["vm_profile_policy"]
            home = Path(contract.raw["vm_profile_policy"]["runtime_home"])
            _json({
                "project_id": project.project_id,
                "profile_name": project.vm_profile.name,
                "gitea_url": contract.governance.base_url,
                "owner": contract.governance.owner,
                "repository": project.repository,
                "identity": project.project_agent,
                "token_file": str(home / policy["token_root"] / f"{project.vm_profile.name}.token"),
                "repo_dir": str(home / project.vm_profile.repo_dir),
                "analysis_provider": project.vm_profile.analysis_provider,
                "implement_provider": project.vm_profile.implement_provider,
            })
            return 0
        if args.command == "profile-consume-check":
            project = contract.project_for_profile(args.profile_name)
            migrator = ProfileMigrator(
                contract, home=contract.raw["vm_profile_policy"]["runtime_home"]
            )
            _json(migrator.consume_check(project.project_id))
            return 0
        if args.command == "credential-helper":
            if sys.stdout.isatty():
                raise BrokerError("CREDENTIAL_PROTOCOL_INVALID",
                                  "credential helper refuses terminal output")
            output = credential_from_protocol(contract, args.action, sys.stdin.read())
            sys.stdout.write(output)
            return 0
        raise BrokerError("COMMAND_INVALID", "unknown host access command")
    except (AccessContractError, BrokerError, OSError, ValueError) as exc:
        code = exc.code if isinstance(exc, BrokerError) else "CONTRACT_INVALID"
        print(json.dumps({
            "status": "BLOCKED_EXTERNAL",
            "code": code,
            "message": str(exc),
        }, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
