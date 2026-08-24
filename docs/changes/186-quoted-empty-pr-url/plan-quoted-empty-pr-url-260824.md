---
issue: 186
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/186
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
branch: change/186-quoted-empty-pr-url
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · backfill-pr-url 对引号空串的取值与报错

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `backfill_pr_url` 改用已解析的 front matter 取 `pr_url`，四种输入的行为由测试钉死 | - | pending |

单 ticket：缺陷、修法与四条验收标准都落在同一个函数上，拆成多片只会制造无法独立验收的
中间态。

## Expected touch points

- T01
  - `codex/runtime/aisoft_loop/documents.py` — `backfill_pr_url` 内取 `current` 的一行
    及其注释；原始行仍用于定位写入位置，只有取值来源改变。
  - `codex/runtime/tests/test_documents.py` — `BackfillPrUrlTests` 新增用例。

范围提示，不授权扩大 spec：`contract.py`、模板与历史文档均不在触点内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 引号空串等价写入 | `python3 -m unittest aisoft_loop... test_a_quoted_empty_pr_url_is_treated_as_empty`（`''` 与 `""` 用 `subTest` 两跑），断言写入 URL、`status: pr-open`、`changed=True` |
| AC-2 真实不同 URL 仍拒写且文案不变 | 既有 `test_a_different_pr_url_is_refused_without_writing` 保持绿，新增 `test_a_quoted_conflicting_pr_url_is_still_refused` 用 `assertRaisesRegex` 断言 `already declares a different pr_url` 字面 |
| AC-3 幂等 | 既有 `test_repeating_the_backfill_produces_no_diff` 保持绿，新增引号包裹正确 URL 的零写入用例 |
| AC-4 全绿与四种输入覆盖 | `bash codex/tests/smoke.sh`；四种输入分别对应上面三行的用例（裸空值由既有 `test_writes_pr_url_and_advances_status_together` 覆盖） |

## 部署与回滚

无部署影响。回滚为 `git revert` 单 commit；该函数不持有状态，也不改任何已落盘文档的
既有内容。
