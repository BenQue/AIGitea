"""Deterministic outer Development Loop controller."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Optional, Sequence

from .contract import (
    DELIVERY_TERMINAL_LABELS,
    Contract,
    ContractError,
    load_contract,
)
from .documents import backfill_pr_number
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
        change_control: str = "production",
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
        # 交付阶段由调用方从 governance manifest 解析后传入；
        # 缺省 production，保证未接线的调用方仍走既有四份文档要求。
        self.change_control = change_control

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

        if pr_number and state.get("stage") in {"awaiting_ci", "awaiting_dependencies"}:
            ci = self.gitea.get_commit_status(head_sha)
            if ci == "success":
                waiting = self._unsatisfied_dependencies(contract)
                if waiting:
                    self._save_progress(
                        issue_number,
                        state,
                        budget,
                        pr_number,
                        head_sha,
                        "",
                        "",
                        "awaiting_dependencies",
                    )
                    return ControllerResult(
                        TerminalState.CONTINUE,
                        "PR CI passed; waiting for completed or deployed dependencies: "
                        + ", ".join(f"#{number}" for number in waiting),
                        pr_number,
                    )
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

            try:
                request = self._provider_request(
                    contract,
                    budget,
                    failure_evidence,
                    pr_number,
                    tuple(str(item) for item in state.get("completed_tickets", [])),
                )
            except ProviderError as exc:
                self._set_lifecycle(contract, "awaiting-triage")
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.NEEDS_HUMAN_DECISION,
                    redact(str(exc)),
                    pr_number,
                    budget=budget,
                    comment=True,
                )
            provider_base_sha = self.git.head_sha()
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

            ticket_id = str(request["ticket_id"])
            try:
                actual_files = tuple(
                    sorted(
                        self.git.validate_provider_commit(
                            provider_base_sha,
                            issue_number,
                            ticket_id,
                        )
                    )
                )
            except ProviderError as exc:
                self._set_lifecycle(contract, "awaiting-triage")
                return self._finish(
                    issue_number,
                    state,
                    TerminalState.NEEDS_HUMAN_DECISION,
                    redact(str(exc)),
                    pr_number,
                    budget=budget,
                    comment=True,
                )
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
                head_sha = self.git.push()
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

            completed_tickets = {
                str(item) for item in state.get("completed_tickets", [])
            }
            completed_tickets.add(ticket_id)
            state["completed_tickets"] = sorted(completed_tickets)
            if contract.effective_complexity == "complex":
                try:
                    select_frontier_ticket(
                        contract,
                        completed_tickets=tuple(completed_tickets),
                    )
                except ProviderError as exc:
                    if "no pending ticket" not in str(exc):
                        self._set_lifecycle(contract, "awaiting-triage")
                        return self._finish(
                            issue_number,
                            state,
                            TerminalState.NEEDS_HUMAN_DECISION,
                            redact(str(exc)),
                            pr_number,
                            budget=budget,
                            comment=True,
                        )
                else:
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
                # The one place where the PR number exists and nothing has to
                # wait for it (#146). Before this, the Loop path left pr_url
                # empty forever: #142 made the backfill a deterministic command
                # but only the interactive path ever called it, and the audit it
                # added cannot see the gap because the summary's status stays at
                # approved. Writing it here also updates that status, so the
                # Gitea label and the document stop disagreeing.
                try:
                    summary_path, backfilled = backfill_pr_number(
                        self.repo, issue_number, pr_number
                    )
                    if backfilled:
                        relative = summary_path.relative_to(
                            Path(self.repo).resolve()
                        ).as_posix()
                        self.git.commit_paths(
                            (relative,),
                            f"docs(change-{issue_number}): "
                            f"回填 pr_url {pr_number} (#{issue_number})",
                        )
                        # head_sha moves with it, so the CI evidence this run
                        # records covers the branch's real HEAD. Until now the
                        # Loop declared READY_FOR_REVIEW against a commit that a
                        # later manual backfill would supersede.
                        head_sha = self.git.push()
                except (ContractError, ProviderError) as exc:
                    self._set_lifecycle(contract, "awaiting-triage")
                    return self._finish(
                        issue_number,
                        state,
                        TerminalState.NEEDS_HUMAN_DECISION,
                        redact(str(exc)),
                        pr_number,
                        budget=budget,
                        head_sha=head_sha,
                        comment=True,
                    )

            ci = self.gitea.get_commit_status(head_sha)
            if ci == "success":
                waiting = self._unsatisfied_dependencies(contract)
                if waiting:
                    self._save_progress(
                        issue_number,
                        state,
                        budget,
                        pr_number,
                        head_sha,
                        "",
                        "",
                        "awaiting_dependencies",
                    )
                    return ControllerResult(
                        TerminalState.CONTINUE,
                        "local verification and PR CI passed; waiting for completed or deployed dependencies: "
                        + ", ".join(f"#{number}" for number in waiting),
                        pr_number,
                    )
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
        return load_contract(
            self.repo,
            issue,
            allowed_lifecycle=lifecycle,
            change_control=self.change_control,
        )

    def _provider_request(
        self,
        contract: Contract,
        budget: LoopBudget,
        failure_evidence: str,
        pr_number: Optional[int],
        completed_tickets: tuple[str, ...] = (),
    ) -> dict[str, object]:
        ticket_id = select_frontier_ticket(
            contract,
            repair=bool(failure_evidence),
            completed_tickets=completed_tickets,
        )
        document_root = contract.document_directory.relative_to(self.repo).as_posix()
        document_paths = [f"{document_root}/{name}" for name in contract.required_docs]
        return {
            "skill": "$implement",
            "ticket_id": ticket_id,
            "prompt": (
                f"$implement Issue #{contract.issue_number} ticket {ticket_id} using "
                + ", ".join(document_paths)
                + f". Commit only to {contract.branch}; do not push, open or merge a PR, or deploy."
            ),
            "issue_number": contract.issue_number,
            "title": contract.title,
            "change_type": contract.change_type,
            "effective_complexity": contract.effective_complexity,
            "contract_effect": contract.contract_effect,
            "risk_flags": list(contract.risk_flags),
            "branch": contract.branch,
            "required_docs": list(contract.required_docs),
            "acceptance_criteria": list(contract.acceptance_criteria),
            "dependencies": list(contract.dependencies),
            "round": budget.rounds,
            "failure_evidence": redact(failure_evidence),
            "pr_number": pr_number,
            "forbidden_actions": [
                "edit governing AGENTS.md",
                "change Issue labels",
                "push",
                "create or merge PR",
                "deploy",
            ],
            "commit_requirements": [
                f"commit only on {contract.branch}",
                f"include #{contract.issue_number} and {ticket_id} in every commit subject",
                "leave the worktree clean",
            ],
        }


    def _set_lifecycle(self, contract: Contract, lifecycle: str) -> None:
        labels = {f"type/{contract.change_type}", f"complexity/{contract.effective_complexity}", lifecycle}
        self.gitea.set_labels(contract.issue_number, labels)

    def _unsatisfied_dependencies(self, contract: Contract) -> tuple[int, ...]:
        waiting: list[int] = []
        for dependency in contract.dependencies:
            issue = self.gitea.get_issue(dependency)
            labels = {
                str(item.get("name")) if isinstance(item, dict) else str(item)
                for item in issue.get("labels", [])
            }
            if issue.get("state") != "closed" or not (
                labels & DELIVERY_TERMINAL_LABELS
            ):
                waiting.append(dependency)
        return tuple(waiting)

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

    def validate_provider_commit(
        self, base_sha: str, issue_number: int, ticket_id: str
    ) -> tuple[str, ...]:
        current = self._run(("git", "branch", "--show-current")).stdout.strip()
        if current != self.branch:
            raise ProviderError(
                f"provider left the worktree on {current or 'detached'}, expected {self.branch}"
            )
        if self._run(("git", "status", "--porcelain")).stdout:
            raise ProviderError("provider must leave a clean worktree after committing")
        if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", base_sha):
            raise ProviderError("provider base SHA is invalid")
        ancestry = subprocess.run(
            ("git", "merge-base", "--is-ancestor", base_sha, "HEAD"),
            cwd=self.repo,
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
        if ancestry.returncode != 0:
            raise ProviderError("provider rewrote or replaced the approved branch history")
        if self.head_sha() == base_sha:
            return ()
        history = self._run(("git", "rev-list", "--parents", f"{base_sha}..HEAD")).stdout
        for line in history.splitlines():
            if len(line.split()) > 2:
                raise ProviderError("provider commits must not contain merge commits")
        subjects = self._run(("git", "log", "--format=%s", f"{base_sha}..HEAD")).stdout
        for subject in subjects.splitlines():
            if f"#{issue_number}" not in subject or ticket_id not in subject:
                raise ProviderError(
                    f"every provider commit subject must contain #{issue_number} and {ticket_id}"
                )
        patch = self._run(
            ("git", "diff", "--no-ext-diff", "--unified=0", base_sha, "HEAD", "--")
        ).stdout
        additions = "\n".join(
            line[1:]
            for line in patch.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        if re.search(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            r"|\bghp_[A-Za-z0-9]{20,}\b"
            r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
            r"|\bsk-[A-Za-z0-9]{20,}\b",
            additions,
        ):
            raise ProviderError("provider commit failed the built-in secret scan")
        changed = self._run(
            ("git", "diff", "--name-only", "-z", base_sha, "HEAD")
        ).stdout
        return tuple(sorted(set(_nul_paths(changed))))

    def commit_paths(self, paths: Sequence[str], subject: str) -> str:
        """Commit exactly these paths, refusing a worktree that holds anything else.

        This is the Controller's own commit path (#146) — until now every commit
        on a change branch came from the provider and was checked by
        validate_provider_commit. "Exactly equal" rather than "contains" is what
        keeps that true: a method that could sweep up whatever else happens to be
        in the worktree would be an unguarded door next to that check. Something
        unexpected being present is itself the anomaly, so it stops the run.
        """
        declared = set(paths)
        if not declared:
            raise ProviderError("controller commit must declare at least one path")
        changed = {
            line[3:].strip().strip('"')
            for line in self._run(("git", "status", "--porcelain")).stdout.splitlines()
            if line.strip()
        }
        if changed != declared:
            raise ProviderError(
                "controller commit must change exactly its declared paths, found: "
                + ", ".join(sorted(changed) or ["nothing"])
            )
        self._run(("git", "add", "--", *sorted(declared)))
        self._run(("git", "commit", "-m", subject))
        return self.head_sha()

    def push(self) -> str:
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


def select_frontier_ticket(
    contract: Contract,
    *,
    repair: bool = False,
    completed_tickets: tuple[str, ...] = (),
) -> str:
    """Select the first unblocked pending ticket from a complex plan.

    Legacy plans predate ticket graphs and keep the historical T01 fallback.
    New plans fail closed when their graph is absent, malformed, or blocked.
    A repair round may return the last completed ticket so CI or verification
    fixes remain attached to an existing audit identifier.
    """
    if contract.effective_complexity != "complex":
        return "T01"

    plan_names = [
        name
        for name in contract.required_docs
        if name == "02-plan.md" or name.startswith("plan-")
    ]
    if len(plan_names) != 1:
        raise ProviderError("complex contract must resolve exactly one plan document")
    plan_name = plan_names[0]
    plan_text = contract.document_directory.joinpath(plan_name).read_text(
        encoding="utf-8"
    )
    graph = _ticket_graph(plan_text)
    if not graph:
        if plan_name == "02-plan.md":
            return "T01"
        raise ProviderError("new plan must contain a valid Ticket graph table")

    completed = {
        ticket_id
        for ticket_id, _, status in graph
        if status in {"complete", "completed", "done"}
    } | set(completed_tickets)
    known = {row[0] for row in graph}
    unknown_completed = completed - known
    if unknown_completed:
        raise ProviderError(
            "completed ticket state is not declared by the plan: "
            + ", ".join(sorted(unknown_completed))
        )
    pending = [
        (ticket_id, blockers)
        for ticket_id, blockers, status in graph
        if ticket_id not in completed
        and status in {"pending", "ready", "in-progress", "in_progress", "implementing"}
    ]
    for ticket_id, blockers in pending:
        if all(blocker in completed for blocker in blockers):
            return ticket_id

    if repair and len(completed) == len(graph):
        return graph[-1][0]
    if pending:
        raise ProviderError("Ticket graph has no unblocked pending frontier")
    raise ProviderError("Ticket graph has no pending ticket")


def _ticket_graph(plan_text: str) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    lines = plan_text.splitlines()
    for index, line in enumerate(lines):
        headers = _table_cells(line)
        normalized = [cell.lower().replace("_", " ") for cell in headers]
        if not {"ticket", "blocked by", "status"}.issubset(normalized):
            continue
        if index + 1 >= len(lines) or not _is_table_separator(lines[index + 1]):
            continue
        ticket_index = normalized.index("ticket")
        blockers_index = normalized.index("blocked by")
        status_index = normalized.index("status")
        rows: list[tuple[str, tuple[str, ...], str]] = []
        for row_line in lines[index + 2 :]:
            cells = _table_cells(row_line)
            if not cells:
                break
            if max(ticket_index, blockers_index, status_index) >= len(cells):
                return ()
            ticket_id = cells[ticket_index].strip().upper()
            if not re.fullmatch(r"T\d{2,}", ticket_id):
                return ()
            blockers_text = cells[blockers_index].strip()
            blockers = tuple(
                match.upper()
                for match in re.findall(r"T\d{2,}", blockers_text, re.IGNORECASE)
            )
            if blockers_text not in {"", "-", "none", "None"} and not blockers:
                return ()
            rows.append((ticket_id, blockers, cells[status_index].strip().lower()))
        if len({row[0] for row in rows}) != len(rows):
            return ()
        known = {row[0] for row in rows}
        if any(blocker not in known for _, blockers, _ in rows for blocker in blockers):
            return ()
        return tuple(rows)
    return ()


def _table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


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
    document_root = contract.document_directory.parts[-3:]
    document_prefix = "/".join(document_root)
    documents = "\n".join(
        f"- {document_prefix}/{name}" for name in contract.required_docs
    )
    dependencies = (
        "\n".join(f"- #{number}" for number in contract.dependencies)
        if contract.dependencies
        else "- None"
    )
    return (
        f"Closes #{contract.issue_number}\n\n"
        "Dependencies:\n"
        f"{dependencies}\n\n"
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
