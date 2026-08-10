import json
from pathlib import Path
import tempfile
import unittest

from aisoft_loop.analysis import (
    AnalysisError,
    AnalysisResult,
    analyze_route,
    render_summary,
    summary_filename,
)


def result_payload(classification: str) -> dict:
    return {
        "classification": classification,
        "document_slug": "pilot-fix",
        "problem_summary": "Restore existing behavior.",
        "impact": "One documented path.",
        "approach": "Add a regression test and minimal fix.",
        "risks": ["Regression in the same local path."],
        "evidence": ["Existing test documents the intended behavior."],
        "missing_acceptance_criteria": [],
    }


SMALL = """change_type: bugfix
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: restore existing behavior
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
"""

COMPLEX = SMALL.replace("bugfix", "feature").replace(
    "assessed_complexity: small\neffective_complexity: small\ncontract_effect: restore",
    "assessed_complexity: complex\neffective_complexity: complex\ncontract_effect: add",
).replace(
    "risk_flags: []\nrequired_docs:\n  - summary",
    "risk_flags:\n  - functional-change\nrequired_docs:\n  - summary\n  - spec\n  - plan",
)

UNCLEAR = SMALL.replace(
    "assessed_complexity: small\neffective_complexity: small\ncontract_effect: restore",
    "assessed_complexity: needs-human-decision\ncontract_effect: unclear",
).replace("confidence: high", "confidence: low")


class AnalysisResultTests(unittest.TestCase):
    def issue(self, labels: list[str] | None = None, body: str | None = None) -> dict:
        return {
            "number": 8,
            "title": "Pilot issue",
            "body": body
            or "## Acceptance criteria\n\n- [ ] Existing behavior is restored.",
            "state": "open",
            "labels": labels or ["needs-analysis"],
        }

    def test_exact_json_schema_and_nonempty_evidence(self) -> None:
        parsed = AnalysisResult.from_json(json.dumps(result_payload(SMALL)))
        self.assertEqual(parsed.classification.change_type, "bugfix")
        for mutation in (
            {**result_payload(SMALL), "extra": True},
            {**result_payload(SMALL), "evidence": []},
            {**result_payload(SMALL), "risks": "none"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(AnalysisError):
                AnalysisResult.from_json(json.dumps(mutation))

    def test_small_complex_and_unclear_routes(self) -> None:
        cases = (
            (SMALL, "small", "approved", "complexity/small"),
            (COMPLEX, "complex", "spec-drafting", "complexity/complex"),
            (UNCLEAR, None, "awaiting-triage", None),
        )
        for classification, effective, lifecycle, label in cases:
            with self.subTest(effective=effective):
                route = analyze_route(
                    self.issue(), AnalysisResult.from_json(json.dumps(result_payload(classification)))
                )
                self.assertEqual(route.effective_complexity, effective)
                self.assertEqual(route.lifecycle_label, lifecycle)
                self.assertEqual(route.complexity_label, label)

    def test_small_without_acceptance_stays_awaiting_triage(self) -> None:
        issue = self.issue(body="Please fix this.")
        route = analyze_route(
            issue, AnalysisResult.from_json(json.dumps(result_payload(SMALL)))
        )
        self.assertEqual(route.lifecycle_label, "awaiting-triage")
        self.assertEqual(route.complexity_label, "complexity/small")

    def test_explicit_issue_complex_cannot_be_downgraded(self) -> None:
        issue = self.issue(labels=["complexity/complex", "needs-analysis"])
        result = AnalysisResult.from_json(json.dumps(result_payload(SMALL)))
        with self.assertRaisesRegex(AnalysisError, "requested_complexity"):
            analyze_route(issue, result)

    def test_explicit_small_forced_complex_is_rendered_as_override(self) -> None:
        forced = SMALL.replace("requested_complexity: auto", "requested_complexity: small").replace(
            "risk_flags: []", "risk_flags:\n  - security"
        )
        issue = self.issue(labels=["complexity/small", "needs-analysis"])
        result = AnalysisResult.from_json(json.dumps(result_payload(forced)))
        route = analyze_route(issue, result)
        self.assertEqual(route.effective_complexity, "complex")
        summary = render_summary(
            issue,
            result,
            route,
            "http://gitea.test",
            "owner",
            "repo",
            date="2026-07-16",
        )
        self.assertIn("effective_complexity: complex", summary)
        self.assertIn("forced complex", summary)
        self.assertIn("  - spec", summary)

    def test_unclear_summary_omits_every_effective_key(self) -> None:
        result = AnalysisResult.from_json(json.dumps(result_payload(UNCLEAR)))
        route = analyze_route(self.issue(), result)
        summary = render_summary(
            self.issue(),
            result,
            route,
            "http://gitea.test",
            "owner",
            "repo",
            date="2026-07-16",
        )
        self.assertNotIn("effective_complexity:", summary)
        self.assertIn("status: awaiting-triage", summary)

    def test_summary_is_bound_to_issue_and_change_branch(self) -> None:
        result = AnalysisResult.from_json(json.dumps(result_payload(SMALL)))
        route = analyze_route(self.issue(), result)
        summary = render_summary(
            self.issue(),
            result,
            route,
            "http://gitea.test",
            "owner",
            "repo",
            date="2026-07-16",
        )
        self.assertIn("issue: 8", summary)
        self.assertIn("branch: change/8-pilot-fix", summary)
        self.assertIn("## AI 判级", summary)
        self.assertIn("Existing test documents", summary)
        self.assertIn("documents:\n  summary: summary-pilot-fix-260716.md", summary)
        self.assertEqual(summary_filename(result, "2026-07-16"), "summary-pilot-fix-260716.md")

    def test_document_slug_must_be_short_lowercase_kebab_case(self) -> None:
        for slug in ("one", "TOO-LONG", "one_two", "one-two-three-four-five", "x" * 33 + "-ok"):
            with self.subTest(slug=slug), self.assertRaisesRegex(AnalysisError, "document_slug"):
                AnalysisResult.from_json(json.dumps({**result_payload(SMALL), "document_slug": slug}))


if __name__ == "__main__":
    unittest.main()
