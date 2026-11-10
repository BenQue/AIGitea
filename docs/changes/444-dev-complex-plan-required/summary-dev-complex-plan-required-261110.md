---
issue: 444
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/444
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变路由表文档义务与随使用发布包分发的使用合同、技能与会话工具的 plan 判定，属平台治理与共享核心
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-dev-complex-plan-required-261110.md
  spec: spec-dev-complex-plan-required-261110.md
  plan: plan-dev-complex-plan-required-261110.md
  verification: verification-dev-complex-plan-required-261110.md
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
override_reason: ''
depends_on: []
status: approved
branch: change/444-dev-complex-plan-required
pr_url:
created: 2026-11-10
updated: 2026-11-10
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/444
- 状态：见 front matter `status`；PR：见 `pr_url`
- 文档：见 front matter `documents`。需求、范围、验收与风险只写在 spec，本文件不重复。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变路由表文档义务与随使用发布包分发的使用合同、技能与会话工具的 plan 判定，属平台治理与共享核心
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改 `skills/aisoft-platform/references/route-policy.md`「文档义务」与 `codex/runtime/aisoft_loop` 的文档义务读取，属平台治理与共享核心。
- 使用合同 `usage/CONTRACT.md` 与项目模板随发布包分发，属外部契约。
