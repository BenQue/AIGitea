---
issue: 215
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/215
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
  - 213
status: approved
branch: change/215-routine-missing-audit
created: 2026-08-27
updated: 2026-08-27
---

# routine account 缺失时审计返回可读 GAP 规格

## 目标与原因

恢复 Issue #213 AC-6：当 NewEMaint routine account/PAT/collaborator 尚未 provision 时，read-only
`host.access.audit` 返回完整、结构化、可区分的 `GAP` evidence，并明确阻塞 live apply；预期缺失不得
伪装为 schema failure，也不得写成 `PASS`。

## Acceptance criteria

- [ ] **AC-1 missing + exact 404**：routine account read 明确得到 404/missing 后，cross-project exact
  collaborator permission GET 的 404/no-collaborator 投影为结构化
  `{repository, state: absent, permission: null}` evidence；top-level 与 routine status 保持 `GAP`，mutation=0。
- [ ] **AC-2 精确 ordering**：account state 必须先于 cross-project missing 判定建立；只有
  `account_state=missing` 能使用 AC-1。account present 时 cross-project 404 继续 `RESPONSE_SCHEMA_INVALID`。
- [ ] **AC-3 strict 200 schema**：无论 account missing 或 present，HTTP 200 只能接受 exact
  `{permission: string}`，且 permission 只允许 `read|write|admin|owner`。malformed root、missing/extra field、
  non-string、unknown value 继续 `RESPONSE_SCHEMA_INVALID`。
- [ ] **AC-4 auth/transport fail closed**：401、403、5xx 与 transport failure 不得降级为 missing，继续返回
  原有稳定 `HTTP_401`、`HTTP_403`、`HTTP_ERROR`、`TRANSPORT_ERROR`。
- [ ] **AC-5 present account permission contract**：account present 时 cross-project exact `read` 是安全 evidence；
  `write|admin|owner` 继续写入 `cross_project_write_violations` 并使 audit 为 `GAP`。
- [ ] **AC-6 target repository 门不回归**：target repository permission 仍必须 exact `write` 才能收敛；missing
  为 `GAP`，malformed 为 `RESPONSE_SCHEMA_INVALID`。routine identity 必须 exact non-admin，PAT scope exact，
  protection 必须 human+routine merge allowlist、required context exact、push/force denied。
- [ ] **AC-7 readable evidence**：routine section 新增完整 `cross_project_permissions`，逐个 manifest repository
  返回 `present/read|write|admin|owner` 或 AC-1 的 `absent/null`；该 inventory 与 violation list 一致，不泄露
  token/path。
- [ ] **AC-8 regression**：补正向、负向、ordering tests，重放 #213 host audit、routine merge、governance、
  bootstrap/rollback/installer 与 full smoke/security tests；所有未运行项照实记录。
- [ ] **AC-9 mutation boundary**：本 Change 全程 live mutation=0；不创建或修改 account、PAT、credential、
  collaborator、protection、allowlist，不 install、不 routine merge、不 deploy；最终 PR policy 固定 manual。

## 接口、数据与兼容性影响

`host.access.audit` 的 `routine_merge` object 增加 `cross_project_permissions` list。既有
`cross_project_write_violations` 保留，不改名、不删除。disabled repository 返回空 inventory；enabled
repository 为每个其他 canonical repository 返回一项，顺序与 governance manifest 一致。

兼容分流只由两项 evidence 合取：routine account 的先行 exact 404/missing，以及当前 cross-project exact
permission GET 的 404。任何一项不成立都不进入 absent 路径。

## 风险与回滚约束

- Source rollback：revert #215 唯一最终 PR；恢复 #213 merge 后行为。
- 无 live rollback：本 Change 禁止 live mutation。
- 所有异常 schema、auth、server 或 transport 响应都在 mutation 前 fail closed；不存在 fallback identity。

## 非目标

- 不改变 routine account/PAT/bootstrap/apply/rollback 的 live 流程。
- 不为第二个 repository 启用 routine merge。
- 不放宽 routine merger 的 target repository、token scope、identity 或 merge hard gates。
- 不修改 `AGENTS.md`、canonical manifests、installer targets 或 deployment contract。

## 未决问题

无。
