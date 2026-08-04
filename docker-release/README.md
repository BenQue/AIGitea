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

V2 image entry 明确区分四类 identity：

```json
{
  "service": "web",
  "reference": "registry.example/admin/newemaint-web@sha256:<manifest-digest>",
  "digest": "sha256:<manifest-digest>",
  "image_id": "sha256:<config-digest>",
  "transport_reference": "aisoft.local/admin/newemaint/web:<40-char-release-sha>",
  "runtime_reference": "aisoft.local/admin/newemaint/web:<40-char-release-sha>"
}
```

- `reference`/`digest` 是 Registry source identity；Registry path 必须验证 `RepoDigests`。
- `image_id` 是 Registry/offline 共同的 local content identity。
- `transport_reference` 是 producer 创建并按其执行 `docker image save` 的 release-scoped tag。
- `runtime_reference` 是 Compose `image:`；V2 首版要求与 transport tag byte-identical。

Tag 由 lower-case source owner/repository、service 和完整 release SHA 确定，只是搬运和本地
解析别名，不是信任根。Producer 必须先按 digest pull/inspect，再创建 tag、重复 inspect exact
image ID/platform，最后按 tag save。Offline consumer 按 runtime tag inspect `RepoTags`、image ID
和 `linux/amd64`，不要求 `RepoDigests`。Registry consumer 则按 digest pull、验证 `RepoDigests`
与 image ID，再创建同一 runtime tag。两条路径均以 `--pull never --no-build` 启动，并在启动后
复核 container `Config.Image`、image ID、release/service labels 与 health。

`architecture.lock.json` 必须是 #23 `schema_version: "1.0"` 的 canonical lock，且
`delivery_contract` 精确为 `docker-release/v1`。Release parser 会验证 lock 的严格字段结构、
canonical `lock_sha256`、source checksums 格式、排序/唯一性，以及 manifest/target profile
中的 `profile_id` 与 `catalog_revision`；它只消费这些治理身份，不复制或选择 catalog 中的
组件版本。

Manifest、architecture lock、Compose、inventory 和 archive 在任何 pull/load/migration/
container replacement 前完成路径与 checksum 验证。`release.json` 不接受未知字段，也不得
包含 URL credential、token、密码、连接串、证书、SSH key、`.env` 内容或任意 command。

V2 offline sub-contract 为 `docker-release-offline-bundle/v2`，inventory 为
`docker-release-offline-inventory/v2`。Archive 必须恢复 manifest 中逐 service 唯一的 transport
tag，`manifest.json` 的 `RepoTags`、config image ID、layer member 与可选 OCI/repositories
references 都在 load 前进入 allowlist 检查。既有未声明四类 identity 的 Registry manifest
继续按 digest 路径读取；legacy offline bundle 在任何 Docker call 前稳定拒绝，迁移方式只能是
由受控 producer 重新 pull/build、tag、save 并发布完整 V2 bundle，不能原地编辑 tar/inventory。

## Docker capability gate

Runtime 以固定 argv、bounded/redacted output 读取 server Engine version、Compose version、
`linux/amd64`、graph driver 与 `docker info -f '{{ .DriverStatus }}'` 等价的 structured
`DriverStatus`。只有 `driver-type=io.containerd.snapshotter.v1` 且 driver 为 `overlayfs` 才归一为
`containerd`；没有 snapshotter marker 且 driver 为 `overlay2` 才归一为 `classic`。缺失、冲突、
未知 marker/driver 都 fail closed，不以 Engine major 猜测 store。

Versioned policy 位于 [`compatibility/image-stores-v1.json`](compatibility/image-stores-v1.json)。
Runtime 只接受唯一匹配且 `status=supported`、带 `kind=real-e2e` evidence 的 row。Issue #27 已在
两个独立 disposable Engine `29.7.1`、Compose `2.40.3`、`linux/amd64` containerd daemon 上完成
Registry push/pull、tag/save/load、offline pull rejection、Compose `--pull never --no-build`、
identity/health 与 exact cleanup；因此 containerd row 由 evidence
`issue-27-containerd-a75181cd7209`（2026-08-04，来源
`docs/changes/27/03-verification.md`）固定为 `supported`。Classic 没有同等级真实证据，继续
`rejected + evidence:null`；不能依据 fake adapter、源码阅读或偶然 `RepoDigests` 标记 PASS。

Disposable harness 位于
[`codex/tests/integration/test-docker-image-store-e2e.sh`](../codex/tests/integration/test-docker-image-store-e2e.sh)。
无参数运行只输出 `NOT RUN`，不会访问 Docker。`--preflight` 与 `--execute` 都要求精确授权 marker、
两个不同 daemon endpoint/target ID、完整 release SHA、digest-pinned 且已预载的 Registry fixture
image；harness 会回读并比较实际 daemon ID、记录 data root，拒绝两个 endpoint 指向同一 daemon。
SSH endpoint 只接受不含密码、path、query 或 fragment 的 `ssh://user@host`；其它 endpoint 仍拒绝
任何 `@` userinfo，避免把 credential 带入 argv 或 evidence。
它不创建 daemon/VM、不改 daemon config、不 restart、不 prune；成功路径在写 evidence 前反向证明
自身 Compose project/network、Registry container 与 release image/tag 已清理。

## Target profile

Target profile 是 root/operator 管理的环境配置，部署时必须是 mode `0400` 或 `0600`、非
symlink，且 owner 是 root 或当前调用者。它只声明环境、host role、hostname、transport、
固定目录、Compose project、外置 env file 路径和 architecture 期望值；模板不包含 Secret。

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

Runtime mutation ordering 固定为：strict files/checksums/archive refs → read-only
Engine/Compose/store capability → normalized Compose → pull/load/tag + exact inspect → migration →
临近启动再次 inspect → Compose `--pull never --no-build` → container identity/health。Wrong store、
legacy offline 或 pre-load tamper 的 Docker mutation count 必须为 0；post-load inspect 失败不得运行
migration/up；post-start identity mismatch 使用既有 previous-container rollback，不自动恢复数据库。

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

## Pinned primary evidence

下列资料于 2026-08-04 固定读取；它们证明 contract 语义与实现选择，但不替代真实 E2E：

- Docker Docs `d1eaa21fd5d7466c698fe7ef11d00bbaab33165e`：
  [`docker image save`](https://github.com/docker/docs/blob/d1eaa21fd5d7466c698fe7ef11d00bbaab33165e/data/cli/engine/docker_image_save.yaml)
  归档 images/tags，
  [`docker image load`](https://github.com/docker/docs/blob/d1eaa21fd5d7466c698fe7ef11d00bbaab33165e/data/cli/engine/docker_image_load.yaml)
  恢复 images/tags；文档没有承诺恢复 registry canonical digest name/`RepoDigests`。
- 同一 Docker Docs commit 的
  [containerd image store](https://github.com/docker/docs/blob/d1eaa21fd5d7466c698fe7ef11d00bbaab33165e/content/manuals/engine/storage/containerd.md)
  说明 Engine 29 fresh install 默认 containerd，而 upgrade 保留 classic，并给出 `DriverStatus`
  marker；因此不能由版本号推断 store。
- Moby `6719bc3c8d675b3ac60a2fd78c630a066177e20d`：classic
  [`tarexport/save.go`](https://github.com/moby/moby/blob/6719bc3c8d675b3ac60a2fd78c630a066177e20d/daemon/internal/image/tarexport/save.go)
  对 canonical reference 不加入 tag association；containerd
  [`image_exporter.go`](https://github.com/moby/moby/blob/6719bc3c8d675b3ac60a2fd78c630a066177e20d/daemon/containerd/image_exporter.go)
  对显式 digest export 同样不保留 tag。由此必须显式创建 release-scoped tag 再 save。
