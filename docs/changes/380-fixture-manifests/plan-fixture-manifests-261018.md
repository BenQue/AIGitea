---
issue: 380
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/380
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on:
  - 377
status: approved
branch: change/380-fixture-manifests
created: 2026-10-18
updated: 2026-10-18
---

# #380 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 映射文档 | - | completed |
| T02 | 基线：逐文件用例数与全量 smoke 基线 | T01 | completed |
| T03 | 合成夹具与生成说明 | T02 | completed |
| T04 | Python 测试改读夹具 | T03 | completed |
| T05 | shell 测试改读夹具，smoke 守卫 | T03 | completed |
| T06 | 回滚工具退役：归档、installer、漂移检查、smoke、泄漏基线 | T02 | completed |
| T07 | 文档、候选 manifest 删项目演示、全量 smoke、verification；Codex 独立审查 | T04、T05、T06 | completed |
| T08 | 判级投影与 PR 候选，等确认点 2 | T07 | in-progress |

## Expected touch points

见 spec 的 `git_scope`。

## 数据库迁移

无。
