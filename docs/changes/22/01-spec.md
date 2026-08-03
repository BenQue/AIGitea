---
issue: 22
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/22
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
  - rollback
  - platform-governance
depends_on:
  - 23
status: approved
branch: change/22
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Spec

## 目标与原因

为新 Linux 应用提供 Docker-first、project-neutral、可在线或完全离线交付的 release
contract。受控 `linux/amd64` builder 一次构建 OCI images；测试和生产只运行同一份 manifest
声明的 immutable digests 与 Compose checksum。目标 AppServer 不执行 `docker build`、
`npm install`、`git pull` 或公网依赖下载。

PM2 继续作为已存在应用的 legacy adapter，只有各项目独立迁移验收后才退出。平台 runtime
无 AI 依赖、不持有 Gitea 或数据库 Secret，也不获得合并权限。

## Acceptance criteria

- [ ] **AC-1** README、02/07/12 分册把新 Linux 默认值统一为“Docker-first + PM2 legacy
  adapter”，明确 builder、Registry、AppServer、共享 Nginx/PostgreSQL 和跨仓边界；历史
  PM2 as-built 不被改写成 Docker 已部署。
- [ ] **AC-2** 提供 release contract v1 JSON Schema 和 strict parser。Manifest 至少包含
  contract version、40 位 Gitea merge SHA、source repository、`linux/amd64`、Compose
  checksum、唯一 service/image digest、runtime services、migration identity，以及 #23 的
  `profile_id`、`catalog_revision` 和 `architecture_lock_sha256`。
- [ ] **AC-3** 无效 SHA、mutable-only image、非批准 platform、重复 service、未知字段、
  路径越界、checksum 不一致、缺 architecture lock 或 profile/catalog mismatch 必须在任何
  Docker mutation 前 fail closed。
- [ ] **AC-4** 提供稳定 CLI `verify`、`deploy`、`status`、`rollback`；CLI 只接受受保护
  target profile 与 release ID，不接受 manifest 提供的任意 shell/remote command。Secret
  只存在于目标机外置文件，不进入 manifest、state、argv 或日志。
- [ ] **AC-5** `RegistryTransport` 按 digest pull；`OfflineBundleTransport` 先验证 manifest、
  Compose、archive inventory 和 SHA256，再 load/inspect。二者消费相同 release identity，
  不能重建“等价”image。
- [ ] **AC-6** Compose config 禁止 `build:`、mutable-only image、privileged/root、Docker
  socket 和非 loopback host publish；runtime service 必须有 healthcheck、read-only rootfs、
  `cap_drop: ALL`、`no-new-privileges`、资源限制、日志轮转、网络分区和精确 release label。
- [ ] **AC-7** target profile 必须声明 #21 定义的 host role；`appserver-test/prod` 才允许
  deploy，`scm-ci` 只能 verify/build/publish。role mismatch 在停止旧容器前失败。
- [ ] **AC-8** 状态机具备进程锁、同 SHA healthy no-op、一次性 migration、
  `compose up --wait`、运行容器 exact-release 检查、原子 state、previous release 和显式
  rollback；rollback 不执行 migration 或 PostgreSQL restore。
- [ ] **AC-9** fake Docker/fixture tests 覆盖 schema、architecture lock、host role、两种
  transport、tamper、幂等、migration failure、health failure 回切、显式 rollback 和 Secret
  不落盘；shell/Python/installer/full smoke 全部通过。
- [ ] **AC-10** 提供无 Secret target profile 和 NewEmaint onboarding 示例；应用仓库必须
  自行实现 Dockerfile、Compose、migration、CI publish、health 和 bundle，且建立自己的
  Issue/spec/plan/PR。
- [ ] **AC-11** `03-verification.md` 分开记录 local candidate、Gitea PR CI、Registry/
  offline 测试 AppServer、重复部署、故意失败回滚和 production promotion；未真实执行保持
  `NOT RUN`。
- [ ] **AC-12** #23 未 closed + `completed/deployed` 时，#22 可实现和测试但不得进入
  `READY_FOR_REVIEW`；依赖满足后从最新 `main` rebase/merge 并运行 integration tests，
  不复制第二份版本目录。

## 接口、数据与兼容性影响

### Release 目录

```text
<release_root>/<40-char-release-id>/
├── release.json
├── compose.yaml
└── images.tar                 # offline transport 可选
```

`release.json` 不包含环境名、URL、密码、token、连接串、证书、SSH key 或任意 command。
Test/prod target profile 只改变 environment、transport、路径、Compose project、host role 与
外置 env file，不改变 release bytes。

### 跨 Issue 所有权

- #21 owns：host role 与 capability allowlist；#22 只消费并验证。
- #23 owns：architecture profile、catalog revision、例外与 lock；#22 不选择组件版本。
- #22 owns：release manifest、OCI/offline transport、deploy/status/rollback state machine。
- 应用仓 owns：Dockerfile、Compose service、migration 和业务 health。

## 风险与回滚约束

- Docker daemon 权限等同主机高权限；production caller 应由 sudo/forced-command 映射到固定
  profile，容器永不挂载 daemon socket。
- 先完成 contract、checksum、architecture lock、host role、Compose config 和 image
  availability 验证，再 migration 或替换容器。
- image 回切只适用于 schema-compatible release；数据库 restore 始终是独立人工审批。
- 平台代码走 revert PR；Registry 不可用时切换同一 manifest 的 offline bundle。
- #23 合并后必须重跑 integration tests；依赖冲突不能靠复制 catalog 文件解决。

## 非目标

- 不实现 Kubernetes、Swarm、多节点零停机编排或数据库 HA。
- 不为每个应用封装独立 Nginx/PostgreSQL/Redis。
- 不修改 NewEmaint 或其它应用仓库，不执行真实 migration 或部署。
- 不安装/启用 Docker daemon、创建 Registry/数据库 Secret 或生产凭据。
- 不清理 `gitea-ci` 现存业务进程；该范围属于 #21。

## 未决问题

无。
