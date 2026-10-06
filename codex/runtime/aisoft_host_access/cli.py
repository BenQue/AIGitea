from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .broker import BrokerError, HostAccessBroker, credential_from_protocol
from .contract import AccessContractError, load_access_contract
from .profiles import ProfileMigrator


class _PreflightArgumentsInvalid(Exception):
    pass


class _PreflightArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse embeds arbitrary request values in errors, including values
        # of otherwise allowed flags supplied in the wrong position.
        raise _PreflightArgumentsInvalid() from None


def build_parser(*, sanitized_errors=False) -> argparse.ArgumentParser:
    parser_type = _PreflightArgumentParser if sanitized_errors else argparse.ArgumentParser
    parser = parser_type(prog="aisoft-host-access")
    parser.add_argument("--access-manifest", required=True)
    parser.add_argument("--governance-manifest", required=True)
    # Fixed install-time configuration supplied by the entrypoint, not a caller
    # argument: gitea.labels.provision needs the canonical label manifest (#108).
    parser.add_argument("--label-manifest")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate")

    broker = commands.add_parser("broker")
    broker.add_argument("--project", required=True)
    broker.add_argument("--operation", required=True)
    broker.add_argument("--target")
    broker.add_argument("--number", type=int)
    broker.add_argument("--reference")
    broker.add_argument("--state", choices=("open", "closed", "all"))
    broker.add_argument("--branch")
    broker.add_argument("--issue", type=int)
    broker.add_argument("--title")
    broker.add_argument("--body")
    broker.add_argument("--comment")
    broker.add_argument("--sha")
    broker.add_argument("--token-kind")
    # Actions job id (#143). Sourced from gitea.actions.run.read output, never
    # scraped out of a commit status target_url.
    broker.add_argument("--job", type=int)
    # The flow entrance a new Issue starts at (#243). Deliberately no choices=
    # and no default: the accepted pair is checked inside the broker against
    # both the entrance set and the installed label manifest, and a default here
    # would put the entrance back out of sight at the call site.
    broker.add_argument("--entry-label")
    # Deliberately no choices=: the accepted lifecycle states are derived from
    # the installed label manifest inside the broker (#115). Listing them here
    # would be another copy of the eight names and would drift from the manifest
    # this install actually ships.
    broker.add_argument("--lifecycle")
    # The analyzer dimensions (#160), same no-choices= rule as --lifecycle: the
    # accepted values come from the installed label manifest. Bare values, not
    # label names — they are copied straight out of the summary front matter,
    # and the broker is what namespaces them.
    broker.add_argument("--change-type")
    broker.add_argument("--complexity")
    # Project-owned label values stay out of every platform manifest. The broker
    # validates these typed scalars against the installed allowed-prefix set.
    broker.add_argument("--label")
    broker.add_argument("--color")
    broker.add_argument("--description")

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


def _reject_preflight_arguments():
    print(json.dumps({'status': 'BLOCKED_EXTERNAL', 'code': 'ARGUMENT_MISMATCH',
                      'message': 'operation arguments do not match the typed contract'}),
          file=sys.stderr)
    return 20


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    preflight = ('application.target.preflight.read' in raw_argv or
                 '--operation=application.target.preflight.read' in raw_argv)
    if preflight:
        # Reject duplicate/foreign flags before argparse can echo their values.
        allowed = {'--access-manifest', '--governance-manifest', '--label-manifest',
                   '--project', '--operation', '--target'}
        seen, index, invalid = set(), 0, False
        while index < len(raw_argv):
            token = raw_argv[index]
            flag = token.split('=', 1)[0]
            if token in ('broker', '--help', '-h'):
                if token in seen:
                    invalid = True
                seen.add(token)
                index += 1
                continue
            if flag not in allowed or flag in seen:
                invalid = True
                break
            seen.add(flag)
            if '=' in token:
                index += 1
            elif index + 1 < len(raw_argv) and not raw_argv[index + 1].startswith('-'):
                index += 2
            else:
                invalid = True
                break
        if invalid:
            return _reject_preflight_arguments()
    try:
        args = build_parser(sanitized_errors=preflight).parse_args(raw_argv)
    except _PreflightArgumentsInvalid:
        return _reject_preflight_arguments()
    try:
        contract = load_access_contract(args.access_manifest, args.governance_manifest)
        if args.command == "validate":
            _json({
                "status": "PASS",
                "contract_version": contract.raw["contract_version"],
                "project_count": len(contract.projects),
                "operation_count": len(contract.operations),
                "merge_operation_count": 1,
            })
            return 0
        if args.command == "broker":
            value = HostAccessBroker(
                contract, label_manifest_path=args.label_manifest
            ).execute(
                args.project,
                args.operation,
                number=args.number,
                **({"reference": args.reference} if args.reference is not None else {}),
                state=args.state,
                branch=args.branch,
                issue=args.issue,
                title=args.title,
                body=args.body,
                comment=args.comment,
                sha=args.sha,
                job=args.job,
                entry_label=args.entry_label,
                lifecycle=args.lifecycle,
                change_type=args.change_type,
                complexity=args.complexity,
                label=args.label,
                color=args.color,
                description=args.description,
                token_kind=args.token_kind,
                **({'target': args.target} if args.target is not None else {}),
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
                "path_prepend": list(project.vm_profile.path_prepend),
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
            "status": "NEEDS_HUMAN_DECISION" if code in {
                "DEPENDENCY_FORMAT_INVALID", "DEPENDENCY_SELF",
                "DEPENDENCY_DUPLICATE", "DEPENDENCY_TARGET_DENIED",
            } else "BLOCKED_EXTERNAL",
            "code": code,
            "message": 'preflight request was refused' if preflight else str(exc),
        }, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
