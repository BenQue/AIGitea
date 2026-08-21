---
issue: 134
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/134
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/134-change-control-phase
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/135
created: 2026-08-21
updated: 2026-08-21
---

# Plan · 按交付阶段分级 required_docs（#134）

```
T01 ──> T02 ──> T03 ──> T04 ──> T05
```

## T01 · governance manifest schema

`_exact_keys` 增加 `optional` 参数；`RepositoryContract` 增加 `change_control`（默认 `production`）与 `in_development`；新增 `CHANGE_CONTROL_PHASES` 常量并校验取值。

**验收（AC-1、AC-2）**：既有 10 个仓库解析为 `production`；非法取值抛 `ContractError`；未知键仍被拒绝。

## T02 · 判级运行时

`Classification.route` 增加 `change_control` 关键字参数；`development` 去掉 spec/plan，`verification` 的条件保持不变。

**验收（AC-3、AC-5）**：两阶段 `required_docs` 符合 spec 表格；`small` 不受影响；非法阶段值 fail closed；analyzer 未要求 verification 时两阶段都不含它。

## T03 · 合同校验与验收标准来源

`load_contract` 增加 `change_control`；无 spec 时 acceptance criteria 改取 Issue 正文，缺失仍然拒绝。

**验收（AC-4、AC-5）**：`development` 的 complex 缺 spec/plan 可通过；缺可测验收被拒；`production` 行为不变（含缺省调用）。

## T04 · 解析链路接线

新增 `change_control.py`；`cli` 从 `GITEA_REPO` 解析后传给 `analyze_route` 与 `Controller`；`Controller` 透传给 `load_contract`。

**验收**：解析器的五条不确定路径全部回落 `production`。

## T05 · 文档与全量回归

更新 `03-Issue-Spec-Plan与单闸门开发流程.md`。

**验收（AC-6）**：`python3 -m unittest discover` 与 `bash codex/tests/smoke.sh` 均退出 0；既有断言无放松。
