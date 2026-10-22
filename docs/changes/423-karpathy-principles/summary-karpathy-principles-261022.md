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
status: pr-open
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/424
---

## 问题/需求总结

负责人要求研究 Karpathy 启发的技能并将思想集成 AISoftPlatform。采用现有共享技能承载平台适配，不增加技能包。
2026-10-22 负责人确认启动 #423，并明确正文定位为编程思想的纲领性指导，不是具体开发方案；完成后由 Claude Code 独立审议。该次启动确认范围是源码实施与验证。随后负责人明确“确认提交”，授权本分支普通推送、创建唯一最终 PR 与合同内 CI 修复；合并、安装和项目采用仍分别处理。

## 影响范围

一份共享 reference、三个技能入口、使用合同、08 适配说明、发布包 member/minor release 与本 Issue 文档。
合同保留两个确认点、平台安全边界、单写者、人工合并与独立安装/项目采用边界。

## 实施与审议结果

T01/T02 已完成：共享纲领正文、三个技能入口、使用合同、08 说明与 1.14.0 候选登记；精确文件范围以映射 spec 的 git_scope 为准。两次完整 smoke 与最终文案的定向回归通过。
经过三轮 Claude Code 双轴只读审议，最终治理源码候选 `c87b66bb811add3f2556afac17d5531cb65d1b42` 在 R3 两轴均 PASS；两项不阻断文风建议及全部发现处置已记入 verification。负责人确认提交后，已首推核验候选并创建唯一 PR #424（地址见 front matter）；审议后只回填证据，已审源码未变。提交后 CI 按 PR 当前 head 单独读回；未安装或更新项目。

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
