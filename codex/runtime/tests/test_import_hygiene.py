"""Issue #205：`codex/runtime/tests/` 内部禁止裸模块名互导。

#203 修好了 `test_parity.py` 那一处 `from test_controller import ...`，但没有留下
任何东西阻止它再长出来。required CI 现在以 `-t "$ROOT/codex/runtime"` 运行 discover
（`codex/tests/smoke.sh`），裸名在那里会变成 `ModuleNotFoundError` ——那是**强**闸门，
覆盖 AST 扫描认不得的写法。可它的失败信息是一条落在几百条测试中间的 ImportError，
读起来像被测代码坏了（2026-08-25 处理 #196 时为此浪费过一轮排查）。

这个模块补的是**可读性**那一半：同一条违规在这里先以「裸模块名互导」的名义失败，
并直接给出改法。两层缺一不可——去掉 `-t`，扫描就只拦得住 AST 认得的形态；去掉扫描，
失败就退回一条裸 ImportError。

扫描按 AST 做而不是按正则：`^from test_` / `^import test_` 拦不住同目录里那个不带
`test_` 前缀的兄弟 helper `release_test_support.py`（当前被 10 个文件导入）。
"""

import ast
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
PACKAGE = TESTS_DIR.name


def _sibling_modules() -> frozenset[str]:
    """本目录里可以被裸名解析到的模块名。"""
    return frozenset(
        path.stem for path in TESTS_DIR.glob("*.py") if path.stem != "__init__"
    )


def _bare_sibling_imports(source: str, siblings: frozenset[str]) -> list[tuple[int, str]]:
    """返回 (行号, 被裸名导入的兄弟模块) 列表。

    只看绝对导入：`from . import x` 与 `from .x import y` 的 `level > 0`，它们本来
    就是包内相对导入，不是本闸门要拦的东西。`import tests.test_controller` 的顶层名
    是 `tests`，同样不算。
    """
    violations: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in siblings:
                    violations.append((node.lineno, top))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                top = node.module.split(".")[0]
                if top in siblings:
                    violations.append((node.lineno, top))
    return violations


class BareSiblingImportTests(unittest.TestCase):
    def test_no_test_module_imports_a_sibling_by_bare_name(self) -> None:
        """闸门本体：整个 tests 目录不得出现裸模块名互导。"""
        siblings = _sibling_modules()
        offences: list[str] = []
        for path in sorted(TESTS_DIR.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            lines = source.splitlines()
            for lineno, module in _bare_sibling_imports(source, siblings):
                statement = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                offences.append(
                    f"  {path.relative_to(REPO_ROOT)}:{lineno}  {statement}\n"
                    f"      → 改成 {PACKAGE}.{module}"
                )
        self.assertEqual(
            offences,
            [],
            "检测到裸模块名互导（#205）——同目录测试模块必须走包路径 "
            f"`from {PACKAGE}.<module> import ...`：\n"
            + "\n".join(offences)
            + "\n  required CI 以 `-t codex/runtime` 运行 discover，裸名在那里是 "
            "ModuleNotFoundError，\n  而导入失败模块的整批测试会从计数里静默消失"
            "（#203/#205）。",
        )

    def test_detector_actually_detects(self) -> None:
        """闸门自身不能静默失效。兄弟集合算错、AST 分支写反，都会让上面那条断言
        真空通过——那是比裸名互导本身更难察觉的失败。"""
        siblings = frozenset({"test_controller", "release_test_support"})
        self.assertEqual(
            _bare_sibling_imports("from test_controller import SUMMARY\n", siblings),
            [(1, "test_controller")],
        )
        self.assertEqual(
            _bare_sibling_imports("import release_test_support\n", siblings),
            [(1, "release_test_support")],
        )
        self.assertEqual(
            _bare_sibling_imports("import test_controller as tc\n", siblings),
            [(1, "test_controller")],
        )

    def test_detector_does_not_flag_package_paths(self) -> None:
        """包路径、相对导入和运行时模块都必须放行，否则闸门会把正确写法逼红。"""
        siblings = frozenset({"test_controller", "release_test_support"})
        for source in (
            "from tests.test_controller import SUMMARY\n",
            "import tests.test_controller\n",
            "from . import test_controller\n",
            "from .test_controller import SUMMARY\n",
            "from aisoft_loop.controller import Controller\n",
        ):
            with self.subTest(source=source.strip()):
                self.assertEqual(_bare_sibling_imports(source, siblings), [])

    def test_sibling_set_is_not_empty(self) -> None:
        """兄弟集合空掉，上面的闸门就退化成一条永远绿的断言。"""
        siblings = _sibling_modules()
        self.assertIn("test_controller", siblings)
        self.assertIn("release_test_support", siblings)

    def test_tests_tree_is_flat(self) -> None:
        """扫描只覆盖 tests/*.py。真出现子包时，裸名解析规则与这里的假设不再一致，
        这条断言必须先变红，逼作者回来扩展闸门，而不是让子包悄悄绕过去。"""
        nested = sorted(
            str(path.relative_to(TESTS_DIR))
            for path in TESTS_DIR.rglob("*.py")
            if path.parent != TESTS_DIR
        )
        self.assertEqual(nested, [], f"tests/ 下出现了子包，闸门需要扩展：{nested}")


if __name__ == "__main__":
    unittest.main()
