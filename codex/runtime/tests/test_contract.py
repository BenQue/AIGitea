import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_loop.contract import (
    COMPLEXITY_LABELS,
    LIFECYCLE_LABELS,
    TRIAGE_LABELS,
    TYPE_LABELS,
    ContractError,
    load_contract,
    resolve_documents,
)


LABEL_MANIFEST = (
    Path(__file__).parents[2] / "config" / "gitea-labels.json"
)


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


class LabelTaxonomyParityTests(unittest.TestCase):
    """The manifest and the runtime must describe one closed taxonomy.

    The manifest is what gets provisioned into a repository; these frozensets
    are what the Loop and the label projector accept. When they disagree, a
    label exists in Gitea, an author applies it, and the Loop then refuses the
    Issue for having no type label at all — a failure whose message points
    nowhere near the manifest that caused it (#108).
    """

    def canonical(self) -> set[str]:
        manifest = json.loads(LABEL_MANIFEST.read_text(encoding="utf-8"))
        return {entry["name"] for entry in manifest["canonical"]}

    def test_type_labels_match_the_manifest(self) -> None:
        canonical = self.canonical()
        self.assertEqual(
            TYPE_LABELS,
            {name for name in canonical if name.startswith("type/")},
        )

    def test_every_managed_dimension_matches_the_manifest(self) -> None:
        canonical = self.canonical()
        self.assertEqual(
            COMPLEXITY_LABELS,
            {name for name in canonical if name.startswith("complexity/")},
        )
        self.assertEqual(
            TRIAGE_LABELS,
            {name for name in canonical if name.startswith("triage/")},
        )
        self.assertEqual(
            LIFECYCLE_LABELS,
            {name for name in canonical if "/" not in name},
        )

    def test_retired_values_are_not_accepted_by_the_runtime(self) -> None:
        manifest = json.loads(LABEL_MANIFEST.read_text(encoding="utf-8"))
        retired = {entry["name"] for entry in manifest["retired"]}
        self.assertTrue(retired, "the retired declaration is the point of this test")
        accepted = TYPE_LABELS | COMPLEXITY_LABELS | LIFECYCLE_LABELS | TRIAGE_LABELS
        self.assertEqual(retired & accepted, set())


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

    def test_development_phase_complex_contract_needs_no_spec_or_plan(self) -> None:
        """AC4：development 项目的强制 complex 不因缺 spec/plan 被拒。"""
        self.write_contract(complexity="complex", change_type="feature", effect="add")
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        contract = load_contract(self.repo, issue, change_control="development")
        self.assertEqual(contract.effective_complexity, "complex")
        self.assertEqual(contract.required_docs, ("00-summary.md",))

    def test_development_phase_still_requires_measurable_acceptance(self) -> None:
        """没有 spec 时验收标准改由 Issue 正文提供，但门槛本身不放宽。"""
        self.write_contract(complexity="complex", change_type="feature", effect="add")
        issue = self.issue(
            labels=["type/feature", "complexity/complex", "approved"],
            body="这个变更很重要，做完就知道了。",
        )
        with self.assertRaisesRegex(ContractError, "acceptance criteria"):
            load_contract(self.repo, issue, change_control="development")

    def test_production_phase_still_rejects_missing_spec_and_plan(self) -> None:
        """AC4 的对照：production 的行为完全不变，缺省亦然。"""
        self.write_contract(complexity="complex", change_type="feature", effect="add")
        issue = self.issue(labels=["type/feature", "complexity/complex", "approved"])
        for missing in ("01-spec.md", "02-plan.md"):
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(ContractError, missing):
                    load_contract(self.repo, issue, change_control="production")
                with self.assertRaisesRegex(ContractError, missing):
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
