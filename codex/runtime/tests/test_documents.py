from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_loop.contract import ContractError
from aisoft_loop.documents import (
    backfill_pr_number,
    backfill_pr_url,
    publish_plan,
    publish_spec,
)


SUMMARY = """---
issue: 57
documents:
  summary: summary-matt-flow-260808.md
  spec: spec-matt-flow-260808.md
  plan: plan-matt-flow-260808.md
branch: change/57
created: 2026-08-08
---

# Summary
"""

SPEC = """---
issue: 57
branch: change/57
created: 2026-08-08
---

# Spec
"""

PLAN = """---
issue: 57
branch: change/57
created: 2026-08-08
---

# Plan

| Ticket | Blocked by | Status |
|---|---|---|
| T01 | - | pending |
"""


class DocumentPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.git("init", "-b", "change/57")
        self.git("config", "user.name", "AISoft Test")
        self.git("config", "user.email", "test@example.invalid")
        directory = self.repo / "docs" / "changes" / "57"
        directory.mkdir(parents=True)
        directory.joinpath("summary-matt-flow-260808.md").write_text(SUMMARY)
        self.git("add", ".")
        self.git("commit", "-m", "test: baseline")
        self.issue = {"number": 57, "state": "open"}

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

    def test_publishes_to_mapped_spec_and_plan_only(self) -> None:
        spec_path = publish_spec(self.repo, self.issue, SPEC)
        plan_path = publish_plan(self.repo, self.issue, PLAN)
        self.assertEqual(spec_path.name, "spec-matt-flow-260808.md")
        self.assertEqual(plan_path.name, "plan-matt-flow-260808.md")
        self.assertEqual(spec_path.read_text(), SPEC)
        self.assertEqual(plan_path.read_text(), PLAN)

    def test_rejects_wrong_issue_branch_and_front_matter(self) -> None:
        with self.assertRaisesRegex(ContractError, "open Gitea Issue"):
            publish_spec(self.repo, {"number": 57, "state": "closed"}, SPEC)
        self.git("switch", "-c", "wrong-branch")
        with self.assertRaisesRegex(ContractError, "current branch must be change/57"):
            publish_spec(self.repo, self.issue, SPEC)
        self.git("switch", "change/57")
        with self.assertRaisesRegex(ContractError, "front matter issue"):
            publish_spec(self.repo, self.issue, SPEC.replace("issue: 57", "issue: 99"))

    def test_rejects_undeclared_duplicate_and_invalid_plan_graph(self) -> None:
        directory = self.repo / "docs" / "changes" / "57"
        directory.joinpath("spec-other-flow-260808.md").write_text(SPEC)
        with self.assertRaisesRegex(ContractError, "not declared"):
            publish_spec(self.repo, self.issue, SPEC)
        directory.joinpath("spec-other-flow-260808.md").unlink()
        with self.assertRaisesRegex(ContractError, "Ticket graph"):
            publish_plan(self.repo, self.issue, PLAN.replace("| T01 | - | pending |", ""))


if __name__ == "__main__":
    unittest.main()


BACKFILL_SUMMARY = """---
issue: 57
gitea_url: http://gitea.example.invalid/admin/demo/issues/57
documents:
  summary: summary-matt-flow-260808.md
status: approved
branch: change/57-matt-flow
pr_url:
created: 2026-08-08
---

# Summary

正文里出现 pr_url: 这样的字样不得被回填改写。
"""

PULL_URL = "http://gitea.example.invalid/admin/demo/pulls/58"


class BackfillPrUrlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.directory = self.repo / "docs" / "changes" / "57-matt-flow"
        self.directory.mkdir(parents=True)
        self.summary = self.directory / "summary-matt-flow-260808.md"
        self.summary.write_text(BACKFILL_SUMMARY, encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_writes_pr_url_and_advances_status_together(self) -> None:
        path, changed = backfill_pr_url(self.repo, 57, PULL_URL)
        self.assertEqual(path.name, self.summary.name)
        self.assertTrue(changed)
        text = self.summary.read_text(encoding="utf-8")
        self.assertIn(f"pr_url: {PULL_URL}\n", text)
        self.assertIn("status: pr-open\n", text)
        # The prose mention must survive untouched: the write is bounded to the
        # front matter block, not to the first line that happens to match.
        self.assertIn("正文里出现 pr_url: 这样的字样不得被回填改写。", text)

    def test_repeating_the_backfill_produces_no_diff(self) -> None:
        backfill_pr_url(self.repo, 57, PULL_URL)
        before = self.summary.read_bytes()
        path, changed = backfill_pr_url(self.repo, 57, PULL_URL)
        self.assertFalse(changed)
        self.assertEqual(self.summary.read_bytes(), before)

    def test_a_different_pr_url_is_refused_without_writing(self) -> None:
        backfill_pr_url(self.repo, 57, PULL_URL)
        before = self.summary.read_bytes()
        with self.assertRaises(ContractError):
            backfill_pr_url(
                self.repo, 57, "http://gitea.example.invalid/admin/demo/pulls/99"
            )
        self.assertEqual(self.summary.read_bytes(), before)

    def test_a_quoted_empty_pr_url_is_treated_as_empty(self) -> None:
        """`pr_url: ''` is empty to every reader here, so it is empty to the writer.

        The template spells one of its own empty keys `override_reason: ''`, so
        the quoted form reaches summaries by being copied from the template
        itself. Refusing it as "a different pr_url" named a second pull request
        that never existed (#186).
        """
        for empty in ("''", '""'):
            with self.subTest(empty=empty):
                self.summary.write_text(
                    BACKFILL_SUMMARY.replace("pr_url:\n", f"pr_url: {empty}\n"),
                    encoding="utf-8",
                )
                path, changed = backfill_pr_url(self.repo, 57, PULL_URL)
                self.assertTrue(changed)
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"pr_url: {PULL_URL}\n", text)
                self.assertIn("status: pr-open\n", text)

    def test_a_quoted_conflicting_pr_url_is_still_refused(self) -> None:
        """Widening what counts as empty must not widen what counts as absent (#142)."""
        other = "http://gitea.example.invalid/admin/demo/pulls/99"
        self.summary.write_text(
            BACKFILL_SUMMARY.replace("pr_url:\n", f"pr_url: '{other}'\n"),
            encoding="utf-8",
        )
        before = self.summary.read_bytes()
        with self.assertRaisesRegex(
            ContractError, "already declares a different pr_url"
        ):
            backfill_pr_url(self.repo, 57, PULL_URL)
        self.assertEqual(self.summary.read_bytes(), before)

    def test_a_quoted_correct_pr_url_is_already_in_place(self) -> None:
        """Idempotence follows the value, not its spelling: nothing is written."""
        self.summary.write_text(
            BACKFILL_SUMMARY.replace(
                "pr_url:\n", f"pr_url: '{PULL_URL}'\n"
            ).replace("status: approved", "status: pr-open"),
            encoding="utf-8",
        )
        before = self.summary.read_bytes()
        _, changed = backfill_pr_url(self.repo, 57, PULL_URL)
        self.assertFalse(changed)
        self.assertEqual(self.summary.read_bytes(), before)

    def test_a_terminal_status_is_not_downgraded(self) -> None:
        self.summary.write_text(
            BACKFILL_SUMMARY.replace("status: approved", "status: deployed"),
            encoding="utf-8",
        )
        backfill_pr_url(self.repo, 57, PULL_URL)
        text = self.summary.read_text(encoding="utf-8")
        self.assertIn("status: deployed\n", text)
        self.assertIn(f"pr_url: {PULL_URL}\n", text)

    def test_a_url_from_another_repository_is_refused(self) -> None:
        with self.assertRaises(ContractError):
            backfill_pr_url(
                self.repo, 57, "http://gitea.example.invalid/admin/other/pulls/58"
            )

    def test_a_url_that_is_not_a_pull_request_is_refused(self) -> None:
        for rejected in (
            "http://gitea.example.invalid/admin/demo/issues/58",
            "http://gitea.example.invalid/admin/demo/pulls/0",
            "http://gitea.example.invalid/admin/demo/pulls/58/files",
            "not-a-url",
        ):
            with self.subTest(rejected=rejected):
                with self.assertRaises(ContractError):
                    backfill_pr_url(self.repo, 57, rejected)

    def test_a_summary_without_gitea_url_is_refused(self) -> None:
        self.summary.write_text(
            BACKFILL_SUMMARY.replace(
                "gitea_url: http://gitea.example.invalid/admin/demo/issues/57\n", ""
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ContractError):
            backfill_pr_url(self.repo, 57, PULL_URL)

    def test_a_summary_without_the_pr_url_key_is_refused(self) -> None:
        self.summary.write_text(
            BACKFILL_SUMMARY.replace("pr_url:\n", ""), encoding="utf-8"
        )
        with self.assertRaises(ContractError):
            backfill_pr_url(self.repo, 57, PULL_URL)


class BackfillPrNumberTests(unittest.TestCase):
    """The Controller reaches the backfill with a number, not a URL (#146)."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        directory = self.repo / "docs" / "changes" / "57-matt-flow"
        directory.mkdir(parents=True)
        self.summary = directory / "summary-matt-flow-260808.md"
        self.summary.write_text(BACKFILL_SUMMARY, encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_derives_the_url_from_the_summary_gitea_url(self) -> None:
        _, changed = backfill_pr_number(self.repo, 57, 58)
        self.assertTrue(changed)
        self.assertIn(f"pr_url: {PULL_URL}\n", self.summary.read_text(encoding="utf-8"))

    def test_is_idempotent_like_the_url_form(self) -> None:
        backfill_pr_number(self.repo, 57, 58)
        before = self.summary.read_bytes()
        _, changed = backfill_pr_number(self.repo, 57, 58)
        self.assertFalse(changed)
        self.assertEqual(self.summary.read_bytes(), before)

    def test_a_second_pr_number_is_refused(self) -> None:
        backfill_pr_number(self.repo, 57, 58)
        with self.assertRaises(ContractError):
            backfill_pr_number(self.repo, 57, 99)

    def test_a_nonpositive_number_is_refused(self) -> None:
        for rejected in (0, -1, True):
            with self.subTest(rejected=rejected):
                with self.assertRaises(ContractError):
                    backfill_pr_number(self.repo, 57, rejected)
