---
issue: 420
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/420
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增随技能分发的上手指南与单独的简明用户手册，改动平台技能 references 与使用发布包成员并发布新版本，属于 Agent 与平台治理变更
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-onboarding-guide-261022.md
  spec: spec-onboarding-guide-261022.md
  plan: plan-onboarding-guide-261022.md
  verification: verification-onboarding-guide-261022.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: grill-me, to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/420-onboarding-guide
pr_url:
created: 2026-10-22
updated: 2026-10-22
---

## 问题/需求总结

平台现有的 `onboarding-runbook.md` 面向维护者（governance 注册、host-role、CI/部署）。新用户缺一条按所用工具
（Claude Code、Codex、Cursor）准备本机环境、拿到新项目、跑通第一张 Issue 的路径。负责人要求两份交付：
随平台技能分发、AI 能逐步执行与核对的上手指南，以及一份给新用户直接阅读的简明使用手册。

## 影响范围

- `skills/aisoft-platform/references/` 新增上手指南；`skills/aisoft-platform/SKILL.md` 加一行入口。
- `usage/` 新增简明用户手册（平台仓文档，不是发布包成员）。
- `README.md` 文档导航加一行；`usage/bundle.json` 登记新 reference 并发布 1.13.0。
- 治理表：`docs/governance/review-evidence-index.md` 追加本批一行。

## 初步方案与建议

见 spec。负责人在线程里选定「技能参考文件」形态，并要求另有单独的简明手册。

## 风险

- 指南里的命令与现行脚本漂移：每条命令在源码中逐条核对存在，并由 smoke 既有守卫兜底站点值与个人路径。
- 与并行的 README 现行性检查撞行：只新增行，不改既有导航行；先合并者为准，后者集成 main。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增随技能分发的上手指南与单独的简明用户手册，改动平台技能 references 与使用发布包成员并发布新版本，属于 Agent 与平台治理变更
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

- 改动平台技能（`skills/aisoft-platform/`）属于 Agent 治理，AGENTS.md「判级与确认」强制 complex。
- 技能 references 是使用发布包成员，须同 PR 发布新版本（平台治理）。
- 交叉审查结论不能由 diff review 与 CI 重放，故声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。
