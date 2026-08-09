from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .contract import AccessContract, AccessContractError, OperationContract, ProjectContract


TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CREDENTIAL_SCALAR_FIELDS = frozenset({"protocol", "host", "path", "username"})
CREDENTIAL_REQUIRED_FIELDS = frozenset({"protocol", "host", "path"})
CREDENTIAL_PROTOCOL_MAX_LINE_BYTES = 65535


class BrokerError(RuntimeError):
    """A sanitized, fail-closed broker failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


Transport = Callable[
    [str, str, Mapping[str, str], bytes | None],
    tuple[int, Mapping[str, str], bytes],
]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _default_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
) -> tuple[int, Mapping[str, str], bytes]:
    request = Request(url, method=method, headers=dict(headers), data=body)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc


def _default_runner(
    argv: Sequence[str],
    *,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@dataclass(frozen=True)
class ResolvedCredential:
    identity: str
    token: str


@dataclass(frozen=True)
class CredentialProtocolRequest:
    scalars: Mapping[str, str]
    multivalued: Mapping[str, tuple[str, ...]]


class CredentialResolver:
    def __init__(self, contract: AccessContract, *, runner: CommandRunner = _default_runner) -> None:
        self.contract = contract
        self.runner = runner

    def resolve(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> ResolvedCredential:
        route = operation.identity_route
        if route == "project-agent":
            binding = self.contract.raw["identity_bindings"]["project_agent"]
            identity = project.project_agent
        elif route == "manager-audit":
            binding = self.contract.raw["identity_bindings"]["manager_audit"]
            identity = self.contract.governance.platform_manager
        elif route == "manager-mutation":
            binding = self.contract.raw["identity_bindings"]["manager_mutation"]
            identity = self.contract.governance.platform_manager
        else:
            raise BrokerError("IDENTITY_ROUTE_INVALID", "operation does not use a credential")
        account = identity if route == "project-agent" else binding["account"]
        result = self.runner([
            "/usr/bin/security",
            "find-generic-password",
            "-w",
            "-s",
            binding["service"],
            "-a",
            account,
        ])
        if result.returncode != 0:
            raise BrokerError("CREDENTIAL_UNAVAILABLE", "approved credential binding is unavailable")
        token = result.stdout.strip()
        if not token or not TOKEN_RE.fullmatch(token):
            raise BrokerError("CREDENTIAL_INVALID", "approved credential binding is invalid")
        return ResolvedCredential(identity, token)


class HostAccessBroker:
    def __init__(
        self,
        contract: AccessContract,
        *,
        credentials: CredentialResolver | None = None,
        transport: Transport = _default_transport,
        runner: CommandRunner = _default_runner,
    ) -> None:
        self.contract = contract
        self.credentials = credentials or CredentialResolver(contract, runner=runner)
        self.transport = transport
        self.runner = runner

    def execute(
        self,
        project_id: str,
        operation_name: str,
        *,
        number: int | None = None,
        state: str | None = None,
        branch: str | None = None,
    ) -> object:
        try:
            project = self.contract.project(project_id)
            operation = self.contract.operation(operation_name)
        except AccessContractError as exc:
            raise BrokerError("REQUEST_DENIED", str(exc)) from exc
        supplied = {
            key for key, value in {"number": number, "state": state, "branch": branch}.items()
            if value is not None
        }
        if supplied != set(operation.arguments):
            raise BrokerError("ARGUMENT_MISMATCH", "operation arguments do not match the typed contract")

        try:
            if operation_name.startswith("gitea."):
                return self._gitea(project, operation, number=number, state=state)
            if operation_name.startswith("git.") or operation_name == "mac.git.bind":
                return self._git(project, operation, branch=branch)
            if operation_name == "orbstack.vm.status":
                return self._orbstack_status(project, operation)
            if operation_name.startswith("vm.profile."):
                return self._vm_profile(project, operation)
        except AccessContractError as exc:
            raise BrokerError("REQUEST_DENIED", str(exc)) from exc
        raise BrokerError("OPERATION_UNIMPLEMENTED", "allowlisted operation has no executor")

    def _gitea(
        self,
        project: ProjectContract,
        operation: OperationContract,
        *,
        number: int | None,
        state: str | None,
    ) -> object:
        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential)
        owner = quote(self.contract.governance.owner, safe="")
        repository = quote(project.repository, safe="")
        base = self.contract.governance.base_url
        repo_api = f"{base}/api/v1/repos/{owner}/{repository}"
        if operation.name == "gitea.repo.read":
            url = repo_api
        elif operation.name == "gitea.issue.read":
            if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
                raise BrokerError("ARGUMENT_INVALID", "Issue number must be a positive integer")
            url = f"{repo_api}/issues/{number}"
        elif operation.name == "gitea.pulls.read":
            if state not in {"open", "closed", "all"}:
                raise BrokerError("ARGUMENT_INVALID", "pull state must be open, closed, or all")
            url = f"{repo_api}/pulls?state={state}&limit=50&page=1"
        elif operation.name == "gitea.protection.read":
            branch = quote(self.contract.governance.default_branch, safe="")
            url = f"{repo_api}/branch_protections/{branch}"
        else:
            raise BrokerError("OPERATION_UNIMPLEMENTED", "Gitea operation is not implemented")
        return self._request_json(url, credential.token)

    def _verify_identity(self, credential: ResolvedCredential) -> None:
        url = f"{self.contract.governance.base_url}/api/v1/user"
        value = self._request_json(url, credential.token)
        if not isinstance(value, dict) or value.get("login") != credential.identity:
            raise BrokerError("IDENTITY_MISMATCH", "credential identity does not match the route")
        if credential.identity != self.contract.governance.human_merge_identity and value.get("is_admin") is True:
            raise BrokerError("IDENTITY_MISMATCH", "automation identity unexpectedly has site-admin permission")

    def _request_json(self, url: str, token: str) -> object:
        try:
            status, _headers, body = self.transport(
                "GET", url, {"Accept": "application/json", "Authorization": f"token {token}"}, None
            )
        except BrokerError:
            raise
        except Exception as exc:  # defensive adapter boundary
            raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc
        if status in {401, 403, 404}:
            raise BrokerError(f"HTTP_{status}", f"Gitea returned HTTP {status}")
        if status < 200 or status >= 300:
            raise BrokerError("HTTP_ERROR", f"Gitea returned HTTP {status}")
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea returned invalid JSON") from exc

    def _git(
        self,
        project: ProjectContract,
        operation: OperationContract,
        *,
        branch: str | None,
    ) -> object:
        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential)
        checkout = project.mac_checkout
        if checkout is None:
            raise BrokerError("TARGET_UNAVAILABLE", "project has no approved Mac checkout")
        expected_remote = (
            f"{self.contract.governance.base_url}/{self.contract.governance.owner}/"
            f"{project.repository}.git"
        )
        remote = self._run(["git", "remote", "get-url", "origin"], cwd=checkout).stdout.strip()
        if remote != expected_remote:
            raise BrokerError("TARGET_MISMATCH", "checkout origin does not match the manifest target")
        if operation.name == "mac.git.bind":
            return self._bind_git(project, checkout, expected_remote)

        helper = self.contract.raw["mac_host"]["credential_helper"]
        env = dict(os.environ)
        env.update({
            "GIT_CONFIG_COUNT": "3",
            "GIT_CONFIG_KEY_0": "credential.helper",
            "GIT_CONFIG_VALUE_0": "",
            "GIT_CONFIG_KEY_1": "credential.helper",
            "GIT_CONFIG_VALUE_1": helper,
            "GIT_CONFIG_KEY_2": "credential.useHttpPath",
            "GIT_CONFIG_VALUE_2": "true",
        })
        if operation.name == "git.fetch.main":
            argv = ["git", "fetch", "origin", "main"]
        elif operation.name == "git.fetch.change":
            assert branch is not None
            safe_branch = self.contract.change_branch(branch)
            argv = ["git", "fetch", "origin", safe_branch]
        elif operation.name == "git.push.change":
            assert branch is not None
            safe_branch = self.contract.change_branch(branch)
            current = self._run(["git", "branch", "--show-current"], cwd=checkout).stdout.strip()
            if current != safe_branch:
                raise BrokerError("TARGET_MISMATCH", "checkout branch does not match requested change branch")
            argv = ["git", "push", "origin", f"refs/heads/{safe_branch}:refs/heads/{safe_branch}"]
        else:
            raise BrokerError("OPERATION_UNIMPLEMENTED", "Git operation is not implemented")
        self._run(argv, cwd=checkout, env=env)
        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "identity": project.project_agent,
        }

    def _bind_git(self, project: ProjectContract, checkout: str, remote: str) -> object:
        helper = self.contract.raw["mac_host"]["credential_helper"]
        url_key = f"credential.{remote}"
        desired = {
            "credential.useHttpPath": "true",
            f"{url_key}.username": project.project_agent,
        }
        changed = False
        for key, value in desired.items():
            result = self.runner(["git", "config", "--local", "--get", key], cwd=checkout)
            current = result.stdout.strip() if result.returncode == 0 else ""
            if current == value:
                continue
            self._run(["git", "config", "--local", "--replace-all", key, value], cwd=checkout)
            changed = True
        helper_key = f"{url_key}.helper"
        result = self.runner(["git", "config", "--local", "--get-all", helper_key], cwd=checkout)
        current_helpers = result.stdout.splitlines() if result.returncode == 0 else []
        if current_helpers != ["", helper]:
            self.runner(["git", "config", "--local", "--unset-all", helper_key], cwd=checkout)
            self._run(["git", "config", "--local", "--add", helper_key, ""], cwd=checkout)
            self._run(["git", "config", "--local", "--add", helper_key, helper], cwd=checkout)
            changed = True
        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": "mac.git.bind",
            "result": "updated" if changed else "no-op",
            "identity": project.project_agent,
        }

    def _orbstack_status(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> object:
        mac = self.contract.raw["mac_host"]
        self._run([
            mac["orbstack_binary"], "-m", mac["orbstack_machine"],
            "-u", mac["orbstack_user"], "/usr/bin/true",
        ])
        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "machine": mac["orbstack_machine"],
        }

    def _vm_profile(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> object:
        if project.vm_profile is None:
            raise BrokerError("TARGET_UNAVAILABLE", "project has no approved VM profile")
        action = operation.name.removeprefix("vm.profile.")
        mac = self.contract.raw["mac_host"]
        result = self._run([
            mac["orbstack_binary"], "-m", mac["orbstack_machine"],
            "-u", mac["orbstack_user"], "/usr/bin/sudo", "-n", mac["vm_profile_tool"],
            "--project", project.project_id, "--action", action,
        ])
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "profile tool returned invalid JSON") from exc
        if not isinstance(payload, dict) or payload.get("project") != project.project_id:
            raise BrokerError("TARGET_MISMATCH", "profile tool read-back target mismatch")
        return payload

    def _run(
        self,
        argv: Sequence[str],
        *,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self.runner(argv, cwd=cwd, env=env)
        except TypeError:
            result = self.runner(argv)
        except Exception as exc:
            raise BrokerError("HOST_COMMAND_FAILED", "structured host operation failed") from exc
        if result.returncode != 0:
            raise BrokerError("HOST_COMMAND_FAILED", "structured host operation failed")
        return result


def _parse_credential_protocol(protocol_input: str) -> CredentialProtocolRequest:
    scalars: dict[str, str] = {}
    multivalued: dict[str, list[str]] = {}
    terminated = False
    for line in protocol_input.split("\n"):
        if line == "":
            terminated = True
            continue
        if terminated or "\0" in line or "\r" in line or "=" not in line:
            raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential request is invalid")
        try:
            line_size = len(line.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise BrokerError(
                "CREDENTIAL_PROTOCOL_INVALID", "Git credential request is invalid"
            ) from exc
        if line_size > CREDENTIAL_PROTOCOL_MAX_LINE_BYTES:
            raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential request is invalid")
        key, value = line.split("=", 1)
        if not key:
            raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential request is invalid")
        if key.endswith("[]"):
            if key == "[]":
                raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential request is invalid")
            multivalued.setdefault(key, []).append(value)
            continue
        if key not in CREDENTIAL_SCALAR_FIELDS:
            raise BrokerError(
                "CREDENTIAL_PROTOCOL_INVALID", "Git credential fields are not allowlisted"
            )
        if key in scalars:
            raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential field is duplicated")
        scalars[key] = value
    if not CREDENTIAL_REQUIRED_FIELDS.issubset(scalars):
        raise BrokerError("CREDENTIAL_PROTOCOL_INVALID", "Git credential fields are not allowlisted")
    return CredentialProtocolRequest(
        scalars=scalars,
        multivalued={key: tuple(values) for key, values in multivalued.items()},
    )


def credential_from_protocol(
    contract: AccessContract,
    action: str,
    protocol_input: str,
    *,
    resolver: CredentialResolver | None = None,
    identity_verifier: Callable[[ResolvedCredential], None] | None = None,
) -> str:
    if action != "get":
        return ""
    request = _parse_credential_protocol(protocol_input)
    fields = request.scalars
    parsed = urlparse(contract.governance.base_url)
    if fields["protocol"] != parsed.scheme or fields["host"] != parsed.netloc:
        raise BrokerError("TARGET_MISMATCH", "Git credential host does not match the manifest")
    normalized_path = fields["path"].lstrip("/")
    project: ProjectContract | None = None
    for candidate in contract.projects:
        expected = f"{contract.governance.owner}/{candidate.repository}.git"
        if normalized_path == expected:
            project = candidate
            break
    if project is None:
        raise BrokerError("CROSS_PROJECT_DENIED", "Git credential path is not an exact managed target")
    if fields.get("username") not in {None, "", project.project_agent}:
        raise BrokerError("IDENTITY_MISMATCH", "Git credential username does not match the project")
    operation = contract.operation("git.fetch.main")
    credential = (resolver or CredentialResolver(contract)).resolve(project, operation)
    if credential.identity != project.project_agent:
        raise BrokerError("IDENTITY_MISMATCH", "Git credential identity does not match the project")
    if identity_verifier is not None:
        identity_verifier(credential)
    else:
        HostAccessBroker(contract, credentials=resolver or CredentialResolver(contract))._verify_identity(
            credential
        )
    # This is the private Git credential protocol pipe, not broker terminal output.
    return f"username={credential.identity}\npassword={credential.token}\n"
