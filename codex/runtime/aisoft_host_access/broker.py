from __future__ import annotations

import json
import base64
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
from urllib.parse import parse_qsl, quote, urlparse
from urllib.request import Request, urlopen

from aisoft_change_name import ChangeName, ChangeNameError, SLUG_PATTERN, select_change_name

from .contract import (
    IDENTIFIER_RE,
    AccessContract,
    AccessContractError,
    OperationContract,
    ProjectContract,
)


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
COLLABORATOR_PAGE_LIMIT = 50
COLLABORATOR_MAX_PAGES = 100
# A page contains at most 50 collaborator objects. 128 KiB allows roughly
# 2.5 KiB per entry (well above the fields this audit consumes) while rejecting
# response amplification before JSON parsing. The audit-wide bound covers all
# canonical repositories in one host.access.audit invocation.
COLLABORATOR_PAGE_MAX_BYTES = 128 * 1024
COLLABORATOR_AUDIT_MAX_BYTES = 4 * 1024 * 1024
COLLABORATOR_AUDIT_MAX_PAGES = 1000


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
    tuple[int, object, bytes],
]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _header_items(headers: object) -> tuple[tuple[str, str], ...]:
    if isinstance(headers, Mapping):
        raw_items: object = headers.items()
    elif isinstance(headers, Sequence) and not isinstance(
        headers, (str, bytes, bytearray)
    ):
        raw_items = headers
    else:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "host response headers are invalid"
        )
    try:
        items = tuple(raw_items)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "host response headers are invalid"
        ) from exc
    normalized: list[tuple[str, str]] = []
    for item in items:
        if (
            not isinstance(item, (tuple, list))
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], str)
            or re.fullmatch(
                r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", item[0]
            ) is None
            or "\r" in item[1]
            or "\n" in item[1]
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID", "host response headers are invalid"
            )
        normalized.append((item[0], item[1]))
    return tuple(normalized)


def _response_header_items(headers: object) -> tuple[tuple[str, str], ...]:
    raw_items = getattr(headers, "raw_items", None)
    if callable(raw_items):
        try:
            return _header_items(tuple(raw_items()))
        except (TypeError, ValueError) as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID", "host response headers are invalid"
            ) from exc
    return _header_items(headers)


def _declared_content_length(headers: object) -> int | None:
    values: list[int] = []
    for key, raw_value in _header_items(headers):
        if key.casefold() != "content-length":
            continue
        for token in raw_value.split(","):
            value = token.strip()
            if re.fullmatch(r"(?:0|[1-9][0-9]*)", value) is None:
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory Content-Length is invalid",
                )
            values.append(int(value))
    if not values:
        return None
    if len(set(values)) != 1:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID",
            "collaborator inventory Content-Length is conflicting",
        )
    return values[0]


def _validate_bounded_response(
    headers: object, body: object, response_limit: int
) -> tuple[tuple[str, str], ...]:
    header_items = _header_items(headers)
    declared = _declared_content_length(header_items)
    if not isinstance(body, bytes):
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "collaborator inventory body is invalid"
        )
    if declared is not None and declared > response_limit:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "collaborator inventory response is too large"
        )
    if len(body) > response_limit:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "collaborator inventory response is too large"
        )
    if declared is not None and declared != len(body):
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID",
            "collaborator inventory Content-Length does not match the body",
        )
    return header_items


def _read_transport_response(
    response: object, response_limit: int | None
) -> tuple[int, tuple[tuple[str, str], ...], bytes]:
    status = getattr(response, "status", None)
    header_items = _response_header_items(getattr(response, "headers", None))
    if response_limit is None:
        body = response.read()  # type: ignore[attr-defined]
        return status, header_items, body
    if (
        not isinstance(response_limit, int)
        or isinstance(response_limit, bool)
        or response_limit <= 0
    ):
        raise BrokerError(
            "ARGUMENT_INVALID", "response limit must be a positive integer"
        )
    declared = _declared_content_length(header_items)
    if declared is not None and declared > response_limit:
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID", "collaborator inventory response is too large"
        )
    body = response.read(response_limit + 1)  # type: ignore[attr-defined]
    _validate_bounded_response(header_items, body, response_limit)
    return status, header_items, body


def _default_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
    *,
    response_limit: int | None = None,
) -> tuple[int, tuple[tuple[str, str], ...], bytes]:
    request = Request(url, method=method, headers=dict(headers), data=body)
    try:
        with urlopen(request, timeout=30) as response:
            return _read_transport_response(response, response_limit)
    except HTTPError as exc:
        status, response_headers, response_body = _read_transport_response(
            exc, response_limit
        )
        return exc.code if status is None else status, response_headers, response_body
    except (URLError, TimeoutError, OSError) as exc:
        raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc


@dataclass
class _CollaboratorInventoryBudget:
    pages: int = 0
    response_bytes: int = 0

    def charge(self, response_bytes: int) -> None:
        next_pages = self.pages + 1
        next_bytes = self.response_bytes + response_bytes
        if (
            next_pages > COLLABORATOR_AUDIT_MAX_PAGES
            or next_bytes > COLLABORATOR_AUDIT_MAX_BYTES
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory exceeds the audit response budget",
            )
        self.pages = next_pages
        self.response_bytes = next_bytes


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
        elif route == "routine-merge-agent":
            repository = self.contract.governance.repository(project.repository)
            if (
                not repository.routine_auto_merge_enabled
                or project.routine_merge_agent is None
                or project.routine_merge_agent != repository.routine_merge_agent
            ):
                raise BrokerError(
                    "ROUTINE_REPOSITORY_DISABLED",
                    "repository is not explicitly enabled for routine merge",
                )
            binding = self.contract.raw["identity_bindings"]["routine_merge_agent"]
            identity = project.routine_merge_agent
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
        change_type: str | None = None,
        complexity: str | None = None,
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
            "change_type": change_type,
            "complexity": complexity,
        }
        supplied = {
            key for key, value in arguments.items()
            if value is not None
        }
        if supplied != set(operation.arguments):
            raise BrokerError("ARGUMENT_MISMATCH", "operation arguments do not match the typed contract")

        try:
            if operation_name.startswith("gitea."):
                if operation_name == "gitea.pull.merge.routine":
                    assert number is not None and sha is not None
                    return self._routine_merge(project, operation, number, sha)
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
                    change_type=change_type,
                    complexity=complexity,
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

    def _routine_merge(
        self,
        project: ProjectContract,
        operation: OperationContract,
        number: int,
        sha: str,
    ) -> dict[str, object]:
        """Fresh, ordered, fail-closed routine merge gate and the sole merge POST."""
        _positive_number(number, "pull request")
        if COMMIT_SHA_RE.fullmatch(sha) is None:
            raise BrokerError("ARGUMENT_INVALID", "routine merge requires an exact lowercase SHA-1")
        repository_contract = self.contract.governance.repository(project.repository)
        if (
            not repository_contract.routine_auto_merge_enabled
            or repository_contract.routine_merge_agent is None
            or project.routine_merge_agent != repository_contract.routine_merge_agent
        ):
            raise BrokerError("ROUTINE_REPOSITORY_DISABLED", "repository routine merge is disabled")
        credential = self.credentials.resolve(project, operation)
        self._verify_identity(credential, require_non_admin_exact=True)
        try:
            actual_scopes = self._probe_token_scopes(credential)
        except BrokerError as exc:
            raise BrokerError(
                "ROUTINE_TOKEN_SCOPE_MISMATCH",
                "routine credential exact scope is unavailable or unsafe",
            ) from exc
        expected_scopes = set(
            self.contract.governance.raw["routine_merge_agent_policy"]["token_scopes"]
        )
        if actual_scopes != expected_scopes:
            raise BrokerError(
                "ROUTINE_TOKEN_SCOPE_MISMATCH",
                "routine credential scopes do not exactly match the manifest",
            )
        owner = quote(self.contract.governance.owner, safe="")
        repository = quote(project.repository, safe="")
        repo_api = f"{self.contract.governance.base_url}/api/v1/repos/{owner}/{repository}"

        # 1. Submit authorization: it binds Issue/branch/policy, never a stale SHA.
        pull = self._request_json(f"{repo_api}/pulls/{number}", credential.token)
        if not isinstance(pull, dict) or not isinstance(pull.get("body"), str):
            raise BrokerError("ROUTINE_AUTHORIZATION_INVALID", "pull authorization is missing")
        markers = re.findall(
            r"(?m)^AISoft-Submit-Authorization: issue=([1-9][0-9]*); "
            r"branch=(change/[1-9][0-9]*-[a-z0-9-]+); policy=(manual|routine-auto)$",
            pull["body"],
        )
        if len(markers) != 1 or markers[0][2] != "routine-auto":
            raise BrokerError("ROUTINE_AUTHORIZATION_INVALID", "routine submit authorization is invalid")
        issue_number = int(markers[0][0])
        branch = markers[0][1]
        closes = re.findall(r"(?mi)^Closes #([1-9][0-9]*)$", pull["body"])
        if closes != [str(issue_number)]:
            raise BrokerError(
                "ROUTINE_AUTHORIZATION_INVALID",
                "routine pull request must close exactly its authorized Issue",
            )
        if issue_number == 208:
            raise BrokerError("ROUTINE_ISSUE_MANUAL_ONLY", "Issue #208 is manual-only")
        pilot = repository_contract.routine_live_pilot
        if pilot is not None and issue_number != pilot.canary_issue:
            raise BrokerError(
                "ROUTINE_CANARY_ONLY",
                "routine live pilot is restricted to its exact canary Issue",
            )
        try:
            change = ChangeName.parse_branch(branch, allow_legacy=False)
        except ChangeNameError as exc:
            raise BrokerError("ROUTINE_TARGET_INVALID", "routine branch is not readable") from exc
        if change.issue_number != issue_number:
            raise BrokerError("ROUTINE_TARGET_INVALID", "Issue and branch do not match")

        # 2. Summary at the supplied final head plus current Gitea classification.
        assert change.slug is not None
        summary_match = re.findall(
            rf"(?m)^- (docs/changes/{issue_number}-{re.escape(change.slug)}/"
            rf"summary-{re.escape(change.slug)}-[0-9]{{6}}\.md)$",
            pull["body"],
        )
        if len(summary_match) != 1:
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "exact semantic summary is missing")
        summary = self._content_at_sha(repo_api, credential.token, summary_match[0], sha)
        front = self._routine_front_matter(summary)
        risk_flags_raw = front.get("risk_flags")
        dependencies = front.get("depends_on", [])
        if (
            not isinstance(risk_flags_raw, list)
            or any(not isinstance(item, str) or not item for item in risk_flags_raw)
            or not isinstance(dependencies, list)
            or any(not isinstance(item, int) or isinstance(item, bool) or item <= 0
                   for item in dependencies)
        ):
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "summary list fields are invalid")
        risk_flags = tuple(risk_flags_raw)
        if (
            front.get("issue") != issue_number
            or front.get("branch") != branch
            or front.get("change_type") in {"feature", "security", "data", "platform"}
            or front.get("effective_complexity") != "small"
            or front.get("contract_effect") not in {"restore", "unchanged"}
            or set(risk_flags) & {
                "functional-change", "schema-change", "data-migration", "security",
                "shared-core", "cross-module", "cross-service", "ci-integration",
                "ci-change", "artifact", "deployment", "deployment-boundary",
                "rollback", "agent-governance", "platform-governance", "major",
                "phase-completion", "milestone-completion",
            }
        ):
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "summary is not routine-small")
        issue = self._request_json(f"{repo_api}/issues/{issue_number}", credential.token)
        labels = {
            item.get("name") for item in issue.get("labels", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        } if isinstance(issue, dict) else set()
        type_labels = {name for name in labels if isinstance(name, str) and name.startswith("type/")}
        complexity_labels = {
            name for name in labels
            if isinstance(name, str) and name.startswith("complexity/")
        }
        if (
            not isinstance(issue, dict)
            or issue.get("number") != issue_number
            or issue.get("state") != "open"
            or complexity_labels != {"complexity/small"}
            or len(type_labels) != 1
            or labels & {
            "type/feature", "type/security", "type/data", "type/platform"
            }
        ):
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "Gitea classification is not routine-small")

        # 3. Exact Issue/branch/docs/PR and one open PR only.
        open_pulls = self._open_pulls(repo_api, credential.token)
        matches = [
            item for item in open_pulls
            if isinstance(item, dict)
            and isinstance(item.get("head"), dict)
            and item["head"].get("ref") == branch
        ]
        same_issue = []
        for item in open_pulls:
            body = item.get("body") if isinstance(item, dict) else None
            if not isinstance(body, str):
                raise BrokerError("ROUTINE_PR_NOT_UNIQUE", "open pull inventory is invalid")
            item_markers = re.findall(
                r"(?m)^AISoft-Submit-Authorization: issue=([1-9][0-9]*); ", body
            )
            item_closes = re.findall(r"(?mi)^Closes #([1-9][0-9]*)$", body)
            if str(issue_number) in item_markers or str(issue_number) in item_closes:
                same_issue.append(item)
        if (
            len(matches) != 1
            or matches[0].get("number") != number
            or len(same_issue) != 1
            or same_issue[0].get("number") != number
        ):
            raise BrokerError("ROUTINE_PR_NOT_UNIQUE", "exact change must have one open pull request")

        # 4. Open, unmerged, main base.
        if (
            pull.get("state") != "open" or pull.get("merged") is True
            or not isinstance(pull.get("base"), dict)
            or pull["base"].get("ref") != self.contract.governance.default_branch
            or not isinstance(pull.get("head"), dict)
            or pull["head"].get("ref") != branch
        ):
            raise BrokerError("ROUTINE_PR_STATE_INVALID", "pull request state or base is invalid")

        # 5. Head equals the caller-supplied final SHA.
        if pull["head"].get("sha") != sha:
            raise BrokerError("ROUTINE_HEAD_DRIFT", "pull request head does not match supplied SHA")

        # 6. Live protection must match the enabled manifest and exact merger.
        protection = self._request_json(
            f"{repo_api}/branch_protections/{quote(self.contract.governance.default_branch, safe='')}",
            credential.token,
        )
        permission = self._request_json(
            f"{repo_api}/collaborators/{quote(credential.identity, safe='')}/permission",
            credential.token,
        )
        contexts = list(repository_contract.status_check_contexts)
        expected_mergers = sorted([
            self.contract.governance.human_merge_identity,
            repository_contract.routine_merge_agent,
        ])
        if (
            not isinstance(protection, dict)
            or not isinstance(permission, dict)
            or permission.get("permission") != "write"
            or protection.get("enable_push") is not False
            or protection.get("enable_push_whitelist") is not False
            or protection.get("push_whitelist_usernames") != []
            or protection.get("push_whitelist_teams") != []
            or protection.get("push_whitelist_deploy_keys") is not False
            or protection.get("enable_force_push") is not False
            or protection.get("enable_force_push_allowlist") is not False
            or protection.get("force_push_allowlist_usernames") != []
            or protection.get("force_push_allowlist_teams") != []
            or protection.get("force_push_allowlist_deploy_keys") is not False
            or protection.get("enable_merge_whitelist") is not True
            or sorted(protection.get("merge_whitelist_usernames") or []) != expected_mergers
            or protection.get("enable_status_check") is not True
            or sorted(protection.get("status_check_contexts") or []) != sorted(contexts)
            or protection.get("required_approvals") != repository_contract.required_approvals
            or protection.get("block_admin_merge_override") is not True
        ):
            raise BrokerError("ROUTINE_PROTECTION_DRIFT", "live protection differs from manifest")

        # 7. Every canonical required context is successful for this exact SHA.
        if not contexts:
            raise BrokerError("ROUTINE_REQUIRED_CONTEXTS_EMPTY", "required contexts are empty")
        combined = self._request_json(f"{repo_api}/commits/{sha}/status", credential.token)
        statuses = combined.get("statuses") if isinstance(combined, dict) else None
        if not isinstance(statuses, list):
            raise BrokerError("ROUTINE_CI_INVALID", "commit status response is invalid")
        by_context = {
            item.get("context"): item.get("status")
            for item in statuses if isinstance(item, dict)
        }
        if any(by_context.get(context) != "success" for context in contexts):
            raise BrokerError("ROUTINE_CI_NOT_GREEN", "required CI is not green for exact head")

        # 8. Any valid rejection blocks merge.
        reviews = self._bounded_list(f"{repo_api}/pulls/{number}/reviews", credential.token)
        for item in reviews:
            if not isinstance(item, dict):
                raise BrokerError("ROUTINE_REVIEW_INVALID", "pull review response is invalid")
        if any(
            str(item.get("state") or item.get("status") or "").upper()
            in {"REQUEST_CHANGES", "REJECTED", "REQUESTED_CHANGES"}
            and item.get("dismissed") is not True
            and item.get("stale") is not True
            for item in reviews
        ):
            raise BrokerError("ROUTINE_REVIEW_REJECTED", "pull request has a rejecting review")

        # 9. Dependencies must be closed and completed/deployed.
        for dependency in dependencies:
            dep = self._request_json(f"{repo_api}/issues/{dependency}", credential.token)
            dep_labels = {
                item.get("name") for item in dep.get("labels", [])
                if isinstance(item, dict)
            } if isinstance(dep, dict) else set()
            if dep.get("state") != "closed" or not dep_labels & {"completed", "deployed"}:
                raise BrokerError("ROUTINE_DEPENDENCY_BLOCKED", "dependency is not terminal")

        # 10. Recompute conservative small scope from the complete final diff.
        files = self._bounded_list(f"{repo_api}/pulls/{number}/files", credential.token)
        entries: list[tuple[str, str]] = []
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
                raise BrokerError("ROUTINE_SCOPE_INVALID", "pull file response is invalid")
            status = str(item.get("status") or "modified")
            entries.append((status, item["filename"]))
        if not self._routine_files_are_local_reversible(entries):
            raise BrokerError("ROUTINE_SCOPE_EXPANDED", "final diff is not local and reversible")

        # 11. Last head read closes the local TOCTOU window; Gitea also checks head_commit_id.
        final_pull = self._request_json(f"{repo_api}/pulls/{number}", credential.token)
        if (
            not isinstance(final_pull, dict)
            or not isinstance(final_pull.get("head"), dict)
            or final_pull["head"].get("sha") != sha
        ):
            raise BrokerError("ROUTINE_HEAD_DRIFT", "pull request head changed before merge")
        payload = {
            "do": "merge",
            "head_commit_id": sha,
            "force_merge": False,
            "merge_when_checks_succeed": False,
            "delete_branch_after_merge": True,
        }
        response = self._request_json(
            f"{repo_api}/pulls/{number}/merge",
            credential.token,
            method="POST",
            payload=payload,
        )
        return {
            "operation": "gitea.pull.merge.routine",
            "pull_request": number,
            "head_sha": sha,
            "status": "AUTO_MERGED",
            "merge_commit_sha": (
                response.get("sha") if isinstance(response, dict) else None
            ),
        }

    def _content_at_sha(self, repo_api: str, token: str, path: str, sha: str) -> str:
        value = self._request_json(
            f"{repo_api}/contents/{quote(path, safe='/')}?ref={sha}", token
        )
        if not isinstance(value, dict) or value.get("encoding") != "base64" \
                or not isinstance(value.get("content"), str):
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "summary content response is invalid")
        try:
            return base64.b64decode(value["content"], validate=True).decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "summary content is invalid") from exc

    @staticmethod
    def _routine_front_matter(text: str) -> dict[str, object]:
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise BrokerError("ROUTINE_CONTRACT_INVALID", "summary front matter is invalid")
        block = text.split("\n---\n", 1)[0].splitlines()[1:]
        result: dict[str, object] = {}
        active: str | None = None
        for line in block:
            if line.startswith("  - ") and active in {"risk_flags", "depends_on"}:
                values = result.setdefault(active, [])
                assert isinstance(values, list)
                raw = line[4:].strip()
                values.append(int(raw) if active == "depends_on" and raw.isdigit() else raw)
                continue
            if line and not line.startswith(" ") and ":" in line:
                key, raw = line.split(":", 1)
                value = raw.strip().strip("'\"")
                active = key if not value else None
                result[key] = (
                    [] if value == "[]"
                    else int(value) if key == "issue" and value.isdigit()
                    else value if value else []
                )
        return result

    def _bounded_list(self, url: str, token: str) -> list[object]:
        values: list[object] = []
        separator = "&" if "?" in url else "?"
        for page in range(1, 101):
            page_value = self._request_json(
                f"{url}{separator}limit=50&page={page}", token
            )
            if not isinstance(page_value, list):
                raise BrokerError("RESPONSE_SCHEMA_INVALID", "bounded list response is invalid")
            values.extend(page_value)
            if len(page_value) < 50:
                return values
        raise BrokerError("RESPONSE_SCHEMA_INVALID", "bounded list exceeded safe limit")

    @staticmethod
    def _routine_files_are_local_reversible(entries: Sequence[tuple[str, str]]) -> bool:
        if not entries:
            return False
        forbidden = (
            ".gitea/", "codex/", "deploy/", "deployment/", "infra/",
            "migrations/", "schema/", "scripts/deploy", "scripts/promote",
        )
        roots: set[str] = set()
        for status, path in entries:
            if path.startswith(forbidden) or PurePosixPath(path).name == "AGENTS.md":
                return False
            if status.lower() in {"deleted", "renamed", "copied", "unmerged"}:
                return False
            if PurePosixPath(path).suffix.lower() in {
                ".sql", ".db", ".sqlite", ".bin", ".tar", ".zip",
            }:
                return False
            roots.add(path.split("/", 1)[0])
        return len(roots) == 1

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
        change_type: str | None,
        complexity: str | None,
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
        elif operation.name == "gitea.issue.labels.classify":
            _positive_number(number, "Issue")
            # Bare front matter values in, namespaced label names out: the
            # caller copies change_type and effective_complexity straight out of
            # the summary and never has to know how the label is spelled.
            # Checked against the installed manifest for the same reason
            # --lifecycle is, and a retired value fails here rather than being
            # attached — complexity/standard is exactly the case that matters.
            # Local file read, so an out-of-range value costs no credential and
            # no request.
            if f"type/{change_type}" not in self._namespaced_labels("type/"):
                raise BrokerError(
                    "ARGUMENT_MISMATCH",
                    "change type must be one of the change types the label manifest declares",
                )
            if f"complexity/{complexity}" not in self._namespaced_labels("complexity/"):
                raise BrokerError(
                    "ARGUMENT_MISMATCH",
                    "complexity must be one of the complexities the label manifest declares",
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
        if operation.name == "gitea.issue.labels.classify":
            assert number is not None
            assert change_type is not None and complexity is not None
            return self._set_issue_classification(
                repo_api, credential.token, number, change_type, complexity
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

    def _namespaced_labels(self, prefix: str) -> set[str]:
        """One namespaced label dimension, derived from the installed manifest.

        The mirror of _lifecycle_labels(): that one takes the canonical names
        carrying no namespace, this one takes the names under a given prefix.
        Derived rather than listed for the same reason — a literal would be a
        second copy of the manifest, and it would keep accepting a value this
        install no longer declares. complexity/standard is the live case:
        retired in the manifest, so not writable here, while an Issue still
        carrying it is a separate question answered in _set_issue_classification.
        """
        return {
            entry["name"]
            for entry in self._label_manifest()["canonical"]
            if entry["name"].startswith(prefix)
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
        """Replace the Issue's lifecycle dimension, leaving every other label."""
        states = self._lifecycle_labels()

        def guard(attached: set[str]) -> None:
            # completed and deployed are the two terminal states and deployed is
            # the stronger one. Demoting a shipped change back to completed is a
            # claim about what actually happened to it, so it stays a human
            # decision and is not reachable through the tool that walks merged
            # Issues.
            if lifecycle == "completed" and "deployed" in attached:
                raise BrokerError(
                    "REQUEST_DENIED",
                    "Issue is already deployed; downgrading it to completed is a human decision",
                )

        return self._replace_issue_label_dimensions(
            repo_api,
            token,
            number,
            in_dimension=lambda name: name in states,
            targets=(lifecycle,),
            guard=guard,
        )

    def _set_issue_classification(
        self, repo_api: str, token: str, number: int, change_type: str, complexity: str
    ) -> dict[str, object]:
        """Project one AI classification onto the Issue's two analyzer dimensions.

        Both move in a single write because they are a single judgement: an
        Issue left holding a type/ from this analysis and a complexity/ from an
        older one is a state the four-dimension contract does not describe.

        Dimension membership is the namespace itself, not the canonical list, so
        an Issue still carrying the retired complexity/standard has it replaced
        rather than kept alongside the new value. Retired labels are never
        removed from the repository (that stays _provision_labels' report-only
        rule); this is about which label the Issue ends up wearing.
        """
        return self._replace_issue_label_dimensions(
            repo_api,
            token,
            number,
            in_dimension=lambda name: name.startswith(("type/", "complexity/")),
            targets=(f"type/{change_type}", f"complexity/{complexity}"),
        )

    def _replace_issue_label_dimensions(
        self,
        repo_api: str,
        token: str,
        number: int,
        *,
        in_dimension: Callable[[str], bool],
        targets: tuple[str, ...],
        guard: Callable[[set[str]], None] | None = None,
    ) -> dict[str, object]:
        """Replace whole label dimensions on one Issue, leaving every other label.

        Attaching is not defining: when a target label has no definition in the
        repository this fails closed and names gitea.labels.provision (#108)
        instead of creating it, so the two operation surfaces stay separate.
        """
        defined = {item["name"]: item for item in self._labels(repo_api, token)}
        target_ids: dict[str, int] = {}
        for name in targets:
            target = defined.get(name)
            if target is None:
                raise BrokerError(
                    "TARGET_MISMATCH",
                    f"the {name} label is not defined in this repository; "
                    "define it with gitea.labels.provision before attaching it",
                )
            target_id = target.get("id")
            if not isinstance(target_id, int) or isinstance(target_id, bool):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "Gitea label is missing a usable id"
                )
            target_ids[name] = target_id

        current = self._issue_labels(repo_api, token, number)
        before = sorted(str(item["name"]) for item in current)
        attached = {str(item["name"]) for item in current if in_dimension(str(item["name"]))}
        if guard is not None:
            guard(attached)

        # Already exactly right: no PUT at all, so a repeated run cannot churn
        # the Issue's label history or its notification stream. The comparison
        # is against the whole dimension, not just membership — an Issue
        # carrying two labels from one dimension still needs the write that
        # leaves it holding one.
        if attached == set(targets):
            return {
                "issue": number,
                "before": before,
                "after": before,
                "result": "no-op",
                "status": "PASS",
            }

        # Everything outside the named dimensions is carried across by id. This
        # is a replacement of dimensions, not an assignment of a label set:
        # there is no way to ask these operations to drop the dimensions they do
        # not own, triage/ or a project extension label.
        final = sorted(
            {
                int(item["id"])
                for item in current
                if not in_dimension(str(item["name"]))
            }
            | set(target_ids.values())
        )
        self._request_json(
            f"{repo_api}/issues/{number}/labels",
            token,
            method="PUT",
            payload={"labels": final},
        )
        by_id = {int(item["id"]): str(item["name"]) for item in current}
        by_id.update({value: name for name, value in target_ids.items()})
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

    def _verify_identity(
        self,
        credential: ResolvedCredential,
        *,
        require_non_admin_exact: bool = False,
    ) -> None:
        url = f"{self.contract.governance.base_url}/api/v1/user"
        value = self._request_json(url, credential.token)
        if not isinstance(value, dict) or value.get("login") != credential.identity:
            raise BrokerError("IDENTITY_MISMATCH", "credential identity does not match the route")
        if require_non_admin_exact and value.get("is_admin") is not False:
            raise BrokerError(
                "IDENTITY_MISMATCH",
                "routine credential identity must explicitly be non-site-admin",
            )
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

    def _optional_json(self, url: str, token: str) -> object | None:
        try:
            status, _headers, body = self.transport(
                "GET",
                url,
                {"Accept": "application/json", "Authorization": f"token {token}"},
                None,
            )
        except BrokerError:
            raise
        except Exception as exc:
            raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc
        if status == 404:
            return None
        if status in {401, 403}:
            raise BrokerError(f"HTTP_{status}", f"Gitea returned HTTP {status}")
        if status < 200 or status >= 300:
            raise BrokerError("HTTP_ERROR", f"Gitea returned HTTP {status}")
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID", "Gitea returned invalid JSON"
            ) from exc

    def _collaborator_page(
        self,
        repo_api: str,
        token: str,
        page: int,
        budget: _CollaboratorInventoryBudget,
    ) -> tuple[object, bool]:
        url = (
            f"{repo_api}/collaborators?limit={COLLABORATOR_PAGE_LIMIT}"
            f"&page={page}"
        )
        try:
            if self.transport is _default_transport:
                status, headers, body = _default_transport(
                    "GET",
                    url,
                    {
                        "Accept": "application/json",
                        "Authorization": f"token {token}",
                    },
                    None,
                    response_limit=COLLABORATOR_PAGE_MAX_BYTES,
                )
            else:
                status, headers, body = self.transport(
                    "GET",
                    url,
                    {
                        "Accept": "application/json",
                        "Authorization": f"token {token}",
                    },
                    None,
                )
        except BrokerError:
            raise
        except Exception as exc:
            raise BrokerError("TRANSPORT_ERROR", "host transport failed") from exc
        header_items = _validate_bounded_response(
            headers, body, COLLABORATOR_PAGE_MAX_BYTES
        )
        budget.charge(len(body))
        if not isinstance(status, int) or isinstance(status, bool):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory HTTP status is invalid",
            )
        if status != 200:
            if status in {401, 403, 404}:
                raise BrokerError(f"HTTP_{status}", f"Gitea returned HTTP {status}")
            if 200 <= status < 300:
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory requires HTTP 200",
                )
            raise BrokerError("HTTP_ERROR", f"Gitea returned HTTP {status}")
        try:
            value = json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory response is invalid",
            ) from exc
        return value, self._has_next_link(header_items, repo_api, page)

    @staticmethod
    def _has_next_link(headers: object, repo_api: str, page: int) -> bool:
        items = _header_items(headers)
        link_values = [
            value for key, value in items
            if key.casefold() == "link"
        ]
        if not link_values:
            return False
        relations: dict[str, int] = {}
        for link_value in link_values:
            segments = link_value.split(",")
            if not segments or any(not segment.strip() for segment in segments):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory pagination header is invalid",
                )
            for segment in segments:
                parts = [part.strip() for part in segment.split(";")]
                target_match = re.fullmatch(r"<([^<>\s]+)>", parts[0])
                if target_match is None or len(parts) < 2:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "collaborator inventory pagination header is invalid",
                    )
                seen_parameters: set[str] = set()
                relation_tokens: tuple[str, ...] | None = None
                for parameter in parts[1:]:
                    match = re.fullmatch(
                        r"([A-Za-z0-9_-]+)=(\"[^\"]*\"|[^;,\s]+)",
                        parameter,
                    )
                    if match is None:
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination header is invalid",
                        )
                    key = match.group(1).casefold()
                    if key in seen_parameters or key != "rel":
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination header is invalid",
                        )
                    seen_parameters.add(key)
                    raw_relation = match.group(2)
                    relation = (
                        raw_relation[1:-1]
                        if raw_relation.startswith('"')
                        else raw_relation
                    )
                    if re.fullmatch(
                        r"[A-Za-z][A-Za-z0-9._-]*"
                        r"(?: [A-Za-z][A-Za-z0-9._-]*)*",
                        relation,
                    ) is None:
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination header is invalid",
                        )
                    relation_tokens = tuple(
                        token.casefold() for token in relation.split(" ")
                    )
                    if len(set(relation_tokens)) != len(relation_tokens):
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination header is invalid",
                        )
                if relation_tokens is None:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "collaborator inventory pagination header is invalid",
                    )
                target_page = HostAccessBroker._collaborator_link_page(
                    target_match.group(1), repo_api
                )
                for relation in relation_tokens:
                    if relation not in {"first", "prev", "next", "last"}:
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination relation is invalid",
                        )
                    if relation in relations:
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "collaborator inventory pagination relation is duplicated",
                        )
                    relations[relation] = target_page
        if relations.get("first", 1) != 1:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory first-page link is invalid",
            )
        if "prev" in relations and (
            page <= 1 or relations["prev"] != page - 1
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory previous-page link is invalid",
            )
        if "next" in relations and relations["next"] != page + 1:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory next-page link is invalid",
            )
        if "last" in relations:
            expected_terminal = page if "next" not in relations else None
            if (
                expected_terminal is not None
                and relations["last"] != expected_terminal
            ) or (
                expected_terminal is None
                and relations["last"] < page + 1
            ):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory last-page link is invalid",
                )
        return "next" in relations

    @staticmethod
    def _collaborator_link_page(target: str, repo_api: str) -> int:
        canonical = urlparse(f"{repo_api}/collaborators")
        candidate = urlparse(target)
        try:
            canonical_port = canonical.port
            candidate_port = candidate.port
        except ValueError as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory pagination URL is invalid",
            ) from exc
        if (
            not candidate.scheme
            or not candidate.hostname
            or candidate.username is not None
            or candidate.password is not None
            or candidate.scheme.casefold() != canonical.scheme.casefold()
            or candidate.hostname.casefold() != canonical.hostname.casefold()
            or candidate_port != canonical_port
            or candidate.path != canonical.path
            or candidate.params
            or candidate.fragment
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory pagination URL is outside the canonical endpoint",
            )
        try:
            query = parse_qsl(
                candidate.query,
                keep_blank_values=True,
                strict_parsing=True,
                separator="&",
            )
        except (UnicodeError, ValueError) as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory pagination query is invalid",
            ) from exc
        if (
            len(query) != 2
            or {key for key, _value in query} != {"limit", "page"}
            or len({key for key, _value in query}) != len(query)
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory pagination query is invalid",
            )
        values = dict(query)
        if (
            values["limit"] != str(COLLABORATOR_PAGE_LIMIT)
            or re.fullmatch(r"[1-9][0-9]*", values["page"]) is None
        ):
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID",
                "collaborator inventory pagination query is invalid",
            )
        return int(values["page"])

    def _collaborator_names(
        self,
        repo_api: str,
        token: str,
        budget: _CollaboratorInventoryBudget,
    ) -> set[str]:
        names: set[str] = set()
        folded_names: set[str] = set()
        for page in range(1, COLLABORATOR_MAX_PAGES + 1):
            value, has_next = self._collaborator_page(
                repo_api, token, page, budget
            )
            if not isinstance(value, list):
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory response is invalid",
                )
            if len(value) > COLLABORATOR_PAGE_LIMIT:
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID",
                    "collaborator inventory page exceeds its requested limit",
                )
            for entry in value:
                login = entry.get("login") if isinstance(entry, dict) else None
                if (
                    not isinstance(entry, dict)
                    or not isinstance(login, str)
                    or login != login.strip()
                    or IDENTIFIER_RE.fullmatch(login) is None
                ):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "collaborator inventory response is invalid",
                    )
                folded = login.casefold()
                if login in names or folded in folded_names:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "collaborator inventory contains duplicate identity",
                    )
                names.add(login)
                folded_names.add(folded)
            if len(value) < COLLABORATOR_PAGE_LIMIT:
                if has_next:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "collaborator inventory pagination is contradictory",
                    )
                return folded_names
        raise BrokerError(
            "RESPONSE_SCHEMA_INVALID",
            "collaborator inventory exceeds the bounded scan",
        )

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
        if project.mac_checkout is None:
            raise BrokerError("TARGET_UNAVAILABLE", "project has no approved Mac checkout")
        access_operation = self.contract.operation("host.access.audit")
        access = self._access_audit(project, access_operation)
        if not isinstance(access, dict) or access.get("status") != "PASS":
            raise BrokerError(
                "ONBOARDING_MISMATCH",
                "host access audit has unresolved routine pilot gaps",
            )
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
        repository_contract = self.contract.governance.repository(project.repository)

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
        if (repository_contract.routine_auto_merge_enabled
                and repository_contract.routine_merge_agent is not None):
            expected_merge.append(repository_contract.routine_merge_agent)
        expected_contexts = sorted(repository_contract.status_check_contexts)
        actual_merge = protection.get("merge_whitelist_usernames") \
            if isinstance(protection, dict) else None
        actual_merge_tuple = tuple(actual_merge) if isinstance(actual_merge, list) else None
        allowed_preapply_merge = [self.contract.governance.human_merge_identity]
        if (
            not isinstance(protection, dict)
            or protection.get("enable_push") is not False
            or protection.get("enable_force_push") is not False
            or protection.get("enable_merge_whitelist") is not True
            or actual_merge_tuple not in {
                tuple(expected_merge), tuple(allowed_preapply_merge)
            }
            or protection.get("enable_status_check") is not bool(expected_contexts)
            or sorted(protection.get("status_check_contexts", [])) != expected_contexts
            or protection.get("required_approvals") != repository_contract.required_approvals
            or protection.get("block_admin_merge_override") is not True
        ):
            raise BrokerError("PROTECTION_MISMATCH", "protected main does not match the governance boundary")

        routine: dict[str, object] = {
            "enabled": repository_contract.routine_auto_merge_enabled,
            "identity": repository_contract.routine_merge_agent,
            "credential": {
                "kind": "protected-file",
                "state": "not-enabled",
                "path_disclosure": "DENIED",
            },
            "account_state": "not-enabled",
            "expected_token_scopes": list(
                self.contract.governance.raw["routine_merge_agent_policy"]["token_scopes"]
            ),
            "actual_token_scopes": None,
            "repository_permission": "not-enabled",
            "cross_project_permissions": [],
            "cross_project_write_violations": [],
            "merge_allowlist_state": (
                "converged" if actual_merge == expected_merge else "pre-apply"
            ),
        }
        routine_gap = False
        if repository_contract.routine_auto_merge_enabled:
            merger = repository_contract.routine_merge_agent
            assert merger is not None
            account = self._optional_json(
                f"{self.contract.governance.base_url}/api/v1/users/"
                f"{quote(merger, safe='')}", manager_token,
            )
            if account is None:
                routine["account_state"] = "missing"
                routine_gap = True
            elif not isinstance(account, dict) or account.get("login") != merger:
                raise BrokerError(
                    "RESPONSE_SCHEMA_INVALID", "routine account response is invalid"
                )
            elif account.get("is_admin") is not False:
                routine["account_state"] = "present-site-admin"
                routine_gap = True
            else:
                routine["account_state"] = "present-non-admin"

            try:
                routine_credential = self.credentials.resolve(
                    project,
                    OperationContract(
                        "host.access.audit", "routine-merge-agent", False, ()
                    ),
                )
            except BrokerError as exc:
                if exc.code != "CREDENTIAL_UNAVAILABLE":
                    raise
                routine["credential"] = {
                    "kind": "protected-file",
                    "state": "missing",
                    "path_disclosure": "DENIED",
                }
                routine_gap = True
            else:
                self._verify_identity(
                    routine_credential, require_non_admin_exact=True
                )
                actual_routine_scopes = self._probe_token_scopes(routine_credential)
                expected_routine_scopes = set(
                    self.contract.governance.raw[
                        "routine_merge_agent_policy"
                    ]["token_scopes"]
                )
                if actual_routine_scopes != expected_routine_scopes:
                    raise BrokerError(
                        "TOKEN_SCOPE_MISMATCH",
                        "routine credential token scopes do not match the manifest",
                    )
                routine["credential"] = {
                    "kind": "protected-file",
                    "state": "present",
                    "path_disclosure": "DENIED",
                }
                routine["actual_token_scopes"] = sorted(actual_routine_scopes)

            account_missing = routine["account_state"] == "missing"
            if account_missing:
                inventory_budget = _CollaboratorInventoryBudget()
                target_collaborators = self._collaborator_names(
                    repo_api, manager_token, inventory_budget
                )
                if merger.casefold() in target_collaborators:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "routine collaborator inventory contradicts missing account",
                    )
                routine["repository_permission"] = "missing"
                routine_gap = True
            else:
                target_permission = self._optional_json(
                    f"{repo_api}/collaborators/{quote(merger, safe='')}/permission",
                    manager_token,
                )
                if target_permission is None:
                    routine["repository_permission"] = "missing"
                    routine_gap = True
                elif (
                    not isinstance(target_permission, dict)
                    or set(target_permission) != {"permission"}
                    or not isinstance(target_permission.get("permission"), str)
                    or target_permission["permission"]
                    not in {"read", "write", "admin", "owner"}
                ):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "routine permission response is invalid",
                    )
                else:
                    routine["repository_permission"] = target_permission["permission"]
                    if target_permission["permission"] != "write":
                        routine_gap = True

            cross_project_permissions: list[dict[str, object]] = []
            violations: list[dict[str, str]] = []
            for other in self.contract.governance.repositories:
                if other.name == repository_contract.name:
                    continue
                full_name = self.contract.governance.full_name(other)
                other_api = (
                    f"{self.contract.governance.base_url}/api/v1/repos/{owner}/"
                    f"{quote(other.name, safe='')}"
                )
                if account_missing:
                    collaborators = self._collaborator_names(
                        other_api, manager_token, inventory_budget
                    )
                    if merger.casefold() in collaborators:
                        raise BrokerError(
                            "RESPONSE_SCHEMA_INVALID",
                            "routine collaborator inventory contradicts missing account",
                        )
                    cross_project_permissions.append({
                        "repository": full_name,
                        "state": "absent",
                        "permission": None,
                    })
                    routine_gap = True
                    continue
                other_permission = self._optional_json(
                    f"{other_api}/collaborators/{quote(merger, safe='')}/permission",
                    manager_token,
                )
                if other_permission is None:
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "cross-project routine permission response is invalid",
                    )
                if (
                    not isinstance(other_permission, dict)
                    or set(other_permission) != {"permission"}
                    or not isinstance(other_permission.get("permission"), str)
                    or other_permission["permission"]
                    not in {"read", "write", "admin", "owner"}
                ):
                    raise BrokerError(
                        "RESPONSE_SCHEMA_INVALID",
                        "cross-project routine permission response is invalid",
                    )
                permission = other_permission["permission"]
                cross_project_permissions.append({
                    "repository": full_name,
                    "state": "present",
                    "permission": permission,
                })
                if permission in {"write", "admin", "owner"}:
                    violations.append({
                        "repository": full_name,
                        "permission": permission,
                    })
            routine["cross_project_permissions"] = cross_project_permissions
            routine["cross_project_write_violations"] = violations
            routine_gap = routine_gap or bool(violations)
            if actual_merge != expected_merge:
                routine_gap = True

        return {
            "status": "GAP" if routine_gap else "PASS",
            "project": project.project_id,
            "operation": operation.name,
            "identities": {
                route: credential.identity for route, credential in credentials.items()
            },
            "token_scopes": token_scopes,
            "repository_permission": permissions,
            "credential_store": credential_store,
            "routine_merge": routine,
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
            "routine_merge_agent": {
                "identity": project.routine_merge_agent,
                "kind": "protected-file",
                "scope": f"project:{project.project_id}:routine-merge",
                "enabled": self.contract.governance.repository(
                    project.repository
                ).routine_auto_merge_enabled,
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
