---
issue: 305
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/305
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - deployment
  - rollback
  - shared-core
depends_on: []
status: approved
branch: change/305-migration-receipt-identity
created: 2026-09-16
updated: 2026-09-16
---

# Implementation plan：#305 migration receipt identity

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 测试夹具能表达「同 identity、不同 release」，并用红色用例钉住三条 AC | - | pending |
| T02 | runner.py 去掉两处 release_id 门，红转绿；推进证据闸门 runner 哈希 | T01 | pending |
| T03 | 合同文档与踩坑集补记 receipt 的 identity 语义 | T02 | pending |
| T04 | 全量 smoke 与 verification 记录 | T02, T03 | pending |

T01 先红后绿：夹具改完、用例写完、`runner.py` 未动时，AC-1 的用例必须以
`migration receipt release identity is stale` 失败。这一条只有在改动前观测得到，
必须写进 `verification`。

## Expected touch points

- T01：`codex/runtime/tests/release_test_support.py`（`create_release` 增加一个
  可选参数，让第二个 release 复用第一个的 migration identity）、
  `codex/runtime/tests/test_release_runner.py`（新增用例）。
  两者都不在 #290/#296 证据闸门的 `SCOPES` 内，可自由增删。
- T02：`codex/runtime/aisoft_release/runner.py` 的 `_run_migration` 与
  `_require_migration_completed`；`codex/tests/check-release-evidence-boundary.py`
  的 `CURRENT_SOURCE_PINS` 中 runner 那一项的取值。
- T03：`docker-release/README.md`（在 `CONTENT_EXEMPT` 内，可改内容）、
  `06-运维踩坑与broker.md`。
- T04：无源码改动。

范围提示，不授权扩大 spec。**明确不碰**：`state.py`、`transport.py`、
`image-stores-v1.json`、`SCOPES`、`CONTENT_EXEMPT`、baseline 常量。

## 数据库迁移

无。本次变更不新增、不修改、不重跑任何数据库 migration；它只决定一套已经跑完的
migration 是否需要再跑一次，答案从「报错」改为「不需要」。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `test_release_runner.py` 新增用例，`python3 -m unittest`；改动前观测红 |
| AC-2 | `test_release_runner.py` 新增反向用例（started 与 failed 两个 subTest） |
| AC-3 | `test_release_runner.py` 新增反向用例（receipt 缺失时 activate 拒绝） |
| AC-4 | `bash codex/tests/smoke.sh`，与基线 962 用例对比 |
| AC-5 | diff review：`docker-release/README.md` 与 `06-运维踩坑与broker.md` |
| AC-6 | `python3 codex/tests/check-release-evidence-boundary.py` 与全量 smoke |

## 部署与回滚

本次变更本身不部署。产物是平台仓源码，合并后由各项目在下一次安装 runtime 时取得；
本 Issue 不安装、不重装、不触碰任何 target。

回滚：`git revert` 本 PR 的 merge commit。无 state 迁移、无制品、无 live 标签变更，
revert 后行为逐字回到修复前。

Issue 正文第 5 条的真实 target 证据（DockerLab 上 `0c2deaf` 从 `staged` 继续
`migrate` → `migration-noop` → `activate`）由 NewEMaint #124 在本修复合并并安装后
执行与记录，不由本 Issue 执行；本次 `verification` 引用它并如实标注未执行。
