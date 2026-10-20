---
issue: 389
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/389
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
status: approved
branch: change/389-adr0002-round2-roadmap
created: 2026-10-20
updated: 2026-10-20
---

# #389 plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | ADR 0002 六节与路由卡合同形状 | - | pending |
| T02 | 路线图第二轮表、退出条件与推荐顺序 | T01 | pending |
| T03 | 平台级 E2E 验收表与 README 导航入口 | T01 | pending |
| T04 | `AGENTS.md` 指向 ADR 0002（治理文件，单独 commit） | T01 | pending |

## Expected touch points

- T01：`docs/adr/0002-deterministic-development-flow.md`
- T02：`docs/governance/remediation-roadmap.md`
- T03：`docs/governance/platform-e2e-acceptance.md`、`README.md`
- T04：`AGENTS.md`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 – AC-4 | `rg -n '^## ' docs/adr/0002-*.md` 列出六节；Codex 只读审查逐条对照裁决原文 |
| AC-5 | 审阅第二轮表四列与四条退出条件；`git diff origin/main -- docs/governance/remediation-roadmap.md` 只有追加与推荐顺序一段 |
| AC-6 | 审阅首行证据与项目库复审线程 03:45Z 核实记录一致 |
| AC-7 | `rg -n 'adr/0002|platform-e2e-acceptance' README.md`；smoke 内泄漏守卫 PASS |
| AC-8 | `wc -c AGENTS.md` ≤ 5120；`git log --stat` 显示该 commit 只含 `AGENTS.md` |
| AC-9 | `bash codex/tests/smoke.sh`；`codex exec -s read-only -C <worktree>` 结论 PASS |

## 部署与回滚

无部署影响；回滚为 revert。
