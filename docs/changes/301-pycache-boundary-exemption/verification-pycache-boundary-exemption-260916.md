---
issue: 301
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/301
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - security
depends_on: []
status: verified
branch: change/301-pycache-boundary-exemption
created: 2026-09-16
updated: 2026-09-16
---

# Verification：release evidence boundary 的 Python 字节码豁免

## 基线与范围

- Commit SHA: `50ba9de4dab7422e6c005e30e69a8a96c4d6286b`（T02），
  其前序为 `a17d3aa8a9ebbc6d3c96cbc48618f3a7a7642755`（T01）与
  `6a57b3a7e56c86ac6dbdde6dd350f11b63caaffe`（合同文档）。
- 基线：`origin/main` = `f6e2e50a57dec93ccec1e7ea58bf760c2309286f`
- 环境：macOS Darwin 27.0.0 (arm64)，CPython 3.14
  （`/opt/homebrew/opt/python@3.14/bin/python3.14`），worktree
  `/private/tmp/issue-301-pycache-boundary-exemption`
- 本记录负责证明的 acceptance criteria：AC-1、AC-2、AC-3、AC-4。
  其中 AC-3 是一次**本地脏工作树**实验：required CI 的工作树永远是干净的，
  它复现不了这个状态，所以证据只能留在这里。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前复现（`origin/main` 代码，植入单个 `.pyc`） | 复现 | `validate(root)` 抛 `current file set differs from the fixed baseline`；`disk_files(root) - set(baseline_files(root))` == `['codex/runtime/aisoft_release/__pycache__/runner.cpython-313.pyc']`；删除该文件后恢复 PASS |
| 先看着测试红（T01） | 红 | `command_env() 必须设置 PYTHONPYCACHEPREFIX…` 与 `AssertionError: 'TAMPERED' != 'SOURCE'`，2 failures |
| 先看着测试红（T02） | 红 | `AssertionError: Items in the first set but not the second: 'codex/runtime/aisoft_release/__pycache__/runner.cpython-313.pyc'`，另加 `validate` 抛 BoundaryError |
| `python3 -B -m unittest tests.test_release_evidence_boundary`（T01 中间态） | PASS | `Ran 20 tests`, `OK` |
| `python3 -B -m unittest tests.test_release_evidence_boundary`（T02 终态） | PASS | `Ran 20 tests`, `OK` |
| `python3 -B codex/tests/check-release-evidence-boundary.py`（T01 中间态） | PASS | `Ran 158 tests`, `OK`, exit 0 |
| `python3 -B codex/tests/check-release-evidence-boundary.py`（T02 终态，干净树） | PASS | `Ran 158 tests`, `OK`, exit 0 |
| **状态 A**：`bash codex/tests/smoke.sh`，干净工作树 | PASS | `Ran 962 tests in 90.579s`, `OK`, `Codex platform static smoke checks passed.`, exit 0 |
| 造脏：`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -p 'test_release*.py'`（**不带** `-B`） | 已造出 | `codex/runtime/aisoft_release/__pycache__/` 下 12 个 `.pyc`，与 Issue 正文记录的 12 项一致 |
| 同一棵脏树上跑**改动前**的检查器（`git show f6e2e50:…`） | FAIL | `FAIL: release evidence boundary: current file set differs from the fixed baseline`, exit 1 |
| 同一棵脏树上跑**改动后**的检查器 | PASS | `Ran 158 tests`, `OK`, exit 0 |
| **状态 B**：`bash codex/tests/smoke.sh`，同一棵脏树（SCOPES 内 12 个 `.pyc`） | PASS | `Ran 962 tests in 88.022s`, `OK`, `Codex platform static smoke checks passed.`, exit 0 |
| 状态 A 与状态 B 的完整 smoke 日志逐行比对 | 一致 | 归一化耗时数字后 `diff` 仅 34 行，全部是临时目录路径与其中随机 fixture 仓库的短 SHA；无任何检查项结论差异 |
| 清理后 `git status --porcelain` | 空 | 脏状态不涉及任何被跟踪文件；`.pyc` 与 `__pycache__` 已全部删除 |

### 守卫反向证明（突变测试）

把 `is_bytecode_artifact()` 的谓词逐一削弱，确认测试真的会拦住：

| 突变 | 结果 |
|---|---|
| `return path.parent.name == "__pycache__"`（退化成路径豁免） | `FAILED (failures=1)` |
| `return path.suffix == ".pyc"`（退化成后缀豁免） | `FAILED (failures=1)` |
| `return False`（豁免失效） | `FAILED (errors=1)` |
| `command_env()` 去掉 `PYTHONPYCACHEPREFIX`（隔离失效） | `FAILED (failures=1, errors=1)` |
| 全部还原 | `Ran 20 tests`, `OK` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 12 个真实 `.pyc` 在位时，`python3 codex/tests/check-release-evidence-boundary.py` exit 0；同一棵树上改动前的检查器 exit 1 |
| AC-2 | PASS | `test_untracked_files_are_rejected_except_python_bytecode_products` 继续拒绝 `extra.py`、`hidden.py`、`__pycache__/notes.md`、`runner.pyc`，只放行 `__pycache__/*.pyc`；三次突变测试证明两个条件都是承重的。`hidden.py` 与 `runner.pyc` 都被 `.gitignore` 覆盖却仍然变红，钉住「判据不是 git 是否忽略它」 |
| AC-3 | PASS | 状态 A 与状态 B 各一次完整 `bash codex/tests/smoke.sh`，均 `Ran 962 tests` / `OK` / exit 0，日志逐行比对无结论差异 |
| AC-4 | PASS | `test_tampered_in_tree_bytecode_is_not_executed`：同一个 header 对齐的篡改 `.pyc`，去掉 `PYTHONPYCACHEPREFIX` 时子进程打印 `TAMPERED`，带上时打印 `SOURCE` |

## 过程中发现并修正的两件事

1. **既有测试显式钉住了相反的合同。**
   `codex/runtime/tests/test_release_evidence_boundary.py` 原有
   `test_ignored_and_untracked_files_including_bytecode_are_rejected`，把
   「包括字节码在内的未跟踪文件一律拒绝」写死。它落在 `test_release*.py` 里，
   因此由检查器自己的 `current_regression()` 执行——第一次全量 smoke 正是红在这里。
   本次没有另起一个并行测试模块，而是把改写后的合同与新增的隔离用例都折回该文件。

2. **测试本身曾经悄悄地什么都证明不了。**
   `importlib.util.cache_from_source()` 会跟随当前进程的 `sys.pycache_prefix`。
   该模块由 `current_regression()` 在**已经设了** `PYTHONPYCACHEPREFIX` 的子进程里
   执行，于是「树内篡改字节码」被写到了树外镜像目录，控制组断言随之从
   `TAMPERED` 变成 `SOURCE`。这一幕只在嵌套运行时出现，单独跑该模块时看不见。
   现在树内缓存路径按 `sys.implementation.cache_tag` 手算，不再依赖环境。

## 遗留风险与未完成项

- `PYTHONPYCACHEPREFIX` 的隔离只覆盖检查器**自己派生**的子进程。任何绕开
  `command_env()` 直接执行 `aisoft_release` 的调用方不在本次范围内；仓库内没有
  这样的调用方，`smoke.sh` 自身也统一 `export PYTHONDONTWRITEBYTECODE=1`。
- 豁免只认 `.pyc`。CPython 3.5 起不再产生 `.pyo`，因此未纳入；若将来出现，
  它会照常让闸门变红——这是有意的 fail-closed 方向。
- 未执行：Docker 相关的真实 E2E（`current_real_e2e`、`installed`、`company_live`
  仍为 `NOT_RUN`），它们由 #65 单独授权，本次未触碰也未推进任何 pin。
- 无部署影响，故删除「部署验收」一节。
