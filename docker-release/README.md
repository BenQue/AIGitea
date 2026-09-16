# AISoftPlatform Docker release contract v1/v2

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
├── compose.model.json          # v2 producer-normalized Compose contract
├── architecture.lock.json
├── images.inventory.json
└── images.tar                 # v2 两种 transport 都用于严格内容图校验
```

`release.json` 固定 source repository、merge SHA、`linux/amd64`、Compose checksum、#23
提供的 architecture profile/catalog/lock checksum、每个 service 的 Registry digest 与
local image ID，以及一次性 migration identity。Registry 和 offline bundle 消费同一份
manifest；transport 不能重写 image、Compose 或 architecture identity。

Top-level `docker-release/v2` 在 v1 基础上要求 architecture `project_id` 以及
`compose.model_path`/`compose.model_sha256`。Project ID 将 manifest 与 exact architecture lock
绑定；Compose model 是 producer 已生成的 normalized Compose JSON，使 artifact
conformance 可以不依赖任何 target Docker Engine/Compose binary。`verify-artifact` 只接受 v2；
既有 v1 release 仍可由 legacy `verify/deploy/status/rollback` 读取，不能补默认字段或原地改写为
v2。迁移必须由 producer 重新 render、checksum 并发布完整 v2 release directory。

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
- `image_id` 固定 producer 的原生 inspect identity；跨存储消费仍绑定这份源记录。
- `transport_reference` 是 producer 创建并按其执行 `docker image save` 的 release-scoped tag。
- `runtime_reference` 是 Compose `image:`；V2 首版要求与 transport tag byte-identical。

`image_id` 是 daemon 对 exact runtime reference 返回的 inspect identity，不等同于所有 archive
中的 Config digest。Docker 29 classic archive 可以使用 image config digest；containerd archive
可以使用 content-verified top-level OCI descriptor digest：无 provenance 时是 direct image manifest，
带 provenance 时是 image index，而其 runnable `linux/amd64` manifest 再指向独立 config digest。
Direct OCI manifest 也允许 daemon 返回其 content-verified Config digest。Preflight 因此验证完整
`index/manifest descriptor -> runnable manifest -> config/layers` graph，并要求 Docker
`manifest.json` 的 Config/layers 与 OCI graph byte-exact 对应；只有该 graph 已验证的 top-level
descriptor digest 或 Config digest能作为 direct manifest `image_id`，任意其它 digest仍 fail closed。

Issue #296 对 v2 增加跨 store 身份校验：两种 transport 均先验证完整 archive、inventory、
checksum 与唯一 runnable `linux/amd64` OCI graph；从该图得出已经验证的 descriptor/config
身份集合，目标 image inspect 的 `Id` 必须命中这个集合。Registry 的 exact `RepoDigests`、
本地 runtime tag、OS/architecture 校验保持。启动后的 `container.Image` 必须等于重新校验
得到的目标本地 image `Id`，release/service labels 与 health 同时满足；仅 tag 或 RootFS 相同
不构成身份证明。Stage receipt 仍记录原 manifest 的 `image_id`，每次消费继续校验本地内容。
Legacy v1 保持原来的严格 ID 比较；发布过的 release/镜像/校验和不改写。

Tag 由 lower-case source owner/repository、service 和完整 release SHA 确定，只是搬运和本地
解析别名，不是信任根。Producer 必须先按 digest pull/inspect，再创建 tag、重复 inspect exact
image ID/platform，最后按 tag save。Offline consumer 按 runtime tag inspect `RepoTags`、image ID
和 `linux/amd64`，不要求 `RepoDigests`。Registry consumer 则按 digest pull、验证 `RepoDigests`
与 image ID，再创建同一 runtime tag。两条路径均以 `--pull never --no-build` 启动，并在启动后
复核 container `Config.Image`、image ID、release/service labels 与 health。

`architecture.lock.json` 必须是 #23 `schema_version: "1.0"` 的 canonical lock，且
`delivery_contract` 精确为 `docker-release/v1`。Release parser 会验证 lock 的严格字段结构、
canonical `lock_sha256`、source checksums 格式、排序/唯一性，以及 manifest/target profile
中的 `profile_id` 与 `catalog_revision`。Transition resolved component 还必须同时包含绝对
HTTPS migration Issue、exception ID 与未到期 expiry，且 `exception_ids` 集合必须精确匹配；
preferred component 不得携带 transition metadata。Parser 只消费这些治理身份，不复制或
选择 catalog 中的组件版本。多个 transition component 可以引用同一个逐项列明范围的 umbrella
Issue，但仍必须使用不同的 component-scoped exception ID/expiry；Issue 存在或状态变化都不
等于 migration 完成，release identity 仍必须与全部真实 bytes 一致。

这里的 `delivery_contract: docker-release/v1` 是 #23 architecture catalog 已发布的 delivery
family lock，不等于 top-level release manifest 的 parser version。Issue #58 不静默改写既有
architecture lock；`docker-release/v2` 只为同一 delivery family 增加可独立校验的 normalized
Compose artifact。Architecture catalog 若未来迁移该字段，必须走独立 versioned Change。

Manifest、architecture lock、Compose、inventory 和 archive 在任何 pull/load/migration/
container replacement 前完成路径与 checksum 验证。`release.json` 不接受未知字段，也不得
包含 URL credential、token、密码、连接串、证书、SSH key、`.env` 内容或任意 command。

Normalized Compose model 的 environment value 只接受 `${NAME}` 或 `${NAME:?required}` 形式的
纯外部引用。敏感命名的 key 仅在 `services.<service>.environment` 这个精确位置且 value 符合上述
语法时允许；`${NAME:-literal}`、`${NAME:+literal}`、literal Secret/connection URL/token/password
和其它位置的 sensitive field 全部 fail closed。该例外不适用于 manifest、architecture lock、
offline inventory、target profile 或 state。

V2 offline sub-contract 为 `docker-release-offline-bundle/v2`，inventory 为
`docker-release-offline-inventory/v2`。Archive 必须恢复 manifest 中逐 service 唯一的 transport
tag，`manifest.json` 的 `RepoTags`、config image ID、layer member 与可选 OCI/repositories
references 都在 load 前进入 allowlist 检查。既有未声明四类 identity 的 Registry manifest
继续按 digest 路径读取；legacy offline bundle 在任何 Docker call 前稳定拒绝，迁移方式只能是
由受控 producer 重新 pull/build、tag、save 并发布完整 V2 bundle，不能原地编辑 tar/inventory。

Docker 29 OCI `index.json` reference binding 接受两种 exact 表达：完整
`org.opencontainers.image.ref.name`，或由同一 descriptor 的
`io.containerd.image.name=<full transport reference>` 与
`org.opencontainers.image.ref.name=<exact release tag>` 共同表达。Tag-only annotation 不能用于
推断 repository；两字段不一致、其它 repository/tag、重复 descriptor、悬空 blob 或 content digest
不匹配都在 load 前拒绝。Containerd attestation child 还必须声明
`vnd.docker.reference.type=attestation-manifest` 并精确指向唯一 runnable manifest。

Docker 29 classic save 可能额外写入 legacy layer metadata。它们只有在 content-addressed filename、
strict Linux metadata、完整无环 parent graph、leaf/config 数量和每个 image layer chain 长度都与
Docker manifest 一致时才进入 allowlist；不存在“允许任意额外 blob”的 fallback。

## Docker capability gate

Capability gate 属于 **target readiness**，不是 producer artifact conformance。Engine、Compose
binary 或 image store 不受支持时，`verify-target` fail closed，但同一 v2 artifact 仍可先由
`verify-artifact` 独立得出 conformance 结果。

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
`docs/changes/27/03-verification.md`）固定为 `supported`。该 Engine29/Compose2.x classic 组合继续
`rejected + evidence:null`；不能依据 fake adapter、源码阅读或偶然 `RepoDigests` 标记 PASS。
Issue #65 又在两个task-owned disposable Engine `29.7.1`、Compose `5.1.4`、containerd `2.2.6`
daemon 上完成public `docker-release/v2` lifecycle、Registry/offline transport、disposable PostgreSQL
migration、negative boundaries与exact cleanup；因此只增加Engine `>=29.7.1,<29.7.2`、Compose
`>=5.1.4,<5.1.5`、linux/amd64/containerd row，evidence为
`issue-65-compose-5.1.4-97445947fff7`（2026-08-09，来源
`docs/changes/65/verification-compose-514-lifecycle-260808.md`）。这不表示Compose其它5.x、classic、
其它Engine/OS/architecture或业务部署受支持。

Issue #296 已在两个独立任务 VM 上完成 Docker29.7.1/Compose5.1.4/containerd →
Docker28.1.1/Compose2.35.1/classic 的完整真实 Registry/offline 生命周期、重复执行、
synthetic PostgreSQL 迁移计数、A→B→A 回滚、故意健康失败恢复及精确清理。
因此 matrix `2026.09.1` 仅新增 Engine `>=28.1.1,<28.1.2`、Compose `>=2.35.1,<2.35.2`、
linux/amd64/classic 的 supported 行，evidence 为 `issue-296-docker28-classic-843672a6a6a4`。
旧三行保持，Engine29 classic 仍拒绝；这不是公司现场部署证明。真实执行源码843672a，
64阶段回执与独立清理证明见 `docs/changes/296-docker28-classic/evidence/amendment/`。
新入口 `codex/tests/integration/test-docker28-classic-e2e.sh` 默认 NOT RUN；它要求两个
由本任务 provision 入口创建并验证所有权的专属 VM，不能用于公司主机或共享 Docker。

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
`architecture_project_id` 是 v1 可选字段，因此旧 target profile 不声明时仍兼容；一旦声明，
lock `project_id` 必须精确匹配。NewEmaint current adoption 必须声明 `newemaint`，不能用
`newemaint-target-candidate` target lock 替换。Project/profile/catalog、release checksum、lock
self-hash 或 exception expiry 任一不匹配，都会在 Docker config/pull/load/migration/up 前拒绝。

Current lock 表达实际 release bytes；target candidate 只表达期望架构。Transition 不授权依赖、
schema、image 或 database migration，也不能绕过 `prohibited`/EOL/digest/expiry/checksum。

目标合同（#290）：`scm-ci` 的受保护 target profile 明确为 `environment=test` 时，允许
`stage`、`migrate`、`activate`、`deploy`、`status` 和 `rollback`；`environment=production`
仍拒绝这些动作。普通 verify/verify-target 和 appserver-test/appserver-prod 既有行为不变。
不新增角色、不伪造主机身份；未知环境/动作不得进入测试例外。
测试应用采用独立 Compose project、数据库、目录与端口，不能覆盖现有SCM资源。
此规则不替代profile保护、制品/兼容性、阶段grant与现场授权；数据库迁移恢复授权仍独立。
`verify-artifact` 不读取 target profile 或 host facts，不授权或执行 #21 的 live cleanup。

实施状态：#290 经独立合同步骤与 fresh run 完成 runtime、方案 B 检查器和本地 fake-adapter
验证：124 项 release tests、包含 890 项 Python 测试的完整 smoke 通过。唯一 manual PR #291
已开放，最终 CI 以其 exact head 回读为准。方案 B 在固定历史本地快照运行原 fake harness，
并在当前 checkout 校验精确源码范围与行为；旧 #65 evidence、真实 harness 和 matrix 原字节
保持。current real Docker、installed/company live 均为 NOT RUN，不能据 source/local 结果
假定现场已放行。详细证据见
[`#290 verification`](../docs/changes/290-scm-test-deploy/verification-scm-test-deploy-260911.md)。

## Stable CLI

```bash
aisoft-docker-release verify-artifact --release-root /opt/aisoft-releases/app --release-id <merge-sha>
aisoft-docker-release verify-target   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release stage           --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release migrate         --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release activate        --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release verify   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release deploy   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release status   --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <merge-sha>
aisoft-docker-release rollback --profile /etc/aisoft-docker-release/targets/app-test.json --release-id <previous-merge-sha>
```

除 artifact-only 入口只接受 absolute release root 外，其余 CLI 只接受受保护 profile 和完整
release ID；所有后续路径由 profile/manifest 派生，不接受 shell、remote command、migration
command 或 Compose override。Docker subprocess 不使用 shell，失败输出不会回显可能含 Secret
的 stdout/stderr。

职责与权限顺序固定为：artifact-only manifest/lock/model/archive validation → read-only target
readiness → image staging receipt → migration receipt → activation/health → status/rollback。`stage`
不读取 env file 且不运行 migration/up；`migrate` 不 stage/up；`activate` 不 stage/migrate。
`deploy` 作为 backward-compatible orchestration 保留，内部沿用同一阶段原语。Wrong store、legacy
offline 或 pre-load tamper 的 Docker mutation count 必须为 0；post-start identity mismatch 只做
previous-container rollback，不自动恢复数据库。

## State and rollback

每个 target 使用单一进程锁和 mode `0600` 的原子 `docker-release-state/v2` JSON state。v2 记录
每个 staged full SHA 的 transport、逐 service exact image ID、migration receipt、current/previous
release 和 last result。合法 v1 state 以 deterministic migration 读入，下一次成功 mutation 写为
v2；因为 v1 没有 staging evidence，不能伪造 receipt，必须重新执行显式 `stage`。

当前 release 已精确 healthy
时，同 SHA deploy 是 no-op。Migration service 名称来自已验证 manifest/Compose，identity 在
运行前写入 `started`，成功后写入 `completed`；`failed` 或中断后的不确定 migration 不会自动
重跑。`compose up --wait` 或 exact-release health 失败时回切旧容器，但不会执行 PostgreSQL
restore。显式 rollback 同样不运行 migration；数据库恢复始终需要独立人工审批。

## Fixed action permission gate

`aisoft-docker-release-gate <action> <target_id> <full-sha>` 只接受
`verify-target/stage/migrate/activate/status/rollback`。每个 root-owned grant 位于固定
`/etc/aisoft-docker-release/action-grants/<action>/<target_id>.json`，只映射一个 action、一个
target、一个受保护 profile 与一个 audit log；调用方不能传 profile、CLI path、Docker argv 或
shell。Gate 使用固定 argv、sanitized environment 和 `shell=false` 执行，并追加 started/completed
JSONL audit record。要授权另一个阶段必须创建另一份 grant；模板
[`templates/action-grant.example.json`](templates/action-grant.example.json) 不包含 Secret。

## Install boundary

`install.sh` 只复制 runtime、schema、CLI、fixed action gate 和非 Secret 示例。它不创建 live
target profile/action grant、Secret、
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
