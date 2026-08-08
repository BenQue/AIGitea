---
issue: 61
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/61
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
depends_on:
  - 35
  - 51
  - 55
status: pr-open
branch: change/61
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/63
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与原因

建立从 Mac host 到本地 OrbStack/Gitea/VM 的唯一结构化访问入口，并让每次请求在执行前绑定 exact
project、target、operation 和 least-privilege identity。正常任务不再先运行双路径诊断来猜测真实
状态；broker 成功即使用 host path，broker 自身失败且状态仍矛盾时才进入 emergency diagnostics。

本合同还关闭 Issue #35 的消费缺口：Mac Git 和 VM poll 必须真正使用 manifest-declared
project-agent，HTTP/identity/target 错误必须作为 `BLOCKED_EXTERNAL` 非零退出，不能被 shell 结构吞掉。

## Acceptance criteria

- [x] **AC-1** strict `host-access-broker/v1` manifest 与 `gitea-governance/v1` byte-exact 交叉验证
  Gitea base URL、owner、human merge identity、manager、repository 与唯一 project-agent；未知、重复、
  identity/target mismatch、跨项目 mapping 或 schema extra key 全部拒绝。
- [x] **AC-2** broker CLI 只接受 manifest project、allowlisted operation 和 operation-specific typed
  argument。不得接受或拼接 shell、URL、owner/repository、checkout path、credential path、Git refspec、
  force、merge 或任意命令；operation catalog 不包含 merge。
- [x] **AC-3** project repository/Issue/PR/Git read/write 路由到自己的 project-agent；settings/protection
  read 路由 manager audit；manager mutation credential 只保留给 purpose-built repository mutation，
  不能用于 ordinary Git 或 merge；人工 `admin` 不进入 broker credential catalog，仍是唯一 merge identity。
- [x] **AC-4** Mac project-agent credential 只从 manifest 固定的 macOS Keychain service/account 读取；
  VM project-agent credential 只从 manifest 固定的 non-symlink mode 400/600 file 读取。Secret 不进入 argv、
  terminal stdout/stderr、日志、Git config、Issue/PR 或仓库；credential helper 只在 exact Git protocol
  host/path 命中时通过私有 pipe 返回给 Git。
- [x] **AC-5** repo-local Mac binding 工具只处理 manifest 中 exact checkout/remote，配置
  `credential.useHttpPath=true` 和 fixed helper，不写 token/path，不改 global/system Git config；
  AISoftPlatform synthetic canary 覆盖 feature push route、`main`/force/merge surface 缺失与二次 no-op。
- [x] **AC-6** profile contract 使用 `GITEA_IDENTITY` + fixed `GITEA_TOKEN_FILE`，profile 本身不含 token。
  `project-poll.sh` 在 provider/API 前验证 profile name/project/URL/owner/repo/identity/token path/mode，
  token identity 或 target 不一致时非零 `BLOCKED_EXTERNAL`。
- [x] **AC-7** NewEMaint=`emaintenance`、HSDB=`hsdb`、rsdesign-new=`rsdesign`、
  SFMDigitalBoard=`sfm` 四个 exact VM profile 支持 `plan/apply/read-back/rollback`。apply 先保存原 bytes/
  uid/gid/mode/hash，拒绝 symlink/宽松 mode/cross-project token，使用同目录 temp + atomic replace；任一失败
  自动恢复全部文件，固定 latest backup 可精确 rollback。
- [x] **AC-8** profile apply 后验证 authenticated exact identity/target 和目标文件 metadata；相同输入第二次
  为 no-op，不创建新 backup。rollback 恢复 bytes/uid/gid/mode并再次 read-back，不影响其它 project。
- [x] **AC-9** Gitea HTTP 401/403/404、transport/API/schema 错误、identity/target mismatch 在 broker 和
  project poll 均输出脱敏 `BLOCKED_EXTERNAL` 并非零退出。`provider-poll.sh` 不再用 process substitution/
  `|| echo` 吞掉 list/analyze/Loop 失败，systemd oneshot 必须真实反映失败。
- [x] **AC-10** installer 只复制 versioned broker/runtime/manifest/helper/profile-migration candidate；不创建
  credential、不修改 Git config/profile/token、不 enable/restart timer/service/VM、不部署应用。二次安装
  byte-identical/no-op，保留上一稳定 runtime 供 post-merge rollback。
- [x] **AC-11** focused tests 覆盖 operation/target allowlist、无 shell/URL/merge surface、credential
  mode/symlink、secret redaction、identity/target mismatch、HTTP 4xx nonzero、cross-project denial、Mac repo
  binding、profile atomic backup/automatic restore/rollback/read-back 与 idempotent second-run no-op。
- [x] **AC-12** `bash -n`、ShellCheck（若可用）、focused tests、`bash codex/tests/smoke.sh`、strict JSON、
  Secret scan 与 `git diff --check` 通过。最终 PR `Closes #61` 并链接本目录；PR 只能由人手工合并。

## 接口、数据与兼容性影响

新增 `host-access-broker/v1` 外部合同，project 使用稳定 `project_id`，不由 checkout 名、profile 名或
URL 猜测。v1 operations 仅包含固定 Gitea read、Git fetch/change push、Mac binding、OrbStack status
和四项目 profile lifecycle；不提供 merge、任意 shell/URL/refspec 或通用 onboarding。

VM profile 从 inline `GITEA_TOKEN` 收敛到：

```text
AISOFT_PROJECT_ID=<manifest project_id>
GITEA_URL=<manifest base_url>
GITEA_OWNER=<manifest owner>
GITEA_REPO=<manifest repository>
GITEA_IDENTITY=<manifest project_agent>
GITEA_TOKEN_FILE=<HOME-relative exact credential target resolved to absolute path>
```

`common.sh` 只在验证 mode 400/600 regular file 后读取 token 到进程环境；token 不传 argv。旧 inline
profile 是迁移输入，不是新 contract；post-merge 工具完成四项目迁移后才切换 poll runtime。

## 安全、部署与回滚约束

broker failure 输出只能含 stable error code/project/operation/status，不回显 URL query、response body 中
疑似 Secret、credential path 或 token。Git push 仅允许当前 exact checkout 的 `change/N` 同名 branch，
不接受 `main`、其它 refspec、delete 或 force。profile lifecycle 只能通过 exact project mapping，backup
目录固定且 mode 700，Secret backup/target mode 600。

本 PR 合并前 host broker live install、Mac Keychain/Git config mutation、VM project profile/token
mutation、timer/service/VM restart、真实 private poll、应用/数据库/公司内网部署全部 `NOT RUN`。
post-merge 只能从 exact protected-main SHA 安装：先 broker health，再逐 project plan/apply/read-back/no-op，
最后只对原 active timers 做受控 poll 验收；失败按 project rollback，不扩大权限、不恢复 `ci-bot`。

## 非目标

- 不实现通用 onboarding v2，不泛化 Issue #35 bootstrap/marker/approval hardcoding。
- 不创建、删除、rotate 或 revoke Gitea 账号/PAT/legacy credential，不修改 ACL/visibility/protection。
- 不修改业务代码、业务数据库、应用 runtime、DockerLab/AppServer、公司内网或生产环境。
- 不自动 merge/close PR，不给 manager/project-agent/`ci-bot` merge 权，不建立 merge 旁路。
- 不删除 `orbstack-access-diagnostics`；只把它从正常前置降级为 broker-failure emergency fallback。

## 未决问题

无。onboarding v2、stable broker 删除诊断技能的评估和公司内网 credential store 分别由后续 Issue 决定。
