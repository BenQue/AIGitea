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
status: pending
branch: change/299-outdated-branch-ruling
created: 2026-09-16
updated: 2026-09-16
---

# 验证记录

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = 9a2fa11
- 环境: Mac 交互会话；Gitea 1.26.4（`gitea-ci.orb.local:3000`）；broker 只读操作
- 本记录负责证明的 acceptance criteria: AC-3（开关切换前后读回）以及裁决落定后适用的 AC-2/AC-4/AC-5

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `gitea.protection.read`（切换前，2026-09-16） | PASS | aisoft-platform / localwms / newemaint：`block_on_outdated_branch: true`，`updated_at 2026-09-05T23:07:43+08:00`；sfm-digital-board：`true`，`updated_at 2026-08-08T18:03:01+08:00` |
| `bash codex/tests/test-project-check.sh`（改动前基线） | PASS | `project check tests passed (58 cases)` |
| `curl /api/v1/version` | PASS | `{"version":"1.26.4"}` |
| swagger `pulls/{index}/update` 与 `BranchProtection` 字段 | PASS | 仅手动更新端点 `POST .../pulls/{index}/update?style=`；保护字段仅 `block_on_outdated_branch`；无自动更新字段 |
| 裁决后步骤 | NOT RUN | 等确认点 1 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待 T02 |
| AC-2 | NOT RUN | 仅选 A |
| AC-3 | NOT RUN | 切换前读回已记录，切换后待负责人操作 |
| AC-4 | NOT RUN | 仅选 B |
| AC-5 | NOT RUN | 仅选 C |
| AC-6 | NOT RUN | 待 PR CI |

## 遗留风险与未完成项

- 裁决未落定；本记录目前只固化改动前才观测得到的基线。
