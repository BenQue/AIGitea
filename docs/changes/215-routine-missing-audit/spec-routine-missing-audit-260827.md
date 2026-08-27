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

- [ ] **AC-1 missing + exact absent inventory**：routine account read 明确得到 404/missing 后，对 target 与
  cross-project repository 读取 exact `GET .../collaborators?limit=50&page=N`。每页必须 exact HTTP 200 array、
  长度不超过 50；默认 transport 必须保留全部重复 `Link` field-values，按 relation token 大小写不敏感语义
  strict parse，`next|prev|first|last` 各自唯一并对应当前 canonical Gitea 的 exact repository collaborators
  endpoint。query 解码后只能且必须是唯一 `limit=50` 与 `page`；`next=当前页+1`、`prev=当前页-1`、
  `first=1`，有 next 时 `last>=next`，无 next 时 `last=当前页`。满页必须读取下一页；短页只有在不存在
  valid next 且其他关系不证明后续页时终止，最多每 repository 100 页、整个 audit 1000 页。每个 entry 的
  `login` 必须是 non-empty、trimmed string，并通过 canonical Gitea identifier contract；同页/跨页 exact
  duplicate、case-fold collision、routine login 的大小写变体均 fail closed。只有完整 bounded inventory 中
  routine login（含 case-fold）缺席时，才投影 `{repository, state: absent, permission: null}` evidence；
  top-level 与 routine status 保持 `GAP`，mutation=0。
- [ ] **AC-2 精确 ordering**：account state 必须先于 cross-project missing 判定建立；只有
  `account_state=missing` 能使用 AC-1。account present 时 cross-project 404 继续 `RESPONSE_SCHEMA_INVALID`。
- [ ] **AC-3 strict 200 schema**：无论 account missing 或 present，HTTP 200 只能接受 exact
  `{permission: string}`，且 permission 只允许 `read|write|admin|owner`。malformed root、missing/extra field、
  non-string、unknown value 继续 `RESPONSE_SCHEMA_INVALID`。
- [ ] **AC-4 ambiguous 404/auth/transport fail closed**：repository-missing、ACL-masked、malformed/unknown
  body 的 inventory 404 均为 `HTTP_404`，201/202/204/206 等非 200 success 均为
  `RESPONSE_SCHEMA_INVALID`，不得降级为 absent；401、403、5xx 与 transport failure 继续返回原有稳定
  `HTTP_401`、`HTTP_403`、`HTTP_ERROR`、`TRANSPORT_ERROR`。inventory 每页在读取/JSON parse 前固定
  `128 KiB` 上限：先验证所有 `Content-Length`（只接受 non-negative decimal 且重复值必须一致），声明超限
  在 read 前拒绝；随后 bounded read `limit+1`，实际超限或声明/实际不一致均 fail closed。整个 audit 的
  inventory response 累计上限为 `4 MiB`，不得形成 absent evidence。
- [ ] **AC-5 present account permission contract**：account present 时 cross-project exact `read` 是安全 evidence；
  `write|admin|owner` 继续写入 `cross_project_write_violations` 并使 audit 为 `GAP`。
- [ ] **AC-6 target repository 门不回归**：target repository permission 仍必须 exact `write` 才能收敛；missing
  为 `GAP`，malformed 为 `RESPONSE_SCHEMA_INVALID`。routine identity 必须 exact non-admin，PAT scope exact，
  protection 必须 human+routine merge allowlist、required context exact、push/force denied。
- [ ] **AC-7 readable evidence**：routine section 新增完整 `cross_project_permissions`。account present 时逐个
  repository 返回 strict permission `present/read|write|admin|owner`；account missing 时只接受 AC-1 的 exact
  collaborator inventory absence 并返回 `absent/null`。该 inventory 与 violation list 一致，不泄露 token/path。
- [ ] **AC-8 regression**：补正向、负向、ordering tests，重放 #213 host audit、routine merge、governance、
  bootstrap/rollback/installer 与 full smoke/security tests；所有未运行项照实记录。
- [ ] **AC-9 mutation boundary**：本 Change 全程 live mutation=0；不创建或修改 account、PAT、credential、
  collaborator、protection、allowlist，不 install、不 routine merge、不 deploy；最终 PR policy 固定 manual。

## 接口、数据与兼容性影响

`host.access.audit` 的 `routine_merge` object 增加 `cross_project_permissions` list。既有
`cross_project_write_violations` 保留，不改名、不删除。disabled repository 返回空 inventory；enabled
repository 为每个其他 canonical repository 返回一项，顺序与 governance manifest 一致。

兼容分流只由两项 evidence 合取：routine account 的先行 exact 404/missing，以及 target/cross-project exact
collaborator inventory 的 strict 200 bounded list 中 exact login 缺席。permission endpoint 的 generic 404 body
不能区分 no-collaborator、repository missing 或 ACL masking，不再作为 absent evidence。任何 inventory 404、
非 200 success、malformed/oversized page、异常/重复/冲突 `Link` 或 pagination、duplicate/case-fold collision、
非法 login、Content-Length drift、单页/全 audit 字节预算或页数预算超限、与 missing account 矛盾的 login 均
fail closed。`128 KiB/page` 以 `50 × 约 2.5 KiB/identity + JSON overhead` 为依据；`4 MiB/audit` 在覆盖
canonical repository 的常规 inventory 同时，为异常多页/多 repository 响应提供确定性总上限。

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
