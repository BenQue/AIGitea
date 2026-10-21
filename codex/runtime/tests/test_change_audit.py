from pathlib import Path
import json
import tempfile
import unittest

from aisoft_loop.change_audit import (
    CHECK_DOCUMENTS,
    CHECK_PR_URL,
    audit_change_documents,
)


SUMMARY = """---
issue: 57
gitea_url: http://gitea.example.invalid/admin/demo/issues/57
required_docs:
  - summary
  - spec
documents:
  summary: summary-matt-flow-260808.md
  spec: spec-matt-flow-260808.md
status: approved
branch: change/57-matt-flow
pr_url:
created: 2026-08-08
---

# Summary
"""

SPEC = """---
issue: 57
branch: change/57-matt-flow
created: 2026-08-08
---

# Spec
"""


class ChangeAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.directory = self.repo / "docs" / "changes" / "57-matt-flow"
        self.directory.mkdir(parents=True)
        self.write("summary-matt-flow-260808.md", SUMMARY)
        self.write("spec-matt-flow-260808.md", SPEC)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, name: str, body: str) -> Path:
        path = self.directory / name
        path.write_text(body, encoding="utf-8")
        return path

    def results(self) -> dict[str, tuple[str, ...]]:
        report = audit_change_documents(self.repo)
        return {check.name: check.problems for check in report.checks}

    def test_a_resolvable_change_passes_both_checks(self) -> None:
        report = audit_change_documents(self.repo)
        self.assertTrue(report.ok)
        self.assertEqual(report.change_count, 1)

    def test_missing_front_matter_names_the_change_and_the_file(self) -> None:
        self.write("spec-matt-flow-260808.md", "# Spec without front matter\n")
        problems = self.results()[CHECK_DOCUMENTS]
        self.assertEqual(len(problems), 1)
        # The acceptance criteria ask for the change and the file, not just the
        # generic parser message resolve-documents would surface on its own.
        self.assertIn("57-matt-flow", problems[0])
        self.assertIn("spec-matt-flow-260808.md", problems[0])
        self.assertIn("YAML front matter", problems[0])

    def test_pr_open_without_a_pr_url_is_reported(self) -> None:
        self.write("summary-matt-flow-260808.md", SUMMARY.replace("status: approved", "status: pr-open"))
        results = self.results()
        self.assertEqual(results[CHECK_DOCUMENTS], ())
        self.assertEqual(len(results[CHECK_PR_URL]), 1)
        self.assertIn("57-matt-flow", results[CHECK_PR_URL][0])
        self.assertIn("pr_url", results[CHECK_PR_URL][0])

    def test_pr_open_with_a_pr_url_passes(self) -> None:
        self.write(
            "summary-matt-flow-260808.md",
            SUMMARY.replace("status: approved", "status: pr-open").replace(
                "pr_url:\n",
                "pr_url: http://gitea.example.invalid/admin/demo/pulls/58\n",
            ),
        )
        self.assertTrue(audit_change_documents(self.repo).ok)

    def test_a_pre_pr_status_is_not_asked_for_a_pr_url(self) -> None:
        self.assertEqual(self.results()[CHECK_PR_URL], ())

    def test_one_broken_change_is_reported_once_not_under_both_checks(self) -> None:
        self.write("spec-matt-flow-260808.md", "no front matter\n")
        self.write("summary-matt-flow-260808.md", SUMMARY.replace("status: approved", "status: pr-open"))
        results = self.results()
        self.assertEqual(len(results[CHECK_DOCUMENTS]), 1)
        self.assertEqual(results[CHECK_PR_URL], ())

    def test_an_unparseable_directory_name_is_a_finding_not_a_crash(self) -> None:
        (self.repo / "docs" / "changes" / "not-a-change").mkdir()
        problems = self.results()[CHECK_DOCUMENTS]
        self.assertEqual(len(problems), 1)
        self.assertIn("not-a-change", problems[0])

    def test_the_template_directory_is_skipped(self) -> None:
        template = self.repo / "docs" / "changes" / "_template"
        template.mkdir()
        (template / "spec.md").write_text("# no front matter\n", encoding="utf-8")
        report = audit_change_documents(self.repo)
        self.assertTrue(report.ok)
        self.assertEqual(report.change_count, 1)

    def test_a_checkout_without_changes_is_vacuously_clean(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            report = audit_change_documents(empty)
            self.assertTrue(report.ok)
            self.assertEqual(report.change_count, 0)

    # R12 (#409): a project registers its history with legacy_changes_before in
    # the usage lock; problems below the threshold are LEGACY, not GAP.
    def declare_legacy(self, value: object) -> None:
        lock = self.repo / ".aisoft" / "platform-usage.lock.json"
        lock.parent.mkdir(exist_ok=True)
        lock.write_text(json.dumps({
            "contract_version": "aisoft-usage-lock/v1",
            "bundle_version": "1.9.0",
            "bundle_digest": "sha256:" + "0" * 64,
            "legacy_changes_before": value,
        }), encoding="utf-8")

    def legacy(self) -> dict[str, tuple[str, ...]]:
        report = audit_change_documents(self.repo)
        return {check.name: check.legacy for check in report.checks}

    def legacy_directory(self, name: str, body: str = "# no front matter\n") -> None:
        directory = self.repo / "docs" / "changes" / name
        directory.mkdir()
        (directory / "01-spec.md").write_text(body, encoding="utf-8")

    def test_legacy_threshold_turns_old_problems_into_registrations(self) -> None:
        self.legacy_directory("13")
        self.legacy_directory("0001-board-fixes")
        self.declare_legacy(57)
        report = audit_change_documents(self.repo)
        self.assertTrue(report.ok)
        legacy = self.legacy()[CHECK_DOCUMENTS]
        self.assertEqual(len(legacy), 2)
        self.assertTrue(any(item.startswith("0001-board-fixes") for item in legacy))
        self.assertTrue(any(item.startswith("13/") for item in legacy))

    def test_directories_at_or_above_the_threshold_still_gap(self) -> None:
        self.write("spec-matt-flow-260808.md", "no front matter\n")
        self.declare_legacy(57)
        results = self.results()
        self.assertEqual(len(results[CHECK_DOCUMENTS]), 1)
        self.assertEqual(self.legacy()[CHECK_DOCUMENTS], ())

    def test_a_pr_url_problem_below_the_threshold_is_legacy(self) -> None:
        self.write("summary-matt-flow-260808.md", SUMMARY.replace("status: approved", "status: pr-open"))
        self.declare_legacy(58)
        self.assertTrue(audit_change_documents(self.repo).ok)
        self.assertEqual(len(self.legacy()[CHECK_PR_URL]), 1)

    def test_a_directory_without_a_number_is_never_legacy(self) -> None:
        (self.repo / "docs" / "changes" / "not-a-change").mkdir()
        self.declare_legacy(10_000)
        self.assertEqual(len(self.results()[CHECK_DOCUMENTS]), 1)

    def test_without_a_declaration_old_problems_stay_gaps(self) -> None:
        self.legacy_directory("13")
        self.assertFalse(audit_change_documents(self.repo).ok)
        self.assertEqual(self.legacy()[CHECK_DOCUMENTS], ())

    def test_an_invalid_threshold_is_a_gap_not_a_silent_pass(self) -> None:
        self.legacy_directory("13")
        for value in (0, -1, True, "57", 1.5):
            with self.subTest(value=value):
                self.declare_legacy(value)
                problems = self.results()[CHECK_DOCUMENTS]
                self.assertTrue(any("legacy_changes_before" in item for item in problems))
                self.assertEqual(self.legacy()[CHECK_DOCUMENTS], ())


if __name__ == "__main__":
    unittest.main()
