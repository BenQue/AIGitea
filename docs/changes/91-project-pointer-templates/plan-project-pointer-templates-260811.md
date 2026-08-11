---
issue: 91
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/91
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/91-project-pointer-templates
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | 项目 AGENTS/CLAUDE 模板 | `templates/project/{AGENTS.md,CLAUDE.md}` | `rg` 四段标题与关键串;CLAUDE 单行 | AC-1、AC-2 |
| T02 | runbook §2 接入与回补程序 | `skill-for-codex/references/onboarding-runbook.md` | `rg 'templates/project'` + 断言串保留 | AC-3、AC-4 |
| T03 | 回归 | — | smoke 全绿（叠加 #82 修复验证如需要） | AC-4、AC-5 |

回滚：新文件删除 + runbook 一处 revert。
