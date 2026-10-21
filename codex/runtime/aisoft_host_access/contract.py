from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from aisoft_gitea_governance.contract import (
    GovernanceContract,
    load_contract as load_governance_contract,
)
from aisoft_change_name import ChangeName, ChangeNameError


IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
GIT_REMOTE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
# #396: every value that names this one installation lives in the manifest's
# site segment; the loader checks its shape and cross-references, never its
# literal values.
SITE_KEYS = {
    "gitea_url", "orbstack_machine", "orbstack_user", "credential_root_mac",
    "credential_root_vm", "platform_checkout_mac", "platform_checkout_vm",
    "npm_registry",
}

ROTATION_POLICY = {
    "operator_uid": 0,
    "grant_root": "/usr/local/etc/aisoft/credential-rotation-grants",
    "source_receipt": "/usr/local/share/aisoft/credential-rotation-source.json",
    "vm_helper": "/usr/local/libexec/aisoft/gitea-pat-helper",
    "vm_operator": "/usr/local/libexec/aisoft/rotate-gitea-service-account",
    "vm_service_user": "git",
    "gitea_binary": "/usr/local/bin/gitea",
    "gitea_config": "/etc/gitea/app.ini",
    "gitea_version": "1.26.4",
}


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


def _git_remote_name(value: Any, context: str) -> str:
    _require(
        isinstance(value, str) and bool(GIT_REMOTE_NAME_RE.fullmatch(value)),
        f"{context} must be a strict Git remote name",
    )
    return value


def _absolute_path(value: Any, context: str) -> str:
    _require(isinstance(value, str) and value.startswith("/"), f"{context} must be absolute")
    parsed = PurePosixPath(value)
    parts = parsed.parts
    # POSIX keeps a leading "//" as its own anchor, which would slip past the
    # parent checks below while the broker still opens it from "/" (#396).
    _require(parsed.anchor == "/", f"{context} must have a single leading slash")
    _require(".." not in parts and "." not in parts, f"{context} must be normalized")
    _require(str(parsed) == value, f"{context} must be normalized")
    return value


def _registry_url(value: Any, context: str) -> str:
    _require(isinstance(value, str), f"{context} must be a URL")
    parsed = urlparse(value)
    _require(parsed.scheme in {"http", "https"} and bool(parsed.hostname),
             f"{context} must be an absolute HTTP(S) URL")
    _require(parsed.username is None and parsed.password is None,
             f"{context} must not embed credentials")
    try:
        parsed.port
    except ValueError as exc:
        raise AccessContractError(f"{context} must use a valid port") from exc
    _require(not parsed.query and not parsed.fragment,
             f"{context} must not contain query or fragment")
    return value


def _inside(path: str, root: str) -> bool:
    candidate, parent = PurePosixPath(path), PurePosixPath(root)
    return candidate == parent or parent in candidate.parents


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
class ProjectContract:
    project_id: str
    repository: str
    project_agent: str
    routine_merge_agent: str | None
    git_remote_name: str
    mac_checkout: str | None
    dependency_read_targets: tuple[str, ...] = ()


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
            return self.raw["site"]["orbstack_user"]
        if operation.identity_route == "credential-operator":
            return "root"
        raise AccessContractError("operation has an unknown identity route")

    def change_branch(self, value: str) -> str:
        try:
            return ChangeName.parse_branch(value).branch
        except ChangeNameError as exc:
            raise AccessContractError(
                "Git branch must be an exact change/N or change/N-short-description branch"
            ) from exc


EXPECTED_OPERATIONS: dict[str, tuple[str, bool, tuple[str, ...]]] = {
    "gitea.credential.rotate": ("credential-operator", True, ("issue", "sha", "token_kind")),
    "gitea.repo.read": ("project-agent", False, ()),
    "gitea.dependency.read": ("manager-audit", False, ("reference",)),
    "gitea.issue.read": ("project-agent", False, ("number",)),
    # Enumerating open Issues (#222). Without it a dispatching session could only
    # read by number, so it could not check for a duplicate before opening one —
    # one project produced two duplicate pairs in a single afternoon that way, each
    # from a session doing exactly the right thing with the surface it had.
    #
    # Named .list rather than the plural .read that gitea.pulls.read uses: the
    # Issue that asked for it and the dispatching-session skill that consumes it
    # both spell it this way, and a rename would silently break the skill's
    # instruction. The split is deliberate, not an oversight.
    #
    # Deliberately no label, author, milestone or keyword filter: every extra
    # argument is another way to ask a question the caller could answer locally
    # from one bounded list, and the exact-set argument gate means each one would
    # also have to be supplied on every call.
    "gitea.issue.list": ("project-agent", False, ("state",)),
    # entry_label is required, not defaulted (#243). The broker argument gate is
    # exact set equality, so this contract has no optional-argument form at all;
    # more to the point, an Issue that reaches the tracker without naming its
    # flow entrance is exactly the inbox this operation created. Required means a
    # caller that forgets fails with ARGUMENT_MISMATCH before a credential is
    # resolved, and the call site says which entrance the Issue took.
    "gitea.issue.create": ("project-agent", True, ("title", "body", "entry_label")),
    "gitea.issue.update": ("project-agent", True, ("number", "title", "body")),
    # The open/closed half of the Issue surface (#222), deliberately separate from
    # gitea.issue.update rather than a fourth field on it: update rewrites the
    # text a human wrote, this one moves the Issue through the flow, and folding
    # them together would make every title fix carry the power to close.
    #
    # Its absence was not merely inconvenient. apply-classification-labels.sh
    # refuses to project a classification onto a closed Issue (#167), so one
    # mistaken close left an implementation session with no way to reach the
    # ready-to-merge state, and no typed way back. Reopening is as much the point
    # as closing.
    "gitea.issue.state.set": ("project-agent", True, ("number", "state")),
    "gitea.issue.comment": ("project-agent", True, ("number", "comment")),
    # The read half of the comment surface (#138). Singular comment posts one;
    # plural comments.read reads the collection — the same number/plural split
    # gitea.issue.labels.* already uses. Deliberately no update or delete
    # counterpart: rewriting or removing someone else's comment is a human
    # decision, and a typed operation would make erasing the discussion record
    # a supported automation.
    "gitea.issue.comments.read": ("project-agent", False, ("number",)),
    "gitea.pulls.read": ("project-agent", False, ("state",)),
    "gitea.pull.create": ("project-agent", True, ("issue", "title", "body")),
    "gitea.pull.read": ("project-agent", False, ("number",)),
    "gitea.pull.update": ("project-agent", True, ("number", "issue", "title", "body")),
    "gitea.commit.status.read": ("project-agent", False, ("sha",)),
    # Actions evidence (#143). commit.status.read stops at a context, a status
    # and a target_url that is a Web UI path nothing here can follow, so a green
    # run could not be read and a red one could not be diagnosed at all.
    # Two operations rather than one: the step-level summary is a few hundred
    # bytes and answers "which steps ran and for how long" without touching a
    # log, while a job log can be megabytes. Folding them together would make
    # the cheap question cost the expensive answer.
    # SHA-keyed like commit.status.read — the caller already holds the SHA, and
    # a run id would have to be scraped out of target_url. Job ids come out of
    # run.read, so no caller ever parses a URL.
    # Deliberately no rerun, cancel or dispatch counterpart: triggering CI is a
    # human decision, and a typed operation would make it a supported automation.
    "gitea.actions.run.read": ("project-agent", False, ("sha",)),
    "gitea.actions.job.logs.read": ("project-agent", False, ("job",)),
    # Repository-level label definitions (#108), distinct from the per-Issue
    # label attachment surface. Deliberately no delete counterpart: retiring a
    # label is a human migration decision, and a typed delete would make it
    # silently automatable.
    "gitea.labels.read": ("project-agent", False, ()),
    "gitea.labels.provision": ("project-agent", True, ()),
    "gitea.labels.extension.define": (
        "project-agent", True, ("label", "color", "description"),
    ),
    # Per-Issue label attachment (#115), the other half of the pair above. The
    # naming rule from #108 holds: an operation with an issue. segment attaches,
    # one without defines. One operation per label dimension, never one that
    # takes a label set: set writes lifecycle, classify writes the analyzer's
    # two dimensions, and neither can drop the other's labels or triage/.
    #
    # classify exists because the analyzer dimensions had exactly one writer,
    # aisoft_loop's apply-analysis, and it only ever runs inside the Development
    # Loop — so every Issue opened from an interactive session carried no type/
    # and no complexity/ at all (#160). What #115 ruled out here was an
    # arbitrary label write, which would indeed be a way around the producing
    # pipeline. This is the projection of the pipeline's own output: its only
    # caller is apply-classification-labels.sh, which reads change_type and
    # effective_complexity out of the Issue's mapped summary front matter and
    # cannot be handed a label by its caller. The bare values are namespaced and
    # checked against the installed manifest here, so the surface still refuses
    # anything the label contract does not define.
    #
    # Both dimensions are required rather than optional: a classification is a
    # (type, complexity) pair, and the supplied-arguments check below is what
    # makes projecting half of one unrepresentable.
    "gitea.issue.labels.read": ("project-agent", False, ("number",)),
    "gitea.issue.labels.set": ("project-agent", True, ("number", "lifecycle")),
    "gitea.issue.labels.extension.set": (
        "project-agent", True, ("number", "label"),
    ),
    "gitea.issue.labels.classify": (
        "project-agent", True, ("number", "change_type", "complexity"),
    ),
    "gitea.protection.read": ("manager-audit", False, ()),
    "host.access.audit": ("manager-audit", False, ()),
    "host.onboarding.check": ("manager-audit", False, ()),
    "git.fetch.main": ("project-agent", False, ()),
    "git.fetch.change": ("project-agent", False, ("branch",)),
    "git.push.change": ("project-agent", True, ("branch",)),
    "mac.git.bind": ("project-agent", True, ()),
    "orbstack.vm.status": ("host-operator", False, ()),
    # act_runner liveness (#228). Separate from vm.status because they answer
    # different questions: vm.status says the VM is reachable, this says whether
    # the one execution slot is idle, working or stuck. Named orbstack. rather
    # than the gitea. the Issue suggested — dispatch routes by prefix, and a
    # gitea. name would send a systemd/journal read down the Gitea HTTP path.
    # Read-only and argument-free on purpose: cancelling a run or killing a
    # stuck process stays a human decision, and a typed operation would make it
    # a supported automation, exactly as the actions.* pair already refuses.
    "orbstack.runner.status": ("host-operator", False, ()),
    # VM timer health (#387). Two agent timers failed every 15 minutes for two
    # months and nothing on the platform could see it: vm.status only proves the
    # machine answers and check-installed-drift compares files, not outcomes.
    # This reads the runtime user's systemd --user timers and counts their
    # services' failures from the journal's structured failure records, so no
    # log text or environment crosses the boundary. Read-only and argument-free:
    # stopping or re-enabling a timer stays a human operation on the VM.
    "orbstack.vm.units.read": ("host-operator", False, ()),
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
            "contract_version", "environment", "site", "governance_contract_version",
            "human_merge_identity", "identity_bindings", "mac_host",
            "vm_runtime", "credential_rotation_policy", "operations", "projects",
        },
        "host access manifest",
    )
    _require(raw["contract_version"] == "host-access-broker/v1",
             "unsupported host access contract version")
    _require(raw["environment"] == "local-orbstack", "unexpected host environment")
    _require(raw["credential_rotation_policy"] == ROTATION_POLICY,
             "credential rotation must use the fixed operator custody/transport policy")
    _require(raw["governance_contract_version"] == "gitea-governance/v1",
             "unexpected governance contract reference")

    governance = load_governance_contract(governance_path)
    _require(raw["human_merge_identity"] == governance.human_merge_identity,
             "human merge identity does not match governance manifest")

    bindings = raw["identity_bindings"]
    _require(isinstance(bindings, dict), "identity_bindings must be an object")
    _exact_keys(bindings, {"manager_audit", "manager_mutation", "project_agent",
                           "routine_merge_agent"},
                "identity_bindings")
    for key, relative_path in (
        ("manager_audit", "manager/audit.token"),
        ("manager_mutation", "manager/mutation.token"),
    ):
        binding = bindings[key]
        _require(isinstance(binding, dict), f"{key} binding must be an object")
        _exact_keys(binding, {"identity", "credential_kind", "relative_path"}, key)
        _require(binding["identity"] == governance.platform_manager,
                 f"{key} identity must be the platform manager")
        _require(binding["credential_kind"] == "protected-file",
                 f"{key} must use a protected file")
        _require(_relative_path(binding["relative_path"], f"{key}.relative_path") == relative_path,
                 f"{key} must use its fixed relative path")
    project_binding = bindings["project_agent"]
    _require(isinstance(project_binding, dict), "project_agent binding must be an object")
    _exact_keys(project_binding,
                {"credential_kind", "relative_path_template", "account_source"},
                "project_agent binding")
    _require(project_binding == {
        "credential_kind": "protected-file",
        "relative_path_template": "projects/{project_id}/project-agent.token",
        "account_source": "manifest-project-agent",
    }, "project agents must use the fixed protected-file binding")
    merger_binding = bindings["routine_merge_agent"]
    _require(isinstance(merger_binding, dict),
             "routine_merge_agent binding must be an object")
    _exact_keys(
        merger_binding,
        {"credential_kind", "relative_path_template", "account_source"},
        "routine_merge_agent binding",
    )
    _require(merger_binding == {
        "credential_kind": "protected-file",
        "relative_path_template": "projects/{project_id}/routine-merge-agent.token",
        "account_source": "manifest-routine-merge-agent",
    }, "routine merger must use the fixed per-project protected-file binding")

    site = raw["site"]
    _require(isinstance(site, dict), "site must be an object")
    _exact_keys(site, SITE_KEYS, "site")
    _require(site["gitea_url"] == governance.base_url,
             "site.gitea_url must equal the governance base_url")
    _identifier(site["orbstack_machine"], "site.orbstack_machine")
    _identifier(site["orbstack_user"], "site.orbstack_user")
    for key in ("credential_root_mac", "credential_root_vm",
                "platform_checkout_mac", "platform_checkout_vm"):
        _absolute_path(site[key], f"site.{key}")
        _require(site[key] != "/", f"site.{key} must not be the filesystem root")
    _registry_url(site["npm_registry"], "site.npm_registry")

    mac = raw["mac_host"]
    _require(isinstance(mac, dict), "mac_host must be an object")
    _exact_keys(mac, {
        "credential_owner", "credential_directory_mode",
        "credential_file_mode", "credential_helper", "orbstack_binary",
    }, "mac_host")
    # One Mac operator account both owns the credential store and runs orb.
    _require(_identifier(mac["credential_owner"], "credential_owner") == site["orbstack_user"],
             "credential owner must be the site OrbStack operator")
    _require(mac["credential_directory_mode"] == "700",
             "credential directories must use mode 700")
    _require(mac["credential_file_mode"] == "600",
             "credential files must use mode 600")
    _require(_absolute_path(mac["credential_helper"], "credential_helper") ==
             "/usr/local/libexec/aisoft/git-credential-aisoft-host",
             "credential helper path must be fixed")
    _require(_absolute_path(mac["orbstack_binary"], "orbstack_binary") ==
             "/usr/local/bin/orb", "OrbStack binary path must be fixed")

    runtime = raw["vm_runtime"]
    _require(isinstance(runtime, dict), "vm_runtime must be an object")
    _exact_keys(runtime, {"runtime_user"}, "vm_runtime")
    _require(runtime["runtime_user"] == "coder", "VM runtime user must be coder")

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
    for index, item in enumerate(projects_raw):
        _require(isinstance(item, dict), f"projects[{index}] must be an object")
        required_project_keys = {
            "project_id", "repository", "project_agent", "routine_merge_agent",
            "mac_checkout",
        }
        project_keys = set(item)
        _require(
            required_project_keys <= project_keys
            and project_keys <= required_project_keys | {"git_remote_name", "dependency_read_targets"},
            f"projects[{index}] keys mismatch",
        )
        project_id = _identifier(item["project_id"], f"projects[{index}].project_id")
        repository = _identifier(item["repository"], f"projects[{index}].repository")
        project_agent = _identifier(item["project_agent"], f"projects[{index}].project_agent")
        routine_merge_raw = item["routine_merge_agent"]
        routine_merge_agent = (
            None if routine_merge_raw is None else
            _identifier(routine_merge_raw, f"projects[{index}].routine_merge_agent")
        )
        git_remote_name = _git_remote_name(
            item.get("git_remote_name", "origin"),
            f"projects[{index}].git_remote_name",
        )
        _require(project_id not in project_ids, f"duplicate project_id: {project_id}")
        _require(repository not in repositories, f"duplicate repository mapping: {repository}")
        project_ids.add(project_id)
        repositories.add(repository)
        _require(repository in governance_by_name, f"repository is absent from governance: {repository}")
        _require(project_agent == governance_by_name[repository].project_agent,
                 f"project-agent mismatch for {repository}")
        _require(
            routine_merge_agent == governance_by_name[repository].routine_merge_agent,
            f"routine-merger mismatch for {repository}",
        )
        pilot = governance_by_name[repository].routine_live_pilot
        if pilot is not None:
            _require(
                project_id == pilot.project_id,
                f"routine live pilot project id mismatch for {repository}",
            )
        mac_checkout = item["mac_checkout"]
        if mac_checkout is not None:
            mac_checkout = _absolute_path(mac_checkout, f"projects[{index}].mac_checkout")
        targets_raw = item.get("dependency_read_targets", [])
        _require(isinstance(targets_raw, list), "dependency_read_targets must be a list")
        targets = tuple(_identifier(target, "dependency_read_targets") for target in targets_raw)
        _require(len(set(targets)) == len(targets) and project_id not in targets,
                 "dependency_read_targets must be unique external project ids")
        projects.append(ProjectContract(project_id, repository, project_agent,
                                        routine_merge_agent, git_remote_name,
                                        mac_checkout, targets))

    _require(all(set(p.dependency_read_targets) <= project_ids for p in projects),
             "dependency_read_targets must name canonical projects")
    _require(repositories == set(governance_by_name),
             "host access projects must exactly cover governance repositories")
    platform_checkouts = {
        project.mac_checkout for project in projects
        if governance_by_name[project.repository].classification == "public-platform"
    }
    _require(platform_checkouts == {site["platform_checkout_mac"]},
             "site.platform_checkout_mac must equal the platform project's mac_checkout")
    checkouts = {project.mac_checkout for project in projects if project.mac_checkout}
    _require(not any(_inside(site["credential_root_mac"], checkout) for checkout in checkouts),
             "credential root must stay outside every repository checkout")
    _require(governance.human_merge_identity not in {
        project.project_agent for project in projects
    }, "human merge identity must never be a broker credential")

    return AccessContract(raw, path, governance, tuple(operations), tuple(projects))
