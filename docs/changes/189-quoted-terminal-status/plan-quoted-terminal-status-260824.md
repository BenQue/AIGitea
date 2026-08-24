---
issue: 189
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/189
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/189-quoted-terminal-status
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · backfill-pr-url 推进 status 时的取值来源

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `backfill_pr_url` 改用已解析的 front matter 取 `status`，引号与裸写两种拼写的行为由测试钉死 | - | pending |

单 ticket：缺陷、修法与四条验收标准都落在同一个函数的同一行上，拆成多片只会制造无法
独立验收的中间态。

## Expected touch points

- T01
  - `codex/runtime/aisoft_loop/documents.py` — `backfill_pr_url` 内取 `status` 的一行
    及其注释；原始行仍用于定位写入位置，只有取值来源改变。
  - `codex/runtime/tests/test_documents.py` — `BackfillPrUrlTests` 新增用例。

范围提示，不授权扩大 spec：`contract.py`、`PR_BEARING_STATUSES`、模板与历史文档均不在
触点内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 引号包裹终态不降级 | 新增 `test_a_quoted_terminal_status_is_not_downgraded`（`'deployed'` 与 `"completed"` 用 `subTest` 两跑），断言该行原样保留 |
| AC-2 引号包裹 pr-open 视为已就位 | 新增 `test_a_quoted_pr_bearing_status_is_already_in_place`，`pr_url` 也已就位时断言 `changed=False` 且文件字节不变 |
| AC-3 裸写形式不变 | 既有 `test_a_terminal_status_is_not_downgraded`、`test_repeating_the_backfill_produces_no_diff`、`test_writes_pr_url_and_advances_status_together` 保持绿 |
| AC-4 全绿与新增覆盖 | `bash codex/tests/smoke.sh`；引号终态与引号承载态分别由上面两条新增用例覆盖 |

## 部署与回滚

无部署影响。回滚为 `git revert` 单 commit；该函数不持有状态，也不改任何已落盘文档的
既有内容。
