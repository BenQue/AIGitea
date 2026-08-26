"""Typed controller adapter for the fixed installed host-access broker."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Callable, Mapping, Sequence

from .broker import BrokerError, _positive_number
from .contract import AccessContract


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

    def issue_create(self, title: str, body: str) -> Mapping[str, object]:
        return self._call("gitea.issue.create", "--title", title, "--body", body)

    def issue_read(self, number: int) -> Mapping[str, object]:
        return self._call("gitea.issue.read", "--number", str(_positive_number(number, "Issue")))

    def issue_update(self, number: int, title: str, body: str) -> Mapping[str, object]:
        return self._call(
            "gitea.issue.update", "--number", str(_positive_number(number, "Issue")),
            "--title", title, "--body", body,
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
            completed = self._command_runner(argv, cwd=self._cwd)
        except Exception as exc:
            raise BrokerError("HOST_BROKER_UNAVAILABLE", "fixed host broker invocation failed") from exc
        if completed.returncode != 0:
            raise BrokerError("HOST_BROKER_FAILED", "fixed host broker operation failed")
        try:
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
        if not isinstance(sha, str) or not sha:
            raise BrokerError("ARGUMENT_INVALID", "head SHA is required")
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
