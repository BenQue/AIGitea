from __future__ import annotations

import json
import os
import pwd
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .contract import AccessContract, AccessContractError, OperationContract, ProjectContract


TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CREDENTIAL_SCALAR_FIELDS = frozenset({"protocol", "host", "path", "username"})
CREDENTIAL_REQUIRED_FIELDS = frozenset({"protocol", "host", "path"})
CREDENTIAL_PROTOCOL_MAX_LINE_BYTES = 65535
TITLE_MAX_BYTES = 255
BODY_MAX_BYTES = 65536
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_CREDENTIAL_BYTES = 4096


class BrokerError(RuntimeError):
    """A sanitized, fail-closed broker failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _positive_number(value: int | None, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise BrokerError("ARGUMENT_INVALID", f"{label} number must be a positive integer")
    return value


def _typed_text(label: str, value: str | None, max_bytes: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BrokerError("ARGUMENT_INVALID", f"{label} must not be empty")
    if "\0" in value or "\r" in value:
        raise BrokerError("ARGUMENT_INVALID", f"{label} contains forbidden characters")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise BrokerError("ARGUMENT_INVALID", f"{label} is not valid UTF-8 text") from exc
    if size > max_bytes:
        raise BrokerError("ARGUMENT_INVALID", f"{label} exceeds its typed size limit")
    return value


def _pull_body(issue: int | None, value: str | None) -> str:
    number = _positive_number(issue, "Issue")
    body = _typed_text("pull request body", value, BODY_MAX_BYTES)
    if not re.search(rf"(?<![0-9])Closes #{number}(?![0-9])", body):
        raise BrokerError("ARGUMENT_INVALID", "pull request body must close its exact Issue")
    summary = re.compile(
        rf"docs/changes/{number}/summary-[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{{6}}\.md"
    )
    if not summary.search(body):
        raise BrokerError("ARGUMENT_INVALID", "pull request body must link its semantic summary")
    return body


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
    def __init__(self, contract: AccessContract, *, expected_uid: int | None = None) -> None:
        self.contract = contract
        mac = contract.raw["mac_host"]
        self.root = mac["credential_root"]
        if expected_uid is None:
            try:
                expected_uid = pwd.getpwnam(mac["credential_owner"]).pw_uid
            except KeyError as exc:
                raise BrokerError(
                    "CREDENTIAL_OWNER_INVALID", "credential owner is unavailable"
                ) from exc
        self.expected_uid = expected_uid
        self.directory_mode = int(mac["credential_directory_mode"], 8)
        self.file_mode = int(mac["credential_file_mode"], 8)

    def resolve(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> ResolvedCredential:
        route = operation.identity_route
        if route == "project-agent":
            binding = self.contract.raw["identity_bindings"]["project_agent"]
            identity = project.project_agent
            relative_path = binding["relative_path_template"].format(
                project_id=project.project_id
            )
        elif route == "manager-audit":
            binding = self.contract.raw["identity_bindings"]["manager_audit"]
            identity = self.contract.governance.platform_manager
            relative_path = binding["relative_path"]
        elif route == "manager-mutation":
            binding = self.contract.raw["identity_bindings"]["manager_mutation"]
            identity = self.contract.governance.platform_manager
            relative_path = binding["relative_path"]
        else:
            raise BrokerError("IDENTITY_ROUTE_INVALID", "operation does not use a credential")
        token = self._read_token(relative_path)
        if not token or not TOKEN_RE.fullmatch(token):
            raise BrokerError("CREDENTIAL_INVALID", "approved credential binding is invalid")
        return ResolvedCredential(identity, token)

    def _read_token(self, relative_path: str) -> str:
        parsed = PurePosixPath(relative_path)
        if (
            parsed.is_absolute()
            or not parsed.parts
            or any(part in {"", ".", ".."} for part in parsed.parts)
        ):
            raise BrokerError("CREDENTIAL_BINDING_INVALID", "credential binding is invalid")

        directory_fd: int | None = None
        credential_fd: int | None = None
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            directory_fd = self._open_root(directory_flags)
            self._validate_directory(os.fstat(directory_fd))
            for component in parsed.parts[:-1]:
                next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
                self._validate_directory(os.fstat(directory_fd))
            credential_fd = os.open(
                parsed.parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
            )
            metadata = os.fstat(credential_fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise BrokerError(
                    "CREDENTIAL_TYPE_INVALID", "credential must be a regular file"
                )
            if metadata.st_uid != self.expected_uid:
                raise BrokerError(
                    "CREDENTIAL_OWNER_INVALID", "credential owner does not match"
                )
            if stat.S_IMODE(metadata.st_mode) != self.file_mode:
                raise BrokerError(
                    "CREDENTIAL_MODE_INVALID", "credential file mode does not match"
                )
            if metadata.st_nlink != 1:
                raise BrokerError(
                    "CREDENTIAL_LINK_INVALID", "credential file link count does not match"
                )
            data = os.read(credential_fd, MAX_CREDENTIAL_BYTES + 1)
        except BrokerError:
            raise
        except OSError as exc:
            raise BrokerError(
                "CREDENTIAL_UNAVAILABLE", "approved credential binding is unavailable"
            ) from exc
        finally:
            if credential_fd is not None:
                os.close(credential_fd)
            if directory_fd is not None:
                os.close(directory_fd)

        if len(data) > MAX_CREDENTIAL_BYTES:
            raise BrokerError("CREDENTIAL_INVALID", "approved credential binding is invalid")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BrokerError("CREDENTIAL_INVALID", "approved credential binding is invalid") from exc
        token = text[:-1] if text.endswith("\n") else text
        if text not in {token, f"{token}\n"}:
            raise BrokerError("CREDENTIAL_INVALID", "approved credential binding is invalid")
        return token

    def _open_root(self, directory_flags: int) -> int:
        parsed = PurePosixPath(self.root)
        if not parsed.is_absolute() or len(parsed.parts) < 2:
            raise BrokerError("CREDENTIAL_BINDING_INVALID", "credential root is invalid")
        current_fd = os.open("/", directory_flags)
        try:
            for component in parsed.parts[1:]:
                next_fd = os.open(component, directory_flags, dir_fd=current_fd)
                os.close(current_fd)
                current_fd = next_fd
            return current_fd
        except Exception:
            os.close(current_fd)
            raise

    def _validate_directory(self, metadata: os.stat_result) -> None:
        if not stat.S_ISDIR(metadata.st_mode):
            raise BrokerError(
                "CREDENTIAL_DIRECTORY_INVALID", "credential directory is invalid"
            )
        if metadata.st_uid != self.expected_uid:
            raise BrokerError(
                "CREDENTIAL_OWNER_INVALID", "credential directory owner does not match"
            )
        if stat.S_IMODE(metadata.st_mode) != self.directory_mode:
            raise BrokerError(
                "CREDENTIAL_MODE_INVALID", "credential directory mode does not match"
            )


class HostAccessBroker:
    def __init__(
        self,
        contract: AccessContract,
        *,
        credentials: CredentialResolver | None = None,
        transport: Transport = _default_transport,
        runner: CommandRunner = _default_runner,
        invocation_cwd: str | None = None,
    ) -> None:
        self.contract = contract
        self.credentials = credentials or CredentialResolver(contract)
        self.transport = transport
        self.runner = runner
        self.invocation_cwd = os.path.realpath(invocation_cwd or os.getcwd())

    def execute(
        self,
        project_id: str,
        operation_name: str,
        *,
        number: int | None = None,
        state: str | None = None,
        branch: str | None = None,
        issue: int | None = None,
        title: str | None = None,
        body: str | None = None,
        comment: str | None = None,
        sha: str | None = None,
    ) -> object:
        try:
            project = self.contract.project(project_id)
            operation = self.contract.operation(operation_name)
        except AccessContractError as exc:
            raise BrokerError("REQUEST_DENIED", str(exc)) from exc
        arguments = {
            "number": number,
            "state": state,
            "branch": branch,
            "issue": issue,
            "title": title,
            "body": body,
            "comment": comment,
            "sha": sha,
        }
        supplied = {
            key for key, value in arguments.items()
            if value is not None
        }
        if supplied != set(operation.arguments):
            raise BrokerError("ARGUMENT_MISMATCH", "operation arguments do not match the typed contract")

        try:
            if operation_name.startswith("gitea."):
                return self._gitea(
                    project,
                    operation,
                    number=number,
                    state=state,
                    issue=issue,
                    title=title,
                    body=body,
                    comment=comment,
                    sha=sha,
                )
            if operation_name.startswith("git.") or operation_name == "mac.git.bind":
                return self._git(project, operation, branch=branch)
            if operation_name == "host.access.audit":
                return self._access_audit(project, operation)
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
        issue: int | None,
        title: str | None,
        body: str | None,
        comment: str | None,
        sha: str | None,
    ) -> object:
        method = "GET"
        payload: object | None = None
        if operation.name == "gitea.issue.create":
            method = "POST"
            payload = {
                "title": _typed_text("Issue title", title, TITLE_MAX_BYTES),
                "body": _typed_text("Issue body", body, BODY_MAX_BYTES),
            }
        elif operation.name == "gitea.issue.update":
            method = "PATCH"
            _positive_number(number, "Issue")
            payload = {
                "title": _typed_text("Issue title", title, TITLE_MAX_BYTES),
                "body": _typed_text("Issue body", body, BODY_MAX_BYTES),
            }
        elif operation.name == "gitea.issue.comment":
            method = "POST"
            _positive_number(number, "Issue")
            payload = {"body": _typed_text("Issue comment", comment, BODY_MAX_BYTES)}
        elif operation.name == "gitea.pull.create":
            _positive_number(issue, "Issue")
            method = "POST"
            payload = {
                "title": _typed_text("pull request title", title, TITLE_MAX_BYTES),
                "body": _pull_body(issue, body),
            }
        elif operation.name == "gitea.pull.update":
            method = "PATCH"
            _positive_number(number, "pull request")
            _positive_number(issue, "Issue")
            payload = {
                "title": _typed_text("pull request title", title, TITLE_MAX_BYTES),
                "body": _pull_body(issue, body),
            }
        elif operation.name == "gitea.commit.status.read":
            if not isinstance(sha, str) or COMMIT_SHA_RE.fullmatch(sha) is None:
                raise BrokerError("ARGUMENT_INVALID", "commit status requires an exact lowercase SHA-1")
        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential)
        owner = quote(self.contract.governance.owner, safe="")
        repository = quote(project.repository, safe="")
        base = self.contract.governance.base_url
        repo_api = f"{base}/api/v1/repos/{owner}/{repository}"
        if operation.name == "gitea.repo.read":
            url = repo_api
        elif operation.name == "gitea.issue.create":
            url = f"{repo_api}/issues"
        elif operation.name == "gitea.issue.read":
            _positive_number(number, "Issue")
            url = f"{repo_api}/issues/{number}"
        elif operation.name == "gitea.issue.update":
            url = f"{repo_api}/issues/{number}"
        elif operation.name == "gitea.issue.comment":
            url = f"{repo_api}/issues/{number}/comments"
        elif operation.name == "gitea.pulls.read":
            if state not in {"open", "closed", "all"}:
                raise BrokerError("ARGUMENT_INVALID", "pull state must be open, closed, or all")
            url = f"{repo_api}/pulls?state={state}&limit=50&page=1"
        elif operation.name == "gitea.pull.create":
            assert issue is not None
            open_pulls = self._request_json(
                f"{repo_api}/pulls?state=open&limit=50&page=1",
                credential.token,
            )
            if not isinstance(open_pulls, list):
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea pull list is invalid")
            matches = [
                item for item in open_pulls
                if isinstance(item, dict)
                and isinstance(item.get("head"), dict)
                and isinstance(item.get("base"), dict)
                and item["head"].get("ref") == f"change/{issue}"
                and item["base"].get("ref") == self.contract.governance.default_branch
            ]
            if len(matches) > 1:
                raise BrokerError("TARGET_MISMATCH", "multiple open pull requests target the change branch")
            if matches:
                return matches[0]
            pull_body = payload if isinstance(payload, dict) else {}
            payload = {
                **pull_body,
                "head": f"change/{issue}",
                "base": self.contract.governance.default_branch,
            }
            url = f"{repo_api}/pulls"
        elif operation.name == "gitea.pull.read":
            _positive_number(number, "pull request")
            url = f"{repo_api}/pulls/{number}"
        elif operation.name == "gitea.pull.update":
            assert issue is not None and number is not None
            current_pull = self._request_json(
                f"{repo_api}/pulls/{number}", credential.token
            )
            if (
                not isinstance(current_pull, dict)
                or not isinstance(current_pull.get("head"), dict)
                or not isinstance(current_pull.get("base"), dict)
                or current_pull["head"].get("ref") != f"change/{issue}"
                or current_pull["base"].get("ref") != self.contract.governance.default_branch
                or current_pull.get("merged") is True
            ):
                raise BrokerError("TARGET_MISMATCH", "pull request does not match the exact change target")
            url = f"{repo_api}/pulls/{number}"
        elif operation.name == "gitea.protection.read":
            branch = quote(self.contract.governance.default_branch, safe="")
            url = f"{repo_api}/branch_protections/{branch}"
        elif operation.name == "gitea.commit.status.read":
            assert sha is not None
            url = f"{repo_api}/commits/{sha}/status"
        else:
            raise BrokerError("OPERATION_UNIMPLEMENTED", "Gitea operation is not implemented")
        return self._request_json(url, credential.token, method=method, payload=payload)

    def _verify_identity(self, credential: ResolvedCredential) -> None:
        url = f"{self.contract.governance.base_url}/api/v1/user"
        value = self._request_json(url, credential.token)
        if not isinstance(value, dict) or value.get("login") != credential.identity:
            raise BrokerError("IDENTITY_MISMATCH", "credential identity does not match the route")
        if credential.identity != self.contract.governance.human_merge_identity and value.get("is_admin") is True:
            raise BrokerError("IDENTITY_MISMATCH", "automation identity unexpectedly has site-admin permission")

    def _request_json(
        self,
        url: str,
        token: str,
        *,
        method: str = "GET",
        payload: object | None = None,
    ) -> object:
        body_data = None
        headers = {"Accept": "application/json", "Authorization": f"token {token}"}
        if payload is not None:
            body_data = json.dumps(
                payload, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            status, _headers, body = self.transport(
                method, url, headers, body_data
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
        canonical = project.mac_checkout
        if canonical is None:
            raise BrokerError("TARGET_UNAVAILABLE", "project has no approved Mac checkout")
        checkout = canonical if operation.name == "mac.git.bind" else self.invocation_cwd
        if operation.name != "mac.git.bind":
            checkout = self._validated_project_worktree(canonical, checkout)
        expected_remote = (
            f"{self.contract.governance.base_url}/{self.contract.governance.owner}/"
            f"{project.repository}.git"
        )
        remote = self._run(["git", "remote", "get-url", "origin"], cwd=checkout).stdout.strip()
        if remote != expected_remote:
            raise BrokerError("TARGET_MISMATCH", "checkout origin does not match the manifest target")
        if operation.name == "mac.git.bind":
            credential = self.credentials.resolve(project, operation)
            self._verify_identity(credential)
            return self._bind_git(project, checkout, expected_remote)

        safe_branch = None
        if branch is not None:
            safe_branch = self.contract.change_branch(branch)
        if operation.name == "git.push.change":
            assert safe_branch is not None
            current = self._run(["git", "branch", "--show-current"], cwd=checkout).stdout.strip()
            if current != safe_branch:
                raise BrokerError("TARGET_MISMATCH", "worktree branch does not match requested change branch")
            status = self._run(["git", "status", "--porcelain"], cwd=checkout).stdout
            if status:
                raise BrokerError("WORKTREE_DIRTY", "change worktree must be clean before push")
            head = self._run(["git", "rev-parse", "HEAD"], cwd=checkout).stdout.strip()
            branch_head = self._run(
                ["git", "rev-parse", f"refs/heads/{safe_branch}"], cwd=checkout
            ).stdout.strip()
            if head != branch_head:
                raise BrokerError("TARGET_MISMATCH", "worktree HEAD does not match its exact branch")

        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential)

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
            assert safe_branch is not None
            argv = ["git", "fetch", "origin", safe_branch]
        elif operation.name == "git.push.change":
            assert safe_branch is not None
            self._run(["git", "fetch", "origin", "main"], cwd=checkout, env=env)
            ancestor = self.runner(
                ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
                cwd=checkout,
            )
            if ancestor.returncode != 0:
                raise BrokerError("BASE_BRANCH_STALE", "change branch is not based on fetched origin/main")
            merge_commits = self._run(
                ["git", "rev-list", "--min-parents=2", "origin/main..HEAD"],
                cwd=checkout,
            ).stdout.strip()
            if merge_commits:
                raise BrokerError("MERGE_COMMIT_DENIED", "change branch contains a merge commit")
            argv = ["git", "push", "origin", f"refs/heads/{safe_branch}:refs/heads/{safe_branch}"]
        else:
            raise BrokerError("OPERATION_UNIMPLEMENTED", "Git operation is not implemented")
        self._run(argv, cwd=checkout, env=env)
        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "identity": project.project_agent,
            "checkout": checkout,
        }

    def _validated_project_worktree(self, canonical: str, candidate: str) -> str:
        canonical_root = self._run(
            ["git", "rev-parse", "--show-toplevel"], cwd=canonical
        ).stdout.strip()
        candidate_root = self._run(
            ["git", "rev-parse", "--show-toplevel"], cwd=candidate
        ).stdout.strip()

        def common_dir(root: str) -> str:
            raw = self._run(["git", "rev-parse", "--git-common-dir"], cwd=root).stdout.strip()
            return os.path.realpath(raw if os.path.isabs(raw) else os.path.join(root, raw))

        if common_dir(canonical_root) != common_dir(candidate_root):
            raise BrokerError("TARGET_MISMATCH", "current worktree is outside the manifest repository")
        return os.path.realpath(candidate_root)

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

    def _access_audit(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> object:
        operations = {
            "manager_audit": operation,
            "manager_mutation": OperationContract(
                "host.access.audit", "manager-mutation", False, ()
            ),
            "project_agent": OperationContract(
                "host.access.audit", "project-agent", False, ()
            ),
        }
        credentials = {
            route: self.credentials.resolve(project, route_operation)
            for route, route_operation in operations.items()
        }
        for credential in credentials.values():
            self._verify_identity(credential)
        credential_store = self._credential_store_contract(project)

        expected_scopes = {
            "manager_audit": set(
                self.contract.governance.raw["platform_manager"]["audit_token_scopes"]
            ),
            "manager_mutation": set(
                self.contract.governance.raw["platform_manager"]["mutation_token_scopes"]
            ),
            "project_agent": set(
                self.contract.governance.raw["project_agent_policy"]["token_scopes"]
            ),
        }
        token_scopes: dict[str, list[str]] = {}
        for route, credential in credentials.items():
            actual = self._probe_token_scopes(credential)
            if actual != expected_scopes[route]:
                raise BrokerError("TOKEN_SCOPE_MISMATCH", "credential token scopes do not match the manifest")
            token_scopes[route] = sorted(actual)

        owner = quote(self.contract.governance.owner, safe="")
        repository = quote(project.repository, safe="")
        repo_api = f"{self.contract.governance.base_url}/api/v1/repos/{owner}/{repository}"
        manager_token = credentials["manager_audit"].token
        permissions: dict[str, str] = {}
        for key, identity, expected in (
            ("manager", credentials["manager_audit"].identity, "admin"),
            ("project_agent", project.project_agent, "write"),
        ):
            value = self._request_json(
                f"{repo_api}/collaborators/{quote(identity, safe='')}/permission",
                manager_token,
            )
            if not isinstance(value, dict) or value.get("permission") != expected:
                raise BrokerError("PERMISSION_MISMATCH", "repository permission does not match the manifest")
            permissions[key] = expected

        default_branch = quote(self.contract.governance.default_branch, safe="")
        protection = self._request_json(
            f"{repo_api}/branch_protections/{default_branch}", manager_token
        )
        expected_merge = [self.contract.governance.human_merge_identity]
        repository_contract = self.contract.governance.repository(project.repository)
        expected_contexts = sorted(repository_contract.status_check_contexts)
        if (
            not isinstance(protection, dict)
            or protection.get("can_push") is not False
            or protection.get("can_force_push") is not False
            or protection.get("enable_merge_whitelist") is not True
            or protection.get("merge_whitelist_usernames") != expected_merge
            or protection.get("enable_status_check") is not bool(expected_contexts)
            or sorted(protection.get("status_check_contexts", [])) != expected_contexts
            or protection.get("required_approvals") != repository_contract.required_approvals
            or protection.get("block_admin_merge_override") is not True
        ):
            raise BrokerError("PROTECTION_MISMATCH", "protected main does not match the governance boundary")

        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "identities": {
                route: credential.identity for route, credential in credentials.items()
            },
            "token_scopes": token_scopes,
            "repository_permission": permissions,
            "credential_store": credential_store,
            "protection": {
                "branch": self.contract.governance.default_branch,
                "can_push": False,
                "can_force_push": False,
                "merge_whitelist_usernames": expected_merge,
                "enable_status_check": protection["enable_status_check"],
                "status_check_contexts": expected_contexts,
                "required_approvals": repository_contract.required_approvals,
                "block_admin_merge_override": True,
            },
        }

    def _probe_token_scopes(self, credential: ResolvedCredential) -> set[str]:
        url = f"{self.contract.governance.base_url}/api/v1/notifications"
        try:
            status, _headers, raw = self.transport(
                "GET",
                url,
                {
                    "Accept": "application/json",
                    "Authorization": f"token {credential.token}",
                },
                None,
            )
        except Exception as exc:
            raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc
        if status != 403:
            raise BrokerError("TOKEN_SCOPE_MISMATCH", "token scope probe did not fail closed")
        try:
            payload = json.loads(raw.decode("utf-8"))
            message = payload["message"]
        except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "token scope probe response is invalid") from exc
        if not isinstance(message, str):
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "token scope probe response is invalid")
        match = re.search(r"token scope=([A-Za-z0-9:,_-]+)", message)
        if match is None:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "token scope evidence is unavailable")
        scopes = {item for item in match.group(1).split(",") if item}
        if not scopes or "all" in scopes or any(item.startswith("write:admin") for item in scopes):
            raise BrokerError("TOKEN_SCOPE_MISMATCH", "credential token scopes are unsafe")
        return scopes

    def _credential_store_contract(self, project: ProjectContract) -> dict[str, object]:
        manager = self.contract.governance.platform_manager
        return {
            "manager_audit": {
                "identity": manager,
                "kind": "protected-file",
                "scope": "platform-manager-audit",
            },
            "manager_mutation": {
                "identity": manager,
                "kind": "protected-file",
                "scope": "platform-manager-mutation",
            },
            "project_agent": {
                "identity": project.project_agent,
                "kind": "protected-file",
                "scope": f"project:{project.project_id}",
            },
            "directory_mode": self.contract.raw["mac_host"]["credential_directory_mode"],
            "file_mode": self.contract.raw["mac_host"]["credential_file_mode"],
            "path_disclosure": "DENIED",
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
