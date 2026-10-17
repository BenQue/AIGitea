---
issue: 364
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/364
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增平台边界ADR与整改路线，属于Agent和平台治理决策
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-platform-boundary-adr-261017.md
  spec: spec-platform-boundary-adr-261017.md
  plan: plan-platform-boundary-adr-261017.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/364-platform-boundary-adr
pr_url:
created: 2026-10-17
updated: 2026-10-17
---

## 问题/需求总结

2026-10-17 平台评审发现项目专属需求经代码、模板和通用文档进入平台，治理与证据负担过重。
负责人要求先写平台边界决策，再制定整改计划，然后分批清理。本票交付前两项：
`docs/adr/0001-platform-boundary.md` 与 `docs/governance/remediation-roadmap.md`。

## 影响范围

只新增两份决策与路线文档及本目录三份映射文档。不修改 `AGENTS.md`、技能、runtime、CI、模板或现有文档，不删除任何文件。

## 初步方案与建议

见 mapped spec。ADR 写定平台交付物、内核五类代码、项目数据位置、准入规则、目录归类、两层分离、发布与技能来源、治理预算和事实来源；路线把评审 §6 A–E 落到 R0–R8 批次。

## 风险

决策一经采纳会约束后续所有平台改动；内容只是文档，revert 即可撤销。不改变 NewEMaint 当前依赖的任何能力。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增平台边界ADR与整改路线，属于Agent和平台治理决策
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- AGENTS.md：Agent 或平台治理变更一律 complex。
- 证据可由 diff review 与 required CI 复现，不声明 verification。

### 缺失的 acceptance criteria 或决策

- 无；ADR 的决定内容需要负责人在确认点 1 确认。
