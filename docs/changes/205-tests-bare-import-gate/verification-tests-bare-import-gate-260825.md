---
issue: 205
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/205
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: verified
branch: change/205-tests-bare-import-gate
created: 2026-08-25
updated: 2026-08-25
---

# Verification：tests 目录内裸模块名互导的回归闸门

本记录之所以必须存在，是因为本次变更的验收证据落在 `03` §3 表格的第二行：
**改动前的基线观测**（不带 `-t` 会发现什么）和**故意失败的现场**（改回裸名后 CI
长什么样）合并后都无法重放。judgement 依据是证据来源，不是复杂度，也不隐含要部署。

## 基线与范围

- Commit SHA: 工作树基于 `d8e2f97`（`origin/main`，PR #204 的 merge commit）
- 基线：`origin/main` = `d8e2f97` — `Merge pull request 'test(runtime): test_parity 改用包路径导入 test_controller (#203)' (#204)`
- 环境：macOS Darwin 25.5.0，`python3` = CPython 3.14.4（Homebrew），`bash -n` + `shellcheck` 可用，worktree `/private/tmp/issue-205-tests-bare-import-gate`
- 本记录负责证明的 acceptance criteria: AC-1、AC-2、AC-3、AC-4

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| EX-0 基线（未改动树）`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v` | PASS | `Ran 538 tests in 29.158s` / `OK` |
| EX-1 未改动树 + 裸名，**不带** `-t` | PASS（**这正是 bug**） | `Ran 538 tests in 28.463s` / `OK` —— 把 `test_parity.py:18` 改回 `from test_controller import ...` 后 required CI 仍然全绿，Issue 的前提被实测复现 |
| EX-2 未改动树 + 裸名，**带** `-t` | FAILED | `Ran 522 tests` / `FAILED (errors=1)`，错误体为 `ModuleNotFoundError: No module named 'test_controller'`，无任何「裸模块名互导」字样 |
| EX-3 AC-3 逐条 ID 对比（同一 commit，带／不带 `-t`） | PASS | 见下方「AC-3 的逐条对比」 |
| EX-4 落地后 `bash codex/tests/smoke.sh` | PASS | `Ran 543 tests in 29.764s` / `OK` / `Codex platform static smoke checks passed.` |
| EX-5 落地后故意红：`test_parity.py:18` 改回裸名，`bash codex/tests/smoke.sh` | FAILED（预期） | `exit=1`；输出含 `检测到裸模块名互导（#205）`；`Ran 527 tests` / `FAILED (failures=1, errors=1)`；`Codex platform static smoke checks passed.` 未出现（`grep -c` = 0） |
| EX-6 恢复包路径后 `bash codex/tests/smoke.sh` | PASS | 同 EX-4 |
| EX-7 `bash -n codex/tests/smoke.sh` | PASS | `bash -n OK` |
| EX-8 `shellcheck -S warning codex/tests/smoke.sh` | PASS | 无输出，`shellcheck OK` |
| EX-9 `git diff --stat` | PASS | `codex/tests/smoke.sh \| 9 ++++++++-` / `1 file changed, 8 insertions(+), 1 deletion(-)`；既有测试文件零 diff |

EX-1 与 EX-2 只在改动**落地之前**观测得到：`-t` 一旦写进 `smoke.sh`，「不带 `-t`
会不会放过裸名」就无法在同一棵树上重放。

### EX-2 的原始输出（A 单独的失败信息形态）

```
ERROR: tests.test_parity (unittest.loader._FailedTest.tests.test_parity)
ImportError: Failed to import test module: tests.test_parity
  File ".../codex/runtime/tests/test_parity.py", line 18, in <module>
    from test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification
ModuleNotFoundError: No module named 'test_controller'

Ran 522 tests in 22.932s
FAILED (errors=1)
```

这是 spec 里「A 单独不满足 AC-1 第二个分句」的直接证据：红是红了，但信息是一条裸
`ImportError`，并且 `test_parity` 的 16 条测试没有失败——它们从计数里**消失**了
（538 → 522），被一条 `_FailedTest` 顶替。

### EX-5 的原始输出（落地后的失败信息形态）

```
FAIL: test_no_test_module_imports_a_sibling_by_bare_name (tests.test_import_hygiene.BareSiblingImportTests....)
AssertionError: ... : 检测到裸模块名互导（#205）——同目录测试模块必须走包路径 `from tests.<module> import ...`：
  codex/runtime/tests/test_parity.py:18  from test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification
      → 改成 tests.test_controller
  required CI 以 `-t codex/runtime` 运行 discover，裸名在那里是 ModuleNotFoundError，
  而导入失败模块的整批测试会从计数里静默消失（#203/#205）。

Ran 527 tests in 23.146s
FAILED (failures=1, errors=1)
```

同一条违规同时产出一条具名 `FAIL`（违规文件、行号、原句、改法）和 EX-2 那条
`ERROR`。AC-1 的两个分句由此都被满足。

## AC-3 的逐条对比

在**未改动的 `d8e2f97` 工作树**上跑两次 `discover -v`，从 `-v` 输出提取测试 ID，
把带 `-t` 那一侧的 `tests.` 前缀去掉后排序对比：

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover \
  -s codex/runtime/tests -v 2>&1 | grep -oE '\([A-Za-z0-9_.]+\)' | tr -d '()' | sort > before.txt
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover \
  -s codex/runtime/tests -t codex/runtime -v 2>&1 | grep -oE '\([A-Za-z0-9_.]+\)' | tr -d '()' \
  | sed 's/^tests\.//' | sort > after.txt
diff before.txt after.txt
```

结果：

```
before:      538  after:      538
=== diff ===
IDENTICAL: 逐条一致
```

`diff` 无输出、退出 0。538 条测试的 ID 集合在 `-t` 前后**逐条相同**，没有任何模块被
静默漏掉。两次运行本身也都是 `OK`（EX-0 与带 `-t` 版本 `Ran 538 tests in 28.277s / OK`）。

### 计数变化的逐条解释

落地后 required CI 报 `Ran 543 tests`，比基线的 538 多 5 条。增量全部来自本次新增的
`codex/runtime/tests/test_import_hygiene.py`，逐条列出：

| # | 测试 | 作用 |
|---|---|---|
| 1 | `test_no_test_module_imports_a_sibling_by_bare_name` | 闸门本体 |
| 2 | `test_detector_actually_detects` | 扫描器正例自测，防真空通过 |
| 3 | `test_detector_does_not_flag_package_paths` | 扫描器反例自测，防误伤正确写法 |
| 4 | `test_sibling_set_is_not_empty` | 兄弟集合非空，防闸门退化成永远绿 |
| 5 | `test_tests_tree_is_flat` | 出现子包时先变红，防子包绕过扫描面 |

538 + 5 = 543，与 EX-4 的读数一致。**没有任何既有测试因 `-t` 消失。**

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | EX-5：`bash codex/tests/smoke.sh` exit=1，输出含 `检测到裸模块名互导（#205）` 与 `codex/runtime/tests/test_parity.py:18` 及改法，不只是一条裸 ImportError |
| AC-2 | PASS | EX-4 / EX-6：恢复包路径后 `Ran 543 tests ... OK`，`Codex platform static smoke checks passed.` |
| AC-3 | PASS | EX-3：同一 commit 上 538 ≡ 538 且测试 ID 逐条一致（`diff` 无输出）；落地后的 +5 已在上表逐条解释 |
| AC-4 | PASS | EX-9：diff 只含 `codex/tests/smoke.sh`（8+/1-）与新增文件；`codex/runtime/tests/` 下既有 36 个文件零 diff，无断言被改动 |

## 遗留风险与未完成项

- 扫描器的覆盖面止于 `codex/runtime/tests/*.py` 的**静态 AST**。动态导入
  （`__import__("test_controller")`、`importlib.import_module(...)`）扫描不到——那一半
  由 `-t` 兜住：它在运行时同样解析不到裸名。这正是保留两层而不是二选一的原因。
- `test_tests_tree_is_flat` 把「tests/ 目前是平铺目录」钉成断言。将来真要加子包时它会
  先变红，届时须同步扩展扫描面，而不是删掉这条断言。
- 本次变更无部署影响，未执行任何主机侧或环境侧操作。
