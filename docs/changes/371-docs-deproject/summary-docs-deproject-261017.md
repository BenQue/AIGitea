---
issue: 371
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/371
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写平台分册与技能中的项目化内容并归档旧文档，涉及Agent技能与平台治理文本
risk_flags:
  - agent-governance
  - cross-module
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-docs-deproject-261017.md
  spec: spec-docs-deproject-261017.md
  plan: plan-docs-deproject-261017.md
confidence: high
override_reason: ''
depends_on:
  - 368
status: pr-open
branch: change/371-docs-deproject
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/372
created: 2026-10-17
updated: 2026-10-17
---

## 问题/需求总结

整改路线 R3。通用分册、README、参考文档、技能与少量注释中仍有项目名、项目事故和已退出项目的 as-built 叙述，违反 ADR 0001 D2/D3。本票清理这些纯文字内容并收紧 R2 的棘轮基线。

## 影响范围

`01`–`05`、`07`、`08`、`09`（归档）、`12` 两份、`13`、`README.md`、两份 `issue-session-flow` 技能、`private-gitea-access.md`、一个 CI 模板注释、一份工具说明、钉住相关短语的测试、基线与路线。

## 初步方案与建议

见 mapped spec 的逐文件处置表。

## 风险

误删仍有效的规则或教训；测试钉住文档短语导致连锁修改。逐文件处置表与 PR 删除清单控制前者，全量 smoke 控制后者。技能源变化后本机已装技能会漂移（R5 重装）。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写平台分册与技能中的项目化内容并归档旧文档，涉及Agent技能与平台治理文本
risk_flags:
  - agent-governance
  - cross-module
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 改写 Agent 技能与平台治理文档、跨多个模块，强制 complex。
- 证据可由 diff review 与 required CI 复现，不声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。
