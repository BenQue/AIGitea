---
issue: 213
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/213
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 35
  - 208
status: approved
branch: change/213-routine-live-pilot
created: 2026-08-27
updated: 2026-08-27
---

# 单仓 routine auto-merge live pilot 与可逆验收规格

## 目标与原因

只为 `admin/NewEMaint`（`project_id=newemaint`）交付可安装、可读回、可回滚的 routine live pilot
source。routine identity 固定 `newemaint-routine-merger`，required context 固定
`CI / verify (pull_request)`，首个且唯一 canary 固定 NewEMaint Issue #74。

本 Change 只实现 source、测试和本地验证。本任务不得创建 live account/PAT/credential，不得修改
collaborator/protection，不得执行 routine merge POST、部署或 merge。source 合并后仍须独立 live 授权；
任何未授权或不完整状态保持 GAP/`NOT RUN`。

## Acceptance criteria

- [ ] **AC-1 单仓 opt-in**：canonical manifest 只把 `admin/NewEMaint` 设置为
  `routine_auto_merge_enabled=true`，绑定 `project_id=newemaint`、identity
  `newemaint-routine-merger`、required context exact 和 canary Issue #74；其他 repository objects
  byte-equivalent、routine eligibility 继续 disabled。`aisoft-platform` 与本 Issue #213 固定 manual。
- [ ] **AC-2 双 provenance + rollout SHA**：live bootstrap/apply/rollback 前同时证明 Issue #208 merged
  SHA `8d109b14b6e0936be30f6f287ff6050e48632e0b` 与 Issue #35 baseline merged SHA
  `69251fd4d07665385eb6d9142038848c2b9392d7` 是 `origin/main` 祖先，并证明当前 manifest bytes 等于
  #213 最终 merged SHA；三个锚任何一个缺失、漂移或不在 main 都在 mutation 前失败。
- [ ] **AC-3 account state**：governance `check --repository NewEMaint` 明确输出 routine account
  `present-non-admin`、`missing` 或 `present-site-admin`；missing 是待 bootstrap GAP，site-admin 是安全
  GAP，不能被同一分支自动修正。project account 的既有输出保持兼容。
- [ ] **AC-4 bootstrap 边界**：routine bootstrap 只接受 exact project/username/credential binding 和 #213
  live mode，创建或复用 ownership markers，输出 account/PAT mutation count 与完整非敏感 readback；
  幂等重跑不得生成第二枚 PAT。其他仓库不因 NewEMaint pilot 获得 live bootstrap 授权。
- [ ] **AC-5 PAT exact scope**：bootstrap readback 与 `gitea.pull.merge.routine` 每次唯一 merge POST 前都
  fresh 验证 PAT scopes 恰为 `write:repository`；缺失、多余、`all`、admin scope 或无法解析均返回稳定
  failure，merge POST=0、fallback=0。
- [ ] **AC-6 host audit**：`host.access.audit` 对所有 project 都返回显式 routine section；disabled 仓库
  为 `not-enabled`。NewEMaint enabled 时覆盖 credential metadata、exact identity、non-admin、exact scope、
  exact repository Write、全部其他 manifest repositories 无 Write/Admin/Owner、protected main 的
  human+routine merge allowlist、required context 与 push/force denial。缺 credential/account/apply 以 GAP
  读回，不把 source opt-in 写成 live PASS，且不泄露 path/token。
- [ ] **AC-7 governance apply**：独立 live 授权后只允许 exact `NewEMaint` pilot apply；pre-snapshot 必须先于
  第一个 write，post-snapshot/plan 必须无 blocker/action，输出 apply operation count 与 API mutation count。
  apply 不改其它 repository、不 deploy、不 merge。
- [ ] **AC-8 canary 限制**：NewEMaint routine broker 只接受 PR body 中授权的 Issue #74；其它 Issue、#213、
  wrong repository、第二个/漂移 canary 均在 POST 前拒绝。成功仍只允许现有 fixed non-force、
  non-scheduled、delete-branch merge payload，最多一个 merge POST，零 deploy。
- [ ] **AC-9 deterministic PAT revoke**：rollback 使用当前 routine PAT 自撤销的 fixed
  `DELETE /api/v1/token`，要求 204，再以同 token 读回 401；随后安全移除 exact credential/token marker，
  输出 revoke mutation count=1，不接受任意 URL/token name/id 参数。
- [ ] **AC-10 account retain/delete**：rollback 顺序固定为 disable source opt-in 的已合并回滚版本 →
  repository rollback/human-only allowlist readback → routine collaborator missing → PAT revoke → 显式
  `account-policy=retain|delete`。`retain` 是默认合同且读回 non-admin account present；`delete` 只允许 #213
  ownership marker 创建的 exact account，执行 `gitea admin user delete --username` 后读回 404 并删除 markers。
- [ ] **AC-11 full readback**：live acceptance receipt 分别记录 source/installed Mac/installed VM/live account/
  credential/repository/protection/canary/rollback 层，包含 bootstrap/apply/canary/revoke/account-delete mutation
  counts；任一未执行项为 `NOT RUN`，任一失败零 fallback。
- [ ] **AC-12 install bytes**：Mac 与 VM installer-declared runtime/tools/config targets 必须逐文件等于 #213
  最终 merged SHA bytes；operation count、source/installed manifests、broker runtime、bootstrap/revoke tools
  均参与检查，不能只比较 Git HEAD。
- [ ] **AC-13 protected-main/manual/deploy 边界**：保留 direct push=false、force push=false、required CI exact、
  human admin merge；仅 live pilot readback 通过后 allowlist 才为 `admin + newemaint-routine-merger`。本 Change
  `complexity/complex + type/platform + policy=manual`，禁止自动合并；部署始终为零。
- [ ] **AC-14 tests**：相关 Python/shell tests、所有修改 shell 的 `bash -n`、可用时 ShellCheck、
  `bash codex/tests/smoke.sh`、semantic document audit 与 controller preflight 真实通过；live account/PAT/
  collaborator/protection/canary/deploy/merge 在本任务中保持 `NOT RUN`。

## 接口、数据与兼容性影响

### Canonical manifests

NewEMaint repository 增加 strict `routine_live_pilot` object，至少绑定 rollout/source/baseline Issue 与 SHA、
project id、routine username、canary Issue、required context 和 mutation maxima。任何 extra/missing/wrong value
都使 manifest validation 失败。其它 repository objects 不改字节；shared runtime 只增加 fail-closed 读回。

### Governance CLI

- `check` 增加 `routine_accounts`，不删除或改名现有 `project_accounts`。
- 新的 pilot mutation provenance gate 不复用只接受 Issue #35 的旧 gate；它显式校验 #35 + #208 + #213。
- apply/rollback receipt 增加确定性 mutation counts 与完整 readback；未获 live mode 时不调用 write API。

### Host-access broker

- operation catalog 不新增任意 target/payload surface；routine merge 仍只有 `(number, sha)`。
- `_probe_token_scopes` 在任何 merge POST 前执行，scope 必须 exact。
- `host.access.audit` 输出 routine section；enabled 但未 provision/apply 时返回 GAP，而不是无字段 PASS。
- NewEMaint canary gate从 manifest 派生 Issue #74；不能由 caller 传入或绕过。

### Bootstrap/revoke/rollback

bootstrap 与 rollback shell 不在 argv/stdout 暴露 token。PAT revoke 固定 self-delete endpoint；account deletion
使用官方 `gitea admin user delete --username`，只有显式 `delete` 且 ownership/readback 条件全满足才执行。
没有 purge/通配符/任意账号参数。

## 风险与回滚约束

- Source rollback：revert #213 唯一最终 PR，使 NewEMaint 回到 disabled；其它 repository manifest bytes 不变。
- Live rollback：必须先使用已合并 disabled source 与 exact snapshot 恢复 human-only protection并移除 routine
  collaborator，再 revoke PAT，最后按显式 retain/delete 处理 account；每一步完成后 readback，失败立即停止。
- `present-site-admin`、cross-project Write/Admin/Owner、scope drift、installed byte drift、protection drift 或 canary
  漂移均阻止 bootstrap/apply/merge/删除，不使用 admin/manager/project-agent/shared bot fallback。
- Gitea 1.26.4 无 merge-only ACL；ordinary Git denial 继续依赖 broker-exclusive custody、typed operation、
  exact manifest/final-head gates 与 zero fallback，不把它描述为 native ACL。

## 非目标

- 不在本任务创建、旋转、撤销任何 live PAT 或 account。
- 不在本任务修改任何 live collaborator、branch protection、required CI 或 allowlist。
- 不在本任务执行 NewEMaint Issue #74 canary、routine merge POST、manual merge 或部署。
- 不为第二个 repository opt-in，不放开 Issue #74 之外的一般 routine traffic。
- 不修改 `AGENTS.md` 或把当前 complex platform Change 变为 routine-auto。

## 未决问题

无。
