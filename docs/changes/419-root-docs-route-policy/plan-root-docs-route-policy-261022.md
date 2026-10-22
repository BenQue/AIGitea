---
issue: 419
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/419
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
depends_on: []
branch: change/419-root-docs-route-policy
created: 2026-10-22
updated: 2026-10-22
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | AGENTS.md 开发编排对齐路由表（AC-1） | - | pending |
| T02 | README §4、§5、§8 三处修正（AC-2、AC-3、AC-4） | - | pending |
| T03 | 验证、反向证明、交叉审查与治理表两行（AC-5、AC-6、AC-7） | T01, T02 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。

## Expected touch points

- T01：`AGENTS.md`
- T02：`README.md`
- T03：本目录 verification，`docs/governance/remediation-roadmap.md`，`docs/governance/review-evidence-index.md`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `grep -F 'references/route-policy.md' AGENTS.md`、`grep -F executing-plans AGENTS.md`、`wc -c AGENTS.md`、smoke |
| AC-2 | `grep -n route-policy.md README.md` 命中 §4 与 §5 |
| AC-3 | README §5 的 08 行显示名对照 `head -1 08-*.md` |
| AC-4 | 对照 `08` §5、§7.1 人工复核 |
| AC-5 | smoke 的 README 日期版本检查；`git diff --stat origin/main -- skills usage templates` 为空 |
| AC-6 | `bash codex/tests/smoke.sh`；临时删链接后 AC-1 检查变红再恢复 |
| AC-7 | `codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="high"` 审查候选 head |

## 部署与回滚

无部署影响。回滚即 revert 本 PR。
