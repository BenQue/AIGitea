---
issue: 423
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/423
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/423-karpathy-principles
created: 2026-10-22
updated: 2026-10-22
reason: 改变跨提供者共享技能的工程行为约束与使用层合同，命中 Agent 和平台治理强制 complex。
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-karpathy-principles-261022.md
  spec: spec-karpathy-principles-261022.md
  plan: plan-karpathy-principles-261022.md
  verification: verification-karpathy-principles-261022.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
override_reason: ''
git_scope:
  - 08-双工具共存与实施.md
  - docs/changes/423-karpathy-principles/plan-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/proposals/engineering-principles.patch
  - docs/changes/423-karpathy-principles/spec-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/summary-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/verification-karpathy-principles-261022.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/engineering-principles.md
  - skills/issue-session-flow/SKILL.md
  - usage/CONTRACT.md
  - usage/bundle.json
status: approved
pr_url:
---

## 问题/需求总结

负责人要求研究 Karpathy 启发的技能并将思想集成 AISoftPlatform。采用现有共享技能承载平台适配，不增加技能包。
2026-10-22 负责人确认启动 #423，并明确正文定位为编程思想的纲领性指导，不是具体开发方案；完成后由 Claude Code 独立审议。确认范围是源码实施与验证，不含 PR 提交、安装或项目采用。

## 影响范围

一份共享 reference、三个技能入口、使用合同、08 适配说明、发布包 member/minor release 与本 Issue 文档。
合同保留两个确认点、平台安全边界、单写者、人工合并与独立安装/项目采用边界。

## 初步方案与建议

先完成 T01 治理步骤并停止；fresh run 重读后完成 T02 验证与独立跨提供者审查。T01 已应用纲领性原则与发布包 1.14.0，局部检查通过；该治理步骤随本次原子提交结束。T02 使用 fresh Claude Code 只读上下文重新阅读合同并审议，完整回归和独立审议尚待完成。

## 风险

需防止过度提问、以简化名义删安全校验、只追求小 diff 和无效测试；六场景评审见 spec。
verification 用于一次性来源观测、桌面评审及跨提供者审查，不表示部署。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变跨提供者共享技能的工程行为约束与使用层合同，命中 Agent 和平台治理强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 任意已注册项目都适用，满足 ADR 0001 D4；平台自定义技能属于 D1/D8 允许的交付物。
- `agent-governance` 与 `platform-governance` 触发路由 R3，平台为 production 默认，confirm 固定 2。

### 缺失的 acceptance criteria 或决策

- 无。负责人已确认本合同，并补充纲领性定位及 Claude Code 审议要求；已在 spec 与 plan 落实。
