"""Provider parity: Codex and Claude must share one controller and one boundary."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from aisoft_loop.cli import main, select_provider_script
from aisoft_loop.controller import Controller
from aisoft_loop.provider import CommandProvider, ProviderError
from aisoft_loop.state import GlobalLock, StateStore, TerminalState

from test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification


PROVIDERS = ("codex", "claude")

STUB = """#!/usr/bin/env python3
import json
from pathlib import Path
import sys

request_path, result_path, worktree = sys.argv[1], sys.argv[2], sys.argv[3]
queue = Path(worktree) / ".parity-queue"
pending = [line for line in queue.read_text().splitlines() if line.strip()]
queue.write_text("\\n".join(pending[1:]))
Path(result_path).write_text(pending[0])
"""

ENV_STUB = """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

Path(sys.argv[2]).write_text(
    json.dumps(
        {
            "status": "COMPLETE",
            "summary": " ".join(sorted(os.environ)),
            "changed_files": [],
            "root_cause": "",
            "escalation": "",
        }
    )
)
"""

LEAKY_STUB = """#!/usr/bin/env python3
import sys

print("GITEA_TOKEN=abcdef0123456789abcdef0123456789abcdef01", file=sys.stderr)
sys.exit(1)
"""


def write_script(path: Path, body: str) -> Path:
    path.write_text(body)
    path.chmod(0o755)
    return path


def result_line(
    status: str = "COMPLETE",
    *,
    changed_files: tuple[str, ...] = ("src/change.txt",),
    escalation: str = "",
) -> str:
    return json.dumps(
        {
            "status": status,
            "summary": "bounded provider turn",
            "changed_files": list(changed_files),
            "root_cause": "",
            "escalation": escalation,
        }
    )


class ProviderSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.agent = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_each_provider_selects_its_own_adapter(self) -> None:
        for name in PROVIDERS:
            with self.subTest(provider=name):
                script = select_provider_script({"IMPLEMENT_PROVIDER": name}, self.agent)
                self.assertEqual(script, (self.agent / f"{name}-provider.sh").resolve())

    def test_disabled_provider_is_rejected(self) -> None:
        for env in ({"IMPLEMENT_PROVIDER": "none"}, {}):
            with self.subTest(env=env), self.assertRaises(ProviderError):
                select_provider_script(env, self.agent)

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaises(ProviderError):
            select_provider_script({"IMPLEMENT_PROVIDER": "gpt"}, self.agent)

    def test_explicit_script_override_is_honoured_per_provider(self) -> None:
        for name in PROVIDERS:
            with self.subTest(provider=name):
                override = write_script(self.agent / f"custom-{name}", STUB)
                script = select_provider_script(
                    {
                        "IMPLEMENT_PROVIDER": name,
                        f"{name.upper()}_PROVIDER_SCRIPT": str(override),
                    },
                    self.agent,
                )
                self.assertEqual(script, override.resolve())


class ProviderEnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.script = write_script(self.root / "env-provider.sh", ENV_STUB)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_provider(self) -> str:
        provider = CommandProvider((str(self.script),))
        return provider.run({"issue_number": 8}, self.root).summary

    def test_each_provider_model_variable_is_forwarded(self) -> None:
        for name in ("CODEX_MODEL", "CLAUDE_MODEL"):
            with self.subTest(variable=name):
                os.environ[name] = "test-model"
                self.addCleanup(os.environ.pop, name, None)
                self.assertIn(name, self.run_provider().split())

    def test_credentials_are_never_forwarded_to_a_provider(self) -> None:
        for name in ("GITEA_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"):
            with self.subTest(variable=name):
                os.environ[name] = "secret-value"
                self.addCleanup(os.environ.pop, name, None)
                self.assertNotIn(name, self.run_provider().split())


class ProviderRoutingTests(unittest.TestCase):
    """`aisoft-loop run` must honour the selected provider, never assume one."""

    def run_cli(self, provider: str) -> tuple[int, str]:
        environment = {
            "GITEA_URL": "http://gitea.test:3000",
            "GITEA_OWNER": "owner",
            "GITEA_REPO": "repo",
            "GITEA_TOKEN": "not-a-real-token",
            "IMPLEMENT_PROVIDER": provider,
        }
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as name:
            with mock.patch.dict(os.environ, environment, clear=False):
                os.environ.pop("CODEX_PROVIDER_SCRIPT", None)
                os.environ.pop("CLAUDE_PROVIDER_SCRIPT", None)
                with contextlib.redirect_stdout(stdout):
                    code = main(["run", "8", "--repo", name])
        return code, stdout.getvalue()

    def test_disabled_provider_never_silently_falls_back_to_codex(self) -> None:
        code, output = self.run_cli("none")
        self.assertEqual(code, 2)
        self.assertIn("implementation provider is disabled", output)

    def test_unknown_provider_is_reported_not_defaulted(self) -> None:
        code, output = self.run_cli("gpt")
        self.assertEqual(code, 2)
        self.assertIn("unsupported implementation provider", output)


class ProviderBoundaryTests(unittest.TestCase):
    def test_provider_failure_output_is_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            script = write_script(root / "leaky-provider.sh", LEAKY_STUB)
            with self.assertRaises(ProviderError) as caught:
                CommandProvider((str(script),)).run({}, root)
        message = str(caught.exception)
        self.assertIn("[REDACTED]", message)
        self.assertNotIn("abcdef0123456789abcdef0123456789abcdef01", message)


class ProviderParityMatrixTests(unittest.TestCase):
    """The same scenario must reach the same terminal state on either provider."""

    def outcome(
        self,
        provider_name: str,
        *,
        results: list[str],
        verifications: list,
        changed: list[tuple[str, ...]],
        statuses: list[str],
        max_rounds: int = 8,
    ) -> tuple[TerminalState, list[dict]]:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = root / "repo"
            (repo / "docs" / "changes" / "8").mkdir(parents=True)
            (repo / "docs" / "changes" / "8" / "00-summary.md").write_text(SUMMARY)
            (repo / ".parity-queue").write_text("\n".join(results))

            agent = root / "agent"
            agent.mkdir()
            write_script(agent / f"{provider_name}-provider.sh", STUB)
            script = select_provider_script({"IMPLEMENT_PROVIDER": provider_name}, agent)

            gitea = FakeGitea(statuses)
            state_root = root / "state"
            controller = Controller(
                repo=repo,
                gitea=gitea,
                provider=CommandProvider((str(script),)),
                verifier=FakeVerifier(verifications),
                git=FakeGit(changed),
                state_store=StateStore(state_root),
                lock=GlobalLock(state_root / "loop.lock"),
                max_rounds=max_rounds,
            )
            return controller.run(8).terminal_state, gitea.created_prs

    def assert_parity(self, expected: TerminalState, **scenario) -> None:
        outcomes = {name: self.outcome(name, **scenario) for name in PROVIDERS}
        for name, (terminal, _) in outcomes.items():
            with self.subTest(provider=name):
                self.assertEqual(terminal, expected)
        self.assertEqual(outcomes["codex"][0], outcomes["claude"][0])

    def test_success_reaches_ready_for_review_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.READY_FOR_REVIEW,
            results=[result_line()],
            verifications=[verification(True)],
            changed=[("src/change.txt",)],
            statuses=["success"],
        )

    def test_verifier_feedback_recovers_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.READY_FOR_REVIEW,
            results=[result_line("CONTINUE"), result_line()],
            verifications=[verification(False), verification(True)],
            changed=[("src/change.txt",), ("src/change.txt",)],
            statuses=["success"],
        )

    def test_ci_feedback_recovers_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.READY_FOR_REVIEW,
            results=[result_line(), result_line(changed_files=("src/fix.txt",))],
            verifications=[verification(True), verification(True)],
            changed=[("src/change.txt",), ("src/fix.txt",)],
            statuses=["failure", "success"],
        )

    def test_scope_expansion_stops_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.NEEDS_HUMAN_DECISION,
            results=[
                result_line(
                    "NEEDS_HUMAN_DECISION",
                    changed_files=(),
                    escalation="the request changes the product contract",
                )
            ],
            verifications=[],
            changed=[],
            statuses=[],
        )

    def test_external_blocker_stops_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.BLOCKED_EXTERNAL,
            results=[
                result_line("BLOCKED_EXTERNAL", changed_files=(), escalation="service is down")
            ],
            verifications=[],
            changed=[],
            statuses=[],
        )

    def test_repeated_root_cause_limit_stops_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.FAILED_LIMIT,
            results=[result_line("CONTINUE")] * 3,
            verifications=[verification(False, "unit")] * 3,
            changed=[("src/change.txt",)] * 3,
            statuses=[],
        )

    def test_round_limit_stops_on_both_providers(self) -> None:
        self.assert_parity(
            TerminalState.FAILED_LIMIT,
            results=[result_line("CONTINUE")] * 2,
            verifications=[verification(True)] * 2,
            changed=[("src/change.txt",)] * 2,
            statuses=[],
            max_rounds=2,
        )

    def test_no_provider_can_merge_or_deploy(self) -> None:
        for name in PROVIDERS:
            with self.subTest(provider=name):
                _, created = self.outcome(
                    name,
                    results=[result_line()],
                    verifications=[verification(True)],
                    changed=[("src/change.txt",)],
                    statuses=["success"],
                )
                self.assertEqual(len(created), 1)
        for forbidden in ("merge", "deploy", "merge_pr", "run_production"):
            with self.subTest(operation=forbidden):
                self.assertFalse(hasattr(FakeGitea, forbidden))
                self.assertFalse(hasattr(CommandProvider, forbidden))


if __name__ == "__main__":
    unittest.main()
