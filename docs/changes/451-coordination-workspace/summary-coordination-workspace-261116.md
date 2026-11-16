---
issue: 451
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/451
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 调整调度会话的合法位置并新增可选的跨项目协调工作区角色边界，同时对齐两处自主采用表述，属于 Agent 与平台治理变更，按强制 complex 处理。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-coordination-workspace-261116.md
  spec: spec-coordination-workspace-261116.md
  plan: plan-coordination-workspace-261116.md
  verification: verification-coordination-workspace-261116.md
route_provider: claude
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: '负责人 2026-11-16 在本票线程回复确认，批准合同并启动实施，未对会话提出的执行强度问题另作说明。会话元数据读回 model claude-opus-5-5、effort medium，与路由 effort max 不一致。T01 按此实际强度执行并如实记录，是否认可由负责人裁决。路由卡其余各格不变。'
depends_on: []
status: approved
branch: change/451-coordination-workspace
pr_url:
created: 2026-11-16
updated: 2026-11-16
---

## 索引

- Issue：[#451](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/451)。状态、PR 和文档映射以 front matter 为准。
- 需求、已确认决定、授权边界、精确文案、验收与风险见 spec；Txx 与验证计划见 plan；准备阶段与后续真实执行记录见 verification。
- 本票只交付平台最小适配。协调工作区仓库自身的建立、采用与试点归它自己的 Issue，见 spec「后续阶段归属」。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 调整调度会话的合法位置并新增可选的跨项目协调工作区角色边界，同时对齐两处自主采用表述，属于 Agent 与平台治理变更，按强制 complex 处理。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: '负责人 2026-11-16 在本票线程回复确认，批准合同并启动实施，未对会话提出的执行强度问题另作说明。会话元数据读回 model claude-opus-5-5、effort medium，与路由 effort max 不一致。T01 按此实际强度执行并如实记录，是否认可由负责人裁决。路由卡其余各格不变。'
```

### 判级证据

- Issue 正文自述「涉及平台/Agent 治理与跨仓协作，后续正式 triage 应按强制 complex 规则处理」。
- 实际改动落在 `skills/issue-session-flow`、`skills/aisoft-platform` 与 `skills/aisoft-matt-workflow`，均为 Agent 行为与平台治理文件，命中 AGENTS.md「Agent 与平台治理一律 complex」。
- 平台仓 `change_control` 为 production，含高风险 flag，路由表命中 R3 与文档义务 D4。

### 缺失的 acceptance criteria 或决策

- 无。D1–D6 与 Home 参数由负责人于 2026-11-16 确认，原话与来源见 spec。
