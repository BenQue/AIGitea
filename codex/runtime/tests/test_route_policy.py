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
HIGH_RISK = frozenset({
    "security", "authentication", "authorization", "schema-change", "data-migration",
    "external-contract", "shared-core", "ci-integration", "ci-change", "artifact",
    "deployment", "deployment-boundary", "rollback", "agent-governance", "platform-governance",
})
SECURITY = frozenset({"security", "authentication", "authorization"})


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


def lookup(classification: Classification, *, change_control: str = "production",
           platform_repo: bool = True) -> dict[str, str]:
    """Walk the table top-down exactly as route-policy.md says a session does."""
    rows, rules, _ = load_policy()
    effective = classification.route(change_control=change_control).effective_complexity
    flags = set(classification.risk_flags)
    high_risk = bool(flags & HIGH_RISK) or classification.change_type in {"security", "data"}
    if effective is None:
        key = "R1"
    elif effective == "complex" and change_control == "development":
        key = "R2"
    elif effective == "complex" and high_risk:
        key = "R3"
    elif effective == "complex":
        key = "R4"
    else:
        key = "R5"
    row = dict(rows[key])
    skills = list(row.pop("skills"))  # type: ignore[arg-type]
    route = {name: str(value) for name, value in row.items()}
    route["review"] = route.pop("review_platform" if platform_repo else "review_project")
    route.pop("review_project" if platform_repo else "review_platform")
    if key == "R5" and classification.change_type == "bugfix":
        route["method"] = _codes(rules["M1"])[0]
    if key == "R4" and "verification" in classification.required_docs:
        route["verify"] = _codes(rules["V1"])[0]
    security = bool(flags & SECURITY) or classification.change_type == "security"
    if key == "R3" and platform_repo and security:
        route["review"] = _codes(rules["S1"])[0]
    if key == "R3" and not platform_repo:
        skills.append(_codes(rules["P1"])[0])
    if key in {"R3", "R4"} and (
        classification.change_type == "feature" or classification.contract_effect == "add"
    ):
        skills.insert(0, _codes(rules["G1"])[0])
    route["skills"] = ", ".join(skills)
    route["confirm"] = "2"
    route["row"] = key
    return route


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


if __name__ == "__main__":
    unittest.main()
