---
issue: 65
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/65
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 22
  - 27
  - 58
status: approved
branch: change/65
pr_url:
created: 2026-08-08
updated: 2026-08-09
---

# Compose 5.1.4 docker-release/v2 lifecycle evidence spec

## Problem Statement

`docker-release/v2` 已把 producer artifact conformance 与 consumer target lifecycle 分开，但当前共享
compatibility matrix 没有 Compose 5.1.4 的同等级真实 consumer evidence。目标组合因此正确地在
`verify-target` fail closed。缺失的是平台自身可审计、可重复、可精确清理的 lifecycle 验证，不是新的
CLI 设计，也不是业务项目部署。

## Solution

增加一个 Issue #65 专用 harness，固定 merged source bytes 和 fixture bytes，在两个用户单独批准的
task-owned disposable Engine 29 containerd daemon 上执行 producer/consumer E2E。Harness 先以
run-scoped candidate matrix 驱动现有 `ReleaseRuntime` public seam；只有完整 lifecycle、negative
paths、PostgreSQL receipt 与 cleanup 全部 PASS 后，才把 production matrix 增加与证据严格相符的
exact row，并提交 immutable evidence。

## User Stories

1. 作为平台维护者，我希望确认 Compose 5.1.4 能执行 merged `docker-release/v2` 全 lifecycle，从而
   只为已验证的 exact 组合开放 target gate。
2. 作为审阅者，我希望 evidence 固定 source SHA、fixture SHA、Engine/Compose/containerd 版本、daemon
   ID/data root 与每个 artifact identity，从而能区分真实证据和环境推断。
3. 作为安全审阅者，我希望 producer 与 consumer 是不同 daemon，并在任何 resource creation 前拒绝
   duplicate daemon identity。
4. 作为 release producer，我希望 Registry digest、release-scoped transport tag、archive/inventory
   checksum 与 image ID 一致，从而证明 offline bundle 来自同一 immutable content。
5. 作为 release consumer，我希望 offline path 在 Registry 不可达时仍按 archive allowlist、image ID、
   runtime tag、`--pull never --no-build` 和 exact container identity 启动并健康。
6. 作为数据库维护者，我希望 migration 只连接 disposable PostgreSQL fixture，并记录 started、completed
   与 same-identity no-op receipt，从而不触碰业务数据库或自动重跑不确定迁移。
7. 作为运维人员，我希望 stage、migrate、activate 的 allowed/forbidden mutations 可从 fixed argv log
   审计，从而确认各 action grant 没有隐式扩大权限。
8. 作为平台维护者，我希望 tamper、wrong store、wrong Compose 和 duplicate daemon identity 在对应
   mutation 前 fail closed，从而不靠失败后的 cleanup 补偿 preflight 缺陷。
9. 作为环境所有者，我希望成功与失败路径只删除 Issue #65 创建的资源，并用 before/after inventory
   证明没有 prune 或删除其它对象。
10. 作为项目消费者，我希望 matrix row 只覆盖 exact tested patch versions，不把 Engine major、Compose 5
    或 containerd family 推断为整体支持。
11. 作为 Gitea 维护者，我希望交付只有一个 `Closes #65` PR，最终 merge 继续由人工执行。

## Acceptance Criteria

- [ ] **AC-1 Source and fixture identity**：从 fresh Gitea
  `main@97445947fff79a4c2db6fa764feb21660e281556` 建立 `change/65`；evidence 固定 source tree、
  `docker-release/` tree、runtime tree、harness/fixture SHA-256、Engine `29.7.1`、Compose `5.1.4`、
  containerd `2.2.6`、linux/amd64 与 containerd store marker。
- [ ] **AC-2 Disposable isolation**：只有 Issue #65 exact authorization marker 才可运行 execute；producer
  与 consumer endpoint、logical target、daemon ID 必须不同，data root 位于不同 task-owned VM/daemon。
  Harness 不创建/restart/switch/prune 任何未列入单独批准的环境。
- [ ] **AC-3 Lifecycle**：同一 offline `docker-release/v2` fixture 依次通过
  `verify-artifact → verify-target → stage → migrate → activate → status → same-SHA activate no-op`；
  每步 JSON result、state v2 receipt 与 fixed argv 被记录。
- [ ] **AC-4 Transport and identity**：producer-side ephemeral Registry 至少覆盖 digest push/pull 与
  release-scoped tag；offline V2 覆盖 archive/inventory checksum、member/reference allowlist、runtime
  tags、distinct image IDs、consumer Registry pull rejection、`--pull never --no-build`、exact container
  labels/image identity 和 health。
- [ ] **AC-5 PostgreSQL fixture**：migration 仅访问本 Issue 创建的 disposable PostgreSQL fixture；首次
  migrate 记录 `started → completed`，相同 identity 第二次为 no-op；不读取 NewEmaint/DockerLab/
  AppServer/production Secret 或 database，不运行 backup/restore/destructive migration。
- [ ] **AC-6 Phase isolation**：stage 不运行 migration/up；migrate 不 pull/load/tag/up；activate 不
  pull/load/tag/migration；status 与 same-SHA no-op 不产生 resource mutation。每步通过 argv log 与
  resource/state readback 共同验证。
- [ ] **AC-7 Negative fail-closed**：artifact tamper 在 Docker call 前拒绝；duplicate daemon identity
  在 resource creation 前拒绝；wrong store/wrong Compose 在 transport/migration/up 前拒绝；phase 前置
  receipt 缺失时下一阶段拒绝。Negative run 的 mutation count 与残留 inventory 必须为 0。
- [ ] **AC-8 Exact cleanup and evidence**：每次 success/failure 都精确处理本 Issue 创建的 Registry、
  PostgreSQL、migration/runtime container、image/tag、network、volume、build 与临时文件；禁止 prune。
  Evidence 保存 before/created/after inventory、exact commands、versions、daemon IDs、release SHA、archive
  SHA、image IDs、state receipts、health、failures 与 cleanup result；未运行项保持 `NOT RUN`。
- [ ] **AC-9 Narrow compatibility promotion**：production matrix 仅在 AC-1–AC-8 real evidence 全 PASS 后
  增加非重叠 row：Engine `>=29.7.1,<29.7.2`、Compose `>=5.1.4,<5.1.5`、linux/amd64、containerd，
  evidence 指向 Issue #65 verification；classic 与 Compose 其它 5.x 继续不支持。
- [ ] **AC-10 Required gates and delivery**：focused release tests、harness fake/static tests、installer
  repeatability、`bash -n`、ShellCheck、full smoke、JSON/Secret/diff checks 全部 PASS；final head 再运行
  required gates，创建唯一 `Closes #65` PR 并停在人工 merge。Remote status context 未配置时如实记录
  `NOT CONFIGURED / NOT RUN`。

## Implementation Decisions

- 复用现有 `ReleaseRuntime` 与 `DockerAdapter(compatibility_path=...)` public seam；不修改 Issue #58 已
  合并的 CLI/lifecycle contract，也不为了测试增加 live target override。
- `verify-artifact` 不接触 target；其余 lifecycle 只指向 consumer daemon。Producer 只负责构建 fixture、
  ephemeral Registry、digest/tag 与 V2 offline archive/inventory。
- Run-scoped candidate matrix 由 harness 在临时目录生成，包含 production matrix 原有 rows 和 AC-9 exact
  row；失败时随 run 删除，不能安装或提交为 production support。它的 exact bytes/SHA 写入 evidence。
- Harness 提供 `--not-run`、`--duplicate-daemon-negative`、`--preflight`、`--execute`；默认永远不调用
  Docker。Preflight 只读回 versions/store/daemon identity/data root/initial inventory，并输出绑定 endpoints、
  prerequisite digests/IDs、candidate matrix bytes、architecture lock、Docker/timeout binaries、exact resources、
  baseline inventory 与 evidence path 的 canonical approval plan SHA-256；execute 必须逐字匹配该 SHA。
- Docker fixed-argv wrapper 只记录 sanitized argv 和 phase boundary，不记录 env-file 内容、Secret、
  Docker stderr 或 credential；真实 subprocess 继续 `shell=false`。Direct Docker calls 使用30秒边界，
  lifecycle wrapper 使用120秒边界，二者均在5秒 grace后KILL；timeout binary本身也绑定approval plan。
- PostgreSQL fixture 使用独立、digest-pinned/preloaded server image和 disposable network/volume；migration
  service 使用不同 image ID 的 release image，通过 external database network 运行，且 migration SQL
  只创建 fixture-owned schema/table/marker。后台migration在任何Docker call前建立 `pid == pgid` 握手；
  timeout/interrupt必须先有界终止整个process group，再允许exact cleanup。
- Evidence 使用 strict JSON exact-key schema或 deterministic validator，并以 mode `0444` 写入新路径；
  PASS/failure evidence 采用同目录hard-link no-clobber发布。失败 run 不写 PASS evidence，保留脱敏failure/
  cleanup；若process group无法确认静止，保留execution lock并禁止并发cleanup/execute。

## Testing Decisions

- **最高 seam 1 — public lifecycle**：通过 `ReleaseRuntime` 的公开 phase methods 检查返回结果、state receipt、
  container identity 与 health，不测试 private helper。
- **最高 seam 2 — real Docker endpoints**：真实 producer/consumer CLI 验证 daemon identity、Registry/offline
  bytes、Compose 5.1.4 和 cleanup inventory；fake harness 只验证授权、argv、解析和 fail-closed 编排。
- **最高 seam 3 — production policy**：`require_supported()` 对 old row、exact new row、5.1.3/5.1.5、classic、
  overlap/evidence 缺失做正反测试；production row 只在 real evidence 后进入 fixture expectation。
- TDD 以一条 harness safety behavior 为一个 red→green tracer bullet；full smoke 只在 focused gate 通过后跑。

## Interface, Data and Compatibility

- 不新增或修改 `docker-release/v2`、state v2、target profile 或 command gate schema。
- 新增 test-only authorization/evidence inputs必须使用 `AISOFT_65_E2E_*` namespace；不得复用 Issue #27 marker。
- Evidence 不含 token、password、env-file value、Docker auth、raw stderr 或数据库连接串。
- Existing Compose 2 containerd row 与 classic rejected row保持不变；新 row与 Compose 2 范围非重叠。
- 如果 Compose 5.1.4 normalized model 与 producer model不一致，先报告独立合同缺陷；不得在本 Issue
  放宽 Compose security validator 或 lifecycle ordering。

## Risks and Rollback

- Platform code/docs 通过人工 revert 最终 PR 回滚；回滚 matrix 时必须同时删除 #65 exact row，不能保留
  无 source evidence 的 supported entry。
- Disposable environment cleanup 只使用 exact object identifiers；cleanup 失败则停止、报告残留并等待新的
  精确授权，不能 prune 或扩展删除范围。
- Migration failure保留 `started/failed` evidence且不自动重跑；数据库 restore始终 `NOT RUN`。

## Out of Scope

- NewEmaint 或其它业务仓库、DockerLab、AppServer、production、公司服务器。
- Gitea 权限/分支保护修改、自动 merge、live service安装/启用、OrbStack/VM/Docker restart、image-store
  switch 或 prune。
- 业务 Secret、业务数据库、migration、backup/restore 与 destructive data operation。
- Compose 5 family、Engine 29 family或 classic store 的宽泛支持结论。

## Further Notes

Gitea 当前未配置 required status context，因此 final PR 的 remote CI 只能记录 `NOT CONFIGURED`；这不会
降低 repository required local gates，也不能被描述为 remote CI PASS。

## 未决问题

无产品或合同未决问题。真实 disposable VM/daemon 与 PostgreSQL fixture 的创建/启动/mutation 必须在
T01 完成、exact命令和资源名确定后取得用户单独批准；未批准只会使 T02 保持 `BLOCKED / NOT RUN`，
不会授权跳过 AC 或晋级 matrix。
