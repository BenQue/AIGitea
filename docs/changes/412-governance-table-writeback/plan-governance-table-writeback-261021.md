---
issue: 412
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/412
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/412-governance-table-writeback
created: 2026-10-21
updated: 2026-10-21
---

# 治理表回写实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 路线图第二轮状态与 E2E 两节回写到读回事实（AC-1、AC-2、AC-3） | - | pending |
| T02 | `03` §7 回写规则、来历行、`AGENTS.md` 指针、两张表「用法」行、smoke 标题钉子与反向证明（AC-4、AC-5） | T01 | pending |

## Expected touch points

- T01：`docs/governance/remediation-roadmap.md`、`docs/governance/platform-e2e-acceptance.md`。
- T02：`03-Issue-Spec-Plan与单闸门开发流程.md`、`AGENTS.md`、`codex/tests/smoke.sh`、两张表的「用法」行。
- 两个 ticket 都更新本目录的 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | broker `gitea.pulls.read --state closed` 读回 PR 390–411 的 merged 与 merge SHA，逐行对照 |
| AC-2 | broker `gitea.pull.read --number 322`（newemaint）读回合并与正文 |
| AC-3 | 各项目 broker `git.fetch.main` 后在 main 合并 SHA 的临时 detached worktree 里跑 `.aisoft/bin/aisoft bundle status` 与 `check-change-documents`，LocalWMS `grep uses:` |
| AC-4 | diff review；`wc -c AGENTS.md` |
| AC-5 | 删标题跑 smoke 看红，恢复后 `bash codex/tests/smoke.sh` 绿 |
| AC-6 | `git diff --stat origin/main...HEAD` |

## 部署与回滚

无部署影响。回滚即 revert 本 PR。
