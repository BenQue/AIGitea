"""Issue #163：仓库有没有应用部署链路，必须由 manifest 声明一次，而不是从
required_docs 里推断。这些断言守住 schema 侧的三件事——声明被读进来、
未声明者取更严的缺省、非法取值 fail closed。合取判定本身在
codex/tests/test-mark-completed-issues.sh 里覆盖。"""

import json
import tempfile
import unittest
from pathlib import Path

from aisoft_gitea_governance.contract import (
    DEFAULT_DEPLOYMENT_LIFECYCLE,
    DEPLOYMENT_LIFECYCLES,
    ContractError,
    load_contract,
)

MANIFEST = Path(__file__).resolve().parents[3] / "codex/config/gitea-governance.json"


class DeploymentLifecycleContractTests(unittest.TestCase):
    def test_default_is_the_stricter_option(self) -> None:
        """缺省必须是「假设有部署链路」。反过来会让任何未声明的应用仓库在部署之前
        就被写成 completed——比本 Issue 修的漏写严重得多。"""
        self.assertEqual(DEFAULT_DEPLOYMENT_LIFECYCLE, "application-deploy")
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

    def test_undeclared_repositories_default_to_application_deploy(self) -> None:
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

    def test_invalid_deployment_lifecycle_is_rejected(self) -> None:
        """非法取值必须 fail closed。静默回落会让一个写错的声明读起来像生效了。"""
        for invalid in ("", "None", "no", "deployed", "application_deploy", True, 1, None):
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
