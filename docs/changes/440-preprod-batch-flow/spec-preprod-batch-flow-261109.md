---
issue: 440
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/440
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
depends_on: []
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - GLOSSARY.md
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/aisoft_loop/route_policy.py
  - codex/runtime/tests/project_source_fixture.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/test_route_policy.py
  - codex/runtime/tests/test_session_contract.py
  - docs/changes/440-preprod-batch-flow/plan-preprod-batch-flow-261109.md
  - docs/changes/440-preprod-batch-flow/spec-preprod-batch-flow-261109.md
  - docs/changes/440-preprod-batch-flow/summary-preprod-batch-flow-261109.md
  - docs/changes/440-preprod-batch-flow/verification-preprod-batch-flow-261109.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/execution-adapter.md
  - skills/aisoft-platform/references/getting-started.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-platform/references/route-policy.md
  - skills/issue-session-flow/SKILL.md
  - templates/project/AGENTS.md
  - usage/CONTRACT.md
  - usage/USER-GUIDE.md
  - usage/bundle.json
branch: change/440-preprod-batch-flow
created: 2026-11-09
updated: 2026-11-09
---

# 开发阶段（首次生产发布前）减少 Issue/PR 与确认点

## 目标与原因

新项目在首次生产发布之前也按「一个改动一张 Issue、一个 PR、两个确认点」推进，Issue 与 PR 过多，审批过频。
负责人 2026-11-09 确认：生产阶段保持现有严格度；首次生产发布前的项目改用更轻的流程，只有不同功能或重大变更
才单独开 Issue/PR，并减少确认点。本票在既有 `change_control: development | production` 开关上落实这条规则。

## 方案与决策

- **D1 阶段声明不加字段。** 「开发阶段」就是 `change_control: development`，「生产阶段」就是 `production`
  （未声明仍按 `production`，读取失败仍回落 `production`）。`templates/project/aisoft-project.json` 的缺省值不改
  （保持 fail closed）；上手指南写明：尚未首次生产发布的新项目在采用时声明 `development`。
- **D2 批次 Issue。** `development` 仓库里一张 Issue 承载一个功能或一组相关改动（批次）。spec 用「条目」列出批次内
  各项，每项有自己的 AC。实现中发现的同一目标内的改动，先在 spec 追加条目、AC 与 `git_scope` 并 commit，再实现；
  这不算范围扩张，不升级给人。以下必须单独开 Issue：不同的功能（能独立验收、独立回退）；重大变更，即含高风险 flag
  的改动（照旧完整版 spec + plan）。零散 small 修复并入当前进行中的批次；没有进行中的批次时可单独开 small Issue。
  一张批次 Issue 仍对应一条 exact 分支、一个最终 PR。
- **D3 确认点减为 1 个。** 路由表新增细化规则 `C1`：`change_control: development` 时 `confirm` 改为 `1`。
  `confirm: 1` 表示只有确认点 1：`approved` 同时授权本 Issue exact 分支的 push 与唯一最终 PR；本地验证与
  `aisoft classify --verify N` 读回 `projected` 后，会话直接 `aisoft open-pr`，把原确认点 2 候选的字段写进 PR 通知。
  `confirm: 2` 的含义不变。合同校验：`complex-production` 只能配 `confirm: 2`。最终 PR 只由人合并、PR merge 不传递
  部署授权、暂停与升级条件，全部不变。
- **D4 单向切换到生产。** 首次生产发布之前，项目必须先合并一张把 `change_control` 改为 `production` 的切换 Issue
  （按 complex 判级）。切换前合并或关闭在途批次；切换后的在途 Issue 重新解析路由。之后不切回 `development`。
  写进使用合同 §3 部署流程不变量。
- **D5 平台仓不受影响。** 平台仓是 `production`，`AGENTS.md` 维护规则不变（不在本票范围）。
- **D6 发布包 1.23.0（minor）。** CONTRACT、项目 AGENTS 指针、技能有字节变化，按发布规则同 PR 发版；notes 写明
  开发阶段项目采用后即按单确认点与批次 Issue 工作，生产阶段项目无行为变化。

## 范围与非范围

范围：`git_scope` 所列文件。runtime 只改 `route_policy.resolve_route` 的 `confirm` 取值（新规则 `C1`）与
`contract` 的 `confirm` 闭集及与 process 的一致性校验。

非范围：不改 broker、`open-pr`/推送守卫、终态工具、`change_control` 解析与缺省值、项目 `project.json` 模板与 schema；
不新增阶段字段或批次机器状态；不改平台仓 `AGENTS.md`；不批改存量 change 文档与历史 route 卡。

## Acceptance criteria

- [ ] AC-1 `resolve_route` 对 `development` 仓库（R2 与 R5）产出 `confirm: 1` 并在 `matched_rules` 记 `C1`；
  `production` 仍为 `2`；`validate_route` 拒绝 `complex-production` + `confirm: 1` 与闭集外取值。有单测。
- [ ] AC-2 路由表、`03`、使用合同、项目 AGENTS 模板、issue-session-flow、aisoft-platform 技能（含 getting-started、
  greenfield-planning、execution-adapter）写明批次 Issue、`confirm: 1` 的单确认点、单向切换，表述互不矛盾；
  `confirm: 2` 的现行规则保持原文可读。
- [ ] AC-3 issue-session-flow 的确认点 1/2 标题与既有钉子短语保留，`test_session_contract.py` 增加 `confirm: 1` 规则的钉子。
- [ ] AC-4 发布包 1.23.0（`compatibility: minor`）发布，`bash codex/tests/smoke.sh` 全绿，runtime 全量测试通过。
- [ ] AC-5 平台仓 complex 交叉审查：Codex（未参与实现）只读审查候选 head 至 PASS，记录进 verification 与审查证据索引。

## 风险与回滚约束

- 风险：取消确认点 2 后，开发阶段的 PR 不再经人预览就开出；人合并仍是唯一交付闸门，且开 PR 不部署，风险可控。
- 风险：项目误把已上生产的仓库声明为 `development`。缓解：使用合同把单向切换写成部署不变量。
- 回滚：revert 本 PR 并重发上一版发布包内容；已采用 1.23.0 的项目回到 1.22.1 即恢复两个确认点。

## 接口、数据与兼容性影响

- route 卡 `confirm` 闭集从 `{2}` 扩为 `{1, 2}`；旧卡（全为 2）仍合法。读 route 卡的工具只有合同校验。
- 已采用旧版本的 development 项目不受影响，直到采用 1.23.0；采用后在途 Issue 的 route 卡重新解析为 `confirm: 1`。
- 无数据迁移。

## 未决问题

无。
