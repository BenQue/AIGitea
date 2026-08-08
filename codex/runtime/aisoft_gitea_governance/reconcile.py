from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .client import ApiError, GiteaClient
from .contract import ContractError, GovernanceContract, RepositoryContract


PROTECTION_FIELDS = (
    "rule_name",
    "priority",
    "enable_push",
    "enable_push_whitelist",
    "push_whitelist_deploy_keys",
    "push_whitelist_usernames",
    "push_whitelist_teams",
    "enable_force_push",
    "enable_force_push_allowlist",
    "force_push_allowlist_deploy_keys",
    "force_push_allowlist_usernames",
    "force_push_allowlist_teams",
    "enable_merge_whitelist",
    "merge_whitelist_usernames",
    "merge_whitelist_teams",
    "enable_status_check",
    "status_check_contexts",
    "required_approvals",
    "enable_approvals_whitelist",
    "approvals_whitelist_username",
    "approvals_whitelist_teams",
    "block_on_rejected_reviews",
    "block_on_official_review_requests",
    "block_on_outdated_branch",
    "dismiss_stale_approvals",
    "ignore_stale_approvals",
    "block_admin_merge_override",
    "require_signed_commits",
    "protected_file_patterns",
    "unprotected_file_patterns",
)

LIST_FIELDS = {
    "push_whitelist_usernames", "push_whitelist_teams",
    "force_push_allowlist_usernames", "force_push_allowlist_teams",
    "merge_whitelist_usernames", "merge_whitelist_teams",
    "status_check_contexts", "approvals_whitelist_username",
    "approvals_whitelist_teams",
}
BOOL_FIELDS = {
    "enable_push", "enable_push_whitelist", "push_whitelist_deploy_keys",
    "enable_force_push", "enable_force_push_allowlist",
    "force_push_allowlist_deploy_keys", "enable_merge_whitelist",
    "enable_status_check", "enable_approvals_whitelist",
    "block_on_rejected_reviews", "block_on_official_review_requests",
    "block_on_outdated_branch", "dismiss_stale_approvals",
    "ignore_stale_approvals", "block_admin_merge_override", "require_signed_commits",
}


def _repo_path(contract: GovernanceContract, repository: RepositoryContract) -> str:
    return f"/repos/{quote(contract.owner, safe='')}/{quote(repository.name, safe='')}"


def normalize_protection(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    normalized: dict[str, Any] = {}
    for field in PROTECTION_FIELDS:
        if field in LIST_FIELDS:
            normalized[field] = sorted(value.get(field) or [])
        elif field in BOOL_FIELDS:
            normalized[field] = bool(value.get(field, False))
        elif field in {"priority", "required_approvals"}:
            normalized[field] = int(value.get(field) or 0)
        elif field == "rule_name":
            normalized[field] = value.get(field) or value.get("branch_name") or "main"
        else:
            normalized[field] = value.get(field) or ""
    return normalized


def desired_protection(
    contract: GovernanceContract,
    repository: RepositoryContract,
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    if current is None:
        desired = normalize_protection({"rule_name": contract.default_branch}) or {}
    else:
        desired = copy.deepcopy(normalize_protection(current)) or {}
    desired.update({
        "rule_name": contract.default_branch,
        "enable_push": False,
        "enable_push_whitelist": False,
        "push_whitelist_deploy_keys": False,
        "push_whitelist_usernames": [],
        "push_whitelist_teams": [],
        "enable_force_push": False,
        "enable_force_push_allowlist": False,
        "force_push_allowlist_deploy_keys": False,
        "force_push_allowlist_usernames": [],
        "force_push_allowlist_teams": [],
        "enable_merge_whitelist": True,
        "merge_whitelist_usernames": [contract.human_merge_identity],
        "merge_whitelist_teams": [],
        "enable_status_check": bool(repository.status_check_contexts),
        "status_check_contexts": sorted(repository.status_check_contexts),
        "required_approvals": repository.required_approvals,
        "block_admin_merge_override": True,
    })
    return desired


def protection_payload(value: dict[str, Any], create: bool) -> dict[str, Any]:
    payload = copy.deepcopy(value)
    if not create:
        payload.pop("rule_name", None)
    return payload


def _get_optional(client: GiteaClient, path: str, operation: str) -> Any | None:
    try:
        return client.get(path, operation)
    except ApiError as exc:
        if exc.status == 404:
            return None
        raise


def _explicit_permissions(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
) -> dict[str, str]:
    path = _repo_path(contract, repository)
    names = _collaborator_names(client, path, contract.full_name(repository))
    result: dict[str, str] = {}
    for username in (contract.platform_manager, repository.project_agent, contract.shared_bot):
        if username not in names:
            result[username] = "missing"
            continue
        permission = client.get(
            f"{path}/collaborators/{quote(username, safe='')}/permission",
            f"read collaborator permission for {username}",
        )
        if not isinstance(permission, dict) or permission.get("permission") not in {
            "read", "write", "admin", "owner"
        }:
            raise ContractError("collaborator permission response is invalid")
        result[username] = permission["permission"]
    return result


def _collaborator_names(client: GiteaClient, path: str, full_name: str) -> set[str]:
    names: set[str] = set()
    for page in range(1, 101):
        collaborators = client.get(
            f"{path}/collaborators?limit=50&page={page}",
            f"list collaborators for {full_name}",
        )
        if not isinstance(collaborators, list):
            raise ContractError("collaborator list response is invalid")
        for entry in collaborators:
            if not isinstance(entry, dict) or not isinstance(entry.get("login"), str):
                raise ContractError("collaborator entry is invalid")
            names.add(entry["login"])
        if len(collaborators) < 50:
            return names
    raise ContractError("collaborator inventory exceeded the safe pagination limit")


def audit_cross_project_writes(
    client: GiteaClient,
    contract: GovernanceContract,
) -> list[dict[str, str]]:
    agents = {repository.project_agent for repository in contract.repositories}
    violations: list[dict[str, str]] = []
    for repository in contract.repositories:
        path = _repo_path(contract, repository)
        explicit = _collaborator_names(client, path, contract.full_name(repository))
        for agent in sorted((agents & explicit) - {repository.project_agent}):
            permission = client.get(
                f"{path}/collaborators/{quote(agent, safe='')}/permission",
                f"read cross-project permission for {agent}",
            )
            value = permission.get("permission") if isinstance(permission, dict) else None
            if value in {"write", "admin", "owner"}:
                violations.append({
                    "repository": contract.full_name(repository),
                    "project_agent": agent,
                    "permission": value,
                })
    return violations


def capture_snapshot(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
) -> dict[str, Any]:
    path = _repo_path(contract, repository)
    repo = client.get(path, f"read repository {contract.full_name(repository)}")
    if not isinstance(repo, dict) or repo.get("full_name") != contract.full_name(repository):
        raise ContractError("repository API target does not match the manifest")
    if repo.get("default_branch") != contract.default_branch:
        raise ContractError("repository default branch is not main")
    protection = _get_optional(
        client,
        f"{path}/branch_protections/{quote(contract.default_branch, safe='')}",
        f"read branch protection for {contract.full_name(repository)}",
    )
    return {
        "snapshot_version": "gitea-governance-snapshot/v1",
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repository": contract.full_name(repository),
        "repo": {
            "private": bool(repo.get("private", False)),
            "default_branch": repo.get("default_branch"),
            "default_delete_branch_after_merge": bool(
                repo.get("default_delete_branch_after_merge", False)
            ),
        },
        "collaborators": _explicit_permissions(client, contract, repository),
        "protection": normalize_protection(protection),
    }


def _protection_blockers(
    repository: RepositoryContract,
    protection: dict[str, Any] | None,
) -> list[str]:
    if protection is None:
        return []
    blockers: list[str] = []
    if sorted(protection["status_check_contexts"]) != sorted(repository.status_check_contexts):
        blockers.append("status-check-context-drift")
    if protection["required_approvals"] != repository.required_approvals:
        blockers.append("required-approvals-drift")
    return blockers


def planned_actions(
    contract: GovernanceContract,
    repository: RepositoryContract,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    actions: list[str] = []
    blockers = _protection_blockers(repository, snapshot["protection"])
    permissions = snapshot["collaborators"]
    if permissions[contract.platform_manager] != "admin":
        actions.append("set-platform-manager-admin")
    if permissions[repository.project_agent] != "write":
        actions.append("set-project-agent-write")
    if snapshot["repo"]["private"] != repository.private:
        actions.append("set-private" if repository.private else "set-public")
    if not snapshot["repo"]["default_delete_branch_after_merge"]:
        actions.append("enable-delete-branch-after-merge")
    expected_protection = desired_protection(contract, repository, snapshot["protection"])
    if snapshot["protection"] is None:
        actions.append("create-main-protection")
    elif snapshot["protection"] != expected_protection:
        actions.append("update-main-protection")
    return {
        "repository": contract.full_name(repository),
        "expected": {
            "visibility": repository.visibility,
            "platform_manager_permission": "admin",
            "project_agent": repository.project_agent,
            "project_agent_permission": "write",
            "shared_bot_default_action": "keep",
            "merge_allowlist_usernames": [contract.human_merge_identity],
            "status_check_contexts": list(repository.status_check_contexts),
            "required_approvals": repository.required_approvals,
        },
        "current": snapshot,
        "planned_actions": actions,
        "blockers": blockers,
    }


def verify_token_identity(
    client: GiteaClient,
    expected_username: str,
    require_site_admin: bool,
) -> None:
    user = client.get("/user", "read authenticated Gitea identity")
    if not isinstance(user, dict) or user.get("login") != expected_username:
        raise ContractError("credential identity does not match the required role")
    if bool(user.get("is_admin", False)) != require_site_admin:
        expected = "site admin" if require_site_admin else "non-site-admin"
        raise ContractError(f"credential identity is not the required {expected} role")


def verify_account(
    client: GiteaClient,
    username: str,
    must_be_site_admin: bool = False,
) -> None:
    user = client.get(f"/users/{quote(username, safe='')}", f"read account {username}")
    if not isinstance(user, dict) or user.get("login") != username:
        raise ContractError(f"account does not match expected identity: {username}")
    if bool(user.get("is_admin", False)) != must_be_site_admin:
        raise ContractError(f"account site-admin state is unsafe: {username}")


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    if path.parent.exists():
        if path.parent.is_symlink() or not path.parent.is_dir():
            raise ContractError("evidence parent must be a non-symlink directory")
        if path.parent.stat().st_mode & 0o077:
            raise ContractError("evidence directory mode must not grant group/other access")
    else:
        try:
            path.parent.mkdir(mode=0o700)
        except OSError as exc:
            raise ContractError(f"cannot create evidence directory: {exc}") from exc
    if path.exists():
        raise ContractError(f"refusing to overwrite evidence snapshot: {path}")
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    path.chmod(0o600)


def bootstrap_repository_manager(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
    evidence_dir: Path,
) -> dict[str, Any]:
    verify_token_identity(client, contract.human_merge_identity, require_site_admin=True)
    verify_account(client, contract.platform_manager, must_be_site_admin=False)
    path = _repo_path(contract, repository)
    before = capture_snapshot(client, contract, repository)
    pre_path = evidence_dir / f"{repository.name}-manager-pre.json"
    post_path = evidence_dir / f"{repository.name}-manager-post.json"
    if pre_path.exists() or post_path.exists():
        raise ContractError("refusing to reuse platform-manager evidence paths")
    write_snapshot(pre_path, before)
    permission = before["collaborators"][contract.platform_manager]
    if permission != "admin":
        client.put(
            f"{path}/collaborators/{quote(contract.platform_manager, safe='')}",
            {"permission": "admin"},
            f"set platform manager Admin on {contract.full_name(repository)}",
        )
    after = capture_snapshot(client, contract, repository)
    if after["collaborators"][contract.platform_manager] != "admin":
        raise ContractError("platform manager Admin read-back mismatch")
    write_snapshot(post_path, after)
    return {
        "repository": contract.full_name(repository),
        "result": "applied" if permission != "admin" else "no-op",
        "pre_snapshot": str(pre_path),
        "post_snapshot": str(post_path),
    }


def apply_repository(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
    evidence_dir: Path,
) -> dict[str, Any]:
    verify_token_identity(client, contract.platform_manager, require_site_admin=False)
    verify_account(client, repository.project_agent, must_be_site_admin=False)
    if audit_cross_project_writes(client, contract):
        raise ContractError("cross-project project-agent write permission must be removed before apply")
    before = capture_snapshot(client, contract, repository)
    plan = planned_actions(contract, repository, before)
    if before["collaborators"][contract.platform_manager] != "admin":
        raise ContractError("platform manager is not Admin on the exact target repository")
    if plan["blockers"]:
        raise ContractError("repository protection drift requires manifest review before apply")
    pre_path = evidence_dir / f"{repository.name}-pre.json"
    post_path = evidence_dir / f"{repository.name}-post.json"
    if pre_path.exists() or post_path.exists():
        raise ContractError("refusing to reuse repository evidence paths")
    write_snapshot(pre_path, before)
    if plan["planned_actions"]:
        path = _repo_path(contract, repository)
        if before["collaborators"][repository.project_agent] != "write":
            client.put(
                f"{path}/collaborators/{quote(repository.project_agent, safe='')}",
                {"permission": "write"},
                f"set project agent Write on {contract.full_name(repository)}",
            )
        repo_patch: dict[str, Any] = {}
        if before["repo"]["private"] != repository.private:
            repo_patch["private"] = repository.private
        if not before["repo"]["default_delete_branch_after_merge"]:
            repo_patch["default_delete_branch_after_merge"] = True
        if repo_patch:
            client.patch(path, repo_patch, f"update repository policy for {contract.full_name(repository)}")
        desired = desired_protection(contract, repository, before["protection"])
        if before["protection"] is None:
            client.post(f"{path}/branch_protections", protection_payload(desired, create=True),
                        f"create main protection for {contract.full_name(repository)}")
        elif before["protection"] != desired:
            client.patch(
                f"{path}/branch_protections/{quote(contract.default_branch, safe='')}",
                protection_payload(desired, create=False),
                f"update main protection for {contract.full_name(repository)}",
            )
    after = capture_snapshot(client, contract, repository)
    post_plan = planned_actions(contract, repository, after)
    if post_plan["blockers"] or post_plan["planned_actions"]:
        raise ContractError("repository policy read-back mismatch")
    write_snapshot(post_path, after)
    return {
        "repository": contract.full_name(repository),
        "result": "applied" if plan["planned_actions"] else "no-op",
        "pre_snapshot": str(pre_path),
        "post_snapshot": str(post_path),
    }


def retire_shared_bot(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
    validation_file: Path,
) -> dict[str, Any]:
    verify_token_identity(client, contract.platform_manager, require_site_admin=False)
    try:
        validation = json.loads(validation_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read project validation evidence: {exc}") from exc
    required = {
        "repository": contract.full_name(repository),
        "project_agent": repository.project_agent,
        "private_repo_read": "PASS",
        "issue_comment_label": "PASS",
        "feature_push": "PASS",
        "pull_request": "PASS",
        "main_push_denied": "PASS",
        "main_merge_denied": "PASS",
    }
    if validation != required:
        raise ContractError("project validation evidence is incomplete or targets another repository")
    snapshot = capture_snapshot(client, contract, repository)
    if snapshot["collaborators"][repository.project_agent] != "write":
        raise ContractError("project agent Write permission is not established")
    if planned_actions(contract, repository, snapshot)["planned_actions"]:
        raise ContractError("repository governance must be converged before shared bot retirement")
    if snapshot["collaborators"][contract.shared_bot] == "missing":
        return {"repository": contract.full_name(repository), "result": "no-op"}
    path = _repo_path(contract, repository)
    client.delete(f"{path}/collaborators/{quote(contract.shared_bot, safe='')}",
                  f"remove shared bot from {contract.full_name(repository)}")
    after = capture_snapshot(client, contract, repository)
    if after["collaborators"][contract.shared_bot] != "missing":
        raise ContractError("shared bot removal read-back mismatch")
    return {"repository": contract.full_name(repository), "result": "retired"}


def restore_permission(
    client: GiteaClient,
    path: str,
    username: str,
    permission: str,
) -> None:
    encoded = quote(username, safe="")
    if permission == "missing":
        try:
            client.delete(f"{path}/collaborators/{encoded}", f"remove collaborator {username}")
        except ApiError as exc:
            if exc.status != 404:
                raise
    elif permission in {"read", "write", "admin"}:
        client.put(f"{path}/collaborators/{encoded}", {"permission": permission},
                   f"restore collaborator {username}")
    else:
        raise ContractError("snapshot contains unsupported collaborator permission")


def rollback_repository(
    client: GiteaClient,
    contract: GovernanceContract,
    repository: RepositoryContract,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    verify_token_identity(client, contract.platform_manager, require_site_admin=False)
    if snapshot.get("snapshot_version") != "gitea-governance-snapshot/v1":
        raise ContractError("unsupported snapshot version")
    if snapshot.get("repository") != contract.full_name(repository):
        raise ContractError("snapshot repository does not match exact target")
    path = _repo_path(contract, repository)
    repo = snapshot.get("repo")
    collaborators = snapshot.get("collaborators")
    if not isinstance(repo, dict) or not isinstance(collaborators, dict):
        raise ContractError("snapshot is incomplete")
    if collaborators.get(contract.platform_manager) != "admin":
        raise ContractError("rollback snapshot must retain platform manager Admin permission")
    client.patch(
        path,
        {
            "private": bool(repo.get("private")),
            "default_delete_branch_after_merge": bool(
                repo.get("default_delete_branch_after_merge")
            ),
        },
        f"restore repository settings for {contract.full_name(repository)}",
    )
    current = capture_snapshot(client, contract, repository)
    previous_protection = snapshot.get("protection")
    protection_path = f"{path}/branch_protections/{quote(contract.default_branch, safe='')}"
    if previous_protection is None and current["protection"] is not None:
        client.delete(protection_path,
                      f"remove main protection for {contract.full_name(repository)}")
    elif isinstance(previous_protection, dict):
        normalized = normalize_protection(previous_protection)
        if current["protection"] is None:
            client.post(f"{path}/branch_protections",
                        protection_payload(normalized or {}, create=True),
                        f"restore main protection for {contract.full_name(repository)}")
        else:
            client.patch(protection_path,
                         protection_payload(normalized or {}, create=False),
                         f"restore main protection for {contract.full_name(repository)}")
    else:
        raise ContractError("snapshot protection is invalid")
    # Restore project and shared identities before manager. Removing or
    # downgrading the manager last prevents a mid-rollback loss of authority.
    for username in (repository.project_agent, contract.shared_bot, contract.platform_manager):
        if username not in collaborators:
            raise ContractError("snapshot collaborator set is incomplete")
        restore_permission(client, path, username, collaborators[username])
    after = capture_snapshot(client, contract, repository)
    if after["repo"] != repo or after["collaborators"] != collaborators or \
            after["protection"] != normalize_protection(previous_protection):
        raise ContractError("rollback read-back mismatch")
    return {"repository": contract.full_name(repository), "result": "rollback-applied"}
