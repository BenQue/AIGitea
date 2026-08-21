from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# 交付阶段。development 只适用于尚未首次生产部署的项目；它只影响强制 complex
# 变更所需的映射文档份数，不影响分支保护、必需 CI、人工合并闸门与判级分类本身。
CHANGE_CONTROL_PHASES = frozenset({"development", "production"})
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ContractError(ValueError):
    """Raised when the governance manifest is unsafe or ambiguous."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _exact_keys(
    value: dict[str, Any],
    expected: set[str],
    context: str,
    optional: set[str] | None = None,
) -> None:
    actual = set(value)
    allowed = expected | (optional or set())
    missing = sorted(expected - actual)
    extra = sorted(actual - allowed)
    if missing or extra:
        raise ContractError(f"{context} keys mismatch: missing={missing} extra={extra}")


def _identifier(value: Any, context: str) -> str:
    _require(isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value)),
             f"{context} must be a safe identifier")
    return value


def _exact_string_list(value: Any, expected: list[str], context: str) -> None:
    _require(value == expected, f"{context} must equal {expected}")


@dataclass(frozen=True)
class RepositoryContract:
    name: str
    classification: str
    visibility: str
    project_agent: str
    status_check_contexts: tuple[str, ...]
    required_approvals: int
    # 交付阶段。未在 manifest 声明时默认 "production"——缺省取更严的一档，
    # 使既有仓库行为完全不变，也保证读不到声明时不会意外放宽。
    change_control: str = "production"

    @property
    def private(self) -> bool:
        return self.visibility == "private"

    @property
    def in_development(self) -> bool:
        return self.change_control == "development"


@dataclass(frozen=True)
class GovernanceContract:
    raw: dict[str, Any]
    path: Path
    owner: str
    base_url: str
    default_branch: str
    human_merge_identity: str
    platform_manager: str
    shared_bot: str
    repositories: tuple[RepositoryContract, ...]

    def repository(self, requested: str) -> RepositoryContract:
        if "/" in requested:
            owner, name = requested.split("/", 1)
            _require(owner == self.owner, "requested repository owner is not in the manifest")
        else:
            name = requested
        for repository in self.repositories:
            if repository.name == name:
                return repository
        raise ContractError("requested repository is not explicitly managed")

    def full_name(self, repository: RepositoryContract) -> str:
        return f"{self.owner}/{repository.name}"

    def declared_service_accounts(self) -> dict[str, tuple[str, ...]]:
        accounts = {
            self.platform_manager: tuple(
                self.raw["platform_manager"]["mutation_token_scopes"]
            )
        }
        for repository in self.repositories:
            accounts[repository.project_agent] = tuple(
                self.raw["project_agent_policy"]["token_scopes"]
            )
        return accounts


def load_contract(path: str | Path) -> GovernanceContract:
    manifest_path = Path(path)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read governance manifest: {exc}") from exc
    _require(isinstance(raw, dict), "manifest root must be an object")
    _exact_keys(
        raw,
        {
            "contract_version", "environment", "gitea_version", "base_url", "owner",
            "default_branch", "unknown_repository_action", "human_merge_identity",
            "site_admin", "platform_manager", "project_agent_policy",
            "shared_bot_migration", "server_policy", "repository_policy",
            "repositories", "vm_identity_policy", "intranet_migration_policy",
        },
        "manifest",
    )
    _require(raw["contract_version"] == "gitea-governance/v1",
             "unsupported contract_version")
    _require(raw["environment"] == "local-orbstack", "unexpected environment")
    _require(raw["gitea_version"] == "1.26.4", "Gitea version must be pinned to 1.26.4")
    parsed_url = urlparse(raw["base_url"])
    _require(parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc),
             "base_url must be an absolute HTTP(S) URL")
    _require(parsed_url.username is None and parsed_url.password is None,
             "base_url must not embed credentials")
    _require(parsed_url.path in {"", "/"} and not parsed_url.query and not parsed_url.fragment,
             "base_url must not contain path, query, or fragment")
    base_url = raw["base_url"].rstrip("/")
    owner = _identifier(raw["owner"], "owner")
    default_branch = _identifier(raw["default_branch"], "default_branch")
    _require(default_branch == "main", "default_branch must be main")
    _require(raw["unknown_repository_action"] == "report-only",
             "unknown repositories must be report-only")
    human = _identifier(raw["human_merge_identity"], "human_merge_identity")

    site_admin = raw["site_admin"]
    _require(isinstance(site_admin, dict), "site_admin must be an object")
    _exact_keys(site_admin, {"username", "routine_automation_allowed",
                             "approved_bootstrap_allowed", "break_glass_only"},
                "site_admin")
    _require(_identifier(site_admin["username"], "site_admin.username") == human,
             "site admin and human merge identity must match")
    _require(site_admin["routine_automation_allowed"] is False,
             "site admin must not be available to routine automation")
    _require(site_admin["approved_bootstrap_allowed"] is True,
             "site admin must allow purpose-built approved bootstrap")
    _require(site_admin["break_glass_only"] is True, "site admin must be break-glass only")

    manager = raw["platform_manager"]
    _require(isinstance(manager, dict), "platform_manager must be an object")
    _exact_keys(
        manager,
        {
            "username", "site_admin", "repository_permission", "ordinary_git_allowed",
            "merge_allowed", "audit_token_scopes", "mutation_token_scopes",
        },
        "platform_manager",
    )
    manager_name = _identifier(manager["username"], "platform_manager.username")
    _require(manager_name != human, "platform manager must differ from human admin")
    _require(manager["site_admin"] is False, "platform manager must not be a site admin")
    _require(manager["repository_permission"] == "admin",
             "platform manager repository permission must be admin")
    _require(manager["ordinary_git_allowed"] is False,
             "platform manager must not be used for ordinary Git")
    _require(manager["merge_allowed"] is False, "platform manager must not merge")
    _exact_string_list(manager["audit_token_scopes"],
                       ["read:issue", "read:repository", "read:user"],
                       "platform_manager.audit_token_scopes")
    _exact_string_list(manager["mutation_token_scopes"],
                       ["write:issue", "write:repository", "read:user"],
                       "platform_manager.mutation_token_scopes")

    agent_policy = raw["project_agent_policy"]
    _require(isinstance(agent_policy, dict), "project_agent_policy must be an object")
    _exact_keys(
        agent_policy,
        {"repository_permission", "merge_allowed", "cross_project_write_allowed", "token_scopes"},
        "project_agent_policy",
    )
    _require(agent_policy["repository_permission"] == "write",
             "project agents must have exactly write permission")
    _require(agent_policy["merge_allowed"] is False, "project agents must not merge")
    _require(agent_policy["cross_project_write_allowed"] is False,
             "cross-project write must be disabled")
    _exact_string_list(agent_policy["token_scopes"],
                       ["write:issue", "write:repository", "read:user"],
                       "project_agent_policy.token_scopes")

    shared = raw["shared_bot_migration"]
    _require(isinstance(shared, dict), "shared_bot_migration must be an object")
    _exact_keys(shared, {"username", "default_action", "retirement_requires_project_validation"},
                "shared_bot_migration")
    shared_bot = _identifier(shared["username"], "shared_bot_migration.username")
    _require(shared_bot not in {human, manager_name}, "shared bot identity overlaps a protected role")
    _require(shared["default_action"] == "keep", "shared bot must be kept by default")
    _require(shared["retirement_requires_project_validation"] is True,
             "shared bot retirement must require project validation")

    server = raw["server_policy"]
    _require(isinstance(server, dict), "server_policy must be an object")
    _exact_keys(server, {"disable_registration", "default_private", "force_private",
                         "require_signin_view"}, "server_policy")
    _require(server == {
        "disable_registration": True,
        "default_private": "private",
        "force_private": False,
        "require_signin_view": False,
    }, "server_policy must enforce disabled registration and private-by-default")

    repository_policy = raw["repository_policy"]
    _require(isinstance(repository_policy, dict), "repository_policy must be an object")
    _exact_keys(
        repository_policy,
        {
            "default_visibility", "public_allowlist", "default_delete_branch_after_merge",
            "protect_default_branch", "direct_push_allowed", "force_push_allowed",
            "merge_allowlist_usernames", "block_admin_merge_override",
            "preserve_unmanaged_protection_fields",
        },
        "repository_policy",
    )
    _require(repository_policy["default_visibility"] == "private",
             "repository default visibility must be private")
    _require(repository_policy["default_delete_branch_after_merge"] is True,
             "merged branches must be deleted by default")
    _require(repository_policy["protect_default_branch"] is True,
             "default branch protection is required")
    _require(repository_policy["direct_push_allowed"] is False,
             "direct push must be disabled")
    _require(repository_policy["force_push_allowed"] is False,
             "force push must be disabled")
    _require(repository_policy["merge_allowlist_usernames"] == [human],
             "merge allowlist must contain only the human identity")
    _require(repository_policy["block_admin_merge_override"] is True,
             "administrator merge override must be blocked")
    _require(repository_policy["preserve_unmanaged_protection_fields"] is True,
             "unmanaged protection fields must be preserved")

    repositories_value = raw["repositories"]
    _require(isinstance(repositories_value, list) and repositories_value,
             "repositories must be a non-empty list")
    repositories: list[RepositoryContract] = []
    names: set[str] = set()
    agents: set[str] = set()
    public_full_names: list[str] = []
    for index, item in enumerate(repositories_value):
        _require(isinstance(item, dict), f"repositories[{index}] must be an object")
        _exact_keys(item, {"name", "classification", "visibility", "project_agent",
                           "status_check_contexts", "required_approvals"},
                    f"repositories[{index}]",
                    optional={"change_control"})
        name = _identifier(item["name"], f"repositories[{index}].name")
        _require(name not in names, f"duplicate repository name: {name}")
        names.add(name)
        classification = item["classification"]
        _require(classification in {"public-platform", "public-test", "internal-application"},
                 f"unsupported classification for {name}")
        visibility = item["visibility"]
        _require(visibility in {"public", "private"}, f"unsupported visibility for {name}")
        if classification.startswith("public-"):
            _require(visibility == "public", f"public classification must be public: {name}")
            public_full_names.append(f"{owner}/{name}")
        else:
            _require(visibility == "private", f"internal application must be private: {name}")
        agent = _identifier(item["project_agent"], f"repositories[{index}].project_agent")
        _require(agent not in {human, manager_name, shared_bot},
                 f"project agent overlaps a protected identity: {agent}")
        _require(agent not in agents, f"project agent is reused across repositories: {agent}")
        agents.add(agent)
        contexts = item["status_check_contexts"]
        _require(isinstance(contexts, list) and all(isinstance(value, str) and value for value in contexts),
                 f"status_check_contexts must be non-empty strings for {name}")
        _require(len(contexts) == len(set(contexts)), f"duplicate status context for {name}")
        approvals = item["required_approvals"]
        _require(isinstance(approvals, int) and not isinstance(approvals, bool) and approvals >= 0,
                 f"required_approvals must be a non-negative integer for {name}")
        change_control = item.get("change_control", "production")
        _require(change_control in CHANGE_CONTROL_PHASES,
                 f"unsupported change_control for {name}: {change_control!r}")
        repositories.append(RepositoryContract(
            name=name,
            classification=classification,
            visibility=visibility,
            project_agent=agent,
            status_check_contexts=tuple(contexts),
            required_approvals=approvals,
            change_control=change_control,
        ))

    _require(repository_policy["public_allowlist"] == public_full_names,
             "public_allowlist must exactly match public repositories in manifest order")
    _require(set(repository_policy["public_allowlist"]) == {
        f"{owner}/aisoft-platform", f"{owner}/myapp", f"{owner}/smoke-test"
    }, "current public allowlist must contain only aisoft-platform, myapp, and smoke-test")

    vm_policy = raw["vm_identity_policy"]
    _require(isinstance(vm_policy, dict), "vm_identity_policy must be an object")
    _exact_keys(vm_policy, {"orbstack_lifecycle_controller", "scm_ci_operator",
                            "project_deploy_identity_required", "shared_project_deploy_identity_allowed",
                            "gitea_credentials_reusable_for_os_access", "production_ai_access_allowed"},
                "vm_identity_policy")
    _require(vm_policy["orbstack_lifecycle_controller"] == "mac-host-user-with-explicit-approval",
             "OrbStack lifecycle must remain host-controlled")
    _require(vm_policy["project_deploy_identity_required"] is True,
             "project deploy identities are required")
    _require(vm_policy["shared_project_deploy_identity_allowed"] is False,
             "shared project deploy identity must be disabled")
    _require(vm_policy["gitea_credentials_reusable_for_os_access"] is False,
             "Gitea credentials must not be reused for OS access")
    _require(vm_policy["production_ai_access_allowed"] is False,
             "AI production access must be disabled")

    intranet = raw["intranet_migration_policy"]
    _require(isinstance(intranet, dict), "intranet_migration_policy must be an object")
    _exact_keys(intranet, {"visibility_strategy", "copy_local_accounts",
                           "copy_local_tokens_or_secrets", "copy_local_issues_or_pull_requests",
                           "requires_target_inventory_and_mapping_approval"},
                "intranet_migration_policy")
    _require(intranet["visibility_strategy"] == "same-classification-policy",
             "intranet must reuse the same classification policy")
    for key in ("copy_local_accounts", "copy_local_tokens_or_secrets",
                "copy_local_issues_or_pull_requests"):
        _require(intranet[key] is False, f"intranet_migration_policy.{key} must be false")
    _require(intranet["requires_target_inventory_and_mapping_approval"] is True,
             "intranet migration must require separate approval")

    return GovernanceContract(
        raw=raw,
        path=manifest_path,
        owner=owner,
        base_url=base_url,
        default_branch=default_branch,
        human_merge_identity=human,
        platform_manager=manager_name,
        shared_bot=shared_bot,
        repositories=tuple(repositories),
    )


def validate_full_sha(value: str) -> str:
    _require(bool(SHA_RE.fullmatch(value)), "merged SHA must be 40 lowercase hex characters")
    return value
