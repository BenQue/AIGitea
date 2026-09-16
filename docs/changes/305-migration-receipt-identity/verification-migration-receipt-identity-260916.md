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
status: verified-local
branch: change/305-migration-receipt-identity
created: 2026-09-16
updated: 2026-09-16
---

# Verification：#305 migration receipt identity

## 基线与范围

- Commit SHA: `43b89ef`（T03）；本文档由其后一条 commit 加入，最终 head 的全量 smoke
  见下表最后一行。
- 基线：`origin/main` = `e5ed35e`（`Merge pull request 'test(#301): release evidence
  boundary 豁免 Python 字节码产物并隔离回归字节码' (#303)`），经 broker `git.fetch.main`
  读回确认。
- 环境：Mac 本机 checkout `/private/tmp/issue-305-migration-receipt-identity`，
  Python 3.14，`rg` 15.2.0（真实二进制，非 PATH shim）。
- 本记录负责证明的 acceptance criteria：spec 的 AC-1 至 AC-6。
  Issue 正文第 5 条（DockerLab 真实 target 证据）不在本 Issue 验收内，见文末。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前复现（pin 同源逻辑，两个 release 声明同一 migration identity） | 复现成功 | A `migrate` → `migration-completed`、`activate` → `activated`；B `stage` → `staged`，`migrate` → `DeploymentError: migration receipt release identity is stale`，`activate` → `DeploymentError: activation migration receipt release identity is stale`。与 DockerLab 现场一致 |
| 改动前基线全量 `bash codex/tests/smoke.sh`（`e5ed35e`，未动任何文件） | PASS | `Ran 962 tests ... OK` / `Codex platform static smoke checks passed.` |
| 覆盖缺口取证 `rg -n "stale" codex/runtime/tests/ docker-release/` | 零命中 | 两句 stale 文案在整个测试树里没有任何断言 |
| T01 后、T02 前 `python3 -B -m unittest tests.test_release_runner.SharedMigrationIdentityTests` | 预期红 | `Ran 3 tests ... FAILED (errors=1)`；唯一失败是 AC-1 的 `test_completed_receipt_makes_a_same_migration_release_a_noop`，在 `runner.py:390` 抛 `DeploymentError: migration receipt release identity is stale`。AC-2、AC-3 两个反向用例此时已绿 |
| T02 后 `python3 -B -m unittest tests.test_release_runner.SharedMigrationIdentityTests` | PASS | `Ran 3 tests ... OK` |
| T02 后 `python3 -B -m unittest discover -s tests -t . -p "test_release*.py"` | PASS | `Ran 161 tests ... OK` |
| T02 后重跑改动前的复现脚本 | PASS | B `migrate` → `migration-noop`，B `activate` → `activated`；migration 容器事件仍只有 A 那一次；receipt 仍为 `{"release_id": SHA_A, "status": "completed"}` |
| `python3 codex/tests/check-release-evidence-boundary.py`（推进 runner 哈希后） | PASS | `current_source_conformance: PASS`、`current_release_regression: PASS`、`historical_evidence_binding: PASS`、`historical_harness_fake_regression: PASS`；`runner_sha256: ec6e0a9e56d8139102fb2a94fc31374886cd97b38e9166fa4f9d411e710533d6` |
| T03 后全量 `bash codex/tests/smoke.sh` | PASS | `Ran 965 tests ... OK` / `Codex platform static smoke checks passed.`；比基线多 3 条，正是新增的三个用例 |
| 最终 head 全量 `bash codex/tests/smoke.sh` | 见下方「最终 head 复核」 | 本文档 commit 之后补记 |

改动前才观测得到的两条证据是本记录的核心：**复现脚本的 stale 报错**与
**T01 之后 T02 之前的红**。修复合并后这两条都无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `test_completed_receipt_makes_a_same_migration_release_a_noop`：B `migrate` 返回 `migration-noop`；`migration_runs()` 为空、`docker.mutations` 为空（无 migration 容器、无数据库写）；receipt 仍是 `{"status": "completed", "release_id": SHA_A}`，即 noop 未改写 state、`release_id` 仍指向实际执行者；随后 `activate` 返回 `activated`，`current_release` = SHA_B、`previous_release` = SHA_A，`status` 为 ok。该用例在 T02 前为红 |
| AC-2 | PASS | `test_uncertain_or_failed_receipt_still_refuses_a_same_migration_release`，两个 subTest：`started`（migration 容器执行中进程死掉，receipt 停在 started）与 `failed`（`fail_migration_for`）。两种情形下 B 的 `migrate` 抛 `uncertain or failed`、`activate` 抛 `completed exact migration receipt`，且 `docker.mutations` 为空、receipt 原样不动。该用例在 T02 前已绿，是放宽边界的反向证明 |
| AC-3 | PASS | `test_missing_receipt_still_refuses_activation_and_runs_the_migration`：identity 相同但无 receipt 时，B `activate` 仍被拒且零 mutation；`migrate` 正常执行并写 `{"status": "completed", "release_id": SHA_B}`，随后 `activate` 成功。该用例在 T02 前已绿 |
| AC-4 | PASS | `Ran 161 tests ... OK`（release 套件）与 `Ran 965 tests ... OK`（全量 smoke）；既有用例一条未改、一条未删 |
| AC-5 | PASS | `docker-release/README.md` 的 State and rollback 一节补写 receipt 以 migration identity 为键、`release_id` 仅审计、放宽只限 `completed` 一支；`06-运维手册与踩坑集.md` 新增踩坑 30 |
| AC-6 | PASS | `CURRENT_SOURCE_PINS[runner.py]` 由 `0f71e8a9…` 推进到 `ec6e0a9e…`；键集合仍是 `{runner, transport, matrix}`，`SCOPES`、`CONTENT_EXEMPT`、`BASELINE`、`RUNNER_BEFORE`、`RUNNER_AFTER`、`EVIDENCE_SHA256` 均未改动 |

## 最终 head 复核

- 最终 head：待本文档 commit 后补记。
- 全量 `bash codex/tests/smoke.sh`：待补记。

## 遗留风险与未完成项

- **DockerLab 真实 target 证据：NOT RUN（本 Issue 不执行）**。Issue 正文验收标准第 5 条
  ——release `0c2deaf7` 在 DockerLab 上从 `staged` 继续 `migrate` → `migration-noop`
  → `activate` 成功——由 NewEMaint Issue #124 在本修复合并并安装后执行与记录。
  本 Issue 按正文要求只引用它，不代为执行，也不改 DockerLab 的 `state.json`、
  已安装 runtime 或任何部署状态。
- **证据闸门的 `current_real_e2e` 仍为 `NOT_RUN`**。
  `check-release-evidence-boundary.py` 的注释要求 `CURRENT_SOURCE_PINS` 只在有行为测试
  **和**真实 E2E 证据时推进。行为测试在本次变更内；真实 E2E 只能由 #124 在 DockerLab 上
  产出，而 #124 正阻塞于本修复，因此顺序上必然在合并之后。该字段由检查器无条件输出
  `NOT_RUN`，不是机器闸门；此处如实记录，不改写为通过。
- **DockerLab 已安装 runtime 与 pin 的 3 文件差异**（`image-stores-v1.json`、
  `runner.py`、`transport.py`）未处理。#124 已如实记录，是否重装另议；本缺口在两版
  `runner.py` 中逻辑相同，因此本修复的判断不受该差异影响。
- **踩坑编号 30 是跨 PR 共享的手工常数**。若另一个并行 PR 先合并并占用了 30，
  由合并者改号；本行内容与编号无关。
- 无数据库风险：修复方向是「少跑一次 migration」，不会让任何 migration 重复执行，
  也不进入 `database_restore` 路径。
- 回滚：`git revert` 本 PR 的 merge commit 即可逐字回到修复前行为。无 state 迁移、
  无制品、无 live 标签变更需要撤销。
