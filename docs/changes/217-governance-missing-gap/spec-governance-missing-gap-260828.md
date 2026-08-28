---
issue: 217
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/217
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 215
status: approved
branch: change/217-governance-missing-gap
created: 2026-08-28
updated: 2026-08-28
---

# governance missing collaborator GAP 规格

## 目标与原因

恢复 #213/#215 的 bootstrap 前只读治理合同：当 NewEMaint routine account 已由 exact account endpoint
明确判定为 `missing`，且 exact collaborator permission GET 返回 HTTP 404/no-collaborator 时，
`gitea-governance check --repository NewEMaint` 必须输出结构化 `DRIFT`/planned action，而不是 schema 或
transport blocker。该计划用于确认后续仍需 bootstrap 与 exact apply；它本身不授权任何 mutation。

## Acceptance criteria

- [ ] **AC-1 evidence-derived missing**：`check` 必须先读取并固定 project/routine account state；只有 exact
  `account_state=missing` identity 对应的 exact collaborator permission HTTP 404 才投影为 `missing`。
  输出仍为 `result=DRIFT`，且 NewEMaint planned actions 精确包含缺失 routine collaborator 所需动作。
- [ ] **AC-2 account 三态与 ordering**：project/routine accounts 保持 `present-non-admin`、`missing`、
  `present-site-admin` 三态；account GET 必须早于第一个可被兼容的 permission GET。present-non-admin 或
  present-site-admin 的 permission 404 继续 fail closed，不得形成 planned action。
- [ ] **AC-3 strict permission schema**：HTTP 200 仍只能接受 exact `{permission: string}`，值仅为
  `read|write|admin|owner`；malformed root、missing/extra field、non-string、unknown value 均
  `RESPONSE_SCHEMA_INVALID`/`ContractError`，不得因 account missing 而降级。
- [ ] **AC-4 auth/server/transport fail closed**：401、403、5xx 与 transport failure 保持原稳定错误；
  非 exact permission endpoint、未建立 account missing evidence、shared/unknown identity 的 404 均不兼容。
- [ ] **AC-5 planned governance 不回归**：target desired permission 仍为 exact `write`；manager=`admin`、
  project agent=`write`、routine account non-admin gate、human+routine merge allowlist、required context、
  direct/force push denial保持；cross-project `write|admin|owner` 继续 blocker，`read` 继续安全。
- [ ] **AC-6 check/apply mutation boundary**：`check` 只允许 GET，API mutation=0。`apply_repository` 不接收
  account-missing 兼容 evidence；enabled routine account 必须先通过 exact non-admin verify，cross-project
  audit/plan blockers 全绿，fresh pre-snapshot 必须先于第一个 write，exact #213 live mode gate不变。
- [ ] **AC-7 接口兼容**：保持现有 JSON keys `repositories`、`project_accounts`、`routine_accounts`、
  `cross_project_write_violations` 与 planned action names；不复制 #215 credential/inventory 接口，不新增
  broker operation、caller target、credential path 或 manifest 字段。
- [ ] **AC-8 regression 与边界**：增加正向、负向、ordering 与 mutation-call tests；重放 governance、
  host-access、routine-merge security suites，bootstrap/rollback/installer shell suites、full smoke、semantic
  audit 与 Controller preflight。全任务不执行 install/live account/PAT/collaborator/protection/#74/merge/deploy。

## 接口、数据与兼容性影响

CLI 输出 schema 与 canonical manifests 均不变化。实现只在内部 read-only call graph 中增加
`known_missing_accounts` evidence：由同一次 `_check` 的 exact account read 派生，不能由 CLI caller、env、
manifest 或 snapshot 文件注入。

HTTP 404 兼容只适用于 exact collaborator permission GET 和已证明 missing 的同一 exact identity。HTTP 200
仍由现有 strict parser 判定；`ApiError` 的其它 status 不转换。`capture_snapshot` 与
`audit_cross_project_writes` 默认参数保持 fail-closed，使 mutation caller 不会自动进入兼容路径。

## 风险与回滚约束

- Source rollback：revert #217 唯一最终 PR，恢复 `78a36de...` 行为。
- 无 live rollback：本 Change 禁止 live mutation。
- 任何 account schema、permission schema、auth/server/transport、target/protection 或 cross-project drift
  均在 mutation 前失败，不使用 admin/manager/project-agent/shared-bot fallback。

## 非目标

- 不修改 `host.access.audit` 的 #215 strict inventory、credential 或输出 schema。
- 不创建/修改/撤销 account、PAT、credential、collaborator、protection 或 allowlist。
- 不执行 governance apply/rollback、NewEMaint #74、routine merge、manual merge、install 或部署。
- 不修改 canonical manifests、`AGENTS.md`、installer targets、Controller 或 CI workflow。

## 未决问题

无。
