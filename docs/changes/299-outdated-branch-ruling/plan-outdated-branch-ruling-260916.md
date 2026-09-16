---
issue: 299
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/299
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-change
depends_on: []
status: contract-drafting
branch: change/299-outdated-branch-ruling
created: 2026-09-16
updated: 2026-09-16
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 取证 + 四文档合同草案 + 确认点 1 拿到 A/B/C 裁决，summary 进入 `approved` | - | pending |
| T02 | `06` 踩坑集新增条目：裁决、理由、残余风险，回指踩坑 22（三选一共用） | T01 | pending |
| T03 | 仅选 A：`check_outdated_branch` 改为读回并报告；`test-project-check.sh` 用例同步 | T01 | pending |
| T04 | 仅选 A：负责人界面切换前后各读一次 `gitea.protection.read`，写 verification 并评论 Issue | T03 | pending |
| T05 | 仅选 B：合并串行化规程写进 `03`/`06`；仅选 C：可行性证据写进 verification 并另立实施 Issue | T01 | pending |
| T06 | smoke、`check-change-documents`、判级投影 `--verify` 读回 `projected`、本地原子 commit、确认点 2、唯一 manual PR | T02 + (T03,T04 或 T05) | pending |

裁决落定后删除未选中选项的 ticket 行，不留条件分支。

## Expected touch points

- T02：`06-运维手册与踩坑集.md` §2 踩坑表末尾新增一行（编号顺延，合并时若撞号由合并者改）。
- T03：`codex/tools/aisoft-project-check.sh` `check_outdated_branch` 尾部判定与注释；
  `codex/tests/test-project-check.sh` 第 831–853 行两条 GAP 用例改为 SKIP 且期望 exit 0；
  其余 `ci-outdated-branch` 用例与 `result:` 计数行不变（aligned fixture 仍是 `true`）。
- T04：`docs/changes/299-outdated-branch-ruling/verification-*.md`；Issue #299 评论。
- T05：`03-Issue-Spec-Plan与单闸门开发流程.md` 或 `06` §1/§6。
- 所有 ticket：`docs/changes/299-outdated-branch-ruling/`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | diff review `06` 新条目；`grep -n "#299" 06-运维手册与踩坑集.md` |
| AC-2 | `bash codex/tests/test-project-check.sh`；`bash codex/tests/smoke.sh`；`bash -n`/ShellCheck |
| AC-3 | `host-access-broker --project <id> --operation gitea.protection.read` 切换前后各一次，四仓 |
| AC-4 | diff review 规程文本 |
| AC-5 | 新 Issue 编号与 verification 里的可行性证据 |
| AC-6 | PR 的 `CI / verify (pull_request)` 读回；`git diff --stat` 不含 `.gitea/workflows/` |

## 部署与回滚

无部署。源码改动 revert 即回滚；开关切换由人在界面反向操作并读回。
