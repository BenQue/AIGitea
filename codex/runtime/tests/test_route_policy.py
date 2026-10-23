"""The routing table in route-policy.md is the single source of the route card (#395).

These tests read the Markdown table itself, so the five classifier cases of
08 §7.1 and the closed sets enforced by contract.validate_route can never drift
from what the skill tells a session to look up.
"""

from pathlib import Path
import re
import unittest

from aisoft_loop.classification import Classification
from aisoft_loop.contract import ROUTE_KEYS, ROUTE_VALUES

POLICY = Path(__file__).parents[3] / "skills" / "aisoft-platform" / "references" / "route-policy.md"
COLUMNS = (
    "process", "tier", "effort", "method", "verify",
    "review_platform", "review_project", "skills",
)


def _section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = lines.index(heading) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return [line for line in lines[start:end] if line.startswith("| ") and not line.startswith("|---")]


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _codes(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def load_policy() -> tuple[dict[str, dict[str, object]], dict[str, str], dict[str, frozenset[str]]]:
    text = POLICY.read_text(encoding="utf-8")
    rows: dict[str, dict[str, object]] = {}
    for line in _section(text, "## 推导表")[1:]:
        cells = _cells(line)
        values = [_codes(cell) for cell in cells[2:]]
        row: dict[str, object] = {name: value[0] for name, value in zip(COLUMNS[:-1], values[:-1])}
        row["skills"] = values[-1]
        rows[cells[0]] = row
    rules = {_cells(line)[0]: _cells(line)[2] for line in _section(text, "## 细化规则")[1:]}
    closed = {
        _cells(line)[0]: frozenset(_codes(_cells(line)[1]))
        for line in _section(text, "## 取值闭集")[1:]
    }
    return rows, rules, closed


def lookup(classification, *, change_control="production", platform_repo=True,
           splits_into_issues=False, provider="claude"):
    from aisoft_loop.route_policy import resolve_route
    result = resolve_route(classification, provider=provider, change_control=change_control,
                           platform_repo=platform_repo, splits_into_issues=splits_into_issues)
    return {**result["route"], "row": result["matched_rules"][0]}


def classified(**overrides: str) -> Classification:
    values = {
        "change_type": "bugfix",
        "requested_complexity": "auto",
        "assessed_complexity": "small",
        "effective_complexity": "small",
        "contract_effect": "restore",
        "reason": "routing case",
        "risk_flags": "[]",
        "required_docs": "\n  - summary",
        "confidence": "high",
        "override_reason": "''",
    }
    values.update(overrides)
    fields = [name for name in values if not (name == "effective_complexity" and values[name] is None)]
    return Classification.from_yaml("\n".join(f"{name}: {values[name]}" for name in fields) + "\n")


COMPLEX_DOCS = "\n  - summary\n  - spec\n  - plan"
PRODUCTION_SKILLS = "to-spec, to-tickets, executing-plans, verification-before-completion"


class RoutePolicyTests(unittest.TestCase):
    def test_policy_has_five_rows_five_rules_and_the_closed_sets(self) -> None:
        rows, rules, closed = load_policy()
        self.assertEqual(sorted(rows), ["R1", "R2", "R3", "R4", "R5"])
        self.assertEqual(sorted(rules), ["G1", "M1", "P1", "S1", "V1"])
        self.assertEqual(set(closed), ROUTE_KEYS - {"skills"})

    def test_contract_closed_sets_are_the_policy_closed_sets(self) -> None:
        _, _, closed = load_policy()
        self.assertEqual({name: frozenset(values) for name, values in ROUTE_VALUES.items()}, closed)

    def test_every_table_cell_is_inside_its_closed_set(self) -> None:
        rows, rules, closed = load_policy()
        for key, row in rows.items():
            for name in ("process", "tier", "effort", "method", "verify"):
                self.assertIn(row[name], closed[name], f"{key}.{name}")
            for name in ("review_platform", "review_project"):
                self.assertIn(row[name], closed["review"], f"{key}.{name}")
        self.assertIn(_codes(rules["M1"])[0], closed["method"])
        self.assertIn(_codes(rules["V1"])[0], closed["verify"])
        self.assertIn(_codes(rules["S1"])[0], closed["review"])

    def test_the_five_classifier_cases_of_08_section_7_1(self) -> None:
        cases = {
            "bugfix/small": (classified(), {
                "row": "R5", "process": "small-direct", "tier": "standard", "effort": "medium",
                "method": "debug-first", "verify": "targeted", "review": "human-merge",
                "skills": "verification-before-completion",
            }),
            "feature/complex": (classified(
                change_type="feature", assessed_complexity="complex", effective_complexity="complex",
                contract_effect="add", required_docs=COMPLEX_DOCS,
            ), {
                "row": "R4", "process": "complex-production", "tier": "frontier", "effort": "high",
                "method": "spec-plan", "verify": "full", "review": "cross-provider",
                "skills": "grill-me, " + PRODUCTION_SKILLS,
            }),
            "explicit-small override": (classified(
                requested_complexity="small", assessed_complexity="complex",
                effective_complexity="complex", contract_effect="change",
                risk_flags="\n  - functional-change", required_docs=COMPLEX_DOCS,
                override_reason="'forced complex: functional-change'",
            ), {
                "row": "R4", "process": "complex-production", "tier": "frontier", "effort": "high",
                "method": "spec-plan", "verify": "full", "review": "cross-provider",
                "skills": PRODUCTION_SKILLS,
            }),
            "explicit-complex preservation": (classified(
                requested_complexity="complex", assessed_complexity="small",
                effective_complexity="complex", required_docs=COMPLEX_DOCS,
            ), {
                "row": "R4", "process": "complex-production", "tier": "frontier", "effort": "high",
                "method": "spec-plan", "verify": "full", "review": "cross-provider",
                "skills": PRODUCTION_SKILLS,
            }),
            "unclear/awaiting-triage": (classified(
                assessed_complexity="needs-human-decision", effective_complexity=None,
                contract_effect="unclear", confidence="low",
            ), {
                "row": "R1", "process": "awaiting-triage", "tier": "frontier", "effort": "high",
                "method": "none", "verify": "none", "review": "none", "skills": "triage",
            }),
        }
        for name, (classification, expected) in cases.items():
            with self.subTest(case=name):
                route = lookup(classification)
                self.assertEqual({key: route[key] for key in expected}, expected)
                self.assertEqual(route["confirm"], "2")

    def test_codex_concrete_default(self):
        route = lookup(classified(requested_complexity="complex", effective_complexity="complex",
                                  required_docs=COMPLEX_DOCS), provider="codex")
        self.assertEqual(route["skills"], "to-spec, to-tickets, implement, issue-session-flow")

    def test_refinements_and_the_other_rows(self) -> None:
        risky = dict(
            change_type="platform", assessed_complexity="complex", effective_complexity="complex",
            contract_effect="change", required_docs=COMPLEX_DOCS + "\n  - verification",
        )
        governance = classified(risk_flags="\n  - platform-governance\n  - shared-core", **risky)
        self.assertEqual(
            {k: lookup(governance)[k] for k in ("row", "effort", "verify", "review", "skills")},
            {"row": "R3", "effort": "max", "verify": "full+reverse-proof",
             "review": "cross-provider", "skills": PRODUCTION_SKILLS},
        )
        self.assertEqual(
            lookup(classified(risk_flags="\n  - authorization", **risky))["review"],
            "cross-provider+security",
        )
        project = lookup(governance, platform_repo=False)
        self.assertEqual((project["review"], project["skills"]),
                         ("human-merge", PRODUCTION_SKILLS + ", code-review"))
        self.assertEqual(lookup(governance, change_control="development")["row"], "R2")
        owed = classified(
            change_type="maintenance", requested_complexity="complex", effective_complexity="complex",
            required_docs=COMPLEX_DOCS + "\n  - verification",
        )
        self.assertEqual((lookup(owed)["row"], lookup(owed)["verify"]), ("R4", "full+verification"))
        self.assertEqual(lookup(classified(change_type="docs"))["method"], "implement-only")
        stage = lookup(governance, splits_into_issues=True)
        self.assertEqual(stage["skills"], "grill-me, " + PRODUCTION_SKILLS)
        self.assertEqual(lookup(owed, splits_into_issues=True)["skills"].split(", ")[0], "grill-me")
        self.assertEqual(lookup(classified(), splits_into_issues=True)["skills"],
                         "verification-before-completion")


class ExecutableRouteTests(unittest.TestCase):
    def test_provider_matrix_retains_priority_and_obligations(self):
        from aisoft_loop.route_policy import resolve_route
        samples = [classified(), classified(assessed_complexity="needs-human-decision", effective_complexity=None, contract_effect="unclear", confidence="low"),
                   classified(requested_complexity="complex", effective_complexity="complex", required_docs=COMPLEX_DOCS),
                   classified(change_type="security", requested_complexity="complex", effective_complexity="complex", required_docs=COMPLEX_DOCS)]
        for provider in ('codex', 'claude', 'cursor'):
            for phase in ('production', 'development'):
                for platform in (True, False):
                    for c in samples:
                        with self.subTest(provider=provider, phase=phase, platform=platform, type=c.change_type):
                            r = resolve_route(c, provider=provider, change_control=phase, platform_repo=platform)
                            skills = r['route']['skills'].split(', ')
                            self.assertEqual(r['route']['confirm'], '2')
                            self.assertNotIn('@', r['route']['skills'])
                            if r['matched_rules'][0] == 'R1':
                                self.assertEqual(skills, ['triage'])
                                continue
                            self.assertIn('issue-session-flow' if provider == 'codex' else 'verification-before-completion', skills)
                            if r['matched_rules'][0] in ('R3', 'R4'):
                                self.assertIn('implement' if provider == 'codex' else 'executing-plans', skills)
                            else:
                                self.assertNotIn('implement', skills)
                                self.assertNotIn('executing-plans', skills)
                            if phase == 'development' and c.effective_complexity == 'complex':
                                self.assertEqual(r['matched_rules'][0], 'R2')

    def test_provider_required_no_fallback(self):
        from aisoft_loop.route_policy import resolve_route
        from aisoft_loop.contract import ContractError
        for provider in ('', None, 'other'):
            with self.subTest(provider=provider), self.assertRaises(ContractError):
                resolve_route(classified(), provider=provider)

    def test_policy_values_drive_runtime_and_digest(self):
        from aisoft_loop.route_policy import resolve_route
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'policy.md'
            p.write_text(POLICY.read_text().replace('| codex | `implement` | `issue-session-flow` |',
                                                   '| codex | `implement` | `verification-before-completion` |'))
            original = resolve_route(classified(), provider='codex')
            altered = resolve_route(classified(), provider='codex', policy=p)
            self.assertEqual(altered['route']['skills'], 'verification-before-completion')
            self.assertNotEqual(original['policy_sha256'], altered['policy_sha256'])
            p.write_text(p.read_text().replace('complex 且 `change_control: development`', 'unknown condition'))
            from aisoft_loop.contract import ContractError
            with self.assertRaisesRegex(ContractError, 'condition'):
                resolve_route(classified(), provider='codex', policy=p)

    def test_legacy_verification_obligation_survives_resolution(self):
        for provider in ('codex', 'claude', 'cursor'):
            c = classified(change_type='maintenance', requested_complexity='complex', effective_complexity='complex',
                required_docs='\n  - 00-summary.md\n  - 01-spec.md\n  - 02-plan.md\n  - 03-verification.md')
            self.assertEqual(lookup(c, provider=provider)['verify'], 'full+verification')

    def test_cli_preserves_legacy_verification(self):
        import subprocess, json
        from tests.test_contract import ContractTests
        fixture = ContractTests(); fixture.setUp()
        try:
            directory = fixture.write_contract(complexity='complex', change_type='maintenance', spec=True, plan=True)
            summary = directory / '00-summary.md'
            summary.write_text(summary.read_text().replace('  - 02-plan.md', '  - 02-plan.md\n  - 03-verification.md'))
            (directory / '03-verification.md').write_text('---\nissue: 12\n---\n')
            before = summary.read_bytes()
            for provider in ('codex', 'claude', 'cursor'):
                run = subprocess.run([str(POLICY.parents[3] / 'codex/tools/aisoft'), 'resolve-route', '12',
                                      '--provider', provider, '--repo', str(fixture.repo)], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(json.loads(run.stdout)['route']['verify'], 'full+verification')
            self.assertEqual(summary.read_bytes(), before)
        finally:
            fixture.tearDown()

    def test_unknown_modifier_action_fails_and_risk_types_are_read(self):
        from aisoft_loop.route_policy import resolve_route
        from aisoft_loop.contract import ContractError
        import tempfile
        c = classified(change_type='reliability', requested_complexity='complex', effective_complexity='complex', required_docs=COMPLEX_DOCS)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'policy.md'
            p.write_text(POLICY.read_text().replace('`change_type` 为 `security` 或\n`data`', '`change_type` 为 `security`、`reliability` 或\n`data`'))
            self.assertEqual(resolve_route(c, provider='codex', policy=p)['matched_rules'][0], 'R3')
            p.write_text(POLICY.read_text().replace('skills 末尾加', 'skills 最前面加'))
            with self.assertRaisesRegex(ContractError, 'modifier action'):
                resolve_route(c, provider='codex', policy=p)

    def test_cli_resolves_historical_summary_without_rewriting(self):
        import tempfile, subprocess, json
        from tests.test_contract import NEW_SUMMARY
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            directory = repo / 'docs/changes/57-matt-flow'; directory.mkdir(parents=True)
            summary = directory / 'summary-matt-flow-260808.md'
            text = NEW_SUMMARY.format(number=57, change_type='bugfix', complexity='small', effect='restore',
                risk_flags='[]', required_docs='  - summary', documents='  summary: summary-matt-flow-260808.md', branch='change/57-matt-flow')
            summary.write_text(text)
            wrapper = POLICY.parents[3] / 'codex/tools/aisoft'
            run = subprocess.run([str(wrapper), 'resolve-route', '57', '--provider', 'codex', '--repo', str(repo)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['route']['skills'], 'issue-session-flow')
            self.assertTrue(json.loads(run.stdout)['historical_card'])
            self.assertEqual(summary.read_text(), text)
            missing = subprocess.run([str(wrapper), 'resolve-route', '57', '--repo', str(repo)], capture_output=True)
            self.assertNotEqual(missing.returncode, 0)

    def test_new_cards_validate_concrete_provider_and_explicit_overrides(self):
        from dataclasses import asdict
        from aisoft_loop.contract import validate_route, ContractError
        from aisoft_loop.route_policy import resolve_route
        c = classified()
        front = asdict(c)
        front['risk_flags'], front['required_docs'] = list(c.risk_flags), list(c.required_docs)
        front['gitea_url'] = 'http://gitea.test/owner/repo/issues/12'
        front.update(route_provider='codex', route=resolve_route(c, provider='codex', platform_repo=False)['route'])
        validate_route(front)
        for skills in ('', 'unknown', '@completion', 'issue-session-flow, issue-session-flow', 'verification-before-completion'):
            with self.subTest(skills=skills), self.assertRaises(ContractError):
                validate_route({**front, 'route': {**front['route'], 'skills': skills}})
        validate_route({**front, 'route': {**front['route'], 'tier': 'frontier'}, 'override_reason': 'tier: approved stronger model'})
        with self.assertRaises(ContractError):
            validate_route({**front, 'route_provider': 'unknown'})
        legacy = dict(front); legacy.pop('route_provider')
        validate_route(legacy)


if __name__ == "__main__":
    unittest.main()
