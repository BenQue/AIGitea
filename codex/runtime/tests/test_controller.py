import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_loop.contract import Contract
from aisoft_loop.controller import (
    Controller,
    ControllerResult,
    LocalGit,
    select_frontier_ticket,
)
from aisoft_loop.provider import ProviderError, ProviderResult
from aisoft_loop.state import GlobalLock, StateStore, TerminalState
from aisoft_loop.verifier import VerificationReport, VerificationResult


SUMMARY = """---
issue: 8
gitea_url: http://gitea.test/owner/repo/issues/8
change_type: bugfix
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: restore existing behavior
risk_flags: []
required_docs:
  - 00-summary.md
confidence: high
override_reason: ''
status: analyzed
branch: change/8
pr_url:
created: 2026-07-16
updated: 2026-07-16
---

## 问题/需求总结

Restore the documented behavior.
"""


def provider_result(
    status: str = "COMPLETE",
    *,
    changed_files: tuple[str, ...] = ("src/change.txt",),
    root_cause: str = "",
    escalation: str = "",
) -> ProviderResult:
    return ProviderResult(
        status=status,
        summary="bounded provider result",
        changed_files=changed_files,
        root_cause=root_cause,
        escalation=escalation,
    )


def verification(passed: bool, name: str = "unit-test") -> VerificationReport:
    return VerificationReport(
        (
            VerificationResult(
                name=name,
                exit_code=0 if passed else 1,
                timed_out=False,
                required=True,
                stdout="ok\n" if passed else "",
                stderr="" if passed else "assertion failed\n",
            ),
        )
    )


class FakeProvider:
    def __init__(self, results: list[ProviderResult]) -> None:
        self.results = list(results)
        self.requests: list[dict[str, object]] = []

    def run(self, request: dict[str, object], worktree: Path) -> ProviderResult:
        self.requests.append(request)
        return self.results.pop(0)


class FakeVerifier:
    def __init__(self, reports: list[VerificationReport]) -> None:
        self.reports = list(reports)
        self.calls = 0

    def run_all(self) -> VerificationReport:
        self.calls += 1
        return self.reports.pop(0)


class FakeGit:
    def __init__(self, changed: list[tuple[str, ...]]) -> None:
        self.changed = list(changed)
        self.validations: list[tuple[str, int, str]] = []
        self.pushes = 0
        self.sha_counter = 0

    def changed_files(self) -> tuple[str, ...]:
        raise AssertionError("controller must validate provider commits, not uncommitted files")

    def commit_and_push(self, paths: tuple[str, ...], message: str) -> str:
        raise AssertionError("controller must not create provider commits")

    def validate_provider_commit(
        self, base_sha: str, issue_number: int, ticket_id: str
    ) -> tuple[str, ...]:
        self.validations.append((base_sha, issue_number, ticket_id))
        files = self.changed.pop(0) if self.changed else ()
        if files:
            self.sha_counter += 1
        return files

    def push(self) -> str:
        self.pushes += 1
        return self.head_sha()

    def head_sha(self) -> str:
        return f"abc{self.sha_counter}"


class FakeGitea:
    def __init__(self, statuses: list[str] | None = None) -> None:
        self.issue = {
            "number": 8,
            "state": "open",
            "title": "Restore behavior",
            "body": (
                "## Acceptance criteria\n\n"
                "- [ ] Existing behavior is restored and the regression test passes."
            ),
            "labels": ["type/bugfix", "complexity/small", "approved"],
        }
        self.statuses = list(statuses or ["success"])
        self.created_prs: list[dict[str, str]] = []
        self.comments: list[str] = []
        self.label_updates: list[set[str]] = []
        self.dependency_issues: dict[int, dict] = {}

    def get_issue(self, issue_number: int) -> dict:
        if issue_number in self.dependency_issues:
            return dict(self.dependency_issues[issue_number])
        return dict(self.issue)

    def create_pr(self, issue_number: int, title: str, head: str, base: str, body: str) -> dict:
        self.created_prs.append(
            {"title": title, "head": head, "base": base, "body": body}
        )
        return {"number": 3, "state": "open"}

    def get_commit_status(self, sha: str) -> str:
        return self.statuses.pop(0)

    def comment(self, issue_number: int, body: str) -> dict:
        self.comments.append(body)
        return {"id": len(self.comments)}

    def set_labels(self, issue_number: int, labels: set[str]) -> None:
        self.label_updates.append(set(labels))
        self.issue["labels"] = sorted(labels)


class ProviderResultTests(unittest.TestCase):
    def test_json_schema_is_exact(self) -> None:
        payload = {
            "status": "COMPLETE",
            "summary": "done",
            "changed_files": ["src/change.txt"],
            "root_cause": "",
            "escalation": "",
        }
        parsed = ProviderResult.from_json(json.dumps(payload))
        self.assertEqual(parsed.changed_files, ("src/change.txt",))
        for mutation in (
            {**payload, "extra": True},
            {**payload, "status": "READY_FOR_REVIEW"},
            {**payload, "changed_files": ["../escape"]},
            {**payload, "changed_files": ["/absolute"]},
            {**payload, "changed_files": [".git/config"]},
            {**payload, "changed_files": ["AGENTS.md"]},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ProviderError):
                ProviderResult.from_json(json.dumps(mutation))


class LocalGitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.git("init", "-b", "change/8")
        self.git("config", "user.name", "AISoft Test")
        self.git("config", "user.email", "test@example.invalid")
        self.repo.joinpath("README.md").write_text("baseline\n")
        self.git("add", "README.md")
        self.git("commit", "-m", "test: baseline")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *args),
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_valid_agent_commit_is_accepted(self) -> None:
        self.repo.joinpath("change.txt").write_text("done\n")
        self.git("add", "change.txt")
        self.git("commit", "-m", "feat: implement #8 T01")
        changed = LocalGit(self.repo, "change/8").validate_provider_commit(
            self.base, 8, "T01"
        )
        self.assertEqual(changed, ("change.txt",))

    def test_uncommitted_or_mislabeled_agent_work_is_rejected(self) -> None:
        local = LocalGit(self.repo, "change/8")
        self.repo.joinpath("change.txt").write_text("dirty\n")
        with self.assertRaisesRegex(ProviderError, "clean worktree"):
            local.validate_provider_commit(self.base, 8, "T01")
        self.git("add", "change.txt")
        self.git("commit", "-m", "feat: missing audit ids")
        with self.assertRaisesRegex(ProviderError, "#8 and T01"):
            local.validate_provider_commit(self.base, 8, "T01")

    def test_committed_secret_is_rejected_before_push(self) -> None:
        self.repo.joinpath("secret.txt").write_text(
            "github_pat_abcdefghijklmnopqrstuvwxyz123456\n"
        )
        self.git("add", "secret.txt")
        self.git("commit", "-m", "test: secret boundary #8 T01")
        with self.assertRaisesRegex(ProviderError, "secret scan"):
            LocalGit(self.repo, "change/8").validate_provider_commit(
                self.base, 8, "T01"
            )


class FrontierTicketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.directory = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def contract(self, plan: str) -> Contract:
        self.directory.joinpath("plan-short-flow-260808.md").write_text(plan)
        return Contract(
            issue_number=57,
            title="Matt workflow",
            change_type="platform",
            effective_complexity="complex",
            contract_effect="change",
            risk_flags=("agent-governance",),
            branch="change/57",
            document_directory=self.directory,
            required_docs=(
                "summary-short-flow-260808.md",
                "spec-short-flow-260808.md",
                "plan-short-flow-260808.md",
            ),
            acceptance_criteria=("bounded",),
            dependencies=(),
        )

    def test_selects_first_unblocked_pending_ticket(self) -> None:
        contract = self.contract(
            """## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | resolver | - | completed |
| T02 | writers | T01 | pending |
| T03 | labels | T02 | pending |
"""
        )
        self.assertEqual(select_frontier_ticket(contract), "T02")

    def test_runtime_completion_advances_without_rewriting_plan(self) -> None:
        contract = self.contract(
            """| Ticket | Blocked by | Status |
|---|---|---|
| T01 | - | pending |
| T02 | T01 | pending |
"""
        )
        self.assertEqual(
            select_frontier_ticket(contract, completed_tickets=("T01",)),
            "T02",
        )

    def test_repair_round_reuses_last_completed_ticket(self) -> None:
        contract = self.contract(
            """| Ticket | Blocked by | Status |
|---|---|---|
| T01 | - | completed |
| T02 | T01 | completed |
"""
        )
        self.assertEqual(select_frontier_ticket(contract, repair=True), "T02")

    def test_new_plan_without_usable_frontier_fails_closed(self) -> None:
        contract = self.contract(
            """| Ticket | Blocked by | Status |
|---|---|---|
| T01 | T02 | pending |
| T02 | T01 | pending |
"""
        )
        with self.assertRaisesRegex(ProviderError, "no unblocked pending frontier"):
            select_frontier_ticket(contract)


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        directory = self.root / "repo" / "docs" / "changes" / "8"
        directory.mkdir(parents=True)
        directory.joinpath("00-summary.md").write_text(SUMMARY)
        self.repo = self.root / "repo"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def controller(
        self,
        *,
        provider: FakeProvider,
        verifier: FakeVerifier,
        git: FakeGit,
        gitea: FakeGitea,
        max_rounds: int = 8,
        max_same_root: int = 3,
    ) -> Controller:
        state_root = self.root / "state"
        return Controller(
            repo=self.repo,
            gitea=gitea,
            provider=provider,
            verifier=verifier,
            git=git,
            state_store=StateStore(state_root),
            lock=GlobalLock(state_root / "loop.lock"),
            max_rounds=max_rounds,
            max_same_root=max_same_root,
        )

    def make_complex_contract(self, gitea: FakeGitea) -> None:
        directory = self.repo / "docs" / "changes" / "8"
        directory.joinpath("00-summary.md").write_text(
            """---
issue: 8
gitea_url: http://gitea.test/owner/repo/issues/8
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: governed workflow change
risk_flags:
  - agent-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
status: approved
branch: change/8
created: 2026-07-16
updated: 2026-07-16
---
"""
        )
        directory.joinpath("01-spec.md").write_text(
            """---
issue: 8
effective_complexity: complex
branch: change/8
---

## Acceptance criteria

- [ ] AC-1 The workflow is deterministic.

## 未决问题

无。
"""
        )
        directory.joinpath("02-plan.md").write_text(
            """---
issue: 8
effective_complexity: complex
branch: change/8
---

## Ticket graph

| Ticket | Blocked by | Status |
|---|---|---|
| T01 | - | pending |
| T02 | T01 | pending |

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -m unittest` |
"""
        )
        gitea.issue["labels"] = ["type/platform", "complexity/complex", "approved"]

    def test_happy_path_reaches_ready_for_review(self) -> None:
        gitea = FakeGitea(["success"])
        provider = FakeProvider([provider_result()])
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(True)]),
            git=FakeGit([("src/change.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(result.pr_number, 3)
        self.assertEqual(len(gitea.created_prs), 1)
        self.assertEqual(gitea.label_updates[-1], {"type/bugfix", "complexity/small", "pr-open"})
        self.assertIn("READY_FOR_REVIEW", gitea.comments[-1])
        self.assertEqual(provider.requests[0]["skill"], "$implement")
        self.assertEqual(provider.requests[0]["ticket_id"], "T01")
        self.assertNotIn("commit", provider.requests[0]["forbidden_actions"])
        self.assertIn("push", provider.requests[0]["forbidden_actions"])

    def test_complex_loop_implements_each_frontier_ticket_before_pr(self) -> None:
        gitea = FakeGitea(["success"])
        self.make_complex_contract(gitea)
        provider = FakeProvider(
            [
                provider_result(changed_files=("src/one.txt",)),
                provider_result(changed_files=("src/two.txt",)),
            ]
        )
        git = FakeGit([("src/one.txt",), ("src/two.txt",)])
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(True), verification(True)]),
            git=git,
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(
            [request["ticket_id"] for request in provider.requests],
            ["T01", "T02"],
        )
        self.assertEqual(git.pushes, 2)
        self.assertEqual(len(gitea.created_prs), 1)

    def test_verifier_failure_is_fed_to_next_provider_turn(self) -> None:
        provider = FakeProvider([provider_result("CONTINUE"), provider_result()])
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(False), verification(True)]),
            git=FakeGit([("src/change.txt",), ("src/change.txt",)]),
            gitea=FakeGitea(["success"]),
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertIn("unit-test", json.dumps(provider.requests[1]))
        self.assertIn("assertion failed", json.dumps(provider.requests[1]))

    def test_scope_expansion_stops_for_human(self) -> None:
        gitea = FakeGitea()
        result = self.controller(
            provider=FakeProvider(
                [
                    provider_result(
                        "NEEDS_HUMAN_DECISION",
                        changed_files=(),
                        escalation="Requested behavior changes the product contract.",
                    )
                ]
            ),
            verifier=FakeVerifier([]),
            git=FakeGit([]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.NEEDS_HUMAN_DECISION)
        self.assertEqual(gitea.created_prs, [])
        self.assertIn("awaiting-triage", gitea.label_updates[-1])

    def test_external_blocker_stops_without_verifier(self) -> None:
        verifier = FakeVerifier([])
        result = self.controller(
            provider=FakeProvider(
                [provider_result("BLOCKED_EXTERNAL", changed_files=(), escalation="service unavailable")]
            ),
            verifier=verifier,
            git=FakeGit([]),
            gitea=FakeGitea(),
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.BLOCKED_EXTERNAL)
        self.assertEqual(verifier.calls, 0)

    def test_third_same_root_failure_reaches_failed_limit(self) -> None:
        provider = FakeProvider([provider_result("CONTINUE")] * 3)
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(False, "unit")] * 3),
            git=FakeGit([("src/change.txt",)] * 3),
            gitea=FakeGitea(),
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.FAILED_LIMIT)
        self.assertEqual(len(provider.requests), 3)

    def test_round_limit_stops_after_configured_turns(self) -> None:
        provider = FakeProvider([provider_result("CONTINUE")] * 2)
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(True)] * 2),
            git=FakeGit([("src/change.txt",)] * 2),
            gitea=FakeGitea(),
            max_rounds=2,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.FAILED_LIMIT)
        self.assertEqual(len(provider.requests), 2)

    def test_ci_failure_is_fed_back_without_creating_second_pr(self) -> None:
        provider = FakeProvider(
            [provider_result(), provider_result(changed_files=("src/fix.txt",))]
        )
        gitea = FakeGitea(["failure", "success"])
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(True), verification(True)]),
            git=FakeGit([("src/change.txt",), ("src/fix.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(len(gitea.created_prs), 1)
        self.assertIn("CI", json.dumps(provider.requests[1]))

    def test_pending_ci_persists_and_next_poll_can_finish(self) -> None:
        provider = FakeProvider([provider_result()])
        verifier = FakeVerifier([verification(True)])
        git = FakeGit([("src/change.txt",)])
        gitea = FakeGitea(["pending", "success"])
        controller = self.controller(
            provider=provider, verifier=verifier, git=git, gitea=gitea
        )
        first = controller.run(8)
        self.assertEqual(first.terminal_state, TerminalState.CONTINUE)
        second = controller.run(8)
        self.assertEqual(second.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(len(provider.requests), 1)

    def test_dependencies_wait_after_ci_without_second_provider_or_pr(self) -> None:
        summary = self.repo / "docs" / "changes" / "8" / "00-summary.md"
        summary.write_text(
            summary.read_text().replace(
                "status: analyzed", "depends_on:\n  - 7\nstatus: analyzed"
            )
        )
        provider = FakeProvider([provider_result()])
        verifier = FakeVerifier([verification(True)])
        git = FakeGit([("src/change.txt",)])
        gitea = FakeGitea(["success", "success"])
        gitea.dependency_issues[7] = {
            "number": 7,
            "state": "closed",
            "labels": ["type/platform", "complexity/complex", "pr-open"],
        }
        controller = self.controller(
            provider=provider, verifier=verifier, git=git, gitea=gitea
        )

        first = controller.run(8)
        self.assertEqual(first.terminal_state, TerminalState.CONTINUE)
        self.assertIn("#7", first.message)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)

        gitea.dependency_issues[7]["labels"] = [
            "type/platform",
            "complexity/complex",
            "deployed",
        ]
        second = controller.run(8)
        self.assertEqual(second.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)

    def test_completed_dependency_is_ready_after_ci(self) -> None:
        summary = self.repo / "docs" / "changes" / "8" / "00-summary.md"
        summary.write_text(
            summary.read_text().replace(
                "status: analyzed", "depends_on:\n  - 7\nstatus: analyzed"
            )
        )
        provider = FakeProvider([provider_result()])
        gitea = FakeGitea(["success"])
        gitea.dependency_issues[7] = {
            "number": 7,
            "state": "closed",
            "labels": ["type/platform", "complexity/complex", "completed"],
        }
        result = self.controller(
            provider=provider,
            verifier=FakeVerifier([verification(True)]),
            git=FakeGit([("src/change.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)

    def test_dependency_must_be_closed_with_delivery_terminal(self) -> None:
        summary = self.repo / "docs" / "changes" / "8" / "00-summary.md"
        summary.write_text(
            summary.read_text().replace(
                "status: analyzed", "depends_on:\n  - 7\nstatus: analyzed"
            )
        )
        gitea = FakeGitea(["success"])
        gitea.dependency_issues[7] = {
            "number": 7,
            "state": "open",
            "labels": ["deployed"],
        }
        result = self.controller(
            provider=FakeProvider([provider_result()]),
            verifier=FakeVerifier([verification(True)]),
            git=FakeGit([("src/change.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.CONTINUE)
        self.assertIn(
            "waiting for completed or deployed dependencies", result.message
        )

    def test_pr_body_renders_dependencies(self) -> None:
        summary = self.repo / "docs" / "changes" / "8" / "00-summary.md"
        summary.write_text(
            summary.read_text().replace(
                "status: analyzed", "depends_on:\n  - 7\nstatus: analyzed"
            )
        )
        gitea = FakeGitea(["pending"])
        self.controller(
            provider=FakeProvider([provider_result()]),
            verifier=FakeVerifier([verification(True)]),
            git=FakeGit([("src/change.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertIn("Dependencies:\n- #7", gitea.created_prs[0]["body"])

    def test_changed_files_must_match_provider_declaration(self) -> None:
        result = self.controller(
            provider=FakeProvider([provider_result(changed_files=("src/claimed.txt",))]),
            verifier=FakeVerifier([]),
            git=FakeGit([("src/actual.txt",)]),
            gitea=FakeGitea(),
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.NEEDS_HUMAN_DECISION)

    def test_controller_surface_has_no_merge_or_deploy_operation(self) -> None:
        self.assertFalse(hasattr(Controller, "merge"))
        self.assertFalse(hasattr(Controller, "deploy"))
        self.assertFalse(hasattr(Controller, "run_production"))


if __name__ == "__main__":
    unittest.main()
