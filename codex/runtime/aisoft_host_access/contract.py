from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from aisoft_gitea_governance.contract import (
    GovernanceContract,
    load_contract as load_governance_contract,
)


IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CHANGE_BRANCH_RE = re.compile(r"^change/[1-9][0-9]*$")


class AccessContractError(ValueError):
    """Raised when host-access configuration is unsafe or ambiguous."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AccessContractError(message)


def _exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AccessContractError(
            f"{context} keys mismatch: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _identifier(value: Any, context: str) -> str:
    _require(
        isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value)),
        f"{context} must be a safe identifier",
    )
    return value


def _absolute_path(value: Any, context: str) -> str:
    _require(isinstance(value, str) and value.startswith("/"), f"{context} must be absolute")
    parsed = PurePosixPath(value)
    parts = parsed.parts
    _require(".." not in parts and "." not in parts, f"{context} must be normalized")
    _require(str(parsed) == value, f"{context} must be normalized")
    return value


def _relative_path(value: Any, context: str) -> str:
    _require(isinstance(value, str) and value and not value.startswith("/"),
             f"{context} must be HOME-relative")
    parsed = PurePosixPath(value)
    parts = parsed.parts
    _require(".." not in parts and "." not in parts, f"{context} must be normalized")
    _require(str(parsed) == value, f"{context} must be normalized")
    return value


@dataclass(frozen=True)
class OperationContract:
    name: str
    identity_route: str
    mutating: bool
    arguments: tuple[str, ...]


@dataclass(frozen=True)
class VMProfileContract:
    name: str
    repo_dir: str
    analysis_provider: str
    implement_provider: str
    timer_unit: str | None


@dataclass(frozen=True)
class ProjectContract:
    project_id: str
    repository: str
    project_agent: str
    mac_checkout: str | None
    vm_profile: VMProfileContract | None


@dataclass(frozen=True)
class AccessContract:
    raw: dict[str, Any]
    path: Path
    governance: GovernanceContract
    operations: tuple[OperationContract, ...]
    projects: tuple[ProjectContract, ...]

    def project(self, project_id: str) -> ProjectContract:
        for project in self.projects:
            if project.project_id == project_id:
                return project
        raise AccessContractError("requested project is not explicitly managed")

    def project_for_profile(self, profile_name: str) -> ProjectContract:
        for project in self.projects:
            if project.vm_profile and project.vm_profile.name == profile_name:
                return project
        raise AccessContractError("requested profile is not explicitly managed")

    def operation(self, name: str) -> OperationContract:
        for operation in self.operations:
            if operation.name == name:
                return operation
        raise AccessContractError("requested operation is not allowlisted")

    def identity_for(self, project: ProjectContract, operation: OperationContract) -> str:
        if operation.identity_route == "project-agent":
            return project.project_agent
        if operation.identity_route in {"manager-audit", "manager-mutation"}:
            return self.governance.platform_manager
        if operation.identity_route == "host-operator":
            return self.raw["mac_host"]["orbstack_user"]
        raise AccessContractError("operation has an unknown identity route")

    def change_branch(self, value: str) -> str:
        _require(bool(CHANGE_BRANCH_RE.fullmatch(value)),
                 "Git branch must be an exact change/N branch")
        return value


EXPECTED_OPERATIONS: dict[str, tuple[str, bool, tuple[str, ...]]] = {
    "gitea.repo.read": ("project-agent", False, ()),
    "gitea.issue.read": ("project-agent", False, ("number",)),
    "gitea.pulls.read": ("project-agent", False, ("state",)),
    "gitea.protection.read": ("manager-audit", False, ()),
    "git.fetch.main": ("project-agent", False, ()),
    "git.fetch.change": ("project-agent", False, ("branch",)),
    "git.push.change": ("project-agent", True, ("branch",)),
    "mac.git.bind": ("project-agent", True, ()),
    "orbstack.vm.status": ("host-operator", False, ()),
    "vm.profile.plan": ("host-operator", False, ()),
    "vm.profile.apply": ("host-operator", True, ()),
    "vm.profile.read-back": ("host-operator", False, ()),
    "vm.profile.rollback": ("host-operator", True, ()),
}


def load_access_contract(
    access_path: str | Path,
    governance_path: str | Path,
) -> AccessContract:
    path = Path(access_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AccessContractError(f"cannot read host access manifest: {exc}") from exc
    _require(isinstance(raw, dict), "host access manifest root must be an object")
    _exact_keys(
        raw,
        {
            "contract_version", "environment", "governance_contract_version",
            "human_merge_identity", "identity_bindings", "mac_host",
            "vm_profile_policy", "operations", "projects",
        },
        "host access manifest",
    )
    _require(raw["contract_version"] == "host-access-broker/v1",
             "unsupported host access contract version")
    _require(raw["environment"] == "local-orbstack", "unexpected host environment")
    _require(raw["governance_contract_version"] == "gitea-governance/v1",
             "unexpected governance contract reference")

    governance = load_governance_contract(governance_path)
    _require(raw["human_merge_identity"] == governance.human_merge_identity,
             "human merge identity does not match governance manifest")

    bindings = raw["identity_bindings"]
    _require(isinstance(bindings, dict), "identity_bindings must be an object")
    _exact_keys(bindings, {"manager_audit", "manager_mutation", "project_agent"},
                "identity_bindings")
    for key, service in (
        ("manager_audit", "aisoft.gitea.manager-audit"),
        ("manager_mutation", "aisoft.gitea.manager-mutation"),
    ):
        binding = bindings[key]
        _require(isinstance(binding, dict), f"{key} binding must be an object")
        _exact_keys(binding, {"identity", "credential_kind", "service", "account"}, key)
        _require(binding["identity"] == governance.platform_manager,
                 f"{key} identity must be the platform manager")
        _require(binding["credential_kind"] == "macos-keychain",
                 f"{key} must use macOS Keychain")
        _require(binding["service"] == service, f"{key} must use its fixed Keychain service")
        _require(binding["account"] == governance.platform_manager,
                 f"{key} account must be the platform manager")
    project_binding = bindings["project_agent"]
    _require(isinstance(project_binding, dict), "project_agent binding must be an object")
    _exact_keys(project_binding, {"credential_kind", "service", "account_source"},
                "project_agent binding")
    _require(project_binding == {
        "credential_kind": "macos-keychain",
        "service": "aisoft.gitea.project-agent",
        "account_source": "manifest-project-agent",
    }, "project agents must use the fixed Keychain binding")

    mac = raw["mac_host"]
    _require(isinstance(mac, dict), "mac_host must be an object")
    _exact_keys(mac, {"credential_helper", "orbstack_binary", "orbstack_machine",
                      "orbstack_user", "vm_profile_tool"}, "mac_host")
    _require(_absolute_path(mac["credential_helper"], "credential_helper") ==
             "/usr/local/libexec/aisoft/git-credential-aisoft-host",
             "credential helper path must be fixed")
    _require(_absolute_path(mac["orbstack_binary"], "orbstack_binary") ==
             "/usr/local/bin/orb", "OrbStack binary path must be fixed")
    _require(mac["orbstack_machine"] == "gitea-ci", "OrbStack machine must be gitea-ci")
    _require(mac["orbstack_user"] == "benque", "OrbStack operator must be benque")
    _require(_absolute_path(mac["vm_profile_tool"], "vm_profile_tool") ==
             "/usr/local/libexec/aisoft/project-profile-migration",
             "VM profile tool path must be fixed")

    policy = raw["vm_profile_policy"]
    _require(isinstance(policy, dict), "vm_profile_policy must be an object")
    _exact_keys(policy, {"runtime_user", "runtime_home", "profile_root", "token_root", "backup_root",
                         "source_credential_root", "source_credential_owner",
                         "allowed_file_modes"},
                "vm_profile_policy")
    _require(policy["runtime_user"] == "coder", "VM runtime user must be coder")
    _require(_absolute_path(policy["runtime_home"], "vm_profile_policy.runtime_home") ==
             "/home/coder", "VM runtime HOME must be fixed")
    for key in ("profile_root", "token_root", "backup_root"):
        _relative_path(policy[key], f"vm_profile_policy.{key}")
    _require(_absolute_path(policy["source_credential_root"],
                            "vm_profile_policy.source_credential_root") ==
             "/home/benque/.config/aisoft/credentials",
             "source credential root must be fixed")
    _require(policy["source_credential_owner"] == "benque",
             "source credential owner must be benque")
    _require(policy["allowed_file_modes"] == ["400", "600"],
             "credential/profile modes must be exactly 400/600")

    operations_raw = raw["operations"]
    _require(isinstance(operations_raw, list), "operations must be a list")
    operations: list[OperationContract] = []
    names: set[str] = set()
    for index, item in enumerate(operations_raw):
        _require(isinstance(item, dict), f"operations[{index}] must be an object")
        _exact_keys(item, {"name", "identity_route", "mutating", "arguments"},
                    f"operations[{index}]")
        name = item["name"]
        _require(isinstance(name, str) and name in EXPECTED_OPERATIONS,
                 "operation is not in the fixed v1 allowlist")
        _require(name not in names, f"duplicate operation: {name}")
        _require(not any(word in name for word in ("merge", "shell", "command", "url")),
                 "unsafe operation surface")
        names.add(name)
        expected_route, expected_mutating, expected_args = EXPECTED_OPERATIONS[name]
        _require(item["identity_route"] == expected_route,
                 f"identity route mismatch for {name}")
        _require(item["mutating"] is expected_mutating, f"mutation flag mismatch for {name}")
        _require(item["arguments"] == list(expected_args), f"argument contract mismatch for {name}")
        operations.append(OperationContract(
            name=name,
            identity_route=expected_route,
            mutating=expected_mutating,
            arguments=expected_args,
        ))
    _require(names == set(EXPECTED_OPERATIONS), "operation catalog must be complete and exact")

    projects_raw = raw["projects"]
    _require(isinstance(projects_raw, list), "projects must be a list")
    governance_by_name = {item.name: item for item in governance.repositories}
    projects: list[ProjectContract] = []
    project_ids: set[str] = set()
    repositories: set[str] = set()
    profile_names: set[str] = set()
    profile_repositories: set[str] = set()
    for index, item in enumerate(projects_raw):
        _require(isinstance(item, dict), f"projects[{index}] must be an object")
        _exact_keys(item, {"project_id", "repository", "project_agent", "mac_checkout",
                           "vm_profile"}, f"projects[{index}]")
        project_id = _identifier(item["project_id"], f"projects[{index}].project_id")
        repository = _identifier(item["repository"], f"projects[{index}].repository")
        project_agent = _identifier(item["project_agent"], f"projects[{index}].project_agent")
        _require(project_id not in project_ids, f"duplicate project_id: {project_id}")
        _require(repository not in repositories, f"duplicate repository mapping: {repository}")
        project_ids.add(project_id)
        repositories.add(repository)
        _require(repository in governance_by_name, f"repository is absent from governance: {repository}")
        _require(project_agent == governance_by_name[repository].project_agent,
                 f"project-agent mismatch for {repository}")
        mac_checkout = item["mac_checkout"]
        if mac_checkout is not None:
            mac_checkout = _absolute_path(mac_checkout, f"projects[{index}].mac_checkout")
        vm_raw = item["vm_profile"]
        vm_profile: VMProfileContract | None = None
        if vm_raw is not None:
            _require(isinstance(vm_raw, dict), f"projects[{index}].vm_profile must be an object")
            _exact_keys(vm_raw, {"name", "repo_dir", "analysis_provider", "implement_provider",
                                 "timer_unit"}, f"projects[{index}].vm_profile")
            profile_name = _identifier(vm_raw["name"], f"projects[{index}].vm_profile.name")
            _require(profile_name not in profile_names, f"duplicate VM profile: {profile_name}")
            profile_names.add(profile_name)
            profile_repositories.add(repository)
            repo_dir = _relative_path(vm_raw["repo_dir"],
                                      f"projects[{index}].vm_profile.repo_dir")
            analysis = vm_raw["analysis_provider"]
            implementation = vm_raw["implement_provider"]
            _require(analysis in {"claude", "codex", "none"}, "invalid analysis provider")
            _require(implementation in {"claude", "codex", "none"},
                     "invalid implementation provider")
            _require(implementation == "none", "implementation must remain disabled during migration")
            timer = vm_raw["timer_unit"]
            _require(timer is None or timer in {
                "aisoft-agent@emaintenance.timer", "aisoft-agent@sfm.timer"
            }, "timer_unit is not allowlisted")
            vm_profile = VMProfileContract(profile_name, repo_dir, analysis, implementation, timer)
        projects.append(ProjectContract(project_id, repository, project_agent,
                                        mac_checkout, vm_profile))

    _require(repositories == set(governance_by_name),
             "host access projects must exactly cover governance repositories")
    _require(profile_repositories == {"NewEMaint", "HSDB", "rsdesign-new", "SFMDigitalBoard"},
             "VM profile migration set must contain exactly the four approved repositories")
    _require(governance.human_merge_identity not in {
        project.project_agent for project in projects
    }, "human merge identity must never be a broker credential")

    return AccessContract(raw, path, governance, tuple(operations), tuple(projects))
