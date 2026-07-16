import json
from pathlib import Path
import tempfile
import unittest

from aisoft_loop.controller import Controller, ControllerResult
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
        self.commits: list[tuple[tuple[str, ...], str]] = []
        self.pushes = 0
        self.sha_counter = 0

    def changed_files(self) -> tuple[str, ...]:
        return self.changed.pop(0)

    def commit_and_push(self, paths: tuple[str, ...], message: str) -> str:
        self.commits.append((paths, message))
        self.pushes += 1
        self.sha_counter += 1
        return f"abc{self.sha_counter}"

    def head_sha(self) -> str:
        return f"abc{max(self.sha_counter, 1)}"


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

    def get_issue(self, issue_number: int) -> dict:
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

    def test_happy_path_reaches_ready_for_review(self) -> None:
        gitea = FakeGitea(["success"])
        result = self.controller(
            provider=FakeProvider([provider_result()]),
            verifier=FakeVerifier([verification(True)]),
            git=FakeGit([("src/change.txt",)]),
            gitea=gitea,
        ).run(8)
        self.assertEqual(result.terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(result.pr_number, 3)
        self.assertEqual(len(gitea.created_prs), 1)
        self.assertEqual(gitea.label_updates[-1], {"type/bugfix", "complexity/small", "pr-open"})
        self.assertIn("READY_FOR_REVIEW", gitea.comments[-1])

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
