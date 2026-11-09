---
issue: 440
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/440
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变项目使用合同的确认点与 Issue 粒度规则，涉及路由表、会话技能、使用合同与路由 runtime，属平台与 Agent 治理、共享核心与外部契约
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
  summary: summary-preprod-batch-flow-261109.md
  spec: spec-preprod-batch-flow-261109.md
  plan: plan-preprod-batch-flow-261109.md
  verification: verification-preprod-batch-flow-261109.md
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
status: analyzed
branch: change/440-preprod-batch-flow
pr_url:
created: 2026-11-09
updated: 2026-11-09
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/440
- 状态：见 front matter `status`；PR：见 `pr_url`
- 文档：见 front matter `documents`。需求、范围、验收与风险只写在 spec，本文件不重复。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变项目使用合同的确认点与 Issue 粒度规则，涉及路由表、会话技能、使用合同与路由 runtime，属平台与 Agent 治理、共享核心与外部契约
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
