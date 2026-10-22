---
issue: 420
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/420
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/420-onboarding-guide
created: 2026-10-22
updated: 2026-10-22
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | AI 上手指南 `getting-started.md` 与 SKILL.md 入口行，命令逐条核对 | - | done |
| T02 | 简明手册 `usage/USER-GUIDE.md` 与 README 导航行 | T01 | done |
| T03 | 发布包登记新 reference、发布 1.13.0，smoke 与反向证明 | T02 | done |
| T04 | Codex 交叉审查、verification 与 review-evidence-index 回写 | T03 | done |

## Expected touch points

- T01：`skills/aisoft-platform/references/getting-started.md`、`skills/aisoft-platform/SKILL.md`
- T02：`usage/USER-GUIDE.md`、`README.md`
- T03：`usage/bundle.json`，以及 smoke 要求同步的计数或钉子（如有）
- T04：本目录 verification、`docs/governance/review-evidence-index.md`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 逐条 `rg` 核对指南中的脚本与子命令；人读一遍三节 |
| AC-2 | 审查指南中每个需 sudo/注册/manifest 的步骤都标维护者 |
| AC-3 | 链接检查（相对路径存在） |
| AC-4 | `bash codex/tests/smoke.sh`；临时副本写入站点主机名后守卫变红 |
| AC-5 | `codex/tools/usage-bundle.sh --verify`；`--build` 到临时目录后 ls 三处落点 |
| AC-6 | `codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="high"` 审查候选 head |

## 部署与回滚

无部署影响；回滚为 revert 本 PR。技能改动合并后需维护者在 Mac 重装技能并读回漂移（收尾时给出命令）。
