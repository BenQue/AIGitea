---
issue: 87
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/87
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/87-claude-skill-onboarding
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | Claude 版 SKILL.md（v3.4 合同、触发词、分工、Common Mistakes） | `skill-for-claude/SKILL.md` | `rg` 关键串（项目名、$triage #N、24、broker、change/N-短描述） | AC-1 |
| T02 | 安装器与漂移检查 | `skill-for-claude/install.sh`、`check-drift.sh` | `bash -n`；tmp HOME 手跑 | AC-2、AC-3 |
| T03 | 幂等/单源/无凭据测试并接入 smoke | `codex/tests/test-install-claude-skills.sh`、`codex/tests/smoke.sh` | 单测输出 `claude skill install tests passed`；smoke 全绿 | AC-4、AC-5 |
| T04 | 合并后部署步骤写入 PR/验收说明 | 本 change docs | 人工按步执行（`bash skill-for-claude/install.sh` + `check-drift.sh` = CLEAN） | AC-6 |

回滚：新文件删除 + smoke 两行 revert;无状态残留（安装动作在合并后另行执行,可用旧
`~/.claude/skills/aisoft-platform` 备份恢复）。
