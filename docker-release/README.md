# AISoftPlatform Docker release contract v1

本目录是新 Linux 项目的 project-neutral、Docker-first 发布合同。它只处理已经由受控
`linux/amd64` builder 生成的 OCI image；目标 AppServer 不执行 `docker build`、依赖安装、
`git pull` 或公网下载。现有 PM2 应用继续使用 legacy adapter，直到各项目通过独立 Change
完成迁移、回滚和环境验收。

## Release identity

每个 release 目录以完整 40 位 Gitea merge SHA 命名，并包含：

```text
<release_root>/<merge-sha>/
├── release.json
├── compose.yaml
├── architecture.lock.json
├── images.inventory.json
└── images.tar                 # 仅 offline-bundle 目标需要传输
```

`release.json` 固定 source repository、merge SHA、`linux/amd64`、Compose checksum、#23
提供的 architecture profile/catalog/lock checksum、每个 service 的 Registry digest 与
local image ID，以及一次性 migration identity。Registry 和 offline bundle 消费同一份
manifest；transport 不能重写 image、Compose 或 architecture identity。

`architecture.lock.json` 必须是 #23 `schema_version: "1.0"` 的 canonical lock，且
`delivery_contract` 精确为 `docker-release/v1`。Release parser 会验证 lock 的严格字段结构、
canonical `lock_sha256`、source checksums 格式、排序/唯一性，以及 manifest/target profile
中的 `profile_id` 与 `catalog_revision`。Transition resolved component 还必须同时包含绝对
HTTPS migration Issue、exception ID 与未到期 expiry，且 `exception_ids` 集合必须精确匹配；
preferred component 不得携带 transition metadata。Parser 只消费这些治理身份，不复制或
选择 catalog 中的组件版本。多个 transition component 可以引用同一个逐项列明范围的 umbrella
Issue，但仍必须使用不同的 component-scoped exception ID/expiry；Issue 存在或状态变化都不
等于 migration 完成，release identity 仍必须与全部真实 bytes 一致。

Manifest、architecture lock、Compose、inventory 和 archive 在任何 pull/load/migration/
container replacement 前完成路径与 checksum 验证。`release.json` 不接受未知字段，也不得
包含 URL credential、token、密码、连接串、证书、SSH key、`.env` 内容或任意 command。

## Target profile

Target profile 是 root/operator 管理的环境配置，部署时必须是 mode `0400` 或 `0600`、非
symlink，且 owner 是 root 或当前调用者。它只声明环境、host role、hostname、transport、
固定目录、Compose project、外置 env file 路径和 architecture 期望值；模板不包含 Secret。
`architecture_project_id` 是 v1 可选字段，因此旧 target profile 不声明时仍兼容；一旦声明，
lock `project_id` 必须精确匹配。NewEmaint current adoption 必须声明 `newemaint`，不能用
`newemaint-target-candidate` target lock 替换。Project/profile/catalog、release checksum、lock
self-hash 或 exception expiry 任一不匹配，都会在 Docker config/pull/load/migration/up 前拒绝。

Current lock 表达实际 release bytes；target candidate 只表达期望架构。Transition 不授权依赖、
schema、image 或 database migration，也不能绕过 `prohibited`/EOL/digest/expiry/checksum。

`scm-ci` 只允许 `verify`，`deploy`、`status` 和 `rollback` 只允许
`appserver-test`/`appserver-prod`。这一 preflight 只消费 #21 的 host-role 语义，不授权或执行
#21 的 live cleanup。

## Stable CLI

```bash
aisoft-docker-release verify   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release deploy   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release status   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release rollback --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <previous-merge-sha>
```

CLI 只接受受保护 profile 和 release ID；所有路径由 profile/manifest 派生，不接受 shell、
remote command、migration command 或 Compose override。Docker subprocess 不使用 shell，失败
输出不会回显可能含 Secret 的 stdout/stderr。

## State and rollback

每个 target 使用单一进程锁和 mode `0600` 的原子 JSON state。当前 release 已精确 healthy
时，同 SHA deploy 是 no-op。Migration service 名称来自已验证 manifest/Compose，identity 在
运行前写入 `started`，成功后写入 `completed`；`failed` 或中断后的不确定 migration 不会自动
重跑。`compose up --wait` 或 exact-release health 失败时回切旧容器，但不会执行 PostgreSQL
restore。显式 rollback 同样不运行 migration；数据库恢复始终需要独立人工审批。

## Install boundary

`install.sh` 只复制 runtime、schema、CLI 和示例。它不创建 live target profile、Secret、
Docker login、systemd unit，不调用 Docker，也不 enable/start/deploy。真实 Registry、offline
media、AppServer 和 production 验收必须在消费项目的独立 Issue/spec/plan/PR 和环境 Gate 中
完成。
