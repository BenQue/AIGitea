---
issue: 99
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/99
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
status: ready-for-review
branch: change/99-skill-governance-alignment
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | broker/readable/small/deployment 合同文本与 #89 事实分层 | - | completed |
| T02 | exact Claude installer、双向 drift 与 negative fixtures | T01 | completed |
| T03 | syntax/targeted/smoke、两轴 review、typed push 与单 PR | T02 | in-progress |

## Expected touch points

- `skill-for-claude/SKILL.md`
- `skill-for-claude/install.sh`
- `skill-for-claude/check-drift.sh`
- `skill-for-codex/references/onboarding-runbook.md`
- `templates/project/AGENTS.md`
- `codex/tests/test-install-claude-skills.sh`
- `docs/changes/89-platform-repo-ci/summary-platform-repo-ci-260811.md`
- `docs/changes/99-skill-governance-alignment/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2/3/4/6 | static grep + spec/standards review |
| AC-5 | `bash codex/tests/test-install-claude-skills.sh` with temporary HOME fixtures |
| AC-7 | `bash -n` + ShellCheck + targeted test + `bash codex/tests/smoke.sh` + two-axis review |

## 部署与回滚

本 PR 不部署也不重装 live skill。人工合并后，Codex 侧显式重装
`~/.agents/skills/aisoft-platform`；Claude 侧由 Claude 会话显式重装并运行 drift。回滚为人工 revert
本 PR 后重装上一版；不触碰其它 skills、credentials、provider state 或 required context。
