---
issue: 445
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/445
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 项目来源模板推送边界及共享 Git 守卫变更
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-project-template-scope-261110.md
  spec: spec-project-template-scope-261110.md
  plan: plan-project-template-scope-261110.md
  verification: verification-project-template-scope-261110.md
route_provider: codex
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, implement, issue-session-flow
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider+security
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/445-project-template-scope
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/446
created: 2026-11-10
updated: 2026-11-10
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/445
- 文档与状态：见 front matter；负责人已选择仅更新 fresh main 中已有的规范模板。

## AI 判级

```yaml
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 项目来源模板推送边界及共享 Git 守卫变更
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 现行 ADR 0003 D4 明确模板路径只能走站点来源；改变此行为涉及授权与共享 Git 守卫。

### 缺失的 acceptance criteria 或决策

- 无；负责人已明确首次新增规范模板仍须拒绝。
