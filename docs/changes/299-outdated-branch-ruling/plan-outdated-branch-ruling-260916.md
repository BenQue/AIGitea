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
status: approved
branch: change/299-outdated-branch-ruling
created: 2026-09-16
updated: 2026-09-16
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 取证 + 四文档合同草案 + 确认点 1 裁决（A 的分仓变体），summary 进入 `approved` | - | done |
| T02 | `06` 踩坑 29：裁决、理由、否定裁决、残余风险，回指踩坑 22 | T01 | pending |
| T03 | `check_outdated_branch` 按 classification 分仓裁定；`test-project-check.sh` 用例同步 | T01 | pending |
| T04 | 负责人界面切换 NewEMaint 与 LocalWMS 后读回四仓 `gitea.protection.read`（SFM 保持 true），写 verification 并评论 Issue | T03 | pending |
| T05 | smoke、`check-change-documents`、判级投影 `--verify` 读回 `projected`、本地原子 commit、确认点 2、唯一 manual PR | T02, T03, T04 | pending |

## Expected touch points

- T02：`06-运维手册与踩坑集.md` §2 踩坑表新增第 29 行（28 由 #298 占用），踩坑 22 对策列加指针。
- T03：`codex/tools/aisoft-project-check.sh` `check_ci_merge_preview` 记下 verdict，
  `check_outdated_branch` 尾部按 classification 与该 verdict 判定；`codex/tests/test-project-check.sh`
  新增「有合并预览的 internal-application」fixture 两例（false/缺键 → SKIP、exit 0）、
  无合并预览仍 GAP 一例、平台仓 GAP/PASS 两例；aligned fixture 的 `result:` 计数行不变。
- T04：`docs/changes/299-outdated-branch-ruling/verification-*.md`；Issue #299 评论。
- 所有 ticket：`docs/changes/299-outdated-branch-ruling/`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | diff review `06` 踩坑 29 与踩坑 22 指针；`grep -n "#299" 06-运维手册与踩坑集.md` |
| AC-2 | `bash codex/tests/test-project-check.sh`；`bash codex/tests/smoke.sh`；`bash -n`/ShellCheck |
| AC-3 | `host-access-broker --project <id> --operation gitea.protection.read` 切换前后各一次，四仓 |
| AC-4 | PR 的 `CI / verify (pull_request)` 读回；`git diff --stat` 不含 `.gitea/workflows/` |

## 部署与回滚

无部署。源码改动 revert 即回滚；开关切换由人在界面反向操作并读回。
