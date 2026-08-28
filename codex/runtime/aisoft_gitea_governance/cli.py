from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

from .client import ApiError, GiteaClient
from .contract import ContractError, GovernanceContract, load_contract, validate_full_sha
from .reconcile import (
    apply_repository,
    account_state,
    audit_cross_project_writes,
    bootstrap_repository_manager,
    capture_snapshot,
    planned_actions,
    retire_shared_bot,
    rollback_repository,
    verify_account,
    verify_token_identity,
)


TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gitea-governance")
    parser.add_argument("--manifest", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")

    account_spec = subparsers.add_parser("account-spec")
    account_spec.add_argument("--username", required=True)
    account_spec.add_argument(
        "--token-kind",
        required=True,
        choices=("manager-audit", "manager-mutation", "project-agent", "routine-merge-agent"),
    )

    verify_merged = subparsers.add_parser("verify-merged")
    verify_merged.add_argument("--issue", required=True, type=int)
    verify_merged.add_argument("--merged-sha", required=True)
    verify_merged.add_argument("--platform-root", required=True)
    verify_merged.add_argument("--repository")

    check = subparsers.add_parser("check")
    check.add_argument("--token-file", required=True)
    check.add_argument("--repository")
    check.add_argument("--required-context-migration", action="store_true")

    for command in ("bootstrap-manager", "apply", "rollback", "retire-shared-bot"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--token-file", required=True)
        subparser.add_argument("--repository", required=True)
        subparser.add_argument("--issue", required=True, type=int)
        subparser.add_argument("--merged-sha", required=True)
        subparser.add_argument("--platform-root", required=True)
        if command in {"bootstrap-manager", "apply"}:
            subparser.add_argument("--evidence-dir", required=True)
        if command == "apply":
            subparser.add_argument("--required-context-migration", action="store_true")
        if command == "rollback":
            subparser.add_argument("--snapshot", required=True)
        if command == "retire-shared-bot":
            subparser.add_argument("--validation-file", required=True)
    return parser


def _read_token(path_value: str) -> str:
    path = Path(path_value)
    try:
        info = path.lstat()
    except OSError as exc:
        raise ContractError(f"cannot stat token file: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ContractError("token file must be a regular non-symlink file")
    mode = stat.S_IMODE(info.st_mode)
    if mode not in {0o400, 0o600}:
        raise ContractError("token file mode must be 400 or 600")
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ContractError(f"cannot read token file: {exc}") from exc
    if not TOKEN_RE.fullmatch(token):
        raise ContractError("token file must contain exactly one safe raw token")
    return token


def _git_output(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ContractError("merged platform Git evidence check failed") from None
    return result.stdout


def _verify_merged_contract(
    contract: GovernanceContract,
    issue: int,
    sha_value: str,
    root_value: str,
    repository_name: str | None = None,
) -> str:
    sha = validate_full_sha(sha_value)
    root = Path(root_value).resolve()
    if not root.is_dir():
        raise ContractError("platform root does not exist")
    repository = contract.repository(repository_name) if repository_name else None
    pilot = repository.routine_live_pilot if repository is not None else None
    if pilot is None:
        if issue != 35:
            raise ContractError("live mutation requires exact approved Issue #35")
    else:
        if issue != pilot.rollout_issue:
            raise ContractError("routine live pilot requires its exact rollout Issue")
        for provenance_sha, label in (
            (pilot.governance_baseline_merged_sha, "governance baseline"),
            (pilot.routine_source_merged_sha, "routine source"),
        ):
            try:
                _git_output(root, "merge-base", "--is-ancestor", provenance_sha, sha)
            except ContractError:
                raise ContractError(
                    f"routine live pilot {label} is not an ancestor of the rollout SHA"
                ) from None
    _git_output(root, "merge-base", "--is-ancestor", sha, "origin/main")
    relative_manifest = contract.path.resolve().relative_to(root).as_posix()
    merged_bytes = _git_output(root, "show", f"{sha}:{relative_manifest}").encode("utf-8")
    current_bytes = contract.path.read_bytes()
    if merged_bytes != current_bytes:
        raise ContractError("current manifest is not byte-identical to the approved merged SHA")
    return sha


def _client(contract: GovernanceContract, token_file: str) -> GiteaClient:
    token = _read_token(token_file)
    return GiteaClient(contract.base_url, token)


def _require_pilot_live_authorization(
    contract: GovernanceContract,
    command: str,
    repository_name: str,
) -> None:
    repository = contract.repository(repository_name)
    pilot = repository.routine_live_pilot
    if pilot is None or command not in {"apply", "rollback"}:
        return
    if command == "rollback" and repository.routine_auto_merge_enabled:
        raise ContractError(
            "routine live pilot source must be disabled before rollback"
        )
    expected = f"approved-issue-{pilot.rollout_issue}-{command}"
    if os.environ.get("AISOFT_ROUTINE_LIVE_MODE") != expected:
        raise ContractError(
            f"routine live pilot requires AISOFT_ROUTINE_LIVE_MODE={expected}"
        )


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _check(
    client: GiteaClient,
    contract: GovernanceContract,
    repository_name: str | None,
    required_context_migration: bool = False,
) -> int:
    verify_token_identity(client, contract.platform_manager, require_site_admin=False)
    repositories = (
        (contract.repository(repository_name),)
        if repository_name
        else contract.repositories
    )
    drift = False
    # Once accounts exist, they must never be site administrators. A missing
    # account is represented as planned provisioning rather than an exception.
    # Establish this exact evidence before the configured routine merger's
    # permission read may safely interpret an exact 404 as absent.
    account_status = []
    routine_account_status = []
    missing_routine_merge_agents: dict[str, str] = {}
    for repository in repositories:
        state = account_state(client, repository.project_agent)
        account_status.append({"username": repository.project_agent, "state": state})
        if state != "present-non-admin":
            drift = True
        if repository.routine_merge_agent is not None:
            routine_state = account_state(client, repository.routine_merge_agent)
            if routine_state == "missing":
                missing_routine_merge_agents[repository.name] = (
                    repository.routine_merge_agent
                )
            routine_account_status.append({
                "repository": contract.full_name(repository),
                "enabled": repository.routine_auto_merge_enabled,
                "username": repository.routine_merge_agent,
                "state": routine_state,
            })
            if repository.routine_auto_merge_enabled and routine_state != "present-non-admin":
                drift = True
    results = []
    for repository in repositories:
        snapshot = capture_snapshot(
            client,
            contract,
            repository,
            missing_routine_merge_agent=missing_routine_merge_agents.get(
                repository.name
            ),
        )
        plan = planned_actions(
            contract, repository, snapshot,
            required_context_migration=required_context_migration,
        )
        results.append(plan)
        drift = drift or bool(plan["planned_actions"] or plan["blockers"])
    cross_project_violations = audit_cross_project_writes(client, contract)
    drift = drift or bool(cross_project_violations)
    _json({
        "contract_version": "gitea-governance/v1",
        "mode": "read-only",
        "repositories": results,
        "project_accounts": account_status,
        "routine_accounts": routine_account_status,
        "cross_project_write_violations": cross_project_violations,
        "result": "DRIFT" if drift else "PASS",
    })
    return 1 if drift else 0


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        contract = load_contract(arguments.manifest)
        if arguments.command == "validate":
            _json({
                "contract_version": contract.raw["contract_version"],
                "environment": contract.raw["environment"],
                "owner": contract.owner,
                "platform_manager": contract.platform_manager,
                "repository_count": len(contract.repositories),
                "public_allowlist": contract.raw["repository_policy"]["public_allowlist"],
                "result": "PASS",
            })
            return 0
        if arguments.command == "account-spec":
            accounts = contract.declared_service_accounts()
            if arguments.username not in accounts:
                raise ContractError("service account is not declared by the manifest")
            if arguments.username == contract.platform_manager:
                if arguments.token_kind == "manager-audit":
                    scopes = contract.raw["platform_manager"]["audit_token_scopes"]
                elif arguments.token_kind == "manager-mutation":
                    scopes = contract.raw["platform_manager"]["mutation_token_scopes"]
                else:
                    raise ContractError("platform manager requires a manager token kind")
            else:
                project_agents = {item.project_agent for item in contract.repositories}
                routine_mergers = {
                    item.routine_merge_agent for item in contract.repositories
                    if item.routine_merge_agent is not None
                }
                if arguments.username in project_agents:
                    if arguments.token_kind != "project-agent":
                        raise ContractError("project account requires project-agent token kind")
                    scopes = contract.raw["project_agent_policy"]["token_scopes"]
                elif arguments.username in routine_mergers:
                    if arguments.token_kind != "routine-merge-agent":
                        raise ContractError(
                            "routine merger requires routine-merge-agent token kind"
                        )
                    scopes = contract.raw["routine_merge_agent_policy"]["token_scopes"]
                else:  # declared_service_accounts() and sets above must agree
                    raise ContractError("service account role is ambiguous")
            _json({
                "username": arguments.username,
                "token_kind": arguments.token_kind,
                "scopes": scopes,
                "site_admin": False,
                "user_type": "bot",
            })
            return 0
        if arguments.command == "verify-merged":
            sha = _verify_merged_contract(
                contract,
                arguments.issue,
                arguments.merged_sha,
                arguments.platform_root,
                arguments.repository,
            )
            receipt = {"issue": arguments.issue, "merged_sha": sha, "result": "PASS"}
            if arguments.repository:
                repository = contract.repository(arguments.repository)
                pilot = repository.routine_live_pilot
                if pilot is not None:
                    receipt.update({
                        "repository": contract.full_name(repository),
                        "routine_source_issue": pilot.routine_source_issue,
                        "routine_source_merged_sha": pilot.routine_source_merged_sha,
                        "governance_baseline_issue": pilot.governance_baseline_issue,
                        "governance_baseline_merged_sha": (
                            pilot.governance_baseline_merged_sha
                        ),
                    })
            _json(receipt)
            return 0

        if arguments.command in {"apply", "rollback"}:
            _require_pilot_live_authorization(
                contract, arguments.command, arguments.repository
            )
        client = _client(contract, arguments.token_file)
        if arguments.command == "check":
            return _check(
                client, contract, arguments.repository,
                required_context_migration=arguments.required_context_migration,
            )

        _verify_merged_contract(
            contract,
            arguments.issue,
            arguments.merged_sha,
            arguments.platform_root,
            arguments.repository,
        )
        repository = contract.repository(arguments.repository)
        if arguments.command == "bootstrap-manager":
            _json(bootstrap_repository_manager(
                client,
                contract,
                repository,
                Path(arguments.evidence_dir),
            ))
            return 0
        if arguments.command == "apply":
            _json(apply_repository(
                client, contract, repository, Path(arguments.evidence_dir),
                required_context_migration=arguments.required_context_migration,
            ))
            return 0
        if arguments.command == "rollback":
            snapshot_path = Path(arguments.snapshot)
            try:
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ContractError(f"cannot read rollback snapshot: {exc}") from exc
            _json(rollback_repository(client, contract, repository, snapshot))
            return 0
        if arguments.command == "retire-shared-bot":
            _json(retire_shared_bot(
                client,
                contract,
                repository,
                Path(arguments.validation_file),
            ))
            return 0
        raise ContractError("unsupported command")
    except (ContractError, ApiError) as exc:
        print(f"BLOCKED_EXTERNAL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
