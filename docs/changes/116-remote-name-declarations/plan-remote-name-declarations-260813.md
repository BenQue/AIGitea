---
issue: 116
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/116
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: ready-for-review
branch: change/116-remote-name-declarations
pr_url:
created: 2026-08-13
updated: 2026-08-13
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | manifest 两行声明 + 语义文档（AC-1、AC-4） | - | pending |
| T02 | 测试与 smoke（AC-2）+ PR | T01 | pending |

## Expected touch points

- T01：`codex/config/host-access-broker.json`、本目录三份文档。
- T02：无新文件。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `git diff origin/main -- codex/config/host-access-broker.json`（恰两行插入） |
| AC-2 | `bash codex/tests/test-host-access-broker.sh`；`bash codex/tests/smoke.sh` |
| AC-3 | 合并后人工：两端重装 + 两仓 `mac.git.bind`/`host.onboarding.check` PASS + `git remote -v` 复核 origin 未变 |
| AC-4 | diff 文件清单 ⊆ spec 治理授权清单 |

## 部署与回滚

合并后需人工重装：Mac `sudo bash codex/install-host-access-broker.sh`、VM
`orb -m gitea-ci sudo bash /mnt/mac/.../codex/install-host-access-broker.sh`；随后复跑
两仓 adoption 闸门（AC-3）。回滚 = revert 单 PR + 重装。
