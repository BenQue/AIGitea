---
issue: 35
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/35
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
  - deployment
depends_on: []
status: pr-open
branch: change/35
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/36
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与原因

建立一套同时适用于本地 OrbStack Gitea 和未来公司内网 Gitea 的最小权限治理合同：平台能够
跨项目审计仓库，但项目自动化身份只能写自己的仓库；所有 `main` 合并只能由人工身份执行；
仓库默认 private，只有版本化 allowlist 中的非内部应用可以 public。

目标不是把一个全站管理员 token 发给所有 Agent，而是把管理面、项目执行面、人工合并面和
VM/部署面分离，并提供默认只读、逐目标、可审计、可回滚的标准工具。

## Acceptance criteria

- [ ] **AC-1** strict JSON governance manifest 明确 `contract_version`、本地 environment、人工
  merge identity、platform manager、shared-bot 迁移规则、server policy 和 9 个 exact repository；
  public allowlist 只能是 `admin/aisoft-platform`、`admin/myapp`、`admin/smoke-test`，其余 6 个
 内部应用均为 private，重复/未知/隐式条目被拒绝。
- [ ] **AC-2** `aisoft-platform-manager` 只作为 9 个显式仓库的 Admin collaborator，不是 Gitea
  site admin；audit PAT scopes 精确为只读，mutation PAT 单独保存。manager 不得出现在普通 Git
  remote、project profile、push/force-push/merge allowlist 或 provider 日志。
- [ ] **AC-3** manifest 为每个仓库指定唯一 project agent，权限精确为 Write。工具拒绝相同 agent
  绑定多个项目、agent=`admin`/manager/shared bot、权限 Admin、跨项目 Write/Admin，以及任何
  agent 进入 `main` allowlist。
- [ ] **AC-4** service-account bootstrap 一次只处理 manifest 中一个已声明身份；使用 Gitea
  `bot` user、`must_change_password=false` 和最小 PAT scopes，Secret 只写 caller 指定的 mode
  600 文件且不进入 argv/stdout/log/Git。账号已存在但 credential file 缺失时 fail closed，不
  静默生成第二个未知 token。
- [ ] **AC-5** governance check 默认只读，输出脱敏 current/expected/planned action；apply 必须
  指定 exact repository、Issue #35、已合并 `origin/main` 完整 SHA、mutation credential 和
  evidence directory。未知仓库、branch、账号、credential mode、API 或 read-back 异常均停止。
- [ ] **AC-6** 每仓库 apply 将 manager 校准为 Admin、project agent 校准为 Write、visibility
  校准为 manifest 值、`default_delete_branch_after_merge=true`，并创建或收紧 `main` protection：
  禁止 direct/force push，merge allowlist 精确为 `admin`，不包含 manager/agent/`ci-bot`；已有
  status contexts、approval/review/file-pattern 字段必须逐项保留。
- [ ] **AC-7** `ci-bot` 默认保持不变。只有 exact project profile 已改用项目 PAT，项目 agent
  完成 private repo read、Issue/comment/label、feature push、PR 和不能 push/merge `main` 的真实
  验证后，才允许通过独立 `--retire-shared-bot` 对该仓库移除；失败立即回加 Write 并恢复 profile。
- [ ] **AC-8** Gitea service policy 在 `/etc/gitea/app.ini` 精确设置
  `service.DISABLE_REGISTRATION=true`、`repository.DEFAULT_PRIVATE=private`、
  `repository.FORCE_PRIVATE=false`；先保存 mode/owner/bytes 受控备份，重启后验证 Gitea health、
  登录和 public/private API。失败恢复备份并再次验证。public 仓库保持匿名可读是显式例外，
  private 仓库匿名访问不得成功。
- [ ] **AC-9** VM/部署合同明确：OrbStack machine lifecycle 仍由 Mac host control + 明确授权；
  `gitea-ci` operator 只管理 SCM/CI；每个应用在其部署 Change 中使用独立 deploy identity 和目录/
  service/database 最小权限。不得把 Gitea manager/PAT 当作 SSH、sudo、OrbStack 或生产凭据。
- [ ] **AC-10** 公司内网重建清单执行相同 private-default/public-allowlist、manager/project-agent、
 人工 merge 和 protection 策略，但重新创建账号/PAT/Secret，不迁移本地身份材料；公司内网
  inventory 与 mapping 必须在 mutation 前单独批准。
- [ ] **AC-11** focused tests 覆盖 manifest schema/semantics、visibility drift、collaborator drift、
  cross-project write、缺失 protection、status/approval preservation、registration drift、API failure、
  read-back mismatch、secret redaction、idempotent no-op 和 rollback。`bash codex/tests/smoke.sh`、
  `bash -n`、ShellCheck（若可用）、JSON parse 和 `git diff --check` 通过。
- [ ] **AC-12** 最终 PR `Closes #35`，只能由人工合并。PR 合并前 live Gitea/VM/公司内网均
  `NOT RUN`；合并后逐仓库 apply 与 service restart 的真实结果追加到 `03-verification.md`，
  未执行不得标为 `completed`/`deployed`。

## 接口、数据与兼容性影响

新增 `gitea-governance/v1` manifest 与命令行合同；不改变应用 API、数据库 schema 或制品格式。
旧 `ensure-gitea-collaborator.sh` 的 fixed `ci-bot` gate 在迁移期保持兼容，但新项目完成 #35
发布后必须消费 manifest 中的 project agent。现有 project profiles 不能原地共享 token；必须
逐项目生成和安装新的 mode 600 profile。

本地环境继续使用 `admin/*` 坐标，不在本 Change 引入 Organization 或转移仓库。未来公司内网
可以使用组织命名空间，但必须通过 migration mapping 将逻辑仓库分类映射到目标坐标；不能因此
扩大 public allowlist。

## 风险与回滚约束

每次 live apply 前保存仓库 metadata、manager/agent/shared-bot permissions 和完整 normalized
branch protection。visibility、collaborator、protection 与 server config 分阶段应用；任一阶段
read-back 不一致就停止，不能继续处理下一个仓库。

仓库回滚使用同一 pre-snapshot 精确恢复 private 值、collaborator permission 和 protection；
如果新 agent 已产生分支/Issue/PR，回滚权限不得删除这些 Git/Gitea 对象。service config 回滚
恢复原始 `/etc/gitea/app.ini` bytes/owner/mode 并重启验证。账号/PAT 不自动删除；先禁用/撤销
token，确认无 project profile 引用后再由独立清理授权处理。

## 非目标

- 不在 PR 合并前创建/修改任何 live Gitea 用户、PAT、仓库、visibility、protection 或 app.ini。
- 不迁移到 Gitea Organization，不改变仓库 owner/URL，不迁移 Issue/PR/评论或账号。
- 不修改业务代码、数据库、Runner、AppServer runtime、容器、公司服务器或生产环境。
- 不自动合并 PR，不给 manager/project agent/shared bot merge 权，不建立任何合并旁路。
- 不按仓库名称、public 状态或搜索结果自动把新仓库纳入 manifest。

## 未决问题

无。未来新增 public 测试仓库、公司内网坐标 mapping 和每个应用 deploy identity 的 OS 细节，
分别由对应的新 Issue/部署 Change 决定，不影响本合同实现。
