---
issue: 203
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/203
change_type: test
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
confidence: high
risk_flags: []
depends_on: []
status: pending
branch: change/203-test-parity-package-import
created: 2026-08-25
updated: 2026-08-25
---

# Verification · Issue #203 test_parity 包路径导入

## 基线与范围

- 基线：`origin/main` = `4710784`（Merge PR #202，Issue #196）
- 分支：`change/203-test-parity-package-import`，worktree `/private/tmp/issue-203-test-parity-package-import`
- 环境：macOS Darwin 25.5.0（Mac 交互开发），`Python 3.14.4 (main, Apr  7 2026, 13:13:20) [Clang 21.0.0]`
- 本记录负责证明的 acceptance criteria：AC-1、AC-2、AC-3、AC-4。
  其中 **AC-1b 是 required CI 不跑的确定性命令**（`unittest discover -t codex/runtime`），
  这正是本次变更声明 `verification` 的原因（`03` §3 判据表第二行）。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前复现（`-t codex/runtime`） | FAIL（预期） | 见下方「改动前基线」 |
| 改动前 smoke.sh 写法（不带 `-t`） | OK（预期，17 tests） | 见下方「改动前基线」 |
| AC-1a `discover -s codex/runtime/tests`（smoke.sh 现有写法） | PASS | `Ran 17 tests ... OK` |
| AC-1b `discover -s codex/runtime/tests -t codex/runtime` | PASS | `Ran 17 tests ... OK` |
| AC-2 `bash codex/tests/smoke.sh` | PASS | `Ran 538 tests in 28.591s` / `OK` / `Codex platform static smoke checks passed.`，exit 0 |
| AC-3 `git diff --stat` | PASS | `1 file changed, 1 insertion(+), 1 deletion(-)` |
| AC-4 `grep -rn "^from test_\|^import test_" codex/runtime/tests/*.py` | PASS | 无命中（exit 1） |

### 改动前基线（合并后无法重放）

在同一 checkout、施加改动**之前**执行：

```
$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_parity.py'
.................
----------------------------------------------------------------------
Ran 17 tests in 6.516s

OK

$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -p 'test_parity.py'
  File ".../codex/runtime/tests/test_parity.py", line 18, in <module>
    from test_controller import SUMMARY, FakeGit, FakeGitea, FakeVerifier, verification
ModuleNotFoundError: No module named 'test_controller'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

这条对比确认：故障只由 discover 的 `top_level_dir` 决定，与被测代码无关；
required CI 用的第一种写法看不见它。

### 改动后（AC-1a / AC-1b）

```
$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -p 'test_parity.py'
Ran 17 tests in 5.855s

OK

$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_parity.py'
Ran 17 tests in 5.711s

OK
```

两种调用都跑满 17 条用例（与改动前 OK 那一路的条数一致），无 ImportError。
因此 `codex/tests/smoke.sh` 的 discover 参数**不需要**调整——这也是判级得以停在 small
（不触发 `ci-change` 强制 complex）的直接证据。

### AC-4

```
$ grep -rn "^from test_\|^import test_" codex/runtime/tests/*.py
$ echo $?
1
```

`codex/runtime/tests/` 内不再有裸模块名互导；全部测试统一走包路径。

### AC-2 全量 smoke

```
$ bash codex/tests/smoke.sh
...
----------------------------------------------------------------------
Ran 538 tests in 28.591s

OK
Codex platform static smoke checks passed.
$ echo $?
0
```

538 条 runtime 用例全绿（含 `test_parity` 的 17 条），smoke.sh 的其余静态闸门
（project check、change-template-sync、change-documents/pr-url 等）一并通过。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 两种 discover 调用都能导入并跑完 test_parity | PASS | 上方「改动后（AC-1a / AC-1b）」，各 `Ran 17 tests ... OK` |
| AC-2 `bash codex/tests/smoke.sh` 全绿 | PASS | `Ran 538 tests in 28.591s` / `OK` / `Codex platform static smoke checks passed.`，exit 0 |
| AC-3 不改断言语义，只改导入路径 | PASS | diff 为单文件单行；smoke.sh 未改动 |
| AC-4 tests 目录内无裸模块名互导 | PASS | 上方 grep，exit 1 无命中 |
