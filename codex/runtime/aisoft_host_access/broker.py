from __future__ import annotations

import json
import os
import pwd
import re
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from aisoft_change_name import ChangeName, ChangeNameError, SLUG_PATTERN, select_change_name

from .contract import AccessContract, AccessContractError, OperationContract, ProjectContract


TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CREDENTIAL_SCALAR_FIELDS = frozenset({"protocol", "host", "path", "username"})
CREDENTIAL_REQUIRED_FIELDS = frozenset({"protocol", "host", "path"})
CREDENTIAL_PROTOCOL_MAX_LINE_BYTES = 65535
TITLE_MAX_BYTES = 255
BODY_MAX_BYTES = 65536
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
# Same ceiling verifier.py already uses for captured command output (#143): one
# number for "how much text may enter an agent's context", not two.
LOG_MAX_BYTES = 65536
# Second-layer log redaction (#143 spec §5.2). Gitea masks its own registered
# Actions secrets; these cover the credential a workflow got from somewhere
# else, which is the shape an accidental leak actually takes.
#
# Bare 40-hex strings are deliberately absent: they are indistinguishable from
# commit SHAs, and SHAs are among the most useful things in a CI log. Masking
# them would trade a certain loss of function for a hypothetical gain — the
# credential in use is already covered exactly, by value, below.
REDACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)\b(authorization\s*:\s*(?:token|bearer|basic)\s+)\S+"
    ),
    re.compile(r"(?i)\b((?:https?|git|ssh)://)[^\s/@]+(?::[^\s/@]*)?(@)"),
    re.compile(
        r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|APIKEY|API_KEY"
        r"|PRIVATE_KEY|CREDENTIAL)[A-Z0-9_]*\s*[:=]\s*)(?!\s)\S+"
    ),
    re.compile(r"\b(gh[pousr]_)[A-Za-z0-9]{16,}"),
    re.compile(r"\b(github_pat_)[A-Za-z0-9_]{20,}"),
    re.compile(
        r"(-----BEGIN [A-Z ]*PRIVATE KEY-----)[\s\S]*?"
        r"(-----END [A-Z ]*PRIVATE KEY-----)"
    ),
)
REDACTED = "[redacted]"
LEASE_REJECTION_MARKERS = ("stale info", "non-fast-forward", "fetch first")
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


def _label_fields(label: Mapping[str, object]) -> tuple[str, str, str]:
    """Comparable form of a label.

    Gitea accepts colors with or without a leading '#' and in either case, so a
    raw comparison would report cosmetic differences as drift and rewrite the
    same label on every provision run.
    """
    name = label.get("name")
    color = label.get("color")
    description = label.get("description")
    return (
        name if isinstance(name, str) else "",
        color.lstrip("#").lower() if isinstance(color, str) else "",
        description.strip() if isinstance(description, str) else "",
    )


def _pull_body(
    issue: int | None,
    value: str | None,
    *,
    allow_legacy: bool = False,
) -> tuple[str, ChangeName]:
    number = _positive_number(issue, "Issue")
    body = _typed_text("pull request body", value, BODY_MAX_BYTES)
    closes = re.findall(r"(?m)^Closes #([1-9][0-9]*)[ \t]*$", body)
    if closes != [str(number)]:
        raise BrokerError(
            "ARGUMENT_INVALID",
            "pull request body must contain exactly one line: Closes #N",
        )
    summary = re.compile(
        rf"(?<![A-Za-z0-9_./-])docs/changes/"
        rf"({number}-({SLUG_PATTERN}))/summary-({SLUG_PATTERN})-[0-9]{{6}}\.md"
        rf"(?![A-Za-z0-9_./-])"
    )
    matches = summary.findall(body)
    if len(matches) == 1 and matches[0][1] == matches[0][2]:
        try:
            change_name = ChangeName.parse_directory(
                matches[0][0], issue_number=number, allow_legacy=False
            )
        except ChangeNameError as exc:
            raise BrokerError("ARGUMENT_INVALID", str(exc)) from exc
        return body, change_name
    if allow_legacy:
        legacy = re.compile(
            rf"(?<![A-Za-z0-9_./-])docs/changes/{number}/(?:00-summary\.md|"
            rf"summary-{SLUG_PATTERN}-[0-9]{{6}}\.md)(?![A-Za-z0-9_./-])"
        )
        if len(legacy.findall(body)) == 1:
            return body, ChangeName(number)
    raise BrokerError("ARGUMENT_INVALID", "pull request body must link its semantic summary")


def _optional_text(value: object) -> str | None:
    """Keep a string field or drop it — never coerce an unexpected type."""
    return value if isinstance(value, str) and value else None


def _duration_seconds(started: object, completed: object) -> int | None:
    """Seconds between two Gitea timestamps, or None when either is unusable.

    None rather than 0: a step that has not finished and a step that took no
    measurable time are different facts, and "0s" for the first one would
    reproduce exactly the kind of number #143 was opened because nobody could
    check.
    """
    if not isinstance(started, str) or not isinstance(completed, str):
        return None
    try:
        start = datetime.fromisoformat(started)
        end = datetime.fromisoformat(completed)
    except ValueError:
        return None
    if end < start:
        return None
    return int((end - start).total_seconds())


def _redact_secrets(text: str, token: str) -> tuple[str, int]:
    """Mask credentials in a job log, reporting how many masks were applied.

    The count is returned rather than swallowed for the same reason truncation
    is announced: a reader who is not told something was removed will assume
    they are looking at the original.
    """
    redactions = 0
    # The exact credential this request used is the strongest rule available:
    # the broker holds its plaintext, so any occurrence in a log is a leak by
    # definition, whatever shape it takes.
    if token:
        occurrences = text.count(token)
        if occurrences:
            text = text.replace(token, REDACTED)
            redactions += occurrences
    for pattern in REDACTION_PATTERNS:
        def _replace(match: re.Match[str]) -> str:
            groups = [group for group in match.groups() if group]
            if len(groups) >= 2:
                return f"{groups[0]}{REDACTED}{groups[-1]}"
            prefix = groups[0] if groups else ""
            return f"{prefix}{REDACTED}"

        text, count = pattern.subn(_replace, text)
        redactions += count
    return text, redactions


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
        label_manifest_path: str | None = None,
    ) -> None:
        self.contract = contract
        self.credentials = credentials or CredentialResolver(contract)
        self.transport = transport
        self.runner = runner
        self.invocation_cwd = os.path.realpath(invocation_cwd or os.getcwd())
        # Fixed install-time configuration, never caller input: the broker's
        # contract is that no path ever crosses its argument surface.
        self.label_manifest_path = label_manifest_path

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
        job: int | None = None,
        lifecycle: str | None = None,
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
            "job": job,
            "lifecycle": lifecycle,
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
                    job=job,
                    lifecycle=lifecycle,
                )
            if operation_name.startswith("git.") or operation_name == "mac.git.bind":
                return self._git(project, operation, branch=branch)
            if operation_name == "host.access.audit":
                return self._access_audit(project, operation)
            if operation_name == "host.onboarding.check":
                return self._onboarding_check(project, operation)
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
        job: int | None,
        lifecycle: str | None,
    ) -> object:
        method = "GET"
        payload: object | None = None
        pull_change: ChangeName | None = None
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
            pull_body, pull_change = _pull_body(issue, body)
            payload = {
                "title": _typed_text("pull request title", title, TITLE_MAX_BYTES),
                "body": pull_body,
            }
        elif operation.name == "gitea.pull.update":
            method = "PATCH"
            _positive_number(number, "pull request")
            _positive_number(issue, "Issue")
            pull_body, pull_change = _pull_body(issue, body, allow_legacy=True)
            payload = {
                "title": _typed_text("pull request title", title, TITLE_MAX_BYTES),
                "body": pull_body,
            }
        elif operation.name == "gitea.commit.status.read":
            if not isinstance(sha, str) or COMMIT_SHA_RE.fullmatch(sha) is None:
                raise BrokerError("ARGUMENT_INVALID", "commit status requires an exact lowercase SHA-1")
        elif operation.name == "gitea.actions.run.read":
            # Exact SHA only, the same rule gitea.commit.status.read already
            # applies. Rejecting before any request is made is what keeps "this
            # commit has no runs" and "you passed the wrong SHA" apart: an
            # abbreviated SHA sent upstream would come back as an empty list,
            # i.e. a success shaped exactly like the first answer.
            if not isinstance(sha, str) or COMMIT_SHA_RE.fullmatch(sha) is None:
                raise BrokerError(
                    "ARGUMENT_INVALID", "Actions run read requires an exact lowercase SHA-1"
                )
        elif operation.name == "gitea.actions.job.logs.read":
            _positive_number(job, "Actions job")
        elif operation.name == "gitea.issue.comments.read":
            _positive_number(number, "Issue")
        elif operation.name == "gitea.issue.labels.read":
            _positive_number(number, "Issue")
        elif operation.name == "gitea.issue.labels.set":
            _positive_number(number, "Issue")
            # Checked against the installed manifest rather than a literal tuple
            # or argparse choices: a literal would be another copy of the eight
            # names (#115 AC-7) and would keep accepting a state this install's
            # manifest no longer declares. Local file read, so an out-of-range
            # value costs no credential and no request.
            if lifecycle not in self._lifecycle_labels():
                raise BrokerError(
                    "ARGUMENT_MISMATCH",
                    "lifecycle must be one of the delivery states the label manifest declares",
                )
        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential)
        owner = quote(self.contract.governance.owner, safe="")
        repository = quote(project.repository, safe="")
        base = self.contract.governance.base_url
        repo_api = f"{base}/api/v1/repos/{owner}/{repository}"
        if operation.name == "gitea.labels.read":
            return self._labels(repo_api, credential.token)
        if operation.name == "gitea.labels.provision":
            return self._provision_labels(repo_api, credential.token)
        if operation.name == "gitea.actions.run.read":
            assert sha is not None
            return self._actions_runs(repo_api, credential.token, sha)
        if operation.name == "gitea.actions.job.logs.read":
            assert job is not None
            return self._actions_job_logs(repo_api, credential.token, job)
        if operation.name == "gitea.issue.comments.read":
            assert number is not None
            return self._issue_comments(repo_api, credential.token, number)
        if operation.name == "gitea.issue.labels.read":
            assert number is not None
            return self._issue_labels(repo_api, credential.token, number)
        if operation.name == "gitea.issue.labels.set":
            assert number is not None and lifecycle is not None
            return self._set_issue_lifecycle(
                repo_api, credential.token, number, lifecycle
            )
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
            assert issue is not None and pull_change is not None
            open_pulls = self._open_pulls(repo_api, credential.token)
            same_issue: list[tuple[ChangeName, dict[str, object]]] = []
            for item in open_pulls:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("head"), dict)
                    or not isinstance(item.get("base"), dict)
                    or item["base"].get("ref") != self.contract.governance.default_branch
                ):
                    continue
                try:
                    candidate = ChangeName.parse_branch(str(item["head"].get("ref")))
                except ChangeNameError:
                    continue
                if candidate.issue_number == issue:
                    same_issue.append((candidate, item))
            try:
                selected = select_change_name(
                    issue, (candidate for candidate, _ in same_issue), required=False
                )
            except ChangeNameError as exc:
                raise BrokerError("CHANGE_NAME_CONFLICT", str(exc)) from exc
            if selected is not None and selected != pull_change:
                raise BrokerError(
                    "CHANGE_NAME_CONFLICT",
                    "an open pull request already uses another name for this Issue",
                )
            matches = [item for candidate, item in same_issue if candidate == pull_change]
            if len(matches) > 1:
                raise BrokerError("TARGET_MISMATCH", "multiple open pull requests target the change branch")
            if matches:
                return matches[0]
            pull_body = payload if isinstance(payload, dict) else {}
            payload = {
                **pull_body,
                "head": pull_change.branch,
                "base": self.contract.governance.default_branch,
            }
            url = f"{repo_api}/pulls"
        elif operation.name == "gitea.pull.read":
            _positive_number(number, "pull request")
            url = f"{repo_api}/pulls/{number}"
        elif operation.name == "gitea.pull.update":
            assert issue is not None and number is not None and pull_change is not None
            current_pull = self._request_json(
                f"{repo_api}/pulls/{number}", credential.token
            )
            if (
                not isinstance(current_pull, dict)
                or not isinstance(current_pull.get("head"), dict)
                or not isinstance(current_pull.get("base"), dict)
                or current_pull["head"].get("ref") != pull_change.branch
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

    def _labels(self, repo_api: str, token: str) -> list[dict[str, object]]:
        labels: list[dict[str, object]] = []
        for page in range(1, 21):
            value = self._request_json(
                f"{repo_api}/labels?limit=50&page={page}", token
            )
            if not isinstance(value, list):
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea label list is invalid")
            for item in value:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("name"), str)
                    or not isinstance(item.get("color"), str)
                    or not isinstance(item.get("description"), str)
                ):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID", "Gitea label entry is invalid"
                    )
                labels.append(item)
            if len(value) < 50:
                return labels
        raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea label list exceeds the bounded scan")

    def _provision_labels(self, repo_api: str, token: str) -> dict[str, object]:
        manifest = self._label_manifest()
        remote = {item["name"]: item for item in self._labels(repo_api, token)}

        created = 0
        updated = 0
        unchanged = 0
        for label in manifest["canonical"]:
            name = label["name"]
            current = remote.get(name)
            if current is None:
                self._request_json(
                    f"{repo_api}/labels", token, method="POST", payload=label
                )
                created += 1
                continue
            if _label_fields(current) == _label_fields(label):
                unchanged += 1
                continue
            label_id = current.get("id")
            if not isinstance(label_id, int) or isinstance(label_id, bool):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea label is missing a usable id"
                )
            self._request_json(
                f"{repo_api}/labels/{label_id}", token, method="PATCH", payload=label
            )
            updated += 1

        # Retired values are reported, never removed. There is no delete
        # operation in the typed surface at all, so a retired label cannot
        # disappear without a human acting on the Issues that still carry it.
        retired_present = sorted(
            entry["name"] for entry in manifest["retired"] if entry["name"] in remote
        )
        return {
            "operation": "gitea.labels.provision",
            "created": created,
            "updated": updated,
            "unchanged": unchanged,
            "retired_present": retired_present,
            "status": "PASS",
        }

    def _lifecycle_labels(self) -> set[str]:
        """The delivery lifecycle dimension, derived from the installed manifest.

        Same rule as aisoft_label_manifest_lifecycle and
        aisoft_loop.contract.LIFECYCLE_LABELS: a canonical name carrying no
        namespace prefix is a delivery state, because every other dimension
        (type/, complexity/, triage/, and whatever project_extensions declares)
        is namespaced. Derived here too rather than imported, because the broker
        must stay runnable from its own install-time manifest alone and never
        depend on aisoft_loop.
        """
        return {
            entry["name"]
            for entry in self._label_manifest()["canonical"]
            if "/" not in entry["name"]
        }

    def _actions_runs(
        self, repo_api: str, token: str, sha: str
    ) -> dict[str, object]:
        """Project one commit's Actions runs down to step-level conclusions.

        Projected rather than passed through: an upstream ActionWorkflowRun
        embeds a full Repository plus two User objects, so returning it verbatim
        would make a governed read surface change shape whenever Gitea's does,
        and would disclose identities this operation has no reason to carry.

        duration_seconds is computed here rather than left to the caller. "How
        long did each step take" is the question #143 was opened to answer;
        handing back two timestamps and expecting the reader to subtract them
        would be doing half the job.
        """
        runs: list[dict[str, object]] = []
        for item in self._paged(
            f"{repo_api}/actions/runs?head_sha={quote(sha, safe='')}",
            token,
            "workflow_runs",
        ):
            run_id = item.get("id")
            if not isinstance(run_id, int) or isinstance(run_id, bool):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Actions run entry is invalid"
                )
            runs.append(
                {
                    "id": run_id,
                    "workflow": _optional_text(item.get("path")),
                    "display_title": _optional_text(item.get("display_title")),
                    "event": _optional_text(item.get("event")),
                    "head_branch": _optional_text(item.get("head_branch")),
                    "head_sha": _optional_text(item.get("head_sha")),
                    "run_number": item.get("run_number")
                    if isinstance(item.get("run_number"), int)
                    and not isinstance(item.get("run_number"), bool)
                    else None,
                    "status": _optional_text(item.get("status")),
                    "conclusion": _optional_text(item.get("conclusion")),
                    "started_at": _optional_text(item.get("started_at")),
                    "completed_at": _optional_text(item.get("completed_at")),
                    "duration_seconds": _duration_seconds(
                        item.get("started_at"), item.get("completed_at")
                    ),
                    "html_url": _optional_text(item.get("html_url")),
                    "jobs": self._actions_jobs(repo_api, token, run_id),
                }
            )
        # A well-formed SHA with no runs is an empty list, not an error: the
        # caller can tell "nothing ran" from "the read failed" by shape alone,
        # because a failure never reaches here — it raises BrokerError.
        return {"sha": sha, "total_count": len(runs), "runs": runs}

    def _actions_jobs(
        self, repo_api: str, token: str, run_id: int
    ) -> list[dict[str, object]]:
        jobs: list[dict[str, object]] = []
        for item in self._paged(
            f"{repo_api}/actions/runs/{run_id}/jobs", token, "jobs"
        ):
            job_id = item.get("id")
            if not isinstance(job_id, int) or isinstance(job_id, bool):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Actions job entry is invalid"
                )
            raw_steps = item.get("steps")
            if raw_steps is not None and not isinstance(raw_steps, list):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Actions job steps are invalid"
                )
            steps: list[dict[str, object]] = []
            for step in raw_steps or []:
                if not isinstance(step, dict):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID", "Gitea Actions step entry is invalid"
                    )
                steps.append(
                    {
                        "number": step.get("number")
                        if isinstance(step.get("number"), int)
                        and not isinstance(step.get("number"), bool)
                        else None,
                        "name": _optional_text(step.get("name")),
                        "status": _optional_text(step.get("status")),
                        "conclusion": _optional_text(step.get("conclusion")),
                        "started_at": _optional_text(step.get("started_at")),
                        "completed_at": _optional_text(step.get("completed_at")),
                        "duration_seconds": _duration_seconds(
                            step.get("started_at"), step.get("completed_at")
                        ),
                    }
                )
            jobs.append(
                {
                    "id": job_id,
                    "name": _optional_text(item.get("name")),
                    "status": _optional_text(item.get("status")),
                    "conclusion": _optional_text(item.get("conclusion")),
                    "started_at": _optional_text(item.get("started_at")),
                    "completed_at": _optional_text(item.get("completed_at")),
                    "duration_seconds": _duration_seconds(
                        item.get("started_at"), item.get("completed_at")
                    ),
                    "runner_name": _optional_text(item.get("runner_name")),
                    "steps": steps,
                }
            )
        return jobs

    def _paged(
        self, url: str, token: str, key: str
    ) -> list[Mapping[str, object]]:
        """Bounded paging over one of Gitea's {total_count, <key>: []} envelopes.

        Bounded like _open_pulls and _issue_comments: reading only the first page
        would make a truncated run list look complete, and a truncated list of
        steps is exactly the false reassurance this operation exists to remove.
        """
        separator = "&" if "?" in url else "?"
        collected: list[Mapping[str, object]] = []
        for page in range(1, 101):
            value = self._request_json(
                f"{url}{separator}limit=50&page={page}", token
            )
            if not isinstance(value, dict):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Actions response is invalid"
                )
            entries = value.get(key)
            if entries is None:
                return collected
            if not isinstance(entries, list):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Actions response is invalid"
                )
            for entry in entries:
                if not isinstance(entry, dict):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID", "Gitea Actions entry is invalid"
                    )
                collected.append(entry)
            if len(entries) < 50:
                return collected
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "Gitea Actions response exceeds the bounded scan"
        )

    def _actions_job_logs(
        self, repo_api: str, token: str, job: int
    ) -> dict[str, object]:
        """Read one job's log, redacted then bounded — in that order.

        Redaction runs before truncation on purpose: truncating first would drop
        whatever credentials sat in the discarded half without ever counting
        them, and the returned redaction count is the reader's only signal that
        anything was masked at all.

        Gitea masks its own registered Actions secrets upstream. This second
        layer covers what that one structurally cannot: a credential the workflow
        obtained from somewhere other than a registered secret — which is the
        common shape of an accidental leak, since forgetting to register it as a
        secret is precisely how it ends up printed.
        """
        text = self._request_text(f"{repo_api}/actions/jobs/{job}/logs", token)
        text, redactions = _redact_secrets(text, token)
        original_bytes = len(text.encode("utf-8"))
        body = text
        truncated = original_bytes > LOG_MAX_BYTES
        if truncated:
            # Tail, not head: a failing step prints its error last, so keeping
            # the beginning would reliably discard the part worth reading.
            body = text.encode("utf-8")[-LOG_MAX_BYTES:].decode("utf-8", "ignore")
            body = (
                f"[truncated: {original_bytes - len(body.encode('utf-8'))}"
                " leading bytes omitted]\n" + body
            )
        return {
            "job": job,
            "truncated": truncated,
            "original_bytes": original_bytes,
            "returned_bytes": len(body.encode("utf-8")),
            "redactions": redactions,
            "log": body,
        }

    def _request_text(self, url: str, token: str) -> str:
        headers = {"Accept": "text/plain", "Authorization": f"token {token}"}
        try:
            status, _headers, body = self.transport("GET", url, headers, None)
        except BrokerError:
            raise
        except Exception as exc:  # defensive adapter boundary
            raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc
        if status in {401, 403, 404}:
            raise BrokerError(f"HTTP_{status}", f"Gitea returned HTTP {status}")
        if status < 200 or status >= 300:
            raise BrokerError("HTTP_ERROR", f"Gitea returned HTTP {status}")
        return body.decode("utf-8", "replace")

    def _issue_comments(
        self, repo_api: str, token: str, number: int
    ) -> list[dict[str, object]]:
        """Read one Issue's comments as a bounded, projected list.

        Projected rather than passed through: a raw Gitea comment embeds a full
        user object, reactions and assets, so returning it verbatim would make a
        governed read surface change shape whenever Gitea's does. The four
        fields kept are the ones the delivery contract actually reads — who said
        what, when, and where to look it up.

        Paged like _open_pulls: comment count has no upper bound, and a silent
        first-page-only read would make a partial discussion look complete.
        """
        comments: list[dict[str, object]] = []
        for page in range(1, 101):
            value = self._request_json(
                f"{repo_api}/issues/{number}/comments?limit=50&page={page}", token
            )
            if not isinstance(value, list):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Issue comment list is invalid"
                )
            for item in value:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("id"), int)
                    or isinstance(item.get("id"), bool)
                    or not isinstance(item.get("body"), str)
                    or not isinstance(item.get("created_at"), str)
                    or not isinstance(item.get("user"), dict)
                    or not isinstance(item["user"].get("login"), str)
                ):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID", "Gitea Issue comment entry is invalid"
                    )
                comments.append(
                    {
                        "id": item["id"],
                        "author": item["user"]["login"],
                        "created_at": item["created_at"],
                        "body": item["body"],
                    }
                )
            if len(value) < 50:
                return comments
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "Gitea Issue comment list exceeds the bounded scan"
        )

    def _issue_labels(
        self, repo_api: str, token: str, number: int
    ) -> list[dict[str, object]]:
        value = self._request_json(f"{repo_api}/issues/{number}/labels", token)
        if not isinstance(value, list):
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea Issue label list is invalid")
        for item in value:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("name"), str)
                or not isinstance(item.get("id"), int)
                or isinstance(item.get("id"), bool)
            ):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea Issue label entry is invalid"
                )
        return value

    def _set_issue_lifecycle(
        self, repo_api: str, token: str, number: int, lifecycle: str
    ) -> dict[str, object]:
        """Replace the Issue's lifecycle dimension, leaving every other label.

        Attaching is not defining: when the target label has no definition in
        the repository this fails closed and names gitea.labels.provision (#108)
        instead of creating it, so the two operation surfaces stay separate.
        """
        states = self._lifecycle_labels()
        defined = {item["name"]: item for item in self._labels(repo_api, token)}
        target = defined.get(lifecycle)
        if target is None:
            raise BrokerError(
                "TARGET_MISMATCH",
                f"the {lifecycle} label is not defined in this repository; "
                "define it with gitea.labels.provision before attaching it",
            )
        target_id = target.get("id")
        if not isinstance(target_id, int) or isinstance(target_id, bool):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID", "Gitea label is missing a usable id"
            )

        current = self._issue_labels(repo_api, token, number)
        before = sorted(str(item["name"]) for item in current)
        attached_states = {str(item["name"]) for item in current if item["name"] in states}

        # completed and deployed are the two terminal states and deployed is the
        # stronger one. Demoting a shipped change back to completed is a claim
        # about what actually happened to it, so it stays a human decision and
        # is not reachable through the tool that walks merged Issues.
        if lifecycle == "completed" and "deployed" in attached_states:
            raise BrokerError(
                "REQUEST_DENIED",
                "Issue is already deployed; downgrading it to completed is a human decision",
            )

        # Already exactly right: no PUT at all, so a repeated run cannot churn
        # the Issue's label history or its notification stream. The comparison
        # is against the whole lifecycle dimension, not just membership — an
        # Issue carrying two lifecycle labels still needs the write that leaves
        # it holding one.
        if attached_states == {lifecycle}:
            return {
                "issue": number,
                "before": before,
                "after": before,
                "result": "no-op",
                "status": "PASS",
            }

        # Everything outside the lifecycle dimension is carried across by id.
        # This is a replacement of one dimension, not an assignment of a label
        # set: there is no way to ask this operation to drop type/, complexity/,
        # triage/ or a project extension label.
        final = sorted(
            {int(item["id"]) for item in current if item["name"] not in states}
            | {target_id}
        )
        self._request_json(
            f"{repo_api}/issues/{number}/labels",
            token,
            method="PUT",
            payload={"labels": final},
        )
        by_id = {int(item["id"]): str(item["name"]) for item in current}
        by_id[target_id] = lifecycle
        return {
            "issue": number,
            "before": before,
            "after": sorted(by_id[value] for value in final),
            "result": "updated",
            "status": "PASS",
        }

    def _label_manifest(self) -> dict[str, list[dict[str, str]]]:
        path = self.label_manifest_path
        if not path:
            raise BrokerError(
                "REQUEST_DENIED", "label manifest is not configured for this broker install"
            )
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise BrokerError("REQUEST_DENIED", "cannot read the label manifest") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != 2:
            raise BrokerError(
                "REQUEST_DENIED", "label manifest must be a schema_version 2 object"
            )
        canonical = raw.get("canonical")
        retired = raw.get("retired")
        if not isinstance(canonical, list) or not canonical or not isinstance(retired, list):
            raise BrokerError("REQUEST_DENIED", "label manifest structure is invalid")
        for entry in canonical:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("name"), str)
                or not entry["name"]
                or not isinstance(entry.get("color"), str)
                or not re.fullmatch(r"[0-9a-fA-F]{6}", entry["color"])
                or not isinstance(entry.get("description"), str)
                or not entry["description"]
            ):
                raise BrokerError("REQUEST_DENIED", "label manifest entry is invalid")
        for entry in retired:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                raise BrokerError("REQUEST_DENIED", "retired label entry is invalid")
        return {
            "canonical": [
                {
                    "name": entry["name"],
                    "color": entry["color"],
                    "description": entry["description"],
                }
                for entry in canonical
            ],
            "retired": [{"name": entry["name"]} for entry in retired],
        }

    def _open_pulls(self, repo_api: str, token: str) -> list[object]:
        pulls: list[object] = []
        for page in range(1, 101):
            value = self._request_json(
                f"{repo_api}/pulls?state=open&limit=50&page={page}", token
            )
            if not isinstance(value, list):
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea pull list is invalid")
            pulls.extend(value)
            if len(value) < 50:
                return pulls
        raise BrokerError("RESPONSE_SCHEMA_INVALID", "Gitea pull list exceeds the bounded scan")

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
        remote_name, expected_remote = self._validated_remote(project, checkout)
        if operation.name == "mac.git.bind":
            credential = self.credentials.resolve(project, operation)
            self._verify_identity(credential)
            return self._bind_git(project, checkout, expected_remote)

        safe_branch = None
        change_name: ChangeName | None = None
        if branch is not None:
            safe_branch = self.contract.change_branch(branch)
            change_name = ChangeName.parse_branch(safe_branch)
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
        main_refspec = f"refs/heads/main:refs/remotes/{remote_name}/main"
        if operation.name == "git.fetch.main":
            argv = ["git", "fetch", remote_name, main_refspec]
        elif operation.name == "git.fetch.change":
            assert safe_branch is not None
            change_refspec = (
                f"refs/heads/{safe_branch}:refs/remotes/{remote_name}/{safe_branch}"
            )
            argv = ["git", "fetch", remote_name, change_refspec]
        elif operation.name == "git.push.change":
            assert safe_branch is not None and change_name is not None
            self._run(
                ["git", "fetch", remote_name, main_refspec], cwd=checkout, env=env
            )
            remote_heads = self._remote_change_heads(
                remote_name, change_name.issue_number, checkout, env
            )
            try:
                selected = select_change_name(
                    change_name.issue_number,
                    [name for name, _sha in remote_heads],
                    required=False,
                )
            except ChangeNameError as exc:
                raise BrokerError("CHANGE_NAME_CONFLICT", str(exc)) from exc
            if selected is not None and selected != change_name:
                raise BrokerError(
                    "CHANGE_NAME_CONFLICT",
                    "remote already uses another change name for this Issue",
                )
            if change_name.is_legacy and selected is None:
                raise BrokerError(
                    "LEGACY_BRANCH_MISSING",
                    "legacy change branches may be maintained only when remote evidence exists",
                )
            remote_main = f"refs/remotes/{remote_name}/main"
            ancestor = self.runner(
                ["git", "merge-base", "--is-ancestor", remote_main, "HEAD"],
                cwd=checkout,
            )
            if ancestor.returncode != 0:
                raise BrokerError(
                    "BASE_BRANCH_STALE",
                    "change branch is not based on the freshly fetched manifest main",
                )
            merge_commits = self._run(
                ["git", "rev-list", "--min-parents=2", f"{remote_main}..HEAD"],
                cwd=checkout,
            ).stdout.strip()
            if merge_commits:
                raise BrokerError("MERGE_COMMIT_DENIED", "change branch contains a merge commit")
            # A rebase onto a freshly advanced main rewrites the change branch, so an
            # already pushed branch can only move forward with force. The lease is the
            # exact ref this push targets, read from the ls-remote above: an empty
            # expectation asserts the branch is still absent, a sha asserts nobody else
            # moved it. Both refuse rather than overwrite when the assertion is stale.
            remote_sha = next(
                (sha for name, sha in remote_heads if name.branch == safe_branch), ""
            )
            argv = [
                "git", "push",
                f"--force-with-lease=refs/heads/{safe_branch}:{remote_sha}",
                remote_name,
                f"refs/heads/{safe_branch}:refs/heads/{safe_branch}",
            ]
        else:
            raise BrokerError("OPERATION_UNIMPLEMENTED", "Git operation is not implemented")
        if operation.name == "git.push.change":
            self._push_leased(argv, checkout, env)
        else:
            self._run(argv, cwd=checkout, env=env)
        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "identity": project.project_agent,
            "checkout": checkout,
            "remote_name": remote_name,
        }

    def _push_leased(
        self, argv: Sequence[str], checkout: str, env: Mapping[str, str]
    ) -> None:
        result = self._run(argv, cwd=checkout, env=env, allow_failure=True)
        if result.returncode == 0:
            return
        report = f"{result.stdout or ''}\n{result.stderr or ''}"
        if any(marker in report for marker in LEASE_REJECTION_MARKERS):
            raise BrokerError(
                "REMOTE_BRANCH_MOVED",
                "remote change branch moved after its lease was read; fetch and re-run",
            )
        raise BrokerError("HOST_COMMAND_FAILED", "structured host operation failed")

    def _remote_change_heads(
        self,
        remote_name: str,
        issue_number: int,
        checkout: str,
        env: Mapping[str, str],
    ) -> list[tuple[ChangeName, str]]:
        result = self.runner(
            [
                "git",
                "ls-remote",
                "--heads",
                remote_name,
                f"refs/heads/change/{issue_number}",
                f"refs/heads/change/{issue_number}-*",
            ],
            cwd=checkout,
            env=env,
        )
        if result.returncode != 0:
            raise BrokerError("TRANSPORT_ERROR", "cannot enumerate remote change names")
        heads: list[tuple[ChangeName, str]] = []
        for line in result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) != 2 or not fields[1].startswith("refs/heads/"):
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "Git remote returned an invalid ref")
            if COMMIT_SHA_RE.fullmatch(fields[0]) is None:
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Git remote returned an invalid object id"
                )
            try:
                name = ChangeName.parse_branch(fields[1].removeprefix("refs/heads/"))
            except ChangeNameError as exc:
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "Git remote returned an invalid change ref") from exc
            if name.issue_number == issue_number:
                heads.append((name, fields[0]))
        return heads

    def _expected_git_url(self, project: ProjectContract) -> str:
        return (
            f"{self.contract.governance.base_url}/{self.contract.governance.owner}/"
            f"{project.repository}.git"
        )

    def _validated_remote(self, project: ProjectContract, checkout: str) -> tuple[str, str]:
        remote_name = project.git_remote_name
        expected_remote = self._expected_git_url(project)
        try:
            fetch = self._run(
                ["git", "remote", "get-url", "--all", remote_name], cwd=checkout
            ).stdout.splitlines()
            push = self._run(
                ["git", "remote", "get-url", "--push", "--all", remote_name],
                cwd=checkout,
            ).stdout.splitlines()
        except BrokerError as exc:
            raise BrokerError(
                "TARGET_MISMATCH", "manifest Git remote is unavailable"
            ) from exc
        if fetch != [expected_remote] or push != [expected_remote]:
            raise BrokerError(
                "TARGET_MISMATCH", "manifest Git remote URLs do not match the target"
            )
        return remote_name, expected_remote

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

    def _bind_git(self, project: ProjectContract, checkout: str, remote_url: str) -> object:
        helper = self.contract.raw["mac_host"]["credential_helper"]
        url_key = f"credential.{remote_url}"
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

    def _onboarding_check(
        self,
        project: ProjectContract,
        operation: OperationContract,
    ) -> object:
        access_operation = self.contract.operation("host.access.audit")
        access = self._access_audit(project, access_operation)
        if project.mac_checkout is None:
            raise BrokerError("ONBOARDING_MISMATCH", "canonical checkout is not configured")
        checkout = os.path.realpath(project.mac_checkout)
        try:
            root = os.path.realpath(
                self._run(["git", "rev-parse", "--show-toplevel"], cwd=checkout)
                .stdout.strip()
            )
        except BrokerError as exc:
            raise BrokerError(
                "ONBOARDING_MISMATCH", "canonical checkout is unavailable"
            ) from exc
        if root != checkout:
            raise BrokerError(
                "ONBOARDING_MISMATCH", "canonical checkout does not match the manifest"
            )
        try:
            remote_name, remote_url = self._validated_remote(project, checkout)
        except BrokerError as exc:
            raise BrokerError(
                "ONBOARDING_MISMATCH", "canonical Git remote does not match the manifest"
            ) from exc

        helper = self.contract.raw["mac_host"]["credential_helper"]
        url_key = f"credential.{remote_url}"
        expected_scalars = {
            "credential.useHttpPath": "true",
            f"{url_key}.username": project.project_agent,
        }
        for key, expected in expected_scalars.items():
            result = self.runner(["git", "config", "--local", "--get", key], cwd=checkout)
            if result.returncode != 0 or result.stdout.strip() != expected:
                raise BrokerError(
                    "ONBOARDING_MISMATCH", "repo-local credential binding does not match"
                )
        helper_result = self.runner(
            ["git", "config", "--local", "--get-all", f"{url_key}.helper"],
            cwd=checkout,
        )
        if (
            helper_result.returncode != 0
            or helper_result.stdout.splitlines() != ["", helper]
        ):
            raise BrokerError(
                "ONBOARDING_MISMATCH", "repo-local credential helper binding does not match"
            )

        return {
            "status": "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "access": access,
            "checkout": {
                "remote_name": remote_name,
                "remote_url": remote_url,
                "binding": "PASS",
            },
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
            or protection.get("enable_push") is not False
            or protection.get("enable_force_push") is not False
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
        # The profile tool is installed by codex/install-host-access-broker.sh, which must
        # run on the VM as well as the Mac host. Probe it first so a missing installation is
        # reported as itself instead of collapsing into an opaque HOST_COMMAND_FAILED. The
        # probe is a fixed exit-code test, never a parse of the underlying stderr text.
        probe = self._run([
            mac["orbstack_binary"], "-m", mac["orbstack_machine"],
            "-u", mac["orbstack_user"], "/usr/bin/test", "-x", mac["vm_profile_tool"],
        ], allow_failure=True)
        if probe.returncode != 0:
            raise BrokerError(
                "VM_TOOL_UNAVAILABLE",
                "VM profile tool is not installed; run codex/install-host-access-broker.sh on the VM",
            )
        result = self._run([
            mac["orbstack_binary"], "-m", mac["orbstack_machine"],
            "-u", mac["orbstack_user"], "/usr/bin/sudo", "-n", mac["vm_profile_tool"],
            "--project", project.project_id, "--action", action,
        ], allow_failure=True)
        if result.returncode != 0:
            # The profile tool reports its own governed error contract on stderr (see
            # aisoft_host_access.cli). Surface it instead of collapsing every profile
            # problem into one opaque code. Only a well-formed code from that fixed
            # vocabulary is propagated; anything else fails closed.
            raise _profile_tool_error(_decode_json(result.stderr))
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
        allow_failure: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self.runner(argv, cwd=cwd, env=env)
        except TypeError:
            result = self.runner(argv)
        except Exception as exc:
            raise BrokerError("HOST_COMMAND_FAILED", "structured host operation failed") from exc
        if result.returncode != 0 and not allow_failure:
            raise BrokerError("HOST_COMMAND_FAILED", "structured host operation failed")
        return result


_PROFILE_TOOL_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,47}$")


def _decode_json(text: str | None) -> object:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _profile_tool_error(payload: object) -> BrokerError:
    """Translate the profile tool's own stdout error contract into a BrokerError.

    The tool is a manifest-fixed platform component with a closed error vocabulary, so
    its code and message are safe to surface. Anything that does not match that shape
    degrades to the generic failure rather than forwarding unvetted text.
    """
    if isinstance(payload, dict):
        code = payload.get("code")
        message = payload.get("message")
        if (
            isinstance(code, str)
            and _PROFILE_TOOL_ERROR_CODE.fullmatch(code)
            and isinstance(message, str)
            and 0 < len(message) <= 200
            and "\n" not in message
        ):
            return BrokerError(code, message)
    return BrokerError("HOST_COMMAND_FAILED", "structured host operation failed")


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
