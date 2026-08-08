from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_loop.contract import ContractError
from aisoft_loop.documents import publish_plan, publish_spec


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
