---
issue: 194
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/194
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
branch: change/194-quoted-invocation-policy
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · matt-snapshot front matter 的取值规则

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `_skill_front_matter` 收敛出单一取值 helper，`name` 与 `disable-model-invocation` 两行都经过它；引号、裸写与畸形三类拼写的行为由测试钉死 | - | pending |

单 ticket：缺陷、修法与五条验收标准都落在同一个函数的相邻两行上，拆片只会制造无法独立
验收的中间态（改一行留一行 = 分歧仍在）。

## Expected touch points

- T01
  - `codex/runtime/aisoft_loop/matt_snapshot.py` — 新增私有 helper（一行 front matter
    → 值，成对引号剥离，失败按调用方给定的错误文本抛 `SnapshotError`），
    `_skill_front_matter` 的两行改为调用它。
  - `codex/runtime/tests/test_matt_snapshot.py` — `MattSnapshotTests` 新增用例。

范围提示，不授权扩大 spec：`contract.py`、`codex/vendor/mattpocock/**`、
`codex/install-skills.sh`、`codex/tests/smoke.sh`、模板与历史文档均不在触点内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 引号包裹的合法策略值 | 新增 `test_a_quoted_invocation_policy_is_accepted`：`'true'` / `"true"` / `'false'` / `"false"` 用 `subTest` 四跑，断言 `_skill_front_matter` 返回对应布尔值 |
| AC-2 裸写不变 | 新增 `subTest` 覆盖 `true` / `false` / `TRUE`；既有 `test_vendored_release_is_complete_and_matches_manifest` 与三个 `classify_update` 用例（全部走 `_write_skill` 的裸 `true`）保持绿 |
| AC-3 非法值仍 fail-closed | 新增 `test_an_invalid_invocation_policy_still_fails_closed`：`yes` / `1` / 空值 / `''` / 未闭合 `'true` 用 `subTest` 各跑一次，`assertRaisesRegex(SnapshotError, "invalid invocation policy")` |
| AC-4 name 引号与裸写都接受 | 新增 `test_a_quoted_skill_name_is_accepted`：`demo-skill` / `'demo-skill'` / `"demo-skill"` 三跑，断言解析成 `demo-skill`；另断言畸形 `'demo-skill` 抛 `invalid skill name`（spec §4 声明的收紧） |
| AC-5 全绿与新增覆盖 | `bash codex/tests/smoke.sh`（含 `unittest discover codex/runtime/tests` 与对 v1.2.2 真实快照的 `matt_snapshot verify`）；引号合法值与非法值分别由上面两条新增用例覆盖 |

## 部署与回滚

无部署影响。回滚为 `git revert` 单 commit；该函数不持有状态，不写任何文件，也不改
`codex/vendor/mattpocock/v1.2.2/manifest.json` 的既有内容。
