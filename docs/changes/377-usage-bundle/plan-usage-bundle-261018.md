---
issue: 377
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/377
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/377-usage-bundle
created: 2026-10-18
updated: 2026-10-18
---

# #377 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 映射文档 | - | completed |
| T02 | 治理文档：使用合同、指针模板、summary 模板、`08` §7 两层、project-align、两侧技能、`03`、README、runbook | T01 | completed |
| T03 | 发布包声明与工具、回归测试、smoke 登记；发布 1.0.0 | T02 | completed |
| T04 | project-check 按 pin 核对与测试同步 | T03 | completed |
| T05 | 路线文档、泄漏基线、全量 smoke、对两个项目的只读核对、verification；Codex 独立审查 | T04 | completed |
| T06 | 判级投影与 PR 候选，等确认点 2 | T05 | in-progress |

## Expected touch points

见 spec 的 `git_scope`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1、AC2、AC6、AC8 | diff review；`check-project-leak.py` |
| AC3、AC4 | `bash codex/tests/test-usage-bundle.sh`；`bash codex/tools/usage-bundle.sh --verify` |
| AC5 | `bash codex/tests/test-project-check.sh` |
| AC7 | `bash codex/tools/change-template-sync.sh --verify-digest`；泄漏检查 |
| AC9 | diff review |
| AC10 | `bash codex/tests/smoke.sh`；verification 记录的只读核对输出 |

## 部署与回滚

无应用部署。合并后负责人重装两侧平台技能。回滚：revert 本 PR 后重装。
