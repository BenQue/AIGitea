---
issue: 379
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/379
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/379-skills-single-source
created: 2026-10-18
updated: 2026-10-18
---

# #379 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 映射文档 | - | in-progress |
| T02 | 治理内容：`skills/` 单一来源与合并正文、交叉审核步骤写入 `03`、`08`、`issue-session-flow`（受控步骤，应用后停止重读） | T01 | pending |
| T03 | 安装器、漂移检查、安装来源闸门与测试改读 `skills/` | T02 | pending |
| T04 | 发布包三种项目级落点与 Cursor 薄指针，外部技能核对 Cursor 段，发布 1.1.0 | T03 | pending |
| T05 | smoke 路径与守卫、文档与路线、泄漏基线、全量 smoke、临时 HOME 安装读回、verification；Codex 独立审查 | T04 | pending |
| T06 | 判级投影与 PR 候选，等确认点 2 | T05 | pending |

## Expected touch points

见 spec 的 `git_scope`（实现完成后按实际 diff 写全）。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1、AC2 | diff review；合并对照表；smoke 单家工具名守卫 |
| AC3 | `bash codex/tests/test-install-claude-skills.sh`；`test-installer-source-guard.sh`；临时 HOME 安装与三项漂移检查 |
| AC4、AC7 | `bash codex/tests/test-usage-bundle.sh`；`usage-bundle.sh --verify --baseline-ref origin/main`；`--build` 产物检查 |
| AC5 | 外部技能核对脚本的回归测试与本机只读运行 |
| AC6、AC8 | diff review；smoke 结构守卫 |
| AC9 | `bash codex/tests/smoke.sh`；Codex 只读审查 |

## 部署与回滚

无应用部署。合并后两侧重装并读回漂移。回滚：revert 本 PR 后重装。
