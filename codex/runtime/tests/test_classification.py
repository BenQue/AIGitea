from pathlib import Path
import unittest

from aisoft_loop.classification import Classification, ClassificationError


FIXTURES = (
    Path(__file__).parents[2] / "tests" / "fixtures" / "classification"
)


def classification_text(**overrides: str) -> str:
    values = {
        "change_type": "bugfix",
        "requested_complexity": "auto",
        "assessed_complexity": "small",
        "effective_complexity": "small",
        "contract_effect": "restore",
        "reason": "restore existing behavior",
        "risk_flags": "[]",
        "required_docs": "\n  - summary",
        "confidence": "high",
        "override_reason": "''",
    }
    values.update(overrides)
    fields = [
        "change_type",
        "requested_complexity",
        "assessed_complexity",
        "effective_complexity",
        "contract_effect",
        "reason",
        "risk_flags",
        "required_docs",
        "confidence",
        "override_reason",
    ]
    if values.get("effective_complexity") is None:
        fields.remove("effective_complexity")
    return "\n".join(f"{name}: {values[name]}" for name in fields) + "\n"


class ClassificationTests(unittest.TestCase):
    def test_canonical_fixtures_route(self) -> None:
        expected = {
            "small.yaml": ("small", "approved", "complexity/small"),
            "complex.yaml": ("complex", "spec-drafting", "complexity/complex"),
            "unclear.yaml": (None, "awaiting-triage", None),
        }
        for filename, route_expected in expected.items():
            with self.subTest(filename=filename):
                parsed = Classification.from_yaml((FIXTURES / filename).read_text())
                route = parsed.route()
                self.assertEqual(
                    (route.effective_complexity, route.lifecycle_label, route.complexity_label),
                    route_expected,
                )

    def test_feature_and_platform_are_forced_complex(self) -> None:
        for change_type in ("feature", "platform"):
            parsed = Classification.from_yaml(
                classification_text(change_type=change_type)
            )
            self.assertEqual(parsed.route().effective_complexity, "complex")

    def test_security_and_data_are_forced_complex_without_risk_flags(self) -> None:
        # AGENTS.md forces complex for 认证/权限/安全 and schema/数据迁移. The
        # matching risk_flags do too, but they are analyzer input that can be
        # omitted; the type label carries the same claim and cannot be. The
        # fixture deliberately declares no risk_flags and a restore effect.
        for change_type in ("security", "data"):
            with self.subTest(change_type=change_type):
                parsed = Classification.from_yaml(
                    classification_text(change_type=change_type)
                )
                route = parsed.route()
                self.assertEqual(route.effective_complexity, "complex")
                self.assertIn(f"type/{change_type}", route.override_reason or "")

    def test_reliability_routes_on_contract_effect(self) -> None:
        # An availability fix that restores existing behavior is a small
        # candidate; the same type with a changed contract is not.
        restore = Classification.from_yaml(
            classification_text(change_type="reliability")
        )
        self.assertEqual(restore.route().effective_complexity, "small")
        changed = Classification.from_yaml(
            classification_text(change_type="reliability", contract_effect="change")
        )
        self.assertEqual(changed.route().effective_complexity, "complex")

    def test_contract_add_or_change_is_forced_complex(self) -> None:
        for effect in ("add", "change"):
            parsed = Classification.from_yaml(
                classification_text(contract_effect=effect)
            )
            self.assertEqual(parsed.route().effective_complexity, "complex")

    def test_explicit_complex_cannot_be_downgraded(self) -> None:
        parsed = Classification.from_yaml(
            classification_text(requested_complexity="complex")
        )
        self.assertEqual(parsed.route().effective_complexity, "complex")

    def test_explicit_small_cannot_bypass_forced_risk(self) -> None:
        parsed = Classification.from_yaml(
            classification_text(
                requested_complexity="small",
                risk_flags="\n  - security",
            )
        )
        route = parsed.route()
        self.assertEqual(route.effective_complexity, "complex")
        self.assertIn("security", route.override_reason)

    def test_unclear_omits_effective_complexity(self) -> None:
        text = classification_text(
            assessed_complexity="needs-human-decision",
            effective_complexity=None,
            contract_effect="unclear",
            confidence="low",
        )
        parsed = Classification.from_yaml(text)
        self.assertIsNone(parsed.effective_complexity)
        self.assertEqual(parsed.route().lifecycle_label, "awaiting-triage")

    def test_unclear_with_effective_complexity_is_rejected(self) -> None:
        with self.assertRaisesRegex(ClassificationError, "omit effective_complexity"):
            Classification.from_yaml(
                classification_text(
                    assessed_complexity="needs-human-decision",
                    contract_effect="unclear",
                    confidence="low",
                )
            )

    def test_safe_result_without_effective_complexity_is_rejected(self) -> None:
        with self.assertRaisesRegex(ClassificationError, "requires effective_complexity"):
            Classification.from_yaml(classification_text(effective_complexity=None))

    def test_unknown_duplicate_and_out_of_order_fields_are_rejected(self) -> None:
        base = classification_text()
        cases = {
            "unknown": base + "extra: value\n",
            "duplicate": base + "confidence: low\n",
            "order": base.replace(
                "change_type: bugfix\nrequested_complexity: auto",
                "requested_complexity: auto\nchange_type: bugfix",
            ),
        }
        for name, text in cases.items():
            with self.subTest(name=name), self.assertRaises(ClassificationError):
                Classification.from_yaml(text)

    def test_illegal_enum_anchor_tag_and_nested_value_are_rejected(self) -> None:
        cases = (
            classification_text(change_type="unknown"),
            classification_text(reason="&shared value"),
            classification_text(reason="!python/object value"),
            classification_text(reason="{nested: value}"),
        )
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ClassificationError):
                Classification.from_yaml(text)

    def test_required_docs_follow_effective_route(self) -> None:
        parsed = Classification.from_yaml(classification_text())
        self.assertEqual(parsed.route().required_docs, ("summary",))
        forced = Classification.from_yaml(
            classification_text(risk_flags="\n  - deployment")
        )
        self.assertEqual(
            forced.route().required_docs,
            ("summary", "spec", "plan"),
        )


if __name__ == "__main__":
    unittest.main()
