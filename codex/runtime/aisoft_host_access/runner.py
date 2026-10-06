"""Typed controller adapter for the fixed installed host-access broker."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Callable, Mapping, Sequence

from .broker import BrokerError, COMMIT_SHA_RE, _positive_number
from .contract import AccessContract
from .dependencies import Dependency, DependencyError, parse_dependencies, resolve_target, identity


BROKER_EXECUTABLE = "/usr/local/libexec/aisoft/host-access-broker"
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _default_runner(
    argv: Sequence[str], *, cwd: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), cwd=cwd, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


class GovernedHostRunner:
    """No-fallback adapter exposing only the governed Issue/change/PR lifecycle."""

    def __init__(
        self,
        contract: AccessContract,
        project_id: str,
        *,
        command_runner: CommandRunner = _default_runner,
    ) -> None:
        contract.project(project_id)
        self._contract = contract
        self._project_id = project_id
        self._command_runner = command_runner
        self._cwd = os.path.realpath(os.getcwd())

    def issue_create(
        self, title: str, body: str, entry_label: str
    ) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.create", "--title", title, "--body", body,
            "--entry-label", entry_label,
        )

    def issue_read(self, number: int) -> Mapping[str, object]:
        return self._call("gitea.issue.read", "--number", str(_positive_number(number, "Issue")))

    def application_target_preflight_read(self, target: str) -> Mapping[str, object]:
        self._contract.application_target(self._project_id, target)
        return self._call('application.target.preflight.read', '--target', target)

    def issue_update(self, number: int, title: str, body: str) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.update", "--number", str(_positive_number(number, "Issue")),
            "--title", title, "--body", body,
        )

    def issue_list(self, state: str) -> Mapping[str, object]:
        # state passes through unvalidated on purpose, the same rule lifecycle
        # follows: the broker owns the accepted set, and a second copy here would
        # drift the first time one side changes (#222).
        return self._call("gitea.issue.list", "--state", state)

    def issue_state_set(self, number: int, state: str) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.state.set", "--number", str(_positive_number(number, "Issue")),
            "--state", state,
        )

    def issue_comment(self, number: int, comment: str) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.comment", "--number", str(_positive_number(number, "Issue")),
            "--comment", comment,
        )

    def labels_read(self) -> Mapping[str, object]:
        return self._call("gitea.labels.read")

    def labels_provision(self) -> Mapping[str, object]:
        return self._call("gitea.labels.provision")

    def labels_extension_define(
        self, label: str, color: str, description: str
    ) -> Mapping[str, object]:
        # Values pass through as typed scalars. The installed broker owns prefix,
        # color and text validation; duplicating those rules here would drift.
        return self._call(
            "gitea.labels.extension.define",
            "--label", label,
            "--color", color,
            "--description", description,
        )

    def issue_labels_read(self, number: int) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.labels.read",
            "--number", str(_positive_number(number, "Issue")),
        )

    def issue_labels_set(self, number: int, lifecycle: str) -> Mapping[str, object]:
        # lifecycle is passed through unvalidated on purpose: the broker checks
        # it against the installed label manifest, and a second check here would
        # be a copy that drifts (#115).
        return self._call(
            "gitea.issue.labels.set",
            "--number", str(_positive_number(number, "Issue")),
            "--lifecycle", lifecycle,
        )

    def issue_labels_extension_set(
        self, number: int, label: str
    ) -> Mapping[str, object]:
        # The broker derives the one owned dimension from its installed prefix
        # manifest. This fixed method cannot pass a prefix or label set.
        return self._call(
            "gitea.issue.labels.extension.set",
            "--number", str(_positive_number(number, "Issue")),
            "--label", label,
        )

    def issue_labels_classify(
        self, number: int, change_type: str, complexity: str
    ) -> Mapping[str, object]:
        # Both values pass through unvalidated, for the same reason lifecycle
        # does: the broker checks them against the installed label manifest and
        # a second check here would be a copy that drifts (#160).
        return self._call(
            "gitea.issue.labels.classify",
            "--number", str(_positive_number(number, "Issue")),
            "--change-type", change_type,
            "--complexity", complexity,
        )

    def push_change(self, issue: int) -> Mapping[str, object]:
        number = _positive_number(issue, "Issue")
        return self._call("git.push.change", "--branch", f"change/{number}")

    def pull_create(self, issue: int, title: str, body: str) -> Mapping[str, object]:
        return self._call(
            "gitea.pull.create", "--issue", str(_positive_number(issue, "Issue")),
            "--title", title, "--body", body,
        )

    def pull_read(self, number: int) -> Mapping[str, object]:
        return self._call("gitea.pull.read", "--number", str(_positive_number(number, "pull request")))

    def pull_update(
        self, number: int, issue: int, title: str, body: str
    ) -> Mapping[str, object]:
        return self._call(
            "gitea.pull.update",
            "--number", str(_positive_number(number, "pull request")),
            "--issue", str(_positive_number(issue, "Issue")),
            "--title", title, "--body", body,
        )

    def commit_status_read(self, sha: str) -> Mapping[str, object]:
        return self._call("gitea.commit.status.read", "--sha", sha)

    def protection_read(self) -> Mapping[str, object]:
        return self._call("gitea.protection.read")

    def access_audit(self) -> Mapping[str, object]:
        return self._call("host.access.audit")

    def onboarding_check(self) -> Mapping[str, object]:
        return self._call("host.onboarding.check")

    def _call(self, operation: str, *arguments: str) -> Mapping[str, object]:
        expected = self._contract.operation(operation)
        argv = [
            BROKER_EXECUTABLE,
            "--project", self._project_id,
            "--operation", expected.name,
            *arguments,
        ]
        try:
            if operation == 'application.target.preflight.read' and self._command_runner is _default_runner:
                from .application_preflight import run_bounded
                raw = run_bounded(argv, limit=262144, timeout=30)
                completed = subprocess.CompletedProcess(argv, 0, raw.decode('utf-8'), '')
            else:
                completed = self._command_runner(argv, cwd=self._cwd)
        except Exception as exc:
            raise BrokerError("HOST_BROKER_UNAVAILABLE", "fixed host broker invocation failed") from exc
        if completed.returncode != 0:
            raise BrokerError("HOST_BROKER_FAILED", "fixed host broker operation failed")
        try:
            if operation == 'application.target.preflight.read':
                from .application_preflight import PreflightError, strict_json, validate_control_reply
                try:
                    value = validate_control_reply(strict_json(completed.stdout.encode('utf-8'), 262144))
                except PreflightError as exc:
                    raise BrokerError(exc.reason, 'fixed preflight response was refused') from None
            else:
                value = json.loads(completed.stdout)
        except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "fixed host broker returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "fixed host broker returned invalid JSON")
        return value


class RoutineMergeRunner:
    """Minimal no-fallback adapter for the routine merger's sole operation.

    This object never receives or resolves the merger credential.  The fixed
    broker selects the manifest-bound identity and repeats every live gate.
    Keeping this surface separate from ``GovernedHostRunner`` makes ordinary
    project Git and arbitrary Gitea requests unrepresentable to this caller.
    """

    def __init__(
        self,
        contract: AccessContract,
        project_id: str,
        *,
        command_runner: CommandRunner = _default_runner,
    ) -> None:
        contract.project(project_id)
        operation = contract.operation("gitea.pull.merge.routine")
        if operation.identity_route != "routine-merge-agent":
            raise BrokerError("CONTRACT_INVALID", "routine merge identity route is invalid")
        self._project_id = project_id
        self._command_runner = command_runner
        self._cwd = os.path.realpath(os.getcwd())

    def merge(self, number: int, sha: str) -> Mapping[str, object]:
        pull_number = _positive_number(number, "pull request")
        if not isinstance(sha, str) or COMMIT_SHA_RE.fullmatch(sha) is None:
            raise BrokerError("ARGUMENT_INVALID", "exact lowercase head SHA is required")
        argv = [
            BROKER_EXECUTABLE,
            "--project", self._project_id,
            "--operation", "gitea.pull.merge.routine",
            "--number", str(pull_number),
            "--sha", sha,
        ]
        try:
            completed = self._command_runner(argv, cwd=self._cwd)
        except Exception as exc:
            raise BrokerError(
                "HOST_BROKER_UNAVAILABLE", "fixed routine merge broker invocation failed"
            ) from exc
        if completed.returncode != 0:
            raise BrokerError("HOST_BROKER_FAILED", "fixed routine merge broker operation failed")
        try:
            value = json.loads(completed.stdout)
        except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError(
                "RESPONSE_SCHEMA_INVALID", "fixed routine merge broker returned invalid JSON"
            ) from exc
        if (
            not isinstance(value, dict)
            or value.get("operation") != "gitea.pull.merge.routine"
            or value.get("pull_request") != pull_number
            or value.get("head_sha") != sha
            or value.get("status") != "AUTO_MERGED"
        ):
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "fixed routine merge receipt is invalid")
        return value


def _dependency_runner(argv: Sequence[str], *, cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), cwd=cwd, check=False, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)


class DependencyReader:
    """Manifest-bound, read-only dependency adapter; never falls back to HTTP."""

    def __init__(self, contract: AccessContract, project_id: str, *,
                 command_runner: CommandRunner = _dependency_runner) -> None:
        self.contract = contract
        self.project = contract.project(project_id)
        self.source_identity = (contract.governance.owner, self.project.repository)
        self.base_url = contract.governance.base_url
        self._command_runner = command_runner
        self._cwd = os.path.realpath(os.getcwd())

    def validate(self, references: Sequence[Dependency], issue_number: int) -> None:
        refs = parse_dependencies(list(references), issue_number, self.source_identity)
        for reference in refs:
            resolve_target(self.contract, self.project, reference)

    def read(self, reference: str) -> Mapping[str, object]:
        _, number, canonical = resolve_target(self.contract, self.project, reference)
        argv = [BROKER_EXECUTABLE, "--project", self.project.project_id,
                "--operation", "gitea.dependency.read", "--reference", canonical]
        try:
            completed = self._command_runner(argv, cwd=self._cwd)
        except Exception as exc:
            raise BrokerError("HOST_BROKER_UNAVAILABLE", "fixed dependency broker unavailable") from exc
        if completed.returncode != 0:
            raise BrokerError("HOST_BROKER_FAILED", "fixed dependency broker read failed")
        try:
            value = json.loads(completed.stdout)
        except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError("DEPENDENCY_RESPONSE_INVALID", "dependency broker JSON is invalid") from exc
        owner, repo, _ = identity(reference, self.source_identity)
        if (not isinstance(value, dict)
                or set(value) != {"repository", "number", "reference", "state", "labels"}
                or value.get("repository") != f"{owner}/{repo}"
                or value.get("number") != number or type(value.get("number")) is not int
                or value.get("reference") != canonical
                or value.get("state") not in ("open", "closed")
                or not isinstance(value.get("labels"), list)
                or any(not isinstance(label, str) or not label for label in value["labels"])):
            raise BrokerError("DEPENDENCY_RESPONSE_INVALID", "dependency broker identity is invalid")
        return value


class CredentialRotationRunner:
    """Independent operator surface; never attached to project/provider runners."""
    def __init__(self, contract, project_id, *, command_runner=_default_runner):
        contract.project(project_id)
        operation = contract.operation('gitea.credential.rotate')
        if operation.identity_route != 'credential-operator':
            raise BrokerError('CONTRACT_INVALID', 'rotation operator route is invalid')
        self.project_id = project_id
        self.command_runner = command_runner

    def rotate(self, issue, source_sha, token_kind):
        issue = _positive_number(issue, 'authorization Issue')
        if not isinstance(source_sha, str) or not COMMIT_SHA_RE.fullmatch(source_sha):
            raise BrokerError('ARGUMENT_INVALID', 'exact merged source SHA required')
        argv = [BROKER_EXECUTABLE, '--project', self.project_id, '--operation',
                'gitea.credential.rotate', '--issue', str(issue), '--sha', source_sha,
                '--token-kind', token_kind]
        try:
            value = self.command_runner(argv, cwd=os.path.realpath(os.getcwd()))
            if value.returncode != 0:
                raise ValueError()
            receipt = json.loads(value.stdout)
            if (not isinstance(receipt, dict) or receipt.get('operation') != 'gitea.credential.rotate'
                    or receipt.get('project_id') != self.project_id or receipt.get('issue') != issue
                    or receipt.get('source_sha') != source_sha or receipt.get('token_kind') != token_kind
                    or receipt.get('status') != 'PASS' or receipt.get('result') not in ('rotated', 'no-op')):
                raise ValueError()
            return receipt
        except Exception:
            raise BrokerError('HOST_BROKER_FAILED', 'operator rotation receipt unavailable') from None
