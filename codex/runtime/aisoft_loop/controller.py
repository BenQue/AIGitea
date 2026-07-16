"""Deterministic outer Development Loop controller."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Optional

from .contract import Contract, ContractError, load_contract
from .provider import ProviderError, ProviderResult
from .state import (
    GlobalLock,
    LockUnavailable,
    LoopBudget,
    StateStore,
    TerminalState,
)
from .verifier import VerificationReport, redact


@dataclass(frozen=True)
class ControllerResult:
    terminal_state: TerminalState
    message: str
    pr_number: Optional[int] = None


class Controller:
    def __init__(
        self,
        *,
        repo: Path | str,
        gitea: object,
        provider: object,
        verifier: object,
        git: object,
        state_store: StateStore,
        lock: GlobalLock,
        max_rounds: int = 8,
        max_same_root: int = 3,
    ) -> None:
        self.repo = Path(repo).resolve()
        self.gitea = gitea
        self.provider = provider
        self.verifier = verifier
        self.git = git
        self.state_store = state_store
        self.lock = lock
        self.max_rounds = max_rounds
        self.max_same_root = max_same_root

    def run(self, issue_number: int) -> ControllerResult:
        try:
            with self.lock:
                return self._run_locked(issue_number)
        except LockUnavailable:
            return ControllerResult(
                TerminalState.BLOCKED_EXTERNAL,
                "another Issue currently owns the Development Loop lock",
            )

    def _run_locked(self, issue_number: int) -> ControllerResult:
        state = self.state_store.load(issue_number)
        persisted_terminal = state.get("terminal")
        if persisted_terminal in {
            TerminalState.READY_FOR_REVIEW.value,
            TerminalState.NEEDS_HUMAN_DECISION.value,
            TerminalState.BLOCKED_EXTERNAL.value,
            TerminalState.FAILED_LIMIT.value,
        }:
            return ControllerResult(
                TerminalState(str(persisted_terminal)),
                str(state.get("message") or "persisted terminal state"),
                _optional_int(state.get("pr_number")),
            )
        budget = LoopBudget.from_dict(
            state.get("budget", {}) if isinstance(state.get("budget", {}), dict) else {}
        )
        budget.max_rounds = self.max_rounds
        budget.max_same_root = self.max_same_root
        pr_number = _optional_int(state.get("pr_number"))
        head_sha = str(state.get("head_sha") or "")
        failure_evidence = str(state.get("failure_evidence") or "")
        failure_kind = str(state.get("failure_kind") or "")

        try:
            contract = self._revalidate(issue_number, pr_number)
        except ContractError as exc:
            return self._contract_failure(issue_number, state, exc)

        if pr_number and state.get("stage") == "awaiting_ci":
            ci = self.gitea.get_commit_status(head_sha)
            if ci == "success":
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.READY_FOR_REVIEW,
                    "PR CI passed; final human review is required",
                    pr_number,
                    comment=True,
                )
            if ci == "pending":
                return ControllerResult(
                    TerminalState.CONTINUE, "PR CI is still pending", pr_number
                )
            failure_evidence = "CI failed for commit " + head_sha
            failure_kind = "ci"
            if budget.record_failure("ci") == TerminalState.FAILED_LIMIT:
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.FAILED_LIMIT,
                    "CI failed three consecutive times",
                    pr_number,
                    budget=budget,
                    comment=True,
                )

        while True:
            limit = budget.start_round()
            if limit is not None:
                return self._finish(
                    issue_number,
                    state,
                    limit,
                    "Development Loop reached its configured round limit",
                    pr_number,
                    budget=budget,
                    comment=True,
                )
            try:
                contract = self._revalidate(issue_number, pr_number)
            except ContractError as exc:
                return self._contract_failure(issue_number, state, exc, budget=budget)

            request = self._provider_request(
                contract, budget, failure_evidence, pr_number
            )
            try:
                provider_result = self.provider.run(request, self.repo)
            except ProviderError as exc:
                failure_evidence = redact(str(exc))
                failure_kind = "provider"
                if budget.record_failure("provider") == TerminalState.FAILED_LIMIT:
                    return self._finish(
                        issue_number,
                        state,
                        TerminalState.FAILED_LIMIT,
                        "provider failed three consecutive times",
                        pr_number,
                        budget=budget,
                        comment=True,
                    )
                self._save_progress(
                    issue_number,
                    state,
                    budget,
                    pr_number,
                    head_sha,
                    failure_evidence,
                    failure_kind,
                    "implementing",
                )
                continue

            if provider_result.status == "NEEDS_HUMAN_DECISION":
                self._set_lifecycle(contract, "awaiting-triage")
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.NEEDS_HUMAN_DECISION,
                    redact(provider_result.escalation),
                    pr_number,
                    budget=budget,
                    comment=True,
                )
            if provider_result.status == "BLOCKED_EXTERNAL":
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.BLOCKED_EXTERNAL,
                    redact(provider_result.escalation),
                    pr_number,
                    budget=budget,
                    comment=True,
                )

            actual_files = tuple(sorted(self.git.changed_files()))
            declared_files = tuple(sorted(provider_result.changed_files))
            if actual_files != declared_files or not _paths_allowed(contract, actual_files):
                self._set_lifecycle(contract, "awaiting-triage")
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.NEEDS_HUMAN_DECISION,
                    "provider changed files outside its declared or authorized scope",
                    pr_number,
                    budget=budget,
                    comment=True,
                )

            report: VerificationReport = self.verifier.run_all()
            if not report.passed:
                failed = report.failed_required
                root_cause = "verify:" + ",".join(result.name for result in failed)
                failure_evidence = _verification_evidence(report)
                failure_kind = "verify"
                if budget.record_failure(root_cause) == TerminalState.FAILED_LIMIT:
                    return self._finish(
                        issue_number,
                        state,
                        TerminalState.FAILED_LIMIT,
                        "deterministic verification failed three consecutive times",
                        pr_number,
                        budget=budget,
                        comment=True,
                    )
                self._save_progress(
                    issue_number,
                    state,
                    budget,
                    pr_number,
                    head_sha,
                    failure_evidence,
                    failure_kind,
                    "implementing",
                )
                continue

            if failure_kind in {"verify", "provider"}:
                budget.clear_failure()
            failure_evidence = ""
            failure_kind = ""
            if actual_files:
                head_sha = self.git.commit_and_push(
                    actual_files,
                    f"fix: implement #{issue_number} within approved contract",
                )
            else:
                head_sha = self.git.head_sha()

            if provider_result.status == "CONTINUE":
                self._save_progress(
                    issue_number,
                    state,
                    budget,
                    pr_number,
                    head_sha,
                    "",
                    "",
                    "implementing",
                )
                continue

            if pr_number is None:
                pr = self.gitea.create_pr(
                    issue_number,
                    f"fix: #{issue_number} {contract.title}",
                    contract.branch,
                    "main",
                    _pr_body(contract),
                )
                pr_number = int(pr["number"])
                self._set_lifecycle(contract, "pr-open")

            ci = self.gitea.get_commit_status(head_sha)
            if ci == "success":
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.READY_FOR_REVIEW,
                    "local verification and PR CI passed; final human review is required",
                    pr_number,
                    budget=budget,
                    head_sha=head_sha,
                    comment=True,
                )
            if ci == "pending":
                self._save_progress(
                    issue_number,
                    state,
                    budget,
                    pr_number,
                    head_sha,
                    "",
                    "",
                    "awaiting_ci",
                )
                return ControllerResult(
                    TerminalState.CONTINUE, "PR CI is pending", pr_number
                )

            failure_evidence = "CI failed for commit " + head_sha
            failure_kind = "ci"
            if budget.record_failure("ci") == TerminalState.FAILED_LIMIT:
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.FAILED_LIMIT,
                    "CI failed three consecutive times",
                    pr_number,
                    budget=budget,
                    head_sha=head_sha,
                    comment=True,
                )
            self._save_progress(
                issue_number,
                state,
                budget,
                pr_number,
                head_sha,
                failure_evidence,
                failure_kind,
                "implementing",
            )

    def _revalidate(self, issue_number: int, pr_number: Optional[int]) -> Contract:
        issue = self.gitea.get_issue(issue_number)
        lifecycle = ("pr-open",) if pr_number is not None else ("approved",)
        return load_contract(self.repo, issue, allowed_lifecycle=lifecycle)

    def _provider_request(
        self,
        contract: Contract,
        budget: LoopBudget,
        failure_evidence: str,
        pr_number: Optional[int],
    ) -> dict[str, object]:
        return {
            "issue_number": contract.issue_number,
            "title": contract.title,
            "change_type": contract.change_type,
            "effective_complexity": contract.effective_complexity,
            "contract_effect": contract.contract_effect,
            "risk_flags": list(contract.risk_flags),
            "branch": contract.branch,
            "required_docs": list(contract.required_docs),
            "acceptance_criteria": list(contract.acceptance_criteria),
            "round": budget.rounds,
            "failure_evidence": redact(failure_evidence),
            "pr_number": pr_number,
            "forbidden_actions": [
                "edit governing AGENTS.md",
                "change Issue labels",
                "commit or push",
                "create or merge PR",
                "deploy",
            ],
        }

    def _set_lifecycle(self, contract: Contract, lifecycle: str) -> None:
        labels = {f"type/{contract.change_type}", f"complexity/{contract.effective_complexity}", lifecycle}
        self.gitea.set_labels(contract.issue_number, labels)

    def _contract_failure(
        self,
        issue_number: int,
        state: dict[str, object],
        error: ContractError,
        *,
        budget: Optional[LoopBudget] = None,
    ) -> ControllerResult:
        terminal = TerminalState(error.terminal_state)
        return self._finish(
            issue_number,
            state,
            terminal,
            str(error),
            _optional_int(state.get("pr_number")),
            budget=budget,
            comment=True,
        )

    def _save_progress(
        self,
        issue_number: int,
        state: dict[str, object],
        budget: LoopBudget,
        pr_number: Optional[int],
        head_sha: str,
        failure_evidence: str,
        failure_kind: str,
        stage: str,
    ) -> None:
        state.update(
            {
                "issue": issue_number,
                "terminal": TerminalState.CONTINUE.value,
                "stage": stage,
                "budget": budget.to_dict(),
                "pr_number": pr_number,
                "head_sha": head_sha,
                "failure_evidence": redact(failure_evidence),
                "failure_kind": failure_kind,
            }
        )
        self.state_store.save(issue_number, state)

    def _finish(
        self,
        issue_number: int,
        state: dict[str, object],
        terminal: TerminalState,
        message: str,
        pr_number: Optional[int],
        *,
        budget: Optional[LoopBudget] = None,
        head_sha: str = "",
        comment: bool = False,
    ) -> ControllerResult:
        safe_message = redact(message)
        state.update(
            {
                "issue": issue_number,
                "terminal": terminal.value,
                "message": safe_message,
                "pr_number": pr_number,
            }
        )
        if budget is not None:
            state["budget"] = budget.to_dict()
        if head_sha:
            state["head_sha"] = head_sha
        self.state_store.save(issue_number, state)
        if comment:
            self.gitea.comment(
                issue_number,
                f"🤖 Development Loop: **{terminal.value}**\n\n{safe_message}",
            )
        return ControllerResult(terminal, safe_message, pr_number)


class LocalGit:
    """Git operations owned by the controller inside one isolated worktree."""

    def __init__(self, repo: Path | str, branch: str) -> None:
        self.repo = Path(repo).resolve()
        self.branch = branch
        current = self._run(("git", "branch", "--show-current")).stdout.strip()
        if current != branch:
            raise ProviderError(f"worktree branch must be {branch}, got {current or 'detached'}")

    def changed_files(self) -> tuple[str, ...]:
        tracked = self._run(("git", "diff", "--name-only", "-z", "HEAD")).stdout
        untracked = self._run(
            ("git", "ls-files", "--others", "--exclude-standard", "-z")
        ).stdout
        return tuple(sorted(set(_nul_paths(tracked) + _nul_paths(untracked))))

    def commit_and_push(self, paths: tuple[str, ...], message: str) -> str:
        if paths:
            self._run(("git", "add", "--", *paths))
            staged = subprocess.run(
                ("git", "diff", "--cached", "--quiet"), cwd=self.repo, check=False
            )
            if staged.returncode == 1:
                self._run(("git", "commit", "-m", message))
            elif staged.returncode != 0:
                raise ProviderError("git failed while checking staged changes")
        self._run(("git", "push", "-u", "origin", self.branch))
        return self.head_sha()

    def head_sha(self) -> str:
        return self._run(("git", "rev-parse", "HEAD")).stdout.strip()

    def _run(self, argv: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            argv,
            cwd=self.repo,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise ProviderError(redact(completed.stderr or completed.stdout)[-4000:])
        return completed


def _paths_allowed(contract: Contract, paths: tuple[str, ...]) -> bool:
    protected_small_prefixes = (
        ".gitea/workflows/",
        "codex/",
        "scripts/deploy",
        "scripts/promote",
    )
    protected_small_files = {"CLAUDE.md", ".npmrc", "ecosystem.config.cjs"}
    for path in paths:
        if Path(path).name == "AGENTS.md" or path.startswith(".git/"):
            return False
        if contract.effective_complexity == "small" and (
            path in protected_small_files
            or any(path.startswith(prefix) for prefix in protected_small_prefixes)
        ):
            return False
    return True


def _verification_evidence(report: VerificationReport) -> str:
    sections: list[str] = []
    for result in report.failed_required:
        detail = result.stderr or result.stdout or "no output"
        sections.append(f"{result.name} exit={result.exit_code}: {detail}")
    return redact("\n".join(sections))[-12000:]


def _pr_body(contract: Contract) -> str:
    documents = "\n".join(
        f"- docs/changes/{contract.issue_number}/{name}" for name in contract.required_docs
    )
    return (
        f"Closes #{contract.issue_number}\n\n"
        "Change documents:\n"
        f"{documents}\n\n"
        "Local deterministic verification passed. Final merge requires a human."
    )


def _optional_int(value: object) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _nul_paths(value: str) -> list[str]:
    return [path for path in value.split("\0") if path]
