---
issue: 436
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/436
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
  - 04-Agent编排与定时任务.md
  - 08-双工具共存与实施.md
  - AGENTS.md
  - GLOSSARY.md
  - README.md
  - codex/config/change-template-sync.json
  - codex/runtime/aisoft_loop/classification.py
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/aisoft_loop/route_policy.py
  - codex/runtime/aisoft_loop/ticket_execution.py
  - codex/runtime/tests/test_analysis.py
  - codex/runtime/tests/test_change_control.py
  - codex/runtime/tests/test_classification.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/project_source_fixture.py
  - codex/runtime/tests/test_main_integration.py
  - codex/runtime/tests/test_project_source_e2e.py
  - codex/runtime/tests/test_project_source_tools.py
  - codex/runtime/tests/test_required_documents.py
  - codex/runtime/tests/test_route_policy.py
  - codex/runtime/tests/test_ticket_execution.py
  - codex/runtime/tests/test_vendored_change_templates.py
  - codex/tests/fixtures/classification/small.yaml
  - codex/tests/smoke.sh
  - codex/tests/test-aisoft-entry.sh
  - codex/tools/aisoft
  - docs/changes/436-spec-for-every-issue/plan-spec-for-every-issue-261031.md
  - docs/changes/436-spec-for-every-issue/spec-spec-for-every-issue-261031.md
  - docs/changes/436-spec-for-every-issue/summary-spec-for-every-issue-261031.md
  - docs/changes/436-spec-for-every-issue/verification-spec-for-every-issue-261031.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/execution-adapter.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/aisoft-platform/references/route-policy.md
  - skills/gitea-analyze-change/SKILL.md
  - skills/gitea-development-loop/SKILL.md
  - skills/gitea-spec-plan/SKILL.md
  - skills/issue-session-flow/SKILL.md
  - templates/docs/changes/_template/spec.md
  - templates/docs/changes/_template/summary.md
  - templates/project/AGENTS.md
  - usage/CONTRACT.md
  - usage/USER-GUIDE.md
  - usage/bundle.json
branch: change/436-spec-for-every-issue
created: 2026-10-31
updated: 2026-10-31
---

# 所有 Issue 交付 spec，small/development 用简版

## 目标与原因

平台合同允许 small 与 development complex 不写 spec，而 typed 推送守卫（`aisoft_main_integration.scope()`）
无条件从映射 spec 读取 `git_scope`。按合同合规的 small/development 变更因此无法经 typed 推送交付（#436 实证）。
负责人决定：所有 Issue 都交付 spec，small/development 用简版，plan 可省略；summary 收缩为短索引。
本票让合同、路由表、模板、技能、会话工具与发布包都按这条规则一致，推送守卫保持不变。

## 方案与决策

- **D1 文档义务表**（唯一来源写进 route-policy 的新节「文档义务」，`03`/CONTRACT/技能只引用）：

  | 路由 | summary | spec | plan |
  |---|---|---|---|
  | R5 small | 短索引 | 简版 | 不写 |
  | R2 development complex，无高风险 flag | 短索引 | 简版 | 不写，合成 `T01` 取 spec 的验收 |
  | R2 development complex，含高风险 flag | 短索引 | 完整版 | 必须（D2） |
  | R3/R4 production complex | 短索引 | 完整版 | 必须（不变） |

  「高风险 flag」沿用 route-policy 已有定义（含 `change_type: security|data`）。`verification` 规则不变。
- **简版 spec**：front matter（issue/branch 绑定、`git_scope`）+ 目标、范围与非范围、Acceptance criteria，需要时
  加风险与回退。**完整版**另加接口/数据/兼容影响与「未决问题」（approved 前须清空），即现行模板。两者共用一份
  模板，模板注释标出哪些节简版可删。不设行数硬上限。
- **D2（负责人 2026-10-31 选 A）**：development complex 含高风险 flag 时必须有 plan，按 Txx 执行；
  无高风险的 development complex 仍免 plan。路由卡八键不变（R2 的 method 仍是 `tdd`），plan 是文档义务；
  `ticket_execution` 有映射 plan 时读 plan，没有时才合成 `T01`。
- **D3 summary 短索引**：正文只留 `## 索引`（Issue、状态、文档、PR 指针）与 `## AI 判级` YAML；front matter 机器字段不变。
  analyzer 输出节同步改为这两节。存量 summary 只读兼容，不改写。
- **D4 验收来源统一为 spec**：small 与 development 的合同验收、合成 `T01` 都从映射 spec 读取，不再读 Issue 正文。
  triage 判 small 时仍要求 Issue 有可测验收（`analysis.py` 不变）。
- **D5 确认点 1 预检**：`aisoft classify N`（计划模式）在路由行后打印一行「文档预检」：
  route 最低角色已声明且有文件、spec 绑定 exact issue/branch、`git_scope` 非空并包含全部映射文档路径；
  缺项时逐条写出补齐办法。确认点 1 候选要求预检 OK。推送守卫 `scope()` 不改。
- **D6 兼容边界**：`check-change-documents` 不追溯检查存量 change 的文档义务；新义务只由预检与合同校验施加于
  新变更。下游采用新发布包后生效；发布说明写迁移方式。

## 范围与非范围

范围：`git_scope` 所列文件。runtime 只改 `classification.route()` 最低文档、`contract.load_contract` 的 spec 校验分级、
`route_policy` 返回文档义务与预检函数、`ticket_execution` 的合成 `T01` 来源、`aisoft classify` 计划模式输出。

非范围：不改 `scope()`、`_pull_body`、`open-pr`/`backfill-pr-url` 的守卫逻辑（只补测试）；不放宽 spec/`git_scope`
要求；不新增 PR 列表 API；不改下游项目仓；不批改存量 change 文档；不改 ADR 0002 的历史决策正文。

## Acceptance criteria

- [ ] AC-1 合同、route-policy、`03`、`AGENTS.md`、模板与技能对文档义务表述一致；平台仓非历史文本里
  `rg` 不再出现「small/development 不写 spec」类说法（来历表与已合并 change 目录除外）。
- [ ] AC-2 small 与无高风险 development complex 在「短 summary + 简版 spec（含 `git_scope`）+ 无 plan」时：
  合同校验通过，预检 OK，`scope()` 通过；`open-pr` 首推/建 PR/回填路径有测试覆盖。含高风险的 development complex
  必须有 plan，缺 plan 时预检与合同校验拒绝，分别测试。
- [ ] AC-3 负向用例继续拒绝：缺 spec；spec 缺 `git_scope` 或绑定不符；提交超出 `git_scope`；错误 Issue/branch；
  main 漂移；非 owner；远端分支移动（新增缺 spec 的 small/development 用例，其余以现有测试读回）。
- [ ] AC-4 production complex 现有行为（spec+plan、Txx）不回退，原有测试全部通过，`bash codex/tests/smoke.sh` 绿。
- [ ] AC-5 发布新的使用发布包版本，notes 写明下游影响与迁移；`change-template-sync` digest 刷新；存量 change 兼容规则写入 `03`。
- [ ] AC-6 预检缺 spec、缺 `git_scope`、`git_scope` 漏映射文档时各给出明确补齐提示，有测试。

## 风险与回退

- 下游 development 项目采用后，在途无 spec 的变更需补简版 spec；发布说明写清。回退：revert 本 PR 并重发上一版内容。
- 模板 digest 变化会让持有副本的项目 `change-templates` 变 GAP，直到同步；这是既有广播机制的预期行为。

## 未决问题

无。
