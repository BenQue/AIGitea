---
issue: 203
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/203
change_type: test
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 把 test_parity 唯一一处裸模块名兄弟导入改成与其余 10 个测试一致的包路径，恢复 unittest discover 在 -t 下的可导入性，不触及任何被测代码或断言语义
risk_flags: []
required_docs:
  - summary
  - verification
documents:
  summary: summary-test-parity-package-import-260825.md
  verification: verification-test-parity-package-import-260825.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/203-test-parity-package-import
pr_url:
created: 2026-08-25
updated: 2026-08-25
---

## 问题/需求总结

`codex/runtime/tests/test_parity.py:18` 用裸模块名导入同目录的兄弟测试模块：

```python
from test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification
```

这条写法只在 `unittest` 的 `top_level_dir` 恰好等于 `codex/runtime/tests` 时成立。
`codex/tests/smoke.sh:208` 的调用不带 `-t`，`top_level_dir` 默认取 `-s` 的值，测试模块
被载为顶层名 `test_parity`，裸名互导可行——所以 required CI 一直是绿的。换成同样合理的

```
PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime
```

模块名变成 `tests.test_parity`，裸名 `test_controller` 不在任何搜索路径上，于是报

```
ERROR: tests.test_parity (unittest.loader._FailedTest.tests.test_parity)
ModuleNotFoundError: No module named 'test_controller'
```

代价是排查误导：这条 ImportError 出现在 520+ 条测试中间，读起来像被测代码坏了，
实际只是 discover 的调用方式不同。2026-08-25 处理 Issue #196 时已经为此浪费过一轮排查。

## 影响范围

- `codex/runtime/tests/test_parity.py`：仅第 18 行的 import 路径。
- 不触及 `codex/tests/smoke.sh`：见下方判级证据，包路径写法在 smoke.sh 现有调用下同样成立，
  因此本次变更不构成 CI 脚本改动。
- 不触及 `aisoft_loop` 任何被测模块、任何断言、任何 fixture 语义。

## 初步方案与建议

改成与其余测试一致的包路径：

```python
from tests.test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification
```

`codex/runtime/tests/__init__.py` 已存在，`PYTHONPATH=codex/runtime` 下 `tests` 本来就是
可导入的包；`test_release_*.py`、`test_company_delivery.py` 等 10 个文件早已在用
`from tests.release_test_support import ...`。这次只是把最后一处例外拉回同一约定。

## 风险

- **双重导入**：不带 `-t` 时 `test_controller` 会同时以顶层名（被 discover 载入）和
  `tests.test_controller`（被本文件 import）存在两份模块对象。`test_controller` 里被引用的
  只有 `SUMMARY` 常量与 `FakeGit`/`FakeGitea`/`FakeVerifier`/`verification` 这几个无跨实例
  可变状态的测试替身，不存在需要跨两份模块共享的模块级状态；AC-1a 的实跑覆盖了这一路径。
- **未做的事**：没有加「禁止裸模块名互导」的回归闸门。加闸门要么改 `smoke.sh`（强制 complex），
  要么新增一个跨文件扫描测试，两者都超出本 Issue 的方向；若日后再复发，应作为独立 Issue 处理。

## AI 判级

```yaml
change_type: test
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 把 test_parity 唯一一处裸模块名兄弟导入改成与其余 10 个测试一致的包路径，恢复 unittest discover 在 -t 下的可导入性，不触及任何被测代码或断言语义
risk_flags: []
required_docs:
  - summary
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: unchanged`：diff 只有一行 import 路径。被导入的名字集合、`test_parity`
  的 17 条用例与全部断言逐字不变，`aisoft_loop` 产品代码零改动，外部行为无任何变化。
- `change_type: test`：改动范围完全落在 `codex/runtime/tests/` 内。`test` 不在
  `FORCED_COMPLEX_TYPES`（feature/platform/security/data）里。
- `risk_flags: []`，特别是**没有 `ci-change`**：候选修复在 smoke.sh 现有调用
  （`-s codex/runtime/tests`，不带 `-t`）下实跑 17/17 OK，因此 `codex/tests/smoke.sh` 无需
  改动。判级前先验证了这一点，正是为了确定强制 complex 的 CI 规则不适用（见 verification AC-1a）。
- 非治理文件：不涉及 `AGENTS.md`、Agent 行为、controller、CI/部署脚本。
- 范围局部、可简单 revert（单行），且 Issue #203 带可测验收标准 AC-1..AC-4。
- 由此 route：`change_type` 不强制、`contract_effect` 不在 {add, change}、`risk_flags` 空、
  `confidence: high` → `complexity/small`、`approved`。

### 声明 `verification` 的理由

AC-1 的后半条（`-t codex/runtime` 调用）是一条 **required CI 不跑的确定性命令**，
落在 `03` §3 判据表的第二行，因此本次变更欠一份验证记录。声明 `verification` 不隐含要部署。

### 缺失的 acceptance criteria 或决策

- 无。
