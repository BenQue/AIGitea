from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_loop.contract import ContractError, load_contract, resolve_documents


SUMMARY = """---
issue: {number}
gitea_url: http://gitea.test/owner/repo/issues/{number}
change_type: {change_type}
requested_complexity: auto
assessed_complexity: {complexity}
effective_complexity: {complexity}
contract_effect: {effect}
reason: contract evidence
risk_flags: {risk_flags}
required_docs:
{required_docs}
confidence: high
override_reason: ''
status: analyzed
branch: {branch}
pr_url:
created: 2026-07-16
updated: 2026-07-16
---

## 问题/需求总结

Bounded change.
"""

SPEC = """---
issue: {number}
change_type: feature
effective_complexity: complex
branch: change/{number}
---

# Spec

## Acceptance criteria

- [ ] AC-1 Observable result is verified by a command.

## 未决问题

无。
"""

PLAN = """---
issue: {number}
change_type: feature
effective_complexity: complex
branch: change/{number}
---

# Implementation plan

## 任务分解

1. Make the bounded change.

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -m unittest` |
"""

NEW_SUMMARY = """---
issue: {number}
gitea_url: http://gitea.test/owner/repo/issues/{number}
change_type: {change_type}
requested_complexity: auto
assessed_complexity: {complexity}
effective_complexity: {complexity}
contract_effect: {effect}
reason: contract evidence
risk_flags: {risk_flags}
required_docs:
{required_docs}
documents:
{documents}
confidence: high
override_reason: ''
status: analyzed
branch: {branch}
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Bounded change.
"""


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        subprocess.run(("git", "init", "-q", "-b", "main"), cwd=self.repo, check=True)
        subprocess.run(("git", "config", "user.name", "AISoft Test"), cwd=self.repo, check=True)
        subprocess.run(("git", "config", "user.email", "test@example.invalid"), cwd=self.repo, check=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def issue(self, number: int = 12, *, labels: list[str] | None = None, body: str | None = None) -> dict:
        return {
            "number": number,
            "state": "open",
            "title": "Bounded test change",
            "body": body
            or "## Acceptance criteria\n\n- [ ] Existing behavior is restored and the regression test passes.",
            "labels": labels
            or ["type/bugfix", "complexity/small", "approved"],
        }

    def write_contract(
        self,
        *,
        number: int = 12,
        complexity: str = "small",
        change_type: str = "bugfix",
        effect: str = "restore",
        risk_flags: str = "[]",
        branch: str | None = None,
        spec: bool = False,
        plan: bool = False,
        depends_on: str | None = None,
    ) -> Path:
        directory = self.repo / "docs" / "changes" / str(number)
        directory.mkdir(parents=True)
        required = ["  - 00-summary.md"]
        if complexity == "complex":
            required.extend(("  - 01-spec.md", "  - 02-plan.md"))
        summary = SUMMARY.format(
                number=number,
                complexity=complexity,
                change_type=change_type,
                effect=effect,
                risk_flags=risk_flags,
                required_docs="\n".join(required),
                branch=branch or f"change/{number}",
            )
        if depends_on is not None:
            summary = summary.replace(
                "status: analyzed", f"depends_on: {depends_on}\nstatus: analyzed"
            )
        directory.joinpath("00-summary.md").write_text(summary)
        if spec:
            directory.joinpath("01-spec.md").write_text(SPEC.format(number=number))
        if plan:
            directory.joinpath("02-plan.md").write_text(PLAN.format(number=number))
        subprocess.run(("git", "add", directory.relative_to(self.repo)), cwd=self.repo, check=True)
        subprocess.run(
            ("git", "commit", "-q", "-m", f"test: legacy Issue {number} evidence"),
            cwd=self.repo,
            check=True,
        )
        return directory

    def test_untracked_numeric_directory_is_not_legacy_evidence(self) -> None:
        directory = self.repo / "docs" / "changes" / "12"
        directory.mkdir(parents=True)
        directory.joinpath("00-summary.md").write_text(
            SUMMARY.format(
                number=12,
                complexity="small",
                change_type="bugfix",
                effect="restore",
                risk_flags="[]",
                required_docs="  - 00-summary.md",
                branch="change/12",
            )
        )
        with self.assertRaisesRegex(ContractError, "history evidence"):
            load_contract(self.repo, self.issue())

    def write_new_contract(
        self,
        *,
        number: int = 57,
        complexity: str = "small",
        change_type: str = "bugfix",
        effect: str = "restore",
        slug: str = "bounded-fix",
        spec: bool = False,
        plan: bool = False,
    ) -> Path:
        directory = self.repo / "docs" / "changes" / f"{number}-{slug}"
        directory.mkdir(parents=True)
        summary_name = f"summary-{slug}-260808.md"
        required = ["  - summary"]
        documents = [f"  summary: {summary_name}"]
        if complexity == "complex":
            required.extend(("  - spec", "  - plan"))
            documents.extend(
                (
                    f"  spec: spec-{slug}-260808.md",
                    f"  plan: plan-{slug}-260808.md",
                )
            )
        directory.joinpath(summary_name).write_text(
            NEW_SUMMARY.format(
                number=number,
                complexity=complexity,
                change_type=change_type,
                effect=effect,
                risk_flags="[]",
                required_docs="\n".join(required),
                documents="\n".join(documents),
                branch=f"change/{number}-{slug}",
            )
        )
        if spec:
            directory.joinpath(f"spec-{slug}-260808.md").write_text(
                SPEC.format(number=number)
                .replace(f"branch: change/{number}", f"branch: change/{number}-{slug}")
                .replace("---\n\n# Spec", "created: 2026-08-08\n---\n\n# Spec")
            )
        if plan:
            directory.joinpath(f"plan-{slug}-260808.md").write_text(
                PLAN.format(number=number)
                .replace(f"branch: change/{number}", f"branch: change/{number}-{slug}")
                .replace(
                    "---\n\n# Implementation plan",
                    "created: 2026-08-08\n---\n\n# Implementation plan",
                )
            )
        return directory

    def test_small_contract_is_accepted(self) -> None:
        self.write_contract()
        contract = load_contract(self.repo, self.issue())
        self.assertEqual(contract.issue_number, 12)
        self.assertEqual(contract.effective_complexity, "small")
        self.assertEqual(contract.required_docs, ("00-summary.md",))
        self.assertEqual(contract.dependencies, ())

    def test_new_named_small_contract_is_resolved_from_explicit_mapping(self) -> None:
        self.write_new_contract()
        self.assertEqual(
            resolve_documents(self.repo, 57),
            {"summary": "summary-bounded-fix-260808.md"},
        )
        contract = load_contract(self.repo, self.issue(number=57))
        self.assertEqual(contract.required_docs, ("summary-bounded-fix-260808.md",))

    def test_new_named_complex_contract_is_resolved_from_explicit_mapping(self) -> None:
        self.write_new_contract(
            complexity="complex",
            change_type="feature",
            effect="add",
            spec=True,
            plan=True,
        )
        issue = self.issue(
            number=57,
            labels=["type/feature", "complexity/complex", "approved"],
        )
        contract = load_contract(self.repo, issue)
        self.assertEqual(
            contract.required_docs,
            (
                "summary-bounded-fix-260808.md",
                "spec-bounded-fix-260808.md",
                "plan-bounded-fix-260808.md",
            ),
        )

    def test_new_named_contract_rejects_slug_and_created_date_drift(self) -> None:
        directory = self.write_new_contract()
        summary = directory.joinpath("summary-bounded-fix-260808.md")
        original = summary.read_text()
        mutations = (
            ("summary-bounded-fix-260808.md", "summary-other-fix-260808.md"),
            ("created: 2026-08-08", "created: 2026-08-09"),
        )
        for old, new in mutations:
            with self.subTest(new=new):
                summary.write_text(original.replace(old, new))
                with self.assertRaises(ContractError):
                    load_contract(self.repo, self.issue(number=57))
        summary.write_text(original)

    def test_new_named_contract_rejects_ambiguous_summary(self) -> None:
        directory = self.write_new_contract()
        directory.joinpath("summary-second-copy-260808.md").write_text(
            directory.joinpath("summary-bounded-fix-260808.md").read_text()
        )
        with self.assertRaisesRegex(ContractError, "exactly one new summary"):
            load_contract(self.repo, self.issue(number=57))

    def test_legacy_and_readable_directories_for_same_issue_are_a_conflict(self) -> None:
        self.write_contract(number=57)
        self.write_new_contract(number=57)
        with self.assertRaisesRegex(ContractError, "CHANGE_NAME_CONFLICT"):
            load_contract(self.repo, self.issue(number=57))

    def test_dependencies_are_parsed_and_ordered(self) -> None:
        self.write_contract(depends_on="\n  - 3\n  - 7")
        contract = load_contract(self.repo, self.issue())
        self.assertEqual(contract.dependencies, (3, 7))

    def test_dependencies_reject_invalid_self_and_duplicates(self) -> None:
        directory = self.write_contract()
        base = directory.joinpath("00-summary.md").read_text()
        for depends_on in ("\n  - 0", "\n  - nope", "\n  - 12", "\n  - 3\n  - 3"):
            with self.subTest(depends_on=depends_on):
                directory.joinpath("00-summary.md").write_text(
                    base.replace(
                        "status: analyzed",
                        f"depends_on: {depends_on}\nstatus: analyzed",
                    )
                )
                with self.assertRaisesRegex(ContractError, "depends_on"):
                    load_contract(self.repo, self.issue())

    def test_small_contract_requires_measurable_acceptance(self) -> None:
        self.write_contract()
        with self.assertRaisesRegex(ContractError, "acceptance criteria") as caught:
            load_contract(self.repo, self.issue(body="Please fix the bug."))
        self.assertEqual(caught.exception.terminal_state, "NEEDS_HUMAN_DECISION")

    def test_complex_contract_requires_spec_and_plan(self) -> None:
        self.write_contract(complexity="complex", change_type="feature", effect="add")
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        for missing in ("01-spec.md", "02-plan.md"):
            with self.subTest(missing=missing), self.assertRaisesRegex(ContractError, missing):
                load_contract(self.repo, issue)

    def test_complete_complex_contract_is_accepted(self) -> None:
        self.write_contract(
            complexity="complex", change_type="feature", effect="add", spec=True, plan=True
        )
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        contract = load_contract(self.repo, issue)
        self.assertEqual(contract.effective_complexity, "complex")
        self.assertEqual(
            contract.required_docs,
            ("00-summary.md", "01-spec.md", "02-plan.md"),
        )

    def test_complex_contract_rejects_unresolved_questions(self) -> None:
        directory = self.write_contract(
            complexity="complex", change_type="feature", effect="add", spec=True, plan=True
        )
        directory.joinpath("01-spec.md").write_text(
            SPEC.format(number=12).replace("无。", "需要决定是否改变 public API。")
        )
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        with self.assertRaisesRegex(ContractError, "未决问题"):
            load_contract(self.repo, issue)

    def test_issue_must_be_open_and_approved(self) -> None:
        self.write_contract()
        closed = self.issue()
        closed["state"] = "closed"
        without_approved = self.issue(labels=["type/bugfix", "complexity/small"])
        for issue in (closed, without_approved):
            with self.subTest(issue=issue), self.assertRaises(ContractError):
                load_contract(self.repo, issue)

    def test_type_and_complexity_labels_are_mutually_consistent(self) -> None:
        self.write_contract()
        cases = (
            ["type/bugfix", "type/docs", "complexity/small", "approved"],
            ["type/bugfix", "complexity/small", "complexity/complex", "approved"],
            ["type/docs", "complexity/small", "approved"],
            ["type/bugfix", "complexity/complex", "approved"],
        )
        for labels in cases:
            with self.subTest(labels=labels), self.assertRaises(ContractError):
                load_contract(self.repo, self.issue(labels=list(labels)))

    def test_summary_issue_and_branch_must_match(self) -> None:
        self.write_contract(number=99, branch="change/12")
        with self.assertRaisesRegex(ContractError, "summary"):
            load_contract(self.repo, self.issue(number=99))

    def test_forced_complex_risk_cannot_run_as_small(self) -> None:
        self.write_contract(risk_flags="\n  - security")
        with self.assertRaisesRegex(ContractError, "forced complex"):
            load_contract(self.repo, self.issue())

    def test_governing_agents_self_modification_is_rejected(self) -> None:
        self.write_contract()
        body = (
            "## Acceptance criteria\n\n"
            "- [ ] The running implementation worker edits its governing AGENTS.md directly."
        )
        with self.assertRaisesRegex(ContractError, "governing AGENTS.md"):
            load_contract(self.repo, self.issue(body=body))

    def test_safe_governing_agents_prohibition_is_not_a_self_mod_request(self) -> None:
        directory = self.write_contract(
            complexity="complex", change_type="feature", effect="add", spec=True, plan=True
        )
        directory.joinpath("01-spec.md").write_text(
            SPEC.format(number=12)
            + "\n普通 implementation worker 永远不得编辑本运行 governing `AGENTS.md`。\n"
        )
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        contract = load_contract(self.repo, issue)
        self.assertEqual(contract.effective_complexity, "complex")

    def test_missing_repository_is_external_blocker(self) -> None:
        missing = self.repo / "missing"
        with self.assertRaises(ContractError) as caught:
            load_contract(missing, self.issue())
        self.assertEqual(caught.exception.terminal_state, "BLOCKED_EXTERNAL")


if __name__ == "__main__":
    unittest.main()
