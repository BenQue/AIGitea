---
issue: 174
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/174
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: approved
branch: change/174-analyze-change-renumber
created: 2026-08-24
updated: 2026-08-24
---

# Plan · 消除 gitea-analyze-change 条目编号的源/渲染歧义

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 源文件编号对齐渲染编号：`SKILL.md` 第 51 行 `11.` → `12.`，第 52 行 `12.` → `13.`，条目文本零改动（AC-1、AC-3） | - | pending |
| T02 | 逐条核对 `grep -rn "第 1[0-9] 条\|item 1[0-9]"` 的全部命中，写明每条归属判定与改/不改理由，并执行需要改的引用更新（AC-2） | T01 | pending |
| T03 | `bash codex/tests/smoke.sh` 全绿 + `check-change-documents` 自查（AC-4） | T01, T02 | pending |

T02 依赖 T01：只有编号定案后，才能判定哪些引用**实际**位移。

## Expected touch points

- **T01**：`codex/skills/gitea-analyze-change/SKILL.md`（仅第 51、52 行行首序号）。
- **T02**：只读核对 `docs/changes/139-push-lease-doc-sync/plan-*.md`、
  `docs/changes/168-decouple-verification-authoring/{spec,plan,verification}-*.md`；
  判定结果写入本 change 的 verification 文档。预期**零处**引用文件被修改。
- **T03**：不改文件。

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `grep -n '^[0-9]\+\.' codex/skills/gitea-analyze-change/SKILL.md` 取出的序号序列等于 `1..13`，用脚本断言严格递增无重复 |
| AC-2 | `grep -rn "第 1[0-9] 条\|item 1[0-9]"`（tracked 文件用 `git grep`）逐条判定，判定表写入 verification；每条命中读其上下文确认「同文件」等指代绑定到哪个文件 |
| AC-3 | `git diff -- codex/skills/gitea-analyze-change/SKILL.md` 逐 hunk 核对：`-`/`+` 配对后仅行首序号不同；用 `sed 's/^[0-9]\+\./N./'` 归一化后 diff 为空 |
| AC-4 | `bash codex/tests/smoke.sh` |

补充自查（非 AC，平台合同要求）：
`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`

## 部署与回滚

无部署影响。回滚为单 commit `git revert`。

本次声明 `verification` 的原因是 AC-2 的证据来自 required CI 不跑的跨仓扫描
（判据见 `03` §3「何时声明 `verification`」），**不是**因为存在部署或迁移。
verification 文档因此不含 `## 部署验收` 一节。
