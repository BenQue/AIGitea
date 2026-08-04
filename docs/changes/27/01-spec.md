---
issue: 27
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/27
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/27
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

# Spec

## 目标与原因

为 `docker-release/v1` 提供不依赖目标 daemon 恢复 `RepoDigests` 的 offline image transport。
Registry 与 offline bundle 继续共享同一 release、Compose、architecture 和 image content
identity；离线目标机不访问 Registry/公网，不 build、不安装依赖，也不根据 mutable tag 猜测
内容。

Docker 官方文档仅承诺 `docker image save` 归档指定 images/tags、`docker image load` 恢复
images/tags。Docker Engine 29 fresh install 默认 containerd image store，而升级主机继续使用
classic store；因此 capability 必须从 daemon 只读事实检测，不能由版本号推断。

## Acceptance criteria

- [ ] **AC-1** Release schema/runtime 明确定义四类 image identity：registry
  `reference@digest`、archive `transport_reference`、Compose `runtime_reference` 和 content
  `image_id`。Transport/runtime references 必须为 deterministic、release-scoped tag，包含
  source repository、service 和完整 40-char release SHA；tag 仅为搬运别名，信任根仍是
  registry digest、image ID、release/Compose/architecture identity 与 archive checksum。
- [ ] **AC-2** 新 bundle 使用 `docker-release-offline-bundle/v2`。Producer 只能在 digest
  reference 与 transport tag inspect 到相同 `image_id`/`linux/amd64` 后按 tag save；inventory
  与 manifest 对 service、registry digest、transport/runtime tag、image ID、platform 和 archive
  SHA256 一一绑定。V2 首版要求 transport/runtime tag 相等，避免 load 后额外 retag mutation。
- [ ] **AC-3** 既有 `docker-release/v1` Registry manifest 保持可读和按 digest pull；缺少 v2
  identity 的 legacy offline bundle 必须以稳定 diagnostic 在任何 `docker image load` 前
  fail closed。Parser 对 legacy/v2 各自使用 exact field set，不接受混合、unknown 或 silent
  default，migration 文档给出重新 publish 而非原地改写 archive 的路径。
- [ ] **AC-4** Docker adapter 以固定 argv、bounded/redacted output 只读检测 server Engine
  version、Compose version、OS/architecture 和 image store。Containerd 仅在
  `DriverStatus` 明确包含 `driver-type=io.containerd.snapshotter.v1` 时成立；classic 仅在
  approved classic driver 事实明确时成立；版本/store output 缺失、冲突或不在 committed
  compatibility matrix 时，在 load/migration/container mutation 前拒绝。
- [ ] **AC-5** Offline prepare 先重复验证 release/Compose/architecture/inventory/archive
  checksums 与 archive member/reference allowlist，再执行一次 load；load 后按
  `runtime_reference` inspect，并验证 exact `image_id`、`linux/amd64` 和 service mapping，不要求
  `RepoDigests`。Compose 固定 `--pull never` 且禁止 build，启动后 container Config.Image、
  container Image ID、release/service labels 和 health 必须再次精确匹配。
- [ ] **AC-6** Registry prepare 按 registry digest pull，验证 `RepoDigests` 与 image ID 后创建/
  验证同一 release-scoped runtime tag；Registry/offline 两条路径的 Compose bytes、runtime tag、
  image ID、release SHA、architecture lock checksum 与 post-start container identity 完全相同。
  Registry 可用性不是 offline target 的运行前提。
- [ ] **AC-7** 在获准的 disposable fresh Docker Engine 29 containerd image-store 环境完成真实
  `build/pull -> tag -> save -> checksum transfer -> load -> exact inspect -> compose --pull never
  --no-build -> health/container identity` E2E；producer 与 consumer 使用独立 daemon/data root，
  证据记录 exact Engine/Compose/store、archive SHA、registry digest、image ID 和清理结果。
- [ ] **AC-8** 对升级保留的 classic image store，只有同一 fixture 的同等级真实 E2E 通过后
  compatibility matrix 才能标记 supported；否则必须标记 rejected，并由 preflight 在 load 前
  给出可操作错误。禁止依据偶然的 `RepoDigests`、fake adapter、Engine 版本或源码推理宣称
  classic PASS。
- [ ] **AC-9** 篡改 archive/inventory/registry digest/transport tag/runtime tag/image ID/platform/
  service mapping/Compose/architecture/release SHA，重复 tag、缺 tag、wrong store 和 TOCTOU 后的
  container image mismatch 均 fail closed；pre-load failures 的 Docker mutation count 为 0，
  post-load/pre-start failures不得执行 migration/up，post-start mismatch 走既有 previous-release
  rollback 且不自动 restore database。
- [ ] **AC-10** NewEmaint consumer fixture 使用 v2 identity 并通过 updated platform verifier；
  fake schema/adapter/runtime tests、installer repeatability、`bash -n`、ShellCheck、full smoke 和
  `git diff --check` 通过。`03-verification.md` 分开记录 fake、containerd real、classic real/
  reject、ephemeral Registry、NewEmaint、AppServer、migration 与 production；未执行保持
  `NOT RUN`。

## 接口、数据与兼容性影响

### V2 image identity

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

- `reference`/`digest`：Registry source identity；Registry path 必须验证 RepoDigest。
- `image_id`：两种 transport load/pull 后共同的 local content identity。
- `transport_reference`：producer 按 tag save、archive load 恢复的别名。
- `runtime_reference`：Compose `image:` 使用的 release-scoped 本地别名；v2 要求与 transport
  reference 相等。

Top-level release contract 继续为 `docker-release/v1`；`offline_bundle.contract_version` 区分
legacy 与 v2。Legacy Registry path 不受影响，legacy offline path 明确 fail closed 并要求从
受控 producer 重新发布整个 bundle。

### Capability evidence

Versioned compatibility matrix 至少记录：matrix revision、Engine range、Compose range、OS/
architecture、normalized store、status `supported|rejected`、real E2E evidence ID/date 和
remediation。Runtime 只接受 `supported` row。Containerd marker 使用 Docker 官方
`docker info -f '{{ .DriverStatus }}'` 语义；unknown/ambiguous store 不 fallback。

### Mutation ordering

```text
strict files/checksums/archive refs
  -> read-only Engine/Compose/store capability
  -> compose config and local prerequisites
  -> image load or digest pull/tag
  -> exact image inspect
  -> migration (if any)
  -> compose --pull never --no-build
  -> exact container identity and health
```

## 风险与回滚约束

- Runtime tag 可以被具有 Docker 权限的 actor 重写；deploy lock、紧邻的 pre-start inspect 与
  post-start container ID check 缩小窗口，但不把 tag升级为信任根。Docker daemon 权限仍按
  host-role/sudo boundary 管理。
- 不在现有 daemon 上切换 `containerd-snapshotter`、修改 daemon.json、重启 Docker 或 prune
  images。真实测试只使用用户另行授权的 disposable environment。
- E2E ephemeral Registry 只属于 producer/test fixture，offline consumer 网络必须证明无法
  pull；它不会成为目标 AppServer 的隐藏依赖。
- 平台代码和 schema 回滚走 revert PR。已经发布的 legacy offline bundle 不原地修改；重新
  publish v2 bundle。Database rollback 仍是独立人工 Gate。

## 非目标

- 不在平台仓修改 NewEmaint 应用代码、Dockerfile、Compose 或 package/database schema。
- 不部署 AppServer，不运行真实 migration，不创建/读取 production Registry 或 Secret。
- 不支持 Kubernetes/Swarm、跨平台 multi-arch archive 或任意 OCI runtime。
- 不以本地 Registry 作为 offline target 的运行前提。
- 不为获得测试结果而启动、切换、重启或清理现有 Docker daemon/VM。

## 未决问题

无。Classic 是否进入 `supported` 由同等级真实 E2E 证据决定；没有证据时 deterministic 结果
固定为 `rejected`，不会改变 v2 identity 设计。
