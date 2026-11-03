---
issue: 438
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复技能 frontmatter 是合法 YAML 的既有合同；改的是随发布包下发的技能正文，并新增 smoke 守卫，属 Agent 治理与 CI 变更
risk_flags:
  - agent-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-skill-frontmatter-yaml-261103.md
  spec: spec-skill-frontmatter-yaml-261103.md
  plan: plan-skill-frontmatter-yaml-261103.md
  verification: verification-skill-frontmatter-yaml-261103.md
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
branch: change/438-skill-frontmatter-yaml
pr_url:
created: 2026-11-03
updated: 2026-11-03
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
- 状态：见 front matter `status`；PR：见 `pr_url`
- 文档：见 front matter `documents`。需求、范围、验收与风险只写在 spec，本文件不重复。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复技能 frontmatter 是合法 YAML 的既有合同；改的是随发布包下发的技能正文，并新增 smoke 守卫，属 Agent 治理与 CI 变更
risk_flags:
  - agent-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: restore`：技能 frontmatter 本应是合法 YAML；8 个平台技能里只有 `skills/aisoft-platform/SKILL.md` 第 3 行 description 含未加引号的 `: `，Ruby Psych 报 `mapping values are not allowed in this context at line 3 column 262`，其余 7 个解析通过。
- `agent-governance`：改技能正文，且它是 `usage/bundle.json` 成员，要同 PR 发布新版本。
- `ci-change`：在 `codex/tests/smoke.sh`（required check 的一部分）登记新守卫。
- 平台仓 `change_control: production` 且含高风险 flag → 路由表 R3；文档义务 D4（完整版 spec + plan）。`verification` 记录反向证明（旧字节被守卫拦下）与交叉审查。

### 缺失的 acceptance criteria 或决策

- 无。Issue 附带的「全局与项目两份同名技能」观察不在本批范围，见 spec 非范围。
