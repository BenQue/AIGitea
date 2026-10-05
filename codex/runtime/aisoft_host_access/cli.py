from __future__ import annotations

import argparse
import json
import hashlib
import os
import sys
from pathlib import Path

from .broker import (BrokerError, HostAccessBroker, ReadCollection, credential_from_protocol,
                     _pull_stdout, PULL_LIMIT, PULL_MAX_PAGES, PULL_MAX_COUNT,
                     CHANGE_READ_MAX_REFS, COMMIT_SHA_RE)
from aisoft_change_name import ChangeName, ChangeNameError
from .contract import AccessContractError, load_access_contract
from .profiles import ProfileMigrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-host-access")
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


PULL_RECEIPT_FIELDS = frozenset({
    "schema", "status", "project", "repository", "operation", "identity", "state",
    "count", "server_total", "scan_count", "terminal_empty_pages", "limit",
    "max_pages_per_scan", "observed_at", "stdout_sha256",
})
NAMESPACE_RECEIPT_FIELDS = frozenset({
    "schema", "status", "project", "repository", "operation", "identity", "issue",
    "branch", "checkout", "remote_name", "scan_count", "complete", "refs",
    "requested_head", "observed_at",
})


def _receipt_error() -> BrokerError:
    return BrokerError("RESPONSE_SCHEMA_INVALID", "broker public read receipt is invalid")


def _validate_scope(receipt, contract, project, operation):
    if type(receipt) is not dict:
        raise _receipt_error()
    expected = {
        "project": project.project_id, "repository": f"{contract.governance.owner}/{project.repository}",
        "operation": operation, "identity": project.project_agent,
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise _receipt_error()


def _validate_namespace(receipt, contract, args):
    if type(receipt) is not dict or set(receipt) != NAMESPACE_RECEIPT_FIELDS:
        raise _receipt_error()
    _validate_scope(receipt, contract, contract.project(args.project), "git.fetch.change")
    if (receipt["schema"] != "aisoft.broker.change-namespace/v1" or receipt["status"] != "PASS"
        or args.project != "aisoft-platform" or receipt["branch"] != args.branch
        or type(receipt["issue"]) is not int or receipt["issue"] != 333
        or type(receipt["scan_count"]) is not int or receipt["scan_count"] != 2
        or receipt["complete"] is not True or type(receipt["observed_at"]) is not int
        or receipt["observed_at"] <= 0 or type(receipt["checkout"]) is not str
        or not os.path.isabs(receipt["checkout"]) or type(receipt["remote_name"]) is not str
        or not receipt["remote_name"] or type(receipt["refs"]) is not list
        or len(receipt["refs"]) > CHANGE_READ_MAX_REFS):
        raise _receipt_error()
    heads = {}
    for item in receipt["refs"]:
        if type(item) is not dict or set(item) != {"branch", "sha"} or type(item["branch"]) is not str or type(item["sha"]) is not str:
            raise _receipt_error()
        try:
            name = ChangeName.parse_branch(item["branch"])
        except ChangeNameError as exc:
            raise _receipt_error() from exc
        if name.issue_number != 333 or item["branch"] in heads or COMMIT_SHA_RE.fullmatch(item["sha"]) is None:
            raise _receipt_error()
        heads[item["branch"]] = item["sha"]
    if list(heads) != sorted(heads) or receipt["requested_head"] != heads.get(args.branch):
        raise _receipt_error()


def _json(value: object) -> None:
    if isinstance(value, ReadCollection):
        raw = _pull_stdout(value)
        receipt = value.read_receipt
        if type(receipt) is not dict or set(receipt) != PULL_RECEIPT_FIELDS:
            raise _receipt_error()
        if (receipt["schema"] != "aisoft.broker.pull-collection/v1" or receipt["status"] != "PASS"
            or any(type(receipt[k]) is not int for k in ("count", "server_total", "scan_count", "limit", "max_pages_per_scan", "observed_at"))
            or receipt["count"] != len(value) or not 0 <= receipt["count"] <= PULL_MAX_COUNT
            or receipt["server_total"] != receipt["count"] or receipt["scan_count"] != 2
            or receipt["limit"] != PULL_LIMIT or receipt["max_pages_per_scan"] != PULL_MAX_PAGES
            or receipt["observed_at"] <= 0 or type(receipt["terminal_empty_pages"]) is not list
            or len(receipt["terminal_empty_pages"]) != 2
            or any(type(page) is not int or not 1 <= page <= PULL_MAX_PAGES for page in receipt["terminal_empty_pages"])
            or receipt["stdout_sha256"] != hashlib.sha256(raw).hexdigest()):
            raise _receipt_error()
        # Emit the exact UTF-8 bytes hashed by the broker, independent of locale.
        stream = getattr(sys.stdout, "buffer", None)
        if stream is None:
            sys.stdout.write(raw.decode("utf-8"))
        else:
            stream.write(raw)
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return
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
            )
            if args.operation == "gitea.pulls.read":
                if not isinstance(value, ReadCollection):
                    raise _receipt_error()
                _validate_scope(value.read_receipt, contract, contract.project(args.project), args.operation)
                if value.read_receipt.get("state") != args.state:
                    raise _receipt_error()
            elif args.operation == "git.fetch.change" and args.project == "aisoft-platform" and args.branch is not None:
                if ChangeName.parse_branch(args.branch).issue_number == 333:
                    if type(value) is not dict or "namespace" not in value:
                        raise _receipt_error()
                    _validate_namespace(value["namespace"], contract, args)
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
        error_payload = {
            "status": "NEEDS_HUMAN_DECISION" if code in {
                "DEPENDENCY_FORMAT_INVALID", "DEPENDENCY_SELF",
                "DEPENDENCY_DUPLICATE", "DEPENDENCY_TARGET_DENIED",
            } else "BLOCKED_EXTERNAL",
            "code": code,
            "message": str(exc),
        }
        if code == "REMOTE_CHANGE_ABSENT" and isinstance(exc, BrokerError):
            proof = getattr(exc, "public_receipt", None)
            try:
                _validate_namespace(proof, contract, args)
                if proof["requested_head"] is not None:
                    raise _receipt_error()
            except (BrokerError, AccessContractError, AttributeError, UnboundLocalError):
                error_payload["code"] = "RESPONSE_SCHEMA_INVALID"
                error_payload["message"] = "broker public read receipt is invalid"
            else:
                error_payload["public_receipt"] = proof
        print(json.dumps(error_payload, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
