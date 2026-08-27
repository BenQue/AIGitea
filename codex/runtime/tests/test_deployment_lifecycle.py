"""Issue #163：仓库有没有应用部署链路，必须由 manifest 声明一次，而不是从
required_docs 里推断。Issue #192 把这个声明收紧成三档——问的不再是「有没有链路」，
而是「这条链路会不会覆盖到本次 merge」，并把缺省换成可自愈的一档。这些断言守住
schema 侧的四件事——三档都被读进来、声明被读进来、未声明者取新缺省、非法取值
fail closed。合取判定本身在 codex/tests/test-mark-completed-issues.sh 里覆盖。"""

import json
import tempfile
import unittest
from pathlib import Path

from aisoft_gitea_governance.contract import (
    DEFAULT_DEPLOYMENT_LIFECYCLE,
    DEPLOYMENT_LIFECYCLES,
    ContractError,
    load_contract,
    repository_declarations_sha256,
)

MANIFEST = Path(__file__).resolve().parents[3] / "codex/config/gitea-governance.json"


class DeploymentLifecycleContractTests(unittest.TestCase):
    @staticmethod
    def _refresh_non_target_digest(raw: dict) -> None:
        next(
            item for item in raw["repositories"] if item["name"] == "NewEMaint"
        )["routine_live_pilot"]["non_target_repositories_sha256"] = (
            repository_declarations_sha256(
                raw["repositories"], exclude_name="NewEMaint"
            )
        )

    def test_three_declarable_lifecycles(self) -> None:
        """三档必须同时存在。少了 selective 这一档，「有链路但只部署一部分 merge」的
        仓库就只能在「假装没有链路」和「等一个不会到来的部署」之间二选一（#192）。"""
        self.assertEqual(
            DEPLOYMENT_LIFECYCLES,
            frozenset({"application-deploy", "application-deploy-selective", "none"}),
        )

    def test_default_is_the_self_healing_option(self) -> None:
        """缺省取可自愈的一档，不是最严的一档。

        #163 曾断言缺省必须是 application-deploy，理由是「反过来会让任何未声明的应用
        仓库在部署之前就被写成 completed」。#192 用两侧的可恢复性推翻了这个比较：早写的
        completed 会被 mark-deployed-issues.sh 剥掉整个生命周期维度重写成 deployed，而
        broker 又拒绝把已 deployed 的 Issue 降级为 completed；漏写方向则没有任何组件会
        回头补——实测是 LocalWMS 上 5 个已合并 Issue 至今一个标签都没有。
        """
        self.assertEqual(
            DEFAULT_DEPLOYMENT_LIFECYCLE, "application-deploy-selective"
        )
        self.assertIn(DEFAULT_DEPLOYMENT_LIFECYCLE, DEPLOYMENT_LIFECYCLES)

    def test_platform_repository_is_declared_none(self) -> None:
        """#163 的核心声明：平台仓库没有会回写 deployed 的应用部署链路。
        它一旦被改回去，#138/#146/#148 那类变更会静默回到「两个终态都没人写」。"""
        contract = load_contract(MANIFEST)
        platform = next(
            repository
            for repository in contract.repositories
            if repository.name == "aisoft-platform"
        )
        self.assertEqual(platform.deployment_lifecycle, "none")
        self.assertFalse(platform.deploys)

    def test_undeclared_repositories_default_to_selective(self) -> None:
        """只遍历未声明的仓库——照 #148 的教训，把「当时谁都没声明」钉成断言会在
        下一个仓库声明时必然变红。"""
        raw = json.loads(MANIFEST.read_text())
        declared = {
            entry["name"]
            for entry in raw["repositories"]
            if "deployment_lifecycle" in entry
        }
        contract = load_contract(MANIFEST)
        checked = 0
        for repository in contract.repositories:
            if repository.name in declared:
                continue
            with self.subTest(repository=repository.name):
                self.assertEqual(
                    repository.deployment_lifecycle, DEFAULT_DEPLOYMENT_LIFECYCLE
                )
                self.assertTrue(repository.deploys)
            checked += 1
        # 防空转：等到所有仓库都显式声明的那天，上面的循环一个都不跑而测试仍然通过，
        # 兜底行为就没有东西守着了，那时必须补一个合成 fixture。
        self.assertGreater(checked, 0, "没有未声明的仓库，缺省断言已空转")

    def test_declaring_one_repository_does_not_touch_the_others(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        raw["repositories"][1]["deployment_lifecycle"] = "none"
        self._refresh_non_target_digest(raw)
        expected = {
            entry["name"]: entry.get(
                "deployment_lifecycle", DEFAULT_DEPLOYMENT_LIFECYCLE
            )
            for entry in raw["repositories"]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(raw))
            contract = load_contract(path)
        declared = contract.repositories[1]
        self.assertEqual(declared.deployment_lifecycle, "none")
        self.assertFalse(declared.deploys)
        for other in contract.repositories:
            if other.name == declared.name:
                continue
            with self.subTest(repository=other.name):
                self.assertEqual(
                    other.deployment_lifecycle, expected[other.name]
                )

    def test_every_declared_lifecycle_round_trips(self) -> None:
        """三档都要能被声明。缺了正向断言，一个只在 DEPLOYMENT_LIFECYCLES 里存在、
        却被别处拒掉的取值会一直读起来像可用。"""
        for value in sorted(DEPLOYMENT_LIFECYCLES):
            with self.subTest(value=value):
                raw = json.loads(MANIFEST.read_text())
                raw["repositories"][1]["deployment_lifecycle"] = value
                self._refresh_non_target_digest(raw)
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "manifest.json"
                    path.write_text(json.dumps(raw))
                    contract = load_contract(path)
                self.assertEqual(
                    contract.repositories[1].deployment_lifecycle, value
                )
                self.assertEqual(
                    contract.repositories[1].deploys, value != "none"
                )

    def test_invalid_deployment_lifecycle_is_rejected(self) -> None:
        """非法取值必须 fail closed。静默回落会让一个写错的声明读起来像生效了。"""
        for invalid in ("", "None", "no", "deployed", "application_deploy",
                        "selective", "application-deploy-partial", True, 1, None):
            with self.subTest(invalid=invalid):
                raw = json.loads(MANIFEST.read_text())
                raw["repositories"][0]["deployment_lifecycle"] = invalid
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "manifest.json"
                    path.write_text(json.dumps(raw))
                    with self.assertRaisesRegex(ContractError, "deployment_lifecycle"):
                        load_contract(path)


if __name__ == "__main__":
    unittest.main()
