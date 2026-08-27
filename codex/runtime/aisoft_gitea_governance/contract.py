from __future__ import annotations

import hashlib
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

# 会回写 deployed 的应用部署链路（02 §9）与**本仓库每一次 merge** 的关系。#163 只问了
# 「有没有这条链路」，#192 把它收紧成「这条链路会不会覆盖到本次 merge」——因为
# mark-completed-issues.sh 用它决定的是「跳过、等 deployed」，而只有等待有保证的终点时
# 跳过才成立：
#   application-deploy           有链路，且每一次 merge 都会被它部署；等待必然结束。
#   application-deploy-selective 有链路，但只覆盖一部分 merge；等待没有保证的终点，
#                                因此终态写 completed，真部署时由部署链路覆盖为 deployed。
#   none                         没有链路，deployed 不可达，completed 是唯一终态。
# 这仍然是仓库属性而不是单次变更的属性：平台仓库里没有任何变更走应用部署链路。
#
# 未声明时取 application-deploy-selective——**可自愈的一档**，不是最宽或最严的一档。
# #163 曾取 application-deploy，理由是「缺省更严」；但两个方向并不对称：早写的 completed
# 会被 mark-deployed-issues.sh 剥掉整个生命周期维度重写成 deployed，而 broker 的
# _set_issue_lifecycle 又拒绝把已经 deployed 的 Issue 降级为 completed，所以这个方向的错
# 有人纠正；漏写方向没有任何组件会回头补（03 §11：没有任何组件处在能观察到合并的位置上），
# 实测就是 LocalWMS 上 5 个已合并 Issue 至今一个标签都没有（#192）。
DEPLOYMENT_LIFECYCLES = frozenset(
    {"application-deploy", "application-deploy-selective", "none"}
)
DEFAULT_DEPLOYMENT_LIFECYCLE = "application-deploy-selective"

# 该仓库有没有 docs/changes/_template/ 下的 vendored 模板副本（#190）。副本与合同源
# templates/docs/changes/_template/ 之间原先没有任何依赖声明，下游因此无从知道自己何时
# 过期；这个键就是那条缺失的声明，codex/tools/change-template-sync.sh 据它广播同步清单。
# 未声明时取 True——读不到声明只会让广播多列一个仓库，而漏列一个持有过期副本的仓库
# 正是本 Issue 要修的失败模式。
DEFAULT_VENDORS_CHANGE_TEMPLATES = True
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


def repository_declarations_sha256(
    repositories: list[dict[str, object]],
    *,
    exclude_name: str,
) -> str:
    canonical = json.dumps(
        [item for item in repositories if item.get("name") != exclude_name],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _identifier(value: Any, context: str) -> str:
    _require(isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value)),
             f"{context} must be a safe identifier")
    return value


def _exact_string_list(value: Any, expected: list[str], context: str) -> None:
    _require(value == expected, f"{context} must equal {expected}")


@dataclass(frozen=True)
class RequiredContextMigration:
    repository: str
    context: str
    pull_request: int
    head_sha: str
    actions_run: int
    commit_status_id: int
    event: str
    state: str


@dataclass(frozen=True)
class RoutineLivePilot:
    project_id: str
    rollout_issue: int
    routine_source_issue: int
    routine_source_merged_sha: str
    governance_baseline_issue: int
    governance_baseline_merged_sha: str
    non_target_repositories_sha256: str
    canary_issue: int
    required_context: str
    bootstrap_max: int
    apply_max: int
    canary_merge_post_max: int


@dataclass(frozen=True)
class RepositoryContract:
    name: str
    classification: str
    visibility: str
    project_agent: str
    routine_auto_merge_enabled: bool
    routine_merge_agent: str | None
    status_check_contexts: tuple[str, ...]
    required_approvals: int
    # 交付阶段。未在 manifest 声明时默认 "production"——缺省取更严的一档，
    # 使既有仓库行为完全不变，也保证读不到声明时不会意外放宽。
    change_control: str = "production"
    # 那条应用部署链路会不会覆盖本仓库的每一次 merge。缺省取可自愈的一档，
    # 见 DEPLOYMENT_LIFECYCLES。
    deployment_lifecycle: str = DEFAULT_DEPLOYMENT_LIFECYCLE
    # 是否持有 change 文档模板的 vendored 副本，见 DEFAULT_VENDORS_CHANGE_TEMPLATES。
    vendors_change_templates: bool = DEFAULT_VENDORS_CHANGE_TEMPLATES
    required_context_migration: RequiredContextMigration | None = None
    routine_live_pilot: RoutineLivePilot | None = None

    @property
    def private(self) -> bool:
        return self.visibility == "private"

    @property
    def in_development(self) -> bool:
        return self.change_control == "development"

    @property
    def deploys(self) -> bool:
        """是否存在一条会把生命周期推进为 deployed 的应用部署链路。

        存在不等于「每一次 merge 都会被它部署」：那是 application-deploy 这一档单独
        声明的更强事实，终态判定要的正是后者（#192）。
        """
        return self.deployment_lifecycle != "none"

    @property
    def merge_allowlist(self) -> tuple[str, ...]:
        if self.routine_auto_merge_enabled:
            assert self.routine_merge_agent is not None
            return (self.routine_merge_agent,)
        return ()


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
            if repository.routine_merge_agent is not None:
                accounts[repository.routine_merge_agent] = tuple(
                    self.raw["routine_merge_agent_policy"]["token_scopes"]
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
            "routine_merge_agent_policy",
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

    merger_policy = raw["routine_merge_agent_policy"]
    _require(isinstance(merger_policy, dict),
             "routine_merge_agent_policy must be an object")
    _exact_keys(
        merger_policy,
        {
            "site_admin", "repository_permission", "ordinary_git_allowed",
            "native_merge_only_acl", "credential_custody", "ordinary_git_control",
            "merge_allowed", "cross_project_write_allowed", "allowed_operation",
            "credential_relative_path_template", "token_scopes",
        },
        "routine_merge_agent_policy",
    )
    _require(merger_policy["site_admin"] is False,
             "routine merger must not be a site admin")
    _require(merger_policy["repository_permission"] == "write",
             "routine merger must have exact repository Write permission")
    _require(merger_policy["ordinary_git_allowed"] is False,
             "routine merger must not be used for ordinary Git")
    _require(merger_policy["native_merge_only_acl"] is False,
             "Gitea 1.26.4 does not provide a native merge-only ACL")
    _require(merger_policy["credential_custody"] == "broker-exclusive",
             "routine merger credential custody must be broker-exclusive")
    _require(
        merger_policy["ordinary_git_control"]
        == "credential-custody-typed-operation-manifest-final-head-zero-fallback",
        "ordinary Git isolation must use the approved custody and hard-gate model",
    )
    _require(merger_policy["merge_allowed"] is True,
             "routine merger policy must allow only the broker merge operation")
    _require(merger_policy["cross_project_write_allowed"] is False,
             "routine merger cross-project write must be disabled")
    _require(merger_policy["allowed_operation"] == "gitea.pull.merge.routine",
             "routine merger must be bound to the fixed typed operation")
    _require(
        merger_policy["credential_relative_path_template"]
        == "projects/{project_id}/routine-merge-agent.token",
        "routine merger credential binding must use the fixed per-project path",
    )
    _exact_string_list(
        merger_policy["token_scopes"], ["write:repository"],
        "routine_merge_agent_policy.token_scopes",
    )

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
    mergers: set[str] = set()
    public_full_names: list[str] = []
    for index, item in enumerate(repositories_value):
        _require(isinstance(item, dict), f"repositories[{index}] must be an object")
        _exact_keys(item, {"name", "classification", "visibility", "project_agent",
                           "routine_auto_merge_enabled", "routine_merge_agent",
                           "status_check_contexts", "required_approvals"},
                    f"repositories[{index}]",
                    optional={"change_control", "deployment_lifecycle",
                              "vendors_change_templates", "required_context_migration",
                              "routine_live_pilot"})
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
        migration_value = item.get("required_context_migration")
        migration = None
        if migration_value is not None:
            _require(isinstance(migration_value, dict),
                     f"required_context_migration must be an object for {name}")
            _exact_keys(
                migration_value,
                {
                    "repository", "context", "pull_request", "head_sha",
                    "actions_run", "commit_status_id", "event", "state",
                },
                f"repositories[{index}].required_context_migration",
            )
            _require(len(contexts) == 1,
                     f"required context migration requires exactly one target context for {name}")
            full_name = f"{owner}/{name}"
            _require(migration_value["repository"] == full_name,
                     f"required context migration repository must equal {full_name}")
            _require(migration_value["context"] == contexts[0],
                     f"required context migration context must equal the canonical context for {name}")
            pull_request = migration_value["pull_request"]
            _require(isinstance(pull_request, int) and not isinstance(pull_request, bool)
                     and pull_request > 0,
                     f"required context migration pull_request must be positive for {name}")
            head_sha = migration_value["head_sha"]
            _require(isinstance(head_sha, str) and bool(SHA_RE.fullmatch(head_sha)),
                     f"required context migration head_sha must be a full lowercase SHA for {name}")
            for evidence_number in ("actions_run", "commit_status_id"):
                value = migration_value[evidence_number]
                _require(isinstance(value, int) and not isinstance(value, bool) and value > 0,
                         f"required context migration {evidence_number} must be positive for {name}")
            _require(migration_value["event"] == "pull_request",
                     f"required context migration event must be pull_request for {name}")
            _require(migration_value["state"] == "success",
                     f"required context migration state must be success for {name}")
            migration = RequiredContextMigration(
                repository=full_name,
                context=contexts[0],
                pull_request=pull_request,
                head_sha=head_sha,
                actions_run=migration_value["actions_run"],
                commit_status_id=migration_value["commit_status_id"],
                event="pull_request",
                state="success",
            )
        routine_enabled = item["routine_auto_merge_enabled"]
        _require(isinstance(routine_enabled, bool),
                 f"routine_auto_merge_enabled must be a boolean for {name}")
        merger_value = item["routine_merge_agent"]
        merger: str | None
        if merger_value is None:
            merger = None
        else:
            merger = _identifier(merger_value, f"repositories[{index}].routine_merge_agent")
            _require(merger not in {human, manager_name, shared_bot, agent},
                     f"routine merger overlaps a protected identity: {merger}")
            _require(merger not in agents and merger not in mergers,
                     f"routine merger identity is reused: {merger}")
            mergers.add(merger)
        if routine_enabled:
            _require(classification == "internal-application",
                     f"routine auto merge requires internal-application: {name}")
            _require(bool(contexts),
                     f"routine auto merge requires canonical status contexts: {name}")
            _require(merger is not None,
                     f"routine auto merge requires a distinct merger identity: {name}")
        pilot_value = item.get("routine_live_pilot")
        pilot = None
        if pilot_value is not None:
            _require(isinstance(pilot_value, dict),
                     f"routine_live_pilot must be an object for {name}")
            _exact_keys(
                pilot_value,
                {
                    "project_id", "rollout_issue", "routine_source_issue",
                    "routine_source_merged_sha", "governance_baseline_issue",
                    "governance_baseline_merged_sha", "canary_issue",
                    "non_target_repositories_sha256", "required_context",
                    "bootstrap_max", "apply_max",
                    "canary_merge_post_max",
                },
                f"repositories[{index}].routine_live_pilot",
            )
            project_id = _identifier(
                pilot_value["project_id"],
                f"repositories[{index}].routine_live_pilot.project_id",
            )
            number_fields = (
                "rollout_issue", "routine_source_issue",
                "governance_baseline_issue", "canary_issue",
            )
            for field in number_fields:
                value = pilot_value[field]
                _require(
                    isinstance(value, int) and not isinstance(value, bool) and value > 0,
                    f"routine_live_pilot {field} must be positive for {name}",
                )
            for field in ("routine_source_merged_sha", "governance_baseline_merged_sha"):
                value = pilot_value[field]
                _require(
                    isinstance(value, str) and bool(SHA_RE.fullmatch(value)),
                    f"routine_live_pilot {field} must be a full lowercase SHA for {name}",
                )
            non_target_digest = pilot_value["non_target_repositories_sha256"]
            _require(
                isinstance(non_target_digest, str)
                and bool(re.fullmatch(r"[0-9a-f]{64}", non_target_digest)),
                f"routine_live_pilot non-target digest must be lowercase SHA-256 for {name}",
            )
            for field in ("bootstrap_max", "apply_max", "canary_merge_post_max"):
                _require(
                    pilot_value[field] == 1,
                    f"routine_live_pilot {field} must equal 1 for {name}",
                )
            _require(len(contexts) == 1,
                     f"routine_live_pilot requires one exact status context: {name}")
            _require(pilot_value["required_context"] == contexts[0],
                     f"routine_live_pilot required context mismatch for {name}")
            _require(pilot_value["rollout_issue"] not in {
                pilot_value["routine_source_issue"],
                pilot_value["governance_baseline_issue"],
                pilot_value["canary_issue"],
            }, f"routine_live_pilot rollout Issue must be distinct for {name}")
            pilot = RoutineLivePilot(
                project_id=project_id,
                rollout_issue=pilot_value["rollout_issue"],
                routine_source_issue=pilot_value["routine_source_issue"],
                routine_source_merged_sha=pilot_value["routine_source_merged_sha"],
                governance_baseline_issue=pilot_value["governance_baseline_issue"],
                governance_baseline_merged_sha=pilot_value["governance_baseline_merged_sha"],
                non_target_repositories_sha256=non_target_digest,
                canary_issue=pilot_value["canary_issue"],
                required_context=pilot_value["required_context"],
                bootstrap_max=1,
                apply_max=1,
                canary_merge_post_max=1,
            )
        _require(name != "aisoft-platform" or not routine_enabled,
                 "aisoft-platform routine auto merge is permanently disabled")
        approvals = item["required_approvals"]
        _require(isinstance(approvals, int) and not isinstance(approvals, bool) and approvals >= 0,
                 f"required_approvals must be a non-negative integer for {name}")
        change_control = item.get("change_control", "production")
        _require(change_control in CHANGE_CONTROL_PHASES,
                 f"unsupported change_control for {name}: {change_control!r}")
        deployment_lifecycle = item.get("deployment_lifecycle",
                                        DEFAULT_DEPLOYMENT_LIFECYCLE)
        _require(deployment_lifecycle in DEPLOYMENT_LIFECYCLES,
                 f"unsupported deployment_lifecycle for {name}: {deployment_lifecycle!r}")
        vendors_templates = item.get("vendors_change_templates",
                                     DEFAULT_VENDORS_CHANGE_TEMPLATES)
        _require(isinstance(vendors_templates, bool),
                 f"vendors_change_templates must be a boolean for {name}: "
                 f"{vendors_templates!r}")
        repositories.append(RepositoryContract(
            name=name,
            classification=classification,
            visibility=visibility,
            project_agent=agent,
            routine_auto_merge_enabled=routine_enabled,
            routine_merge_agent=merger,
            status_check_contexts=tuple(contexts),
            required_approvals=approvals,
            change_control=change_control,
            deployment_lifecycle=deployment_lifecycle,
            vendors_change_templates=vendors_templates,
            required_context_migration=migration,
            routine_live_pilot=pilot,
        ))

    live_pilots = [repository for repository in repositories
                   if repository.routine_live_pilot is not None]
    _require(len(live_pilots) == 1 and live_pilots[0].name == "NewEMaint",
             "the only routine live pilot must be NewEMaint")
    newemaint_pilot = live_pilots[0].routine_live_pilot
    assert newemaint_pilot is not None
    _require(newemaint_pilot.project_id == "newemaint",
             "NewEMaint routine live pilot project id must be newemaint")
    _require(newemaint_pilot.rollout_issue == 213,
             "NewEMaint routine live pilot rollout Issue must be 213")
    _require(newemaint_pilot.routine_source_issue == 208,
             "NewEMaint routine source Issue must be 208")
    _require(
        newemaint_pilot.routine_source_merged_sha
        == "8d109b14b6e0936be30f6f287ff6050e48632e0b",
        "NewEMaint routine source SHA must be the merged Issue #208 SHA",
    )
    _require(newemaint_pilot.governance_baseline_issue == 35,
             "NewEMaint governance baseline Issue must be 35")
    _require(
        newemaint_pilot.governance_baseline_merged_sha
        == "69251fd4d07665385eb6d9142038848c2b9392d7",
        "NewEMaint governance baseline SHA must be the merged Issue #35 SHA",
    )
    _require(newemaint_pilot.canary_issue == 74,
             "NewEMaint routine canary Issue must be 74")
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

    _require(
        repository_declarations_sha256(
            repositories_value, exclude_name="NewEMaint"
        )
        == newemaint_pilot.non_target_repositories_sha256,
        "non-target repository declarations changed during the NewEMaint pilot",
    )

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
