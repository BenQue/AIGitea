---
issue: 150
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/150
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - deployment-boundary
  - platform-governance
depends_on: []
status: approved
branch: change/150-systemd-native-profile
pr_url:
created: 2026-08-23
updated: 2026-08-23
---

# Verification：systemd 原生 profile 与 `systemd-native/v1`

## 环境与版本

- 基线 `6401954`（`origin/main`，含 #149）
- worktree `/private/tmp/issue-150-systemd-native-profile`，分支 `change/150-systemd-native-profile`
- macOS / Python 3，catalog revision `2026.08.3`；无新增依赖、不改 broker、不需重装
- 全部命令在 worktree 根目录执行，`--today` 未覆盖（除 CI 内既有测试自身固定的 `2026-08-06`）

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `architecture/bin/aisoft-architecture validate --project architecture/fixtures/valid/linux-systemd-project.json` | PASS | `{"catalog_revision":"2026.08.3","lock_sha256":"b1adea4d0bd2567d53e378b2f9ecbcbf852dc3d4685d9d1d9cf56c7deacfa383","profile_id":"linux-node-systemd-postgres-v1","project_id":"fixture-linux-systemd","valid":true}`，rc=0 |
| `aisoft-architecture lock` 连续两次 + `cmp` | PASS | 两次输出 sha256 均为 `7b7b11c82a6cf88431f19001c75d47aec137c4a1f48a5e0623948757ba1b0f27`，`cmp` 无差异 |
| `bash codex/tests/test-architecture-install.sh` | PASS | `architecture installer idempotence: PASS`（新增 profile 与 ADR 随 installer 幂等复制） |
| `bash codex/tests/smoke.sh`（CI 的唯一 job） | PASS | `Ran 508 tests ... OK` + `Codex platform static smoke checks passed.`，rc=0 |
| `python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `result: changes=70 pass=2 gap=0` |
| `python3 -m aisoft_loop.cli resolve-documents 150 --repo .` | PASS | 四个角色全部解析到本目录真实文件名 |

## Acceptance criteria 结果

- **新 profile 通过 schema 与语义校验** — PASS。`test_catalog_and_all_profiles_validate` 对 `architecture/profiles/*.json` 逐个跑 `validate_profile`，计数由 3 改为 4。
- **profile 不含 container/OCI/proxy/ORM/framework/frontend slot** — PASS。新增 `test_systemd_native_profile_has_no_container_or_frontend_slot` 把五个 slot 与被排除的 category 集合钉死；这是本 profile 的存在理由，靠人工复核守不住。
- **两处枚举含 `systemd-native/v1`，schema 校验通过** — PASS。profile 侧由 `validate_profile` 覆盖，project 侧由候选 fixture 的 `validate_schema` 覆盖；smoke 另对 `architecture/**/*.json` 跑 `jq empty`。
- **候选声明 `valid: true`** — PASS，见上表第 1 行。候选形态 = Ubuntu 24.04.4 + Node 24.18.0 + npm 11.19.0 + PostgreSQL 18.4 + TypeScript 6.0.2，`delivery_contract: systemd-native/v1`。
- **lock 连续两次 byte-identical** — PASS。终端实测见上表第 2 行；同时把 `test_lock_twice_is_byte_identical_and_validates` 改成对 `linux-project.json` 与 `linux-systemd-project.json` 两个 fixture 各跑一遍（lock ×2 + `cmp` + `validate --lock`），硬验收因此进了 CI，不只停留在本次终端。
- **既有 profile 与既有声明不被破坏** — PASS。`test_valid_fixtures_pass_schema_and_runtime`（valid fixtures glob，现含新 fixture）、`test_invalid_fixtures_fail_runtime`（五个 invalid fixture 的诊断码不变）、`test_committed_reference_locks_cross_check`（`reference/newemaint/target-candidate`、`reference/windows`、`reference/sqlite` 三份已提交 lock 逐字节交叉校验）全部在 508 个测试里通过。既有三个 profile 文件与三份 reference lock 本次零改动（`git diff --stat` 可核）。
- **runbook §4/§9 同步** — PASS（人工复核）。§4 新增 4.1 小节写共用/不适用/改为要求三段；§9 第 2 步写 profile 选择依据与「没有 profile 能如实描述时开平台 Issue 而不是虚报 component」，第 3 步写 `delivery_contract` 取值互斥。`test_governance_docs_keep_candidate_and_delivery_boundaries` 断言的 runbook marker 仍在。

## 重复部署

- 第一次：N/A
- 第二次：N/A

本变更无部署影响：只新增平台合同对象（profile / 枚举取值 / fixture / ADR / 文档）与测试，不触碰任何目标机、service、timer、凭据或数据库。唯一的幂等性要求落在 installer 与 lock 上，两者都已连续执行两次并比对（见上表第 2、3 行）。

## 故意失败与回滚

- 失败场景：N/A（无部署动作）
- 停止/回滚结果：回滚方式为 revert 本 PR。新增文件与两处枚举追加均为纯增量，revert 后既有 profile、fixture 与 reference lock 回到基线状态。
- 数据恢复验证：N/A（不涉及数据）

负向证据仍然存在：`test_invalid_fixtures_fail_runtime` 证明 fail-closed 诊断未被本次枚举扩展削弱；Issue 正文实测的 `PROFILE_COMPONENT_MISSING` 行为未被改动——新 profile 是补齐 slot，不是给 validator 开逃生口。

## 遗留风险与未完成项

- 第一个消费者 LocalWMS 的 `.aisoft/architecture.json` 在 LocalWMS 仓库另开 Issue，依赖本 PR 合并；本 PR 合并前不得提交引用 `systemd-native/v1` 的项目声明。
- 本变更不授予任何部署能力，也未验证任何 systemd 部署脚本；systemd 原生部署的首次验收仍须在应用仓自己的 Change 中按 runbook §4.1 完成。
- CI 状态见 PR；本文件在开 PR 前写就，PR 上的 CI 结果由 `gitea.commit.status.read`（完整 40 位 SHA）回读，不在此处预写。
