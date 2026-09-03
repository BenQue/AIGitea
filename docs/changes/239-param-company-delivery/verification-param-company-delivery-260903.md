---
issue: 239
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/239
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - ci-change
depends_on:
  - 237
status: verified
branch: change/239-param-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Verification · company-delivery runtime 参数化

## 基线与范围

- Commit SHA: T00 `c52fa3c`（合同）、T01 `aa07099`、T02 `c6b330a`、T03 `97cc741`、T04 `dfb072d`；T05 与本记录定稿同一 commit，SHA 见 PR
- 基线：`origin/main` = `2482584`（Merge PR #238，#237 deproject-company-delivery）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-239-param-company-delivery`）
- 本记录负责证明的 acceptance criteria: AC-1～AC-6（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.issue.read --project newemaint --number 75`（会话开始，2026-09-03） | `state: open`，`closed_at: null` | 「承接平台 company-delivery pilot 归属…（平台 #237）」；删除副本软依赖未满足 → plan T05 |
| `grep -rci newemaint codex/runtime/aisoft_company_delivery/` | 4 处 | `bundle.py` 1（`:33` `COMPATIBILITY_PATH`）、`contract.py` 2（`:49`、`:357`）、`collector.py` 1（`:350`）；`__init__.py`/`cli.py`/`secret_scan.py` 0 |
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'` | 合计 9 | `compatibility/newemaint-company-pilot-v1.json` 1、`schema/inventory-v1` 3、`inventory-v2` 2、`inventory-v3` 2、`templates/handoff-manifest.example.json` 1（与 Issue 正文一致） |
| `grep -ci newemaint codex/runtime/tests/test_company_delivery.py` | 13 | fixture timer 名 ×9、pilot matrix 路径 ×3、方法名 ×1 |
| `cat company-delivery/VERSION`；`find company-delivery -type f \| wc -l` | `1.2.0`；19 | 与 #237 判定表一致 |
| `bash codex/tests/integration/test-company-delivery-real-release.sh`（默认调用） | NOT RUN | `NOT RUN: Issue #124 exact real-release regression requires explicit --execute.` |
| `bash codex/tests/smoke.sh`（pristine `origin/main` = `2482584` detached worktree） | PASS，rc=0 | `Ran 651 tests in 38.099s … OK` + `Codex platform static smoke checks passed.` |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery`（改动前） | 76 tests OK | #237 verification 同值 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `grep -rci newemaint codex/runtime/aisoft_company_delivery/` | 6 个文件全部 0（基线 4 处） | `bundle.py`/`collector.py`/`contract.py`/`cli.py`/`__init__.py`/`secret_scan.py` 均 0 |
| `grep -n COMPATIBILITY_PATH codex/runtime/aisoft_company_delivery/*.py` | 空，rc=1 | 常量已删除；bundle.py 只保留 `COMPATIBILITY_DIRECTORY = "operator/compatibility"` 与 basename 白名单 |
| `python3 -c 'from aisoft_company_delivery.contract import OPERATOR_VERSION, SYNC_TIMER_DECLARATION_VERSION'` | `1.3.0 (1, 3, 0)` | 与 `cat company-delivery/VERSION` = `1.3.0` 一致 |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery`（T01 后） | 82 tests OK | 基线 76 + R-03/R-04/R-05/R-06/R-07 用例 6 条：`test_inventory_accepts_any_sync_timer_instance_exactly_once`、`test_handoff_sync_timer_unit_is_required_from_operator_1_3`、`test_compatibility_matrix_binds_only_contract_version_and_timer`、`test_transition_verifier_cross_checks_sync_timer_with_handoff`、`test_sync_timer_unit_resolves_only_from_a_verified_handoff`、`test_scm_inventory_records_the_declared_sync_timer_instance` |
| 同上（T02 后） | 85 tests OK | 新增 R-08/R-09 用例 3 条：`test_builder_carries_the_callers_matrix_and_binds_no_project_path`（含「runtime 包无 `aisoft-inbound-sync@<实例>` 硬编码、无 `COMPATIBILITY_PATH`、`ROLE_UNIT_NAMES` 无 timer」断言、同 matrix 字节重复构建 byte-identical、不同 matrix 字节改变 archive 身份）、`test_builder_rejects_unusable_matrix_before_output`（相对路径/缺文件/非 `.json`/隐藏名/错 contract/缺 timer/畸形 timer/mode 0666/symlink/与 tracked 同名冲突，输出目录保持为空）、`test_cli_requires_matrix_for_build_and_handoff_for_scm_collection` |
| 首次修改 `write_matrix` 后单测 | FAILED（errors=10） | `CompanyDeliveryArchiveScannerTests` 借用 `CompanyDeliveryBundleTests.setUp` 却没有 `write_matrix`；补 `write_matrix = CompanyDeliveryBundleTests.write_matrix` 后 85 tests OK |
| `grep -n -i newemaint codex/runtime/tests/test_company_delivery.py` | 1 处（基线 13） | `:3411` #237 否定断言 `assertNotIn("NewEmaint 公司交付 runbook", …)`；fixture timer 名改 `aisoft-inbound-sync@example.timer`（`TIMER`）、matrix 路径改 `MATRIX_PATH`、方法名改 `test_docs_never_reuse_company_rebuild_as_local_evidence` |
| `grep -ci newemaint company-delivery/templates/compatibility-matrix.example.json` | 0 | 项目中立示例（`example` 实例名、role 描述、policy 三个 BLOCKED 项，无 stage_map） |
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'`（T03 后） | `compatibility/newemaint-company-pilot-v1.json:1`（基线合计 9） | 只剩 pilot 副本本身：`schema/inventory-v{1,2,3}` enum/const 改 pattern 并删 `$comment`，`templates/handoff-manifest.example.json` `matrix_path` 改 `operator/compatibility/compatibility-matrix.example.json`；`README.md`/`runbook.md` 0 |
| `for f in company-delivery/schema/*.json company-delivery/templates/*.json; do jq empty $f; done` | 全部通过 | 含新增 `schema/compatibility-v1.schema.json`、`templates/compatibility-matrix.example.json` |
| `bash -n` + `shellcheck`（默认 info 级）`codex/tests/integration/test-company-delivery-real-release.sh` `codex/tests/test-company-delivery-real-release-harness.sh` | 通过 | 首轮全量 smoke 红在 harness 新守卫 SC2016（smoke 用 info 级，本地 `-S warning` 未拦）；按同文件既有做法加 `# shellcheck disable=SC2016` 后通过 |
| `bash codex/tests/test-company-delivery-real-release-harness.sh` | `PASS: Issue #124 real-release harness default/guard contract` | 新增静态守卫 `--compatibility-matrix "$compatibility_matrix"` 命中两次 build |
| `bash codex/tests/integration/test-company-delivery-real-release.sh`（默认） | NOT RUN | `NOT RUN: Issue #124 exact real-release regression requires explicit --execute.` |
| 同上 `--execute --repository-root $PWD --release-root /tmp --release-id 006d0c43…`（无 matrix） | `BLOCKED: repository root, release root and compatibility matrix must be absolute`，rc=1 | 缺 matrix 在任何 release 操作前失败；`--execute` 完整路径本 Issue **NOT RUN**（无 exact release bytes，且脚本钉住 #124 历史分支） |
| `bash codex/tests/smoke.sh`（T03 全部改动，change worktree） | PASS，rc=0 | `Ran 660 tests in 37.125s … OK` + `Codex platform static smoke checks passed.`（基线 651 tests OK；+9 = 本 Issue 新增用例） |
| `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/config codex/tools AGENTS.md skill-for-codex skill-for-claude codex/skills codex/runtime/aisoft_loop codex/runtime/aisoft_release` | 空 | 非目标路径零 diff |
| `git diff --stat origin/main...HEAD` | 23 files（T03 时） | 全部为平台仓路径：runtime 4、tests 1、`company-delivery/` 13（含 2 个新文件）、integration/harness 2、docs/changes 3 |
| broker `gitea.issue.read --project newemaint --number 75`（T04 定稿前再次读回） | `state: open`，`closed_at: null`，`updated_at: 2026-09-03T09:36:39+08:00` | T05 前置未满足，停在 T05 前报告调度会话 |
| broker `gitea.issue.read --project newemaint --number 75`（T05 放行后本会话再次读回） | `state: closed`，`closed_at: 2026-09-03T15:55:48+08:00`，labels `completed`/`complexity/small`/`type/docs` | 调度会话独立核实：NewEmaint merge `f687f279eb989b84ea1ad6ba78833c46385823df` 在 `gitea/main`（PR admin/NewEMaint #76，head `e7300c2`，required CI success） |
| `git rm company-delivery/compatibility/newemaint-company-pilot-v1.json`；`find company-delivery -type f \| wc -l` | 目录 `compatibility/` 消失；20 个文件（基线 19 − 1 + 新增 2） | 平台仓不再保存任何项目的 matrix |
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'`（T05 后） | 空，rc=1（基线合计 23 → #237 后 9 → 本 Issue 0） | Issue 验收第 2 条 |
| `smoke.sh` 守卫块：`rg -ni <#231 pattern> "$ROOT/company-delivery"`，退出信息「company-delivery 不得出现具体项目名（#239 AC-2）」；`bash -n` + `shellcheck codex/tests/smoke.sh` | 通过 | 守卫从 README/runbook 两文件扩展到整个目录 |
| 守卫反向证明：`cp -R company-delivery <tmp>/`，向副本 `templates/compatibility-matrix.example.json` 追加 `参照 NewEMaint 的旧 profile。`，`ROOT=<tmp>` 单独执行守卫块 | 报红，rc=1 | 打印 `…/company-delivery/templates/compatibility-matrix.example.json:26:参照 NewEMaint 的旧 profile。` + `company-delivery 不得出现具体项目名（#239 AC-2）` |
| 同一守卫块对真实 worktree 执行（`ROOT=$PWD`） | `guard did not fire`，rc=0 | 真实树全目录计数 0 |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery`（T05 后） | 85 tests OK | 模板/runbook 测试已改读 `templates/compatibility-matrix.example.json`，删副本不影响 |
| `bash codex/tests/smoke.sh`（T05 全部改动，change worktree） | PASS，rc=0 | `Ran 660 tests in 40.228s … OK` + `Codex platform static smoke checks passed.` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <worktree>` | `pass=2 gap=0` | `PASS: change-documents`、`PASS: change-pr-url` |
| `codex/tools/apply-classification-labels.sh 239` → `--apply` → `--verify 239` | `projected` | plan `applied:false`；apply `result:updated`；verify `result:projected`，`type/platform` + `complexity/complex` |

## 平台侧读取 compatibility matrix 的路径（AC-5）

pilot matrix 归属项目仓（NewEmaint #75 承接）后，平台侧在三个点读取它，均不依赖平台仓保存任何项目的副本：

1. **构建（Stage 00 之前，开发侧）**：调用方在 `build-bundle --compatibility-matrix <项目仓 matrix 绝对路径>` 传入。
   builder 经 `load_compatibility_matrix` 只校验 `contract_version` = `company-delivery-compatibility/v1` 与
   `sync_timer_unit` 匹配 `^aisoft-inbound-sync@[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.timer$`，把文件原字节复制到 bundle
   `operator/compatibility/<basename>`，并把 `matrix_path`/`matrix_sha256`/`sync_timer_unit` 写入 handoff manifest
   `compatibility` 段。矩阵其余内容（拓扑、版本窗口、stage 进度、policy）是项目数据，runtime 不解释。
2. **Stage 10（公司 scm-ci）**：`collect-inventory --role scm-ci … --handoff-manifest <bundle>/handoff-manifest.json`
   经 `sync_timer_unit_from_handoff` 重新校验整个 bundle 后读出 `compatibility.sync_timer_unit`，按该实例名探测
   timer；缺省、legacy（< 1.3.0）或校验失败一律 fail-closed，不回退到任何默认值。
3. **Stage 20（cross-host review）**：`verify-gitea-transition` 读回 handoff 声明的 `sync_timer_unit` 并与 scm-ci
   inventory 记录的唯一 timer 实例交叉校验，不一致即 `INVALID_CONTRACT`。

项目仓侧的归属副本：`admin/NewEMaint` `ops/aisoft/company-delivery/compatibility/newemaint-company-pilot-v1.json`（#75 落地，
顶层已含 `sync_timer_unit: "aisoft-inbound-sync@newemaint.timer"`，其余与平台 #237 原件逐字节相同，`matrix_revision`
`2026.08.4`，`gitea/main` 实测 SHA-256 `3279c65e9ec4eda5521b487cc26cdcb24d0856e59f951e82e119ec506c0b8f0a`，用本分支
`schema/compatibility-v1.schema.json` 校验 PASS——以上由 #75 会话与调度会话核实）。构建时调用方即传
`--compatibility-matrix <NewEMaint checkout>/ops/aisoft/company-delivery/compatibility/newemaint-company-pilot-v1.json`；
平台 `templates/compatibility-matrix.example.json` 与 `schema/compatibility-v1.schema.json` 只给结构。

## 与 NewEmaint #75 的衔接（T05 前置）

- 会话开始（基线）：`state: open`。
- T04 定稿前再次读回（2026-09-03）：`state: open`，停在 T05 前报告调度会话。
- 调度会话放行后本会话再次读回：`state: closed`（`closed_at` 2026-09-03T15:55:48+08:00）；随后执行 T05。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 runtime 参数化 | PASS | runtime 6 文件项目名 0；`COMPATIBILITY_PATH` 不存在；R-03～R-09 正反向用例 9 条随 85 tests OK |
| AC-2 副本删除与守卫扩展 | PASS | 副本已删（`test -e` 失败）；全目录计数 0；守卫覆盖整个 `company-delivery/`，反向证明报红/真实树静默；前置 NewEmaint #75 `closed` 已读回 |
| AC-3 VERSION 与 legacy | PASS | `VERSION` = `OPERATOR_VERSION` = `1.3.0`；archive 名前缀 `aisoft-company-delivery-1.3.0-`；legacy 1.2.0 handoff 可读（`test_handoff_sync_timer_unit_is_required_from_operator_1_3`）且 transition 拒绝旧 operator（既有 `test_transition_verifier_rejects_handoff_source_version_and_package_drift` 1.0.1 用例）；仓库内无 1.2.0 handoff 补写 |
| AC-4 测试与守卫 | PASS | smoke 660 tests OK rc=0（T03、T05 各一次）；测试模块只剩 #237 否定断言；template matrix 0；`bash -n`/shellcheck 通过；harness PASS；integration `--execute` NOT RUN |
| AC-5 与 #75 衔接 | PASS | 上节三点读取路径 + #75 state 读回 |
| AC-6 非目标守卫 | PASS | 非目标路径 diff 为空；全部改动为平台仓路径 |

## 遗留风险与未完成项

- integration `test-company-delivery-real-release.sh --execute`：NOT RUN（无 exact release bytes；脚本本身钉住 #124
  历史分支 `change/124-secret-scan-false-positive`，只能作历史回归骨架）。
- 项目仓归属 matrix 已含 `sync_timer_unit`（#75），本 Issue 未在本机对该文件运行 `build-bundle`（无 exact release bytes），只经 #75 会话按 schema 校验。
- 根文档 `README.md:23`、`13:60` 的「operator 1.2.0」为状态句/参考记录，spec 非目标，未改。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
