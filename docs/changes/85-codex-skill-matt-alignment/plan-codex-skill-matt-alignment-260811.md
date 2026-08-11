---
issue: 85
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/85
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/85-codex-skill-matt-alignment
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | 绑定模型与判级清单改 readable 元组 + 语义文档 + triage 维度；技能路由改 Matt 主路径 + gitea-* 兼容 adapter | `skill-for-codex/SKILL.md` | `rg` 断言 AC-1/2/3/5 关键串 | AC-1/2/3/5 |
| T02 | 模板清单实名化、Matt 初始化条目、triage 标签、readable 分支表述、analyzer 措辞 | `skill-for-codex/references/onboarding-runbook.md` | `rg` + `ls templates/docs/changes/_template/` 逐名比对 | AC-2/3/4/5 |
| T03 | 合同回归 | — | `bash codex/tests/smoke.sh` 全绿（含 #82 处置说明） | AC-6 |

回滚：两文件单 commit revert；无 runtime/状态影响。
