---
issue: 436
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/436
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变所有路由的文档义务（small 与 development 也交付 spec），同步合同、路由表、模板、技能、会话工具与发布包；属平台治理与共享核心
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
  summary: summary-spec-for-every-issue-261031.md
  spec: spec-spec-for-every-issue-261031.md
  plan: plan-spec-for-every-issue-261031.md
  verification: verification-spec-for-every-issue-261031.md
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
branch: change/436-spec-for-every-issue
pr_url:
created: 2026-10-31
updated: 2026-10-31
---

## 索引

- Issue：[#436](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/436) 统一所有 Issue 的 spec 要求与轻量文档流程
- 需求、范围、验收与风险：见映射的 spec；本文件只作索引与机器元信息。
- PR：见 front matter `pr_url`。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变所有路由的文档义务（small 与 development 也交付 spec），同步合同、路由表、模板、技能、会话工具与发布包；属平台治理与共享核心
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

- `contract_effect: change`：small 与 development 的文档最低义务从 summary 改为 summary+spec（`classification.py` `route()`、`contract.py` `spec_required`）。
- 改 `AGENTS.md`、技能与路由表（`platform-governance`、`agent-governance`）；`classification`/`route_policy`/`ticket_execution` 是所有项目共用的核心（`shared-core`）；模板与 `usage/CONTRACT.md` 随发布包下发（`external-contract`）。
- 平台仓 `change_control: production` → R3。`verification` 记录交叉审查与发布包/模板 digest 读回。

### 缺失的 acceptance criteria 或决策

- 无；D2 由负责人 2026-10-31 选 A（development complex 含高风险 flag 时必须有 plan）。
