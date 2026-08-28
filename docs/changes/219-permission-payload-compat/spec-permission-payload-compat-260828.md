---
issue: 219
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/219
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
  - 217
status: spec-drafting
branch: change/219-permission-payload-compat
created: 2026-08-28
updated: 2026-08-28
---

# Gitea collaborator permission payload 安全兼容规格

## 目标与原因

恢复 #213/#215/#217 的只读 rollout preflight：在 Gitea 1.26.4 返回官方 extended collaborator
permission response 时，governance `check` 与 host-access permission readback 能解析可信 permission、role 与
exact collaborator identity；异常或越权 payload 继续在 mutation 前 fail closed。完成本 source change 后的真实目标仍是
`DRIFT/GAP + planned actions`，不是 `PASS`，更不表示 account/PAT/apply/install/live rollout 已授权或完成。

官方 v1.26.4 source contract：

- `modules/structs/repo_collaborator.go` 的 `RepoCollaboratorPermission` 固定为
  `permission:string`、`role_name:string`、`user:*User`。
- `services/convert/user.go` 的 `ToUserAndPermission` 把 `Permission` 与 `RoleName` 都设为同一个
  `accessMode.ToString()`，并由 `ToUser` 生成 nested user。
- `modules/structs/user.go` 定义 nested `User` 字段并由 `MarshalJSON` 增加兼容字段 `username`。

## Acceptance criteria

- [ ] **AC-1 两个固定顶层 variant**：parser 只能接受：
  1. legacy exact root keys `{"permission"}`；
  2. Gitea 1.26.4 extended exact root keys `{"permission","role_name","user"}`。
  root 非 object、空对象、缺字段、混合子集、任何未知 top-level field 均返回现有稳定 schema error；不得通过删除
  extra-field 检查实现兼容。
- [ ] **AC-2 permission 与 role 一致**：两个 variant 的 `permission` 都必须是 exact string，值只允许既有
  `read|write|admin|owner`。extended `role_name` 也必须是 exact string、使用同一 allowlist，并且 exact 等于
  `permission`。`none`、unknown、空白/case variant、non-string、permission-role conflict 均 fail closed。
- [ ] **AC-3 bounded user schema**：extended `user` 必须是 object，required subset 固定为
  `login`、`username`、`is_admin`。允许出现但可在类型验证后忽略的 metadata 只能来自 Gitea 1.26.4 User schema：
  `id`、`login_name`、`source_id`、`full_name`、`email`、`avatar_url`、`html_url`、`language`、
  `last_login`、`created`、`restricted`、`active`、`prohibit_login`、`location`、`website`、`description`、
  `visibility`、`followers_count`、`following_count`、`starred_repos_count`。任何其它 nested key fail closed。
  `login|username|login_name|full_name|email|avatar_url|html_url|language|last_login|created|location|website|description|visibility`
  只接受 string；`id|source_id|followers_count|following_count|starred_repos_count` 只接受 integer 且 boolean 不得冒充；
  `is_admin|restricted|active|prohibit_login` 只接受 exact boolean。metadata 值不参与权限决策。
- [ ] **AC-4 exact identity 与 site-admin denial**：validator 必须接收当前 fixed request 的 exact collaborator identity；
  extended `user.login` 与 `user.username` 必须各自 exact 等于 requested identity 且彼此相等，复用 canonical Gitea
  identifier contract，不允许另一个 identity、case-fold-only match、空白或 alias。`user.is_admin` 必须是 exact
  boolean `false`；`true`、`"false"`、0、missing 均 fail closed。repo-level `permission=admin` 与 site-admin=false
  不冲突。
- [ ] **AC-5 全调用面一致且 caller 不可注入**：governance target snapshot、cross-project audit，以及
  host-access manager/project/routine/cross-project permission readback 都使用等价的两个-variant安全合同；每次
  requested identity 由 manifest/credential route/fixed loop variable 派生，不从 response、CLI、env、snapshot
  或 caller payload 接受。existing expected permission、target Write、cross-project read/write/admin/owner
  判定与 violation 逻辑不变。
- [ ] **AC-6 #217 404 隔离不回归**：只有同一次 governance `_check` 先证明 exact configured routine account
  `missing`，且该 target routine permission endpoint 返回 404 时，才能继续投影 `missing` planned action。
  account present/site-admin、project agent、platform manager、shared/unknown identity、cross-project same-name identity、
  非 exact endpoint 与未建立 evidence 的 404 均 fail closed；host-access account-missing 路径继续只依赖 #215
  strict bounded collaborator inventory。401/403/5xx/transport 保持稳定 fail closed。
- [ ] **AC-7 check 与 apply 安全门不放宽**：governance `check` 与 host-access audit 全部 call inventory 仍为 GET，
  API mutation=0。`apply_repository` 不接收 account-missing 兼容 evidence，仍要求 enabled routine account exact
  non-admin、PAT exact scope、target/cross-project permission安全、protection/required context/human+routine allowlist、
  direct/force denial、action-specific live mode 与 fresh pre-snapshot-before-first-write；任何 extended schema failure
  在 credential/protection mutation 前停止。
- [ ] **AC-8 fixtures 与 ordering**：正向 fixtures 至少覆盖 legacy exact variant和本次真实脱敏 extended variant
  （root exact 三字段；permission=role_name；login=username=requested；is_admin=false；完整 known metadata types）。
  负向矩阵覆盖 malformed root、legacy extra、extended missing/extra、wrong types、unknown permission/role、role conflict、
  user non-object、unknown nested、missing required、metadata type drift、wrong/case-only identity、login/username conflict、
  is_admin true/string false。ordering 断言 account evidence 早于可兼容 404，所有 schema/security failures 早于
  PUT/PATCH/POST/DELETE、evidence snapshot 与 apply mutation。
- [ ] **AC-9 分层验证与发布边界**：运行 governance/host-access targeted/security suites、四个 routine shell suites、
  full smoke、semantic audit、`git diff --check` 与 Controller contract preflight。source/local PASS、installed bytes、
  live check、install/apply/#74/merge/deploy 分层报告；本 Issue 只实现 source/tests/docs，policy 固定 manual。
  安装后的真实 check 预期输出可信 `DRIFT/GAP/planned actions`，不得把它写成 live readiness PASS。

## 接口、数据与兼容性影响

不改变 CLI JSON output、canonical manifests、snapshot schema或 host-access typed operations。内部 permission validator
从只返回 permission string 的 legacy schema检查扩展为接收 `requested_identity` 并返回同一个 permission string；
extended 的 role/user 只用于一致性、identity 与 site-admin安全验证，不进入持久 snapshot/output。

legacy exact `{permission}` 保持兼容，但不能与 extended 字段混搭；extended 必须满足全部身份/安全条件。known nested
metadata 允许忽略是为了容纳 Gitea 官方 `User` 的非权限字段，不代表允许任意 object 或未知字段。

## 风险与回滚约束

- Source rollback：revert #219 唯一最终 PR，恢复 #217 merge 后 parser 行为。
- 无 live rollback：本 Change 禁止 install、live mutation、apply、merge 与 deploy。
- 任一 variant/schema/identity/site-admin/permission-role/auth/server/transport drift 都在 mutation 前 fail closed；
  不使用 admin、manager、project-agent、shared bot 或其它 identity fallback。

## 非目标

- 不创建、修改、撤销 account、PAT、credential、collaborator、protection、allowlist 或 required CI。
- 不执行 governance apply/rollback、NewEMaint #74、routine merge、manual merge、install 或部署。
- 不新增第三个宽松 variant，不接受 GitHub schema aliases，不修改 Gitea server 或 canonical manifests。
- 不修改 `AGENTS.md`、Controller、CI workflow、installer targets 或 deployment contract。

## 未决问题

无。
