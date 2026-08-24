"""Issue #190：「这个仓库持不持有 change 模板的 vendored 副本」必须由 manifest 声明
一次，而不是靠谁记得。这些断言守住 schema 侧的三件事——声明被读进来、未声明者取
「持有」这个更安全的缺省、非布尔取值 fail closed。广播清单本身的行为在
codex/tests/test-change-template-sync.sh 里覆盖。"""

import json
import tempfile
import unittest
from pathlib import Path

from aisoft_gitea_governance.contract import (
    DEFAULT_VENDORS_CHANGE_TEMPLATES,
    ContractError,
    load_contract,
)

MANIFEST = Path(__file__).resolve().parents[3] / "codex/config/gitea-governance.json"


class VendoredChangeTemplatesContractTests(unittest.TestCase):
    def test_default_over_reports_rather_than_missing_a_holder(self) -> None:
        """缺省必须是「持有副本」。反过来会让一个未声明的仓库从广播清单里消失，
        而「持有过期副本却没人告诉它」正是本 Issue 要修的失败模式。"""
        self.assertIs(DEFAULT_VENDORS_CHANGE_TEMPLATES, True)

    def test_platform_repository_is_the_source_not_a_holder(self) -> None:
        """平台仓库是合同源 templates/docs/changes/_template/ 本身，没有
        docs/changes/_template/ 副本。它一旦被读成 holder，广播清单每次都会
        多出一个永远同步不掉的条目。"""
        contract = load_contract(MANIFEST)
        platform = next(
            repository
            for repository in contract.repositories
            if repository.name == "aisoft-platform"
        )
        self.assertFalse(platform.vendors_change_templates)

    def test_undeclared_repositories_default_to_holding_a_copy(self) -> None:
        """只遍历未声明的仓库——照 #148/#163 的写法，把「当时谁都没声明」钉成断言
        会在下一个仓库声明时必然变红。"""
        raw = json.loads(MANIFEST.read_text())
        declared = {
            entry["name"]
            for entry in raw["repositories"]
            if "vendors_change_templates" in entry
        }
        contract = load_contract(MANIFEST)
        checked = 0
        for repository in contract.repositories:
            if repository.name in declared:
                continue
            with self.subTest(repository=repository.name):
                self.assertIs(
                    repository.vendors_change_templates,
                    DEFAULT_VENDORS_CHANGE_TEMPLATES,
                )
            checked += 1
        # 防空转：等到所有仓库都显式声明的那天，上面的循环一个都不跑而测试仍然通过。
        self.assertGreater(checked, 0, "没有未声明的仓库，缺省断言已空转")

    def test_declaring_one_repository_does_not_touch_the_others(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        raw["repositories"][1]["vendors_change_templates"] = False
        expected = {
            entry["name"]: entry.get(
                "vendors_change_templates", DEFAULT_VENDORS_CHANGE_TEMPLATES
            )
            for entry in raw["repositories"]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(raw))
            contract = load_contract(path)
        declared = contract.repositories[1]
        self.assertFalse(declared.vendors_change_templates)
        for other in contract.repositories:
            if other.name == declared.name:
                continue
            with self.subTest(repository=other.name):
                self.assertIs(other.vendors_change_templates, expected[other.name])

    def test_non_boolean_declaration_is_rejected(self) -> None:
        """非布尔取值必须 fail closed。"false" 是真值、0 是假值——静默强转会让一个
        写错的声明读起来像生效了，方向还未必是作者想要的那个。"""
        for invalid in ("", "false", "true", "no", 0, 1, None, []):
            with self.subTest(invalid=invalid):
                raw = json.loads(MANIFEST.read_text())
                raw["repositories"][0]["vendors_change_templates"] = invalid
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "manifest.json"
                    path.write_text(json.dumps(raw))
                    with self.assertRaisesRegex(
                        ContractError, "vendors_change_templates"
                    ):
                        load_contract(path)


if __name__ == "__main__":
    unittest.main()
