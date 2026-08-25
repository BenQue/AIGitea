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
status: contract-drafting
branch: change/205-tests-bare-import-gate
created: 2026-08-25
updated: 2026-08-25
---

# Spec：tests 目录内裸模块名互导的回归闸门

## 目标与原因

`codex/runtime/tests/` 内部的测试模块之间必须走包路径 `from tests.<module> import ...`。
今天全部 36 个文件都满足这条，但那是**一个当下为真的状态，不是一条被执行的约束**。

`codex/tests/smoke.sh` 的 required CI 调用不带 `-t`，`top_level_dir` 默认取 `-s` 的值，
`codex/runtime/tests` 因此被塞进 `sys.path`，裸模块名互导在 required CI 下**永远解析
得成功**。#203 那条 bug 正是因此潜伏到有人换了调用方式才暴露，暴露时是一条落在 538 条
测试中间的 `ModuleNotFoundError`，读起来像被测代码坏了（2026-08-25 处理 #196 时为此
浪费过一轮排查）。

本次变更把这条约束变成两层被执行的闸门。

## 采用的方案：A + B 两层，而不是二选一

Issue 列出两条候选路径并倾向 A。按证据判定的结果是**两条都需要**，理由是两条各自
拦不住对方拦得住的东西：

| | 方案 A（`-t`） | 方案 B（扫描断言） |
|---|---|---|
| 覆盖面 | 严格模块名跑全套，任何解析不到的写法都会炸 | 只拦扫描器认得的形态 |
| 失败信息 | 一条 `ModuleNotFoundError`，落在几百条测试中间 | 直接以「裸模块名互导」的名义失败并给出改法 |

- **A 单独不满足 AC-1 的第二个分句。** AC-1 要求失败信息「能指向裸模块名互导而不只是
  一条裸 ImportError」。实测 A 的输出就是一条裸 `ModuleNotFoundError`（证据见
  verification 的 EX-1），而 Issue 作者在 #196 中亲历过这个阅读体验并把它写成了本
  Issue 的背景。
- **B 单独不够强，且 Issue 写的模式在本目录里有活着的盲点。** `codex/runtime/tests/`
  里有一个不带 `test_` 前缀的兄弟 helper `release_test_support.py`，当前被 10 个文件
  导入；Issue 描述的 `^from test_` / `^import test_` 模式完全拦不住
  `from release_test_support import ...`。

因此 B 在实现上做两点收紧：按 **AST** 而不是正则扫描，且兄弟集合取**本目录全部模块名**
而不是 `test_` 前缀模块。

## Acceptance criteria

- [ ] **AC-1** 在任一 tests 文件里改回裸模块名后 `bash codex/tests/smoke.sh` 变红，
      且失败信息以「裸模块名互导」的名义出现，并给出违规文件、行号与改法。
- [ ] **AC-2** 恢复包路径后 `bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-3** 在**同一 commit**（`origin/main` = `d8e2f97`，本次新增测试文件之前）
      上对比加 `-t` 前后 CI 发现并执行的测试：数量一致，且测试 ID 集合在去掉
      `tests.` 前缀后**逐条一致**。本次新增测试文件带来的计数增量单独逐条解释。
- [ ] **AC-4** 不改动任何既有测试的断言语义；既有测试文件零 diff。

## 接口、数据与兼容性影响

- 运行时（`aisoft_loop`、`aisoft_release`、`aisoft_architecture`、`aisoft_host_access`、
  `aisoft_gitea_governance`）的外部行为不变；`contract_effect: unchanged`。
- 变的是 required CI 的调用形态与新增一个测试模块。`ci-change` 因此进入 `risk_flags`，
  按 `classification.py` 的 `FORCED_COMPLEX_RISKS` 强制 complex。
- 对下游项目零影响：闸门只作用于本仓库的 `codex/runtime/tests/`，不向任何目标仓库
  新增 check（与 #190 对 `change-template-sync` 的 `downstream_required_check:
  forbidden` 立场一致）。

## 风险与回滚约束

- 主要风险是 `-t` 导致模块被静默漏发现——发现数变少比测试变红更难察觉。AC-3 用
  逐条 ID 对比而不是只比总数来关掉这个风险。
- 次要风险是扫描器真空通过（兄弟集合算空、AST 分支写反）。用扫描器自测
  （正例、反例、非空断言）关掉。
- 回滚是纯 revert：撤掉 `smoke.sh` 的 `-t` 与新增测试文件即可，无状态、无迁移。

## 非目标

- 不改任何既有测试的断言。
- 不重排、不重命名 `codex/runtime/tests/` 下的任何既有文件。
- 不给下游项目新增任何 check。
- 不处理 `codex/tests/*.sh` 那批 shell 测试的组织方式。

## 未决问题

- 无。
