"""Project-declared source for the typed access engine (#434, ADR 0003).

The site source binds a project through the two platform manifests and a
root-installed broker. This module is the other source: one project declares
itself in its own `.aisoft/project.json`, the engine runs unprivileged as the
current user, and the credential comes from the user's own Git credential
helper. Everything after the source — the push gates, body contract, label set,
read-backs — is the same HostAccessBroker code; this module only supplies the
values the platform manifests would have supplied and the two places where the
source genuinely differs (where the credential comes from, who it must be).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import quote, urlparse

from aisoft_gitea_governance.contract import CHANGE_CONTROL_PHASES, DEPLOYMENT_LIFECYCLES
from aisoft_main_integration import git_environment

from .broker import (
    BrokerError, HostAccessBroker, ResolvedCredential, TOKEN_RE, MAX_CREDENTIAL_BYTES,
    _default_transport,
)
from .contract import (
    EXPECTED_OPERATIONS, GIT_REMOTE_NAME_RE, AccessContract, OperationContract, ProjectContract,
)


PROJECT_FILE = ".aisoft/project.json"
SCHEMA_VERSION = 1
REQUIRED_KEYS = frozenset({
    "schema_version", "repository", "project_agent", "deployment_lifecycle",
    "classification", "status_check_contexts", "protection_evidence",
})
OPTIONAL_KEYS = frozenset({"git_remote_name", "change_control"})
# Same literal set the governance manifest loader accepts.
CLASSIFICATIONS = frozenset({"public-platform", "public-test", "internal-application"})
# Gitea owner and repository names; deliberately no dot-only or leading-dot names.
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")

# The closed operation set of the project source (spec D6 table). Names and
# argument sets are taken from EXPECTED_OPERATIONS so the two can never drift;
# every maintenance-layer operation is absent on purpose.
PROJECT_OPERATIONS = (
    "git.fetch.main", "git.fetch.change", "git.push.change",
    "gitea.repo.read",
    "gitea.issue.read", "gitea.issue.list", "gitea.issue.create", "gitea.issue.update",
    "gitea.issue.comment", "gitea.issue.comments.read",
    "gitea.issue.labels.read", "gitea.issue.labels.set", "gitea.issue.labels.classify",
    "gitea.labels.read", "gitea.labels.provision",
    "gitea.pulls.read", "gitea.pull.create", "gitea.pull.read",
    "gitea.commit.status.read", "gitea.actions.run.read", "gitea.actions.job.logs.read",
)

# Environment the user's credential helper must never see: anything that would
# make Git print the exchange.
_TRACE_PREFIXES = ("GIT_TRACE", "GIT_CURL_VERBOSE", "GIT_REDACT_COOKIES")


@dataclass(frozen=True)
class ProjectGovernance:
    """The few governance values the engine reads, derived for one project."""
    base_url: str
    owner: str
    default_branch: str = "main"
    platform_manager: None = None
    human_merge_identity: None = None


@dataclass(frozen=True)
class ProjectDeclaration:
    path: Path
    checkout: str
    canonical: str
    remote_url: str
    base_url: str
    owner: str
    repository: str
    project_agent: str
    git_remote_name: str
    change_control: str
    deployment_lifecycle: str
    classification: str
    status_check_contexts: tuple[str, ...]
    protection_evidence: int
    raw: Mapping[str, object] = field(repr=False)


def _deny(message: str) -> BrokerError:
    return BrokerError("PROJECT_DECLARATION_INVALID", message)


def _git_text(argv: Sequence[str], cwd: str) -> str | None:
    result = subprocess.run(list(argv), cwd=cwd, env=git_environment(), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout if result.returncode == 0 else None


def _toplevel(cwd: str) -> str:
    value = _git_text(["git", "rev-parse", "--show-toplevel"], cwd)
    if not value:
        raise BrokerError("TARGET_MISMATCH", "current directory is not inside a Git checkout")
    return os.path.realpath(value.strip())


def _canonical(checkout: str) -> str:
    raw = _git_text(["git", "rev-parse", "--git-common-dir"], checkout)
    if not raw:
        raise BrokerError("TARGET_MISMATCH", "cannot resolve the repository common directory")
    raw = raw.strip()
    common = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(checkout, raw))
    if os.path.basename(common) != ".git":
        raise BrokerError("TARGET_MISMATCH", "project source requires a non-bare repository")
    return os.path.dirname(common)


def _parse_remote(url: str, repository: str) -> tuple[str, str]:
    """Return (base_url, normalized_url) or refuse anything but exact http(s)."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BrokerError("TARGET_MISMATCH", "project source requires an http(s) remote")
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        raise BrokerError("TARGET_MISMATCH", "remote URL must not carry userinfo")
    if parsed.params or parsed.query or parsed.fragment:
        raise BrokerError("TARGET_MISMATCH", "remote URL must be a plain repository URL")
    if parsed.path not in {f"/{repository}", f"/{repository}.git"}:
        raise BrokerError("TARGET_MISMATCH", "remote URL does not name the declared repository")
    return f"{parsed.scheme}://{parsed.netloc}", url


def load_project_declaration(cwd: str) -> ProjectDeclaration:
    checkout = _toplevel(cwd)
    path = Path(checkout) / PROJECT_FILE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise _deny(f"{PROJECT_FILE} is required for the project source") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _deny(f"{PROJECT_FILE} is not readable JSON") from exc
    if not isinstance(raw, dict):
        raise _deny(f"{PROJECT_FILE} must be a JSON object")
    keys = set(raw)
    if not REQUIRED_KEYS <= keys or not keys <= REQUIRED_KEYS | OPTIONAL_KEYS:
        raise _deny(f"{PROJECT_FILE} keys do not match the schema")
    if raw["schema_version"] != SCHEMA_VERSION or type(raw["schema_version"]) is not int:
        raise _deny("unsupported schema_version")
    repository = raw["repository"]
    parts = repository.split("/") if isinstance(repository, str) else []
    if len(parts) != 2 or not all(NAME_RE.fullmatch(part) for part in parts):
        raise _deny("repository must be exactly owner/name")
    owner, name = parts
    agent = raw["project_agent"]
    if not isinstance(agent, str) or not LOGIN_RE.fullmatch(agent):
        raise _deny("project_agent must be a Gitea login")
    remote_name = raw.get("git_remote_name", "origin")
    if not isinstance(remote_name, str) or not GIT_REMOTE_NAME_RE.fullmatch(remote_name):
        raise _deny("git_remote_name is invalid")
    change_control = raw.get("change_control", "production")
    if change_control not in CHANGE_CONTROL_PHASES:
        raise _deny("change_control is out of range")
    lifecycle = raw["deployment_lifecycle"]
    if lifecycle not in DEPLOYMENT_LIFECYCLES:
        raise _deny("deployment_lifecycle is out of range")
    if raw["classification"] not in CLASSIFICATIONS:
        raise _deny("classification is out of range")
    contexts = raw["status_check_contexts"]
    if (not isinstance(contexts, list) or not contexts
            or not all(isinstance(item, str) and item.strip() == item and item for item in contexts)
            or len(set(contexts)) != len(contexts)):
        raise _deny("status_check_contexts must be a non-empty list of distinct names")
    evidence = raw["protection_evidence"]
    if type(evidence) is not int or evidence <= 0:
        raise _deny("protection_evidence must be a positive Issue number")

    remote_url = _validated_remote_config(checkout, remote_name)
    base_url, remote_url = _parse_remote(remote_url, repository)
    return ProjectDeclaration(
        path=path, checkout=checkout, canonical=_canonical(checkout), remote_url=remote_url,
        base_url=base_url, owner=owner, repository=name, project_agent=agent,
        git_remote_name=remote_name, change_control=change_control,
        deployment_lifecycle=lifecycle, classification=raw["classification"],
        status_check_contexts=tuple(contexts), protection_evidence=evidence, raw=raw,
    )


def _validated_remote_config(checkout: str, remote_name: str) -> str:
    """The configured URL, refusing rewrites and split push URLs up front."""
    configured = _git_text(["git", "config", "--get-all", f"remote.{remote_name}.url"], checkout)
    if configured is None:
        raise BrokerError("TARGET_MISMATCH", "declared Git remote does not exist")
    urls = configured.splitlines()
    if len(urls) != 1:
        raise BrokerError("TARGET_MISMATCH", "declared Git remote must have exactly one URL")
    push = _git_text(["git", "config", "--get-all", f"remote.{remote_name}.pushurl"], checkout)
    if push is not None and push.splitlines() != urls:
        raise BrokerError("TARGET_MISMATCH", "declared Git remote has a separate push URL")
    rewrites = _git_text(["git", "config", "--get-regexp", r"^url\..*\.(pushinsteadof|insteadof)$"], checkout)
    if rewrites:
        raise BrokerError("TARGET_MISMATCH", "URL rewrites are not allowed for the project source")
    return urls[0]


def declared_contract(declaration: ProjectDeclaration) -> AccessContract:
    project = ProjectContract(
        project_id=declaration.repository, repository=declaration.repository,
        project_agent=declaration.project_agent, git_remote_name=declaration.git_remote_name,
        mac_checkout=declaration.canonical,
    )
    operations = tuple(
        OperationContract(name, *EXPECTED_OPERATIONS[name][:2], EXPECTED_OPERATIONS[name][2])
        for name in PROJECT_OPERATIONS
    )
    governance = ProjectGovernance(base_url=declaration.base_url, owner=declaration.owner)
    return AccessContract(raw={}, path=declaration.path, governance=governance,  # type: ignore[arg-type]
                          operations=operations, projects=(project,))


def _helper_environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(_TRACE_PREFIXES)}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/usr/bin/false", SSH_ASKPASS="/usr/bin/false")
    return env


def credential_fill(declaration: ProjectDeclaration) -> tuple[str | None, str]:
    """Ask the user's own Git credential helper for the exact remote URL."""
    parsed = urlparse(declaration.remote_url)
    request = (f"protocol={parsed.scheme}\nhost={parsed.netloc}\n"
               f"path={parsed.path.lstrip('/')}\n\n")
    try:
        result = subprocess.run(["git", "credential", "fill"], cwd=declaration.checkout,
                                env=_helper_environment(), input=request, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BrokerError("CREDENTIAL_UNAVAILABLE", "Git credential helper failed") from exc
    if result.returncode != 0:
        raise BrokerError("CREDENTIAL_UNAVAILABLE", "Git credential helper has no credential for the remote")
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key] = value
    return fields.get("username"), fields.get("password", "")


class ProjectCredentials:
    """One credential per invocation, fetched once and held only in memory."""

    def __init__(self, declaration: ProjectDeclaration,
                 fill: Callable[[ProjectDeclaration], tuple[str | None, str]] = credential_fill) -> None:
        self.declaration = declaration
        self.fill = fill
        self._credential: ResolvedCredential | None = None

    def resolve(self, project: ProjectContract, operation: OperationContract) -> ResolvedCredential:
        if operation.identity_route != "project-agent":
            raise BrokerError("REQUEST_DENIED", "operation is not available to the project source")
        if self._credential is None:
            username, token = self.fill(self.declaration)
            if username not in {None, "", self.declaration.project_agent}:
                raise BrokerError("IDENTITY_MISMATCH", "credential helper returned another username")
            if (not token or len(token.encode("utf-8")) > MAX_CREDENTIAL_BYTES
                    or not TOKEN_RE.fullmatch(token)):
                raise BrokerError("CREDENTIAL_INVALID", "credential helper returned an invalid token")
            self._credential = ResolvedCredential(self.declaration.project_agent, token)
        return self._credential


def _no_redirect_transport(transport):
    def wrapped(method, url, headers, body, *, response_limit=None, follow_redirects=True):
        # Never follow a Location: the credential stays on the declared origin.
        options = {} if response_limit is None else {"response_limit": response_limit}
        try:
            return transport(method, url, headers, body, follow_redirects=False, **options)
        except TypeError:
            return transport(method, url, headers, body)
    return wrapped


class ProjectSourceBroker(HostAccessBroker):
    def __init__(self, declaration: ProjectDeclaration, *, credentials=None,
                 transport=_default_transport, runner=None, label_manifest_path: str | None = None,
                 invocation_cwd: str | None = None) -> None:
        options = {} if runner is None else {"runner": runner}
        super().__init__(declared_contract(declaration),
                         credentials=credentials or ProjectCredentials(declaration),
                         transport=_no_redirect_transport(transport),
                         invocation_cwd=invocation_cwd or declaration.checkout,
                         label_manifest_path=label_manifest_path, **options)
        self.declaration = declaration
        self._credential_dir: str | None = None

    def execute(self, project_id: str | None, operation_name: str, **arguments) -> object:
        if operation_name not in PROJECT_OPERATIONS:
            raise BrokerError("REQUEST_DENIED", "operation is not available to the project source")
        try:
            return super().execute(self.declaration.repository, operation_name, **arguments)
        finally:
            self._drop_credential_file()

    def _expected_git_url(self, project: ProjectContract) -> str:
        return self.declaration.remote_url

    def _verify_identity(self, credential: ResolvedCredential, *, require_non_admin_exact: bool = False,
                         response_limit: int | None = None, follow_redirects: bool = True) -> None:
        base = self.declaration.base_url
        user = self._request_json(f"{base}/api/v1/user", credential.token)
        if not isinstance(user, dict) or user.get("login") != self.declaration.project_agent:
            raise BrokerError("IDENTITY_MISMATCH", "credential identity is not the declared project agent")
        if user.get("is_admin") is not False:
            raise BrokerError("IDENTITY_MISMATCH", "project source refuses a site-admin identity")
        owner = quote(self.declaration.owner, safe="")
        name = quote(self.declaration.repository, safe="")
        repo = self._request_json(f"{base}/api/v1/repos/{owner}/{name}", credential.token)
        permissions = repo.get("permissions") if isinstance(repo, dict) else None
        if not isinstance(permissions, dict):
            raise BrokerError("IDENTITY_MISMATCH", "repository permissions are unreadable")
        if permissions.get("admin") is not False:
            raise BrokerError("IDENTITY_MISMATCH", "project source refuses a repository-admin identity")
        if permissions.get("push") is not True:
            raise BrokerError("IDENTITY_MISMATCH", "project identity lacks push permission")

    def _git_credential_environment(self, credential: ResolvedCredential) -> dict[str, str]:
        # Hand Git the credential already verified above, through a helper that
        # reads a mode-600 file in a mode-700 directory removed when the call
        # ends. The token is never in argv or the environment.
        if self._credential_dir is None:
            self._credential_dir = tempfile.mkdtemp(prefix="aisoft-access-")
            os.chmod(self._credential_dir, 0o700)
        secret = os.path.join(self._credential_dir, "credential")
        descriptor = os.open(secret, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"username={credential.identity}\npassword={credential.token}\n")
        helper = f"!f() {{ test \"$1\" = get && cat '{secret}'; }}; f"
        fixed = {"GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "credential.helper",
                 "GIT_CONFIG_VALUE_0": "", "GIT_CONFIG_KEY_1": "credential.helper",
                 "GIT_CONFIG_VALUE_1": helper, "GIT_CONFIG_KEY_2": "credential.useHttpPath",
                 "GIT_CONFIG_VALUE_2": "true"}
        return git_environment(fixed)

    def _drop_credential_file(self) -> None:
        if self._credential_dir is not None:
            shutil.rmtree(self._credential_dir, ignore_errors=True)
            self._credential_dir = None

    def _template_context(self, project: ProjectContract) -> object:
        raise BrokerError("SCOPE_DENIED", "template-owning changes are only available through the site source")
