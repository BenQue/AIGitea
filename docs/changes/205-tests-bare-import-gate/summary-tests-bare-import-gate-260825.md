---
issue: 205
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/205
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 把 codex/runtime/tests 内「不得裸模块名互导」从当下为真的状态变成两层被执行的闸门；修改 required CI 脚本 codex/tests/smoke.sh 触发 ci-change 强制 complex
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-tests-bare-import-gate-260825.md
  spec: spec-tests-bare-import-gate-260825.md
  plan: plan-tests-bare-import-gate-260825.md
  verification: verification-tests-bare-import-gate-260825.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/205-tests-bare-import-gate
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/206
created: 2026-08-25
updated: 2026-08-25
---

## 问题/需求总结

衍生自 Issue #203 / PR #204（merge commit `d8e2f97`）。#203 修好了 `test_parity.py`
那**一处**裸模块名兄弟导入，但没有留下任何东西阻止它复发。

`codex/tests/smoke.sh` 的 required CI 调用不带 `-t`，`unittest discover` 的
`top_level_dir` 默认取 `-s` 的值，`codex/runtime/tests` 因此进入 `sys.path`，
裸模块名互导在 required CI 下**永远解析得成功**。这一点已被实测复现：在未改动的
`d8e2f97` 上把 `test_parity.py:18` 改回裸名，CI 仍报 `Ran 538 tests ... OK`。

## 影响范围

- `codex/tests/smoke.sh`：discover 调用加 `-t "$ROOT/codex/runtime"`（8 插入 / 1 删除，含解释性注释）。
- `codex/runtime/tests/test_import_hygiene.py`：新增，AST 扫描闸门 + 扫描器自测（5 条测试）。
- `codex/runtime/tests/` 下既有 36 个文件：**零 diff**，无断言被改动。
- 运行时外部行为不变；下游项目不新增任何 check。

## 初步方案与建议

Issue 列出两条候选路径并倾向 A。按证据判定的结果是**两条都要**：

- **A 单独不满足 AC-1 的第二个分句**——实测它的失败信息就是一条裸
  `ModuleNotFoundError`（`Ran 522 tests / FAILED (errors=1)`），而 Issue 作者在 #196
  中亲历过这个阅读体验并把它写成了本 Issue 的背景。
- **B 单独不够强，且 Issue 写的模式在本目录里有活着的盲点**——`codex/runtime/tests/`
  有一个不带 `test_` 前缀的兄弟 helper `release_test_support.py`，当前被 10 个文件
  导入，`^from test_` / `^import test_` 完全拦不住它。

落地时 B 因此收紧为按 **AST** 扫描、兄弟集合取本目录**全部**模块名。A 提供强度
（严格模块名跑全套），B 提供可读性（以「裸模块名互导」的名义失败并给出改法）。

## 风险

- `-t` 导致模块被静默漏发现——比测试变红更难察觉。用同一 commit 上的逐条测试 ID
  对比关掉（538 ≡ 538，`diff` 无输出）。
- 扫描器真空通过（兄弟集合算空、AST 分支写反）——用扫描器自测的正例／反例／非空断言关掉。
- 回滚是纯 revert，无状态、无迁移、无部署影响。

## AI 判级

```yaml
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 把 codex/runtime/tests 内「不得裸模块名互导」从当下为真的状态变成两层被执行的闸门；修改 required CI 脚本 codex/tests/smoke.sh 触发 ci-change 强制 complex
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- **强制 complex 来自 `ci-change`。** 本次变更修改 required CI 脚本
  `codex/tests/smoke.sh`（`codex/tests/smoke.sh:208` 的 discover 调用）。`ci-change`
  在 `codex/runtime/aisoft_loop/classification.py` 的 `FORCED_COMPLEX_RISKS` 里，
  AGENTS.md 也把「CI/制品/部署/回滚」一律按 complex 处理。
- **`contract_effect: unchanged` 是诚实取值。** 五个运行时包的外部行为一个字节没变，
  既有测试断言零改动（AC-4）。变的是 CI 的调用形态与仓库自身的约束，平台把它记在
  `risk_flags` 而不是 `contract_effect` 上。`unchanged` 单独只是 small 候选，
  最终判级由 `ci-change` 决定。
- **路由已确定性复核**：`Classification.from_yaml(...).route()` 返回
  `effective_complexity=complex`、`lifecycle_label=spec-drafting`、
  `complexity_label=complexity/complex`、
  `required_docs=('summary', 'spec', 'plan', 'verification')`、`override_reason=''`。
- **`verification` 的声明依据是证据来源，不是复杂度**（`03` §3）。本次变更有两类
  合并后无法重放的证据：改动前的基线观测（不带 `-t` 会放过裸名）与故意失败的现场
  （改回裸名后 CI 的完整输出）。它们落在判据表的第二行。声明 `verification`
  **不隐含要部署**——本次变更无部署影响。
- **`change_type: test`** 取自 Issue 标题 `test(runtime)`，且交付物确实是测试与测试
  执行方式；没有产品功能被新增或改变，故不落 `feature`/`platform`。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出 AC-1..AC-4；spec 只在 AC-3 上做了一处**收紧**而非改写：
  把「发现并执行的测试数一致」明确为「在同一 commit 上、测试 ID 集合逐条一致」，
  并把本次新增测试文件带来的 +5 单独逐条解释。
