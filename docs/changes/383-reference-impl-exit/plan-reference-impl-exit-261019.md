---
issue: 383
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/383
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
  - 380
status: approved
branch: change/383-reference-impl-exit
created: 2026-10-19
updated: 2026-10-19
---

# #383 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 映射文档与基线 smoke | - | completed |
| T02 | 治理文件受控步骤：`AGENTS.md` 目录行、onboarding runbook；单独 commit 后停止并重读 | T01 | completed |
| T03 | 删除参考实现、测试、harness、夹具与证据闸门；smoke、source guard、漂移检查与夹具同步 | T02 | completed |
| T04 | architecture inventory 与治理测试、活文档断链、迁出说明、archive 索引 | T03 | completed |
| T05 | 发布包升版、泄漏基线、路线图、全量 smoke、verification；Codex 独立审查 | T04 | completed |
| T06 | 判级投影与 PR 候选，等 NewEMaint 第 4 步回告后确认点 2 | T05 | in-progress |

## Expected touch points

见 spec 的 `git_scope`。
