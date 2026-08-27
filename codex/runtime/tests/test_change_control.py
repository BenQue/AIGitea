import json
import tempfile
import unittest
from pathlib import Path

from aisoft_gitea_governance.contract import (
    ContractError, load_contract, repository_declarations_sha256,
)
from aisoft_loop.change_control import PHASES, resolve_change_control
from aisoft_loop.classification import Classification, ClassificationError

MANIFEST = Path(__file__).resolve().parents[3] / "codex/config/gitea-governance.json"


def _complex_classification() -> Classification:
    return Classification(
        change_type="feature",
        requested_complexity="auto",
        assessed_complexity="complex",
        effective_complexity="complex",
        contract_effect="add",
        confidence="high",
        reason="forced complex by type and contract effect",
        risk_flags=(),
        required_docs=("summary", "spec", "plan", "verification"),
        override_reason="",
    )


class ChangeControlContractTests(unittest.TestCase):
    """AC2：未声明的既有仓库必须默认 production，行为逐字段不变。"""

    def test_undeclared_repositories_default_to_production(self) -> None:
        """原断言是「每个仓库都是 production」——那把「当时没有任何仓库声明过」这个事实
        钉成了测试，Issue #148 给 LocalWMS 声明 development 时它必然变红。AC2 真正要保的是
        **未声明者默认 production**，因此改为只遍历未声明的仓库。"""
        raw = json.loads(MANIFEST.read_text())
        declared = {
            entry["name"] for entry in raw["repositories"] if "change_control" in entry
        }
        contract = load_contract(MANIFEST)
        checked = 0
        for repository in contract.repositories:
            if repository.name in declared:
                continue
            with self.subTest(repository=repository.name):
                self.assertEqual(repository.change_control, "production")
                self.assertFalse(repository.in_development)
            checked += 1
        # 防空转：等到所有仓库都显式声明的那天，上面的循环会一个都不跑，
        # 而测试仍然「通过」。那时兜底行为就没有任何东西守着了，必须补一个合成 fixture。
        self.assertGreater(checked, 0, "没有未声明的仓库，AC2 的兜底断言已空转")

    def test_localwms_is_declared_development(self) -> None:
        """Issue #148：机制自 #134 起就在，但十个仓库无一声明，收益一直是零。
        这条把「LocalWMS 已降到 development」钉住——它一旦被改回去，判级会静默恢复四份文档。"""
        contract = load_contract(MANIFEST)
        localwms = next(
            repository
            for repository in contract.repositories
            if repository.name == "LocalWMS"
        )
        self.assertEqual(localwms.change_control, "development")
        self.assertTrue(localwms.in_development)

    def test_declared_development_is_parsed(self) -> None:
        """本条要证的是「给一个仓声明 development 不会污染其它仓」。原来把「其它仓都是
        production」写死了，这在 Issue #148 给 LocalWMS 声明之后不再成立——改为逐仓比对
        manifest 里各自的声明值（缺省 production），断言的意图不变而不再依赖当时的快照。"""
        raw = json.loads(MANIFEST.read_text())
        raw["repositories"][1]["change_control"] = "development"
        next(
            item for item in raw["repositories"] if item["name"] == "NewEMaint"
        )["routine_live_pilot"]["non_target_repositories_sha256"] = (
            repository_declarations_sha256(
                raw["repositories"], exclude_name="NewEMaint"
            )
        )
        expected = {
            entry["name"]: entry.get("change_control", "production")
            for entry in raw["repositories"]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(raw))
            contract = load_contract(path)
        declared = contract.repositories[1]
        self.assertEqual(declared.change_control, "development")
        self.assertTrue(declared.in_development)
        for other in contract.repositories:
            if other.name == declared.name:
                continue
            with self.subTest(repository=other.name):
                self.assertEqual(other.change_control, expected[other.name])

    def test_invalid_change_control_is_rejected(self) -> None:
        """AC1：非法取值必须 fail closed，不得静默回落。"""
        for invalid in ("", "dev", "Development", "staging", True, 1, None):
            with self.subTest(invalid=invalid):
                raw = json.loads(MANIFEST.read_text())
                raw["repositories"][0]["change_control"] = invalid
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "manifest.json"
                    path.write_text(json.dumps(raw))
                    with self.assertRaisesRegex(ContractError, "change_control"):
                        load_contract(path)

    def test_unknown_repository_key_is_still_rejected(self) -> None:
        """可选键的放行不得退化为「任意键都接受」。"""
        raw = json.loads(MANIFEST.read_text())
        raw["repositories"][0]["unexpected_key"] = "x"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ContractError, "keys mismatch"):
                load_contract(path)


class ChangeControlRouteTests(unittest.TestCase):
    """AC3：判级对两个阶段输出不同的 required_docs。"""

    def test_production_keeps_four_documents(self) -> None:
        route = _complex_classification().route(change_control="production")
        self.assertEqual(route.effective_complexity, "complex")
        self.assertEqual(route.required_docs, ("summary", "spec", "plan", "verification"))

    def test_development_keeps_only_summary_and_verification(self) -> None:
        route = _complex_classification().route(change_control="development")
        self.assertEqual(route.effective_complexity, "complex")
        self.assertEqual(route.required_docs, ("summary", "verification"))

    def test_verification_stays_conditional_in_development(self) -> None:
        """required_docs 含 verification 说的是「这次变更欠一份验证记录」，
        由 analyzer 决定；development 不得改变这个条件。（#163 之前它还兼答
        「该变更要部署」，那半边已交给 manifest 的 deployment_lifecycle；
        本条守的是 route() 侧的条件不变。）"""
        shipping = _complex_classification()
        self.assertIn("verification", shipping.route(change_control="development").required_docs)

        non_shipping = Classification(
            change_type="feature",
            requested_complexity="auto",
            assessed_complexity="complex",
            effective_complexity="complex",
            contract_effect="add",
            confidence="high",
            reason="does not ship",
            risk_flags=(),
            required_docs=("summary", "spec", "plan"),
            override_reason="",
        )
        for phase in sorted(PHASES):
            with self.subTest(phase=phase):
                self.assertNotIn(
                    "verification", non_shipping.route(change_control=phase).required_docs
                )
        self.assertEqual(
            non_shipping.route(change_control="development").required_docs, ("summary",)
        )

    def test_default_is_production(self) -> None:
        self.assertEqual(
            _complex_classification().route().required_docs,
            ("summary", "spec", "plan", "verification"),
        )

    def test_phase_does_not_change_complexity_or_lifecycle(self) -> None:
        """AC6 的一部分：放宽只影响文档份数，不得改变判级或生命周期。"""
        production = _complex_classification().route(change_control="production")
        development = _complex_classification().route(change_control="development")
        self.assertEqual(production.effective_complexity, development.effective_complexity)
        self.assertEqual(production.lifecycle_label, development.lifecycle_label)
        self.assertEqual(production.complexity_label, development.complexity_label)

    def test_small_route_is_unaffected_by_phase(self) -> None:
        small = Classification(
            change_type="bugfix",
            requested_complexity="auto",
            assessed_complexity="small",
            effective_complexity="small",
            contract_effect="restore",
            confidence="high",
            reason="restores existing behaviour",
            risk_flags=(),
            required_docs=("summary",),
            override_reason="",
        )
        for phase in sorted(PHASES):
            with self.subTest(phase=phase):
                route = small.route(change_control=phase)
                self.assertEqual(route.effective_complexity, "small")
                self.assertEqual(route.required_docs, ("summary",))

    def test_unsupported_phase_fails_closed(self) -> None:
        with self.assertRaisesRegex(ClassificationError, "change_control"):
            _complex_classification().route(change_control="staging")


class ChangeControlResolverTests(unittest.TestCase):
    """解析器的每条不确定路径都必须回落到更严的 production。"""

    def test_resolves_declared_phase(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        raw["repositories"][0]["change_control"] = "development"
        target = raw["repositories"][0]["name"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(raw))
            self.assertEqual(resolve_change_control(target, manifest=path), "development")

    def test_falls_back_to_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.json"
            malformed = Path(tmp) / "malformed.json"
            malformed.write_text("{ not json")
            shaped_wrong = Path(tmp) / "shape.json"
            shaped_wrong.write_text(json.dumps({"repositories": "not-a-list"}))
            bad_phase = Path(tmp) / "bad-phase.json"
            bad_phase.write_text(json.dumps(
                {"repositories": [{"name": "X", "change_control": "staging"}]}
            ))
            cases = {
                "manifest missing": (missing, "X"),
                "manifest malformed": (malformed, "X"),
                "repositories wrong shape": (shaped_wrong, "X"),
                "unknown repository": (MANIFEST, "NoSuchRepository"),
                "invalid phase value": (bad_phase, "X"),
            }
            for label, (path, repo) in cases.items():
                with self.subTest(case=label):
                    self.assertEqual(resolve_change_control(repo, manifest=path), "production")


if __name__ == "__main__":
    unittest.main()
