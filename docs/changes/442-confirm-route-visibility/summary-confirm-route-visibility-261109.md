---
issue: 442
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/442
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变随使用发布包分发的会话工具输出（classify 路由行、resolve-route JSON）与 summary 解析报错，属外部契约与共享核心
risk_flags:
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-confirm-route-visibility-261109.md
  spec: spec-confirm-route-visibility-261109.md
  plan: plan-confirm-route-visibility-261109.md
  verification: verification-confirm-route-visibility-261109.md
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
branch: change/442-confirm-route-visibility
pr_url:
created: 2026-11-09
updated: 2026-11-09
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/442
- 状态：见 front matter `status`；PR：见 `pr_url`
- 文档：见 front matter `documents`。需求、范围、验收与风险只写在 spec，本文件不重复。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变随使用发布包分发的会话工具输出（classify 路由行、resolve-route JSON）与 summary 解析报错，属外部契约与共享核心
risk_flags:
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
