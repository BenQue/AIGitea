---
issue: 58
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/58
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
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 22
  - 27
  - 37
  - 40
status: approved
branch: change/58
pr_url: null
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与原因

现有 `verify` 同时读取 producer release artifact、target profile/hostname、Docker Engine、Compose
binary 和 target-side Compose render。结果是 producer artifact 的 conformance 结论会被 target
Docker/Compose compatibility 阻塞，并且 `deploy` 把 transport、migration、activation 合并为一个
mutation surface，无法按最小权限逐阶段授权、审计和恢复。

本 Change 建立七个有序责任域：artifact verification、target readiness、image staging、database
migration、application activation/health、status、rollback。任何阶段只拥有完成该阶段所需的最小
输入与 mutation 权限；后续阶段通过 versioned state receipt 消费前序阶段结果。

## Acceptance criteria

- [x] **AC-1 Artifact verification**：只接受 `release_root` 与 full release SHA；验证 release manifest、
  architecture lock、Compose artifact contract、offline inventory/archive/checksum 与 migration identity。
  不读取 target profile/hostname/Secret，不调用 Docker Engine 或 Compose binary；fake adapter 的
  Docker call count 必须为 0。
- [x] **AC-2 Target readiness**：只做 target profile/host-role/capability、Engine/image-store、Compose
  version 与 target-side Compose render 的 read-only 验证；不 pull/load/tag，不执行 migration/up/down。
- [x] **AC-3 Image staging**：只完成 Registry pull+inspect+exact tag 或 offline preflight+load+inspect，
  写入 exact release/image identity staging receipt；不要求 database Secret，不执行 migration 或
  application activation。
- [x] **AC-4 Database migration**：必须消费 completed staging receipt 和 exact local image identity；只
  运行 allowlisted migration service/command，并沿用 uncertain migration fail-closed 规则；不 stage，
  不执行 application activation。
- [x] **AC-5 Activation/health**：必须消费 completed staging receipt，并在需要 migration 时消费同一
  identity 的 completed migration receipt；只执行 Compose activation、health/container identity 与
  state promotion；不得隐式 transport 或 migration。
- [x] **AC-6 Stable CLI/contract/version compatibility**：新增稳定命令
  `verify-artifact/verify-target/stage/migrate/activate`；既有 `verify/deploy/status/rollback` 参数和
  legacy 语义继续可用。新 artifact contract 与 state contract 必须显式 versioned，并提供 legacy
  migration guidance；禁止在旧版本名下静默改变语义。
- [x] **AC-7 Status/rollback**：status 保持 read-only。新分阶段 contract 的 rollback 只消费已记录、
  已在本地验证的 previous release，不隐式 transport 或 database restore/migration；legacy rollback
  的旧行为保持兼容。rollback failure 保持 failed result，不伪造成功。
- [x] **AC-8 最小权限 gate/template**：固定 `action + target_id + full SHA`，由 root-owned action grant
  解析为固定 profile 与固定 CLI argv；拒绝任意 shell、任意 Docker、任意 profile path 和短 SHA，
  每次 action 独立授权并写审计记录，不读取或打印 Secret。
- [x] **AC-9 State/rollback**：state schema 记录 staged releases、exact image IDs、migration receipt、
  current/previous release 与 last result；v1 state 以显式 deterministic migration 读入 v2，未知版本、
  不完整 receipt 或 identity drift 全部 fail closed。
- [x] **AC-10 Compatibility matrix**：producer artifact conformance 与 consumer target support 分开说明。
  不修改现有 supported row 来接受 Compose 5.1.4；只有同等级 disposable real Engine 29/containerd
  consumer E2E 与 versioned committed evidence PASS 后才能提升。
- [x] **AC-11 Negative call-count**：覆盖 artifact、readiness、stage、migrate、activate 各阶段的 positive
  和关键 negative path，明确断言 forbidden Docker/transport/migration/application mutation count=0。
- [ ] **AC-12 Real E2E gate**：真实 build/save/transfer/load/Compose/health/rollback 只在用户对指定
  disposable daemon/VM 精确授权后运行；否则分别记录 `NOT RUN / BLOCKED`，不得从 fake tests 或
  静态 contract 推断真实 consumer support。
- [x] **AC-13 Documentation and verification**：同步 CLI、contract、权限、state、migration、部署阶段、
  rollback 与 adopter guidance；focused runtime、fake integration、installer twice、shell syntax、
  ShellCheck（可用时）、full smoke 和 `git diff --check` 如实记录，final-head CI 与 deployment 分离。

## 接口、数据与兼容性影响

新增 `docker-release/v2` release manifest，在 v1 字段基础上增加 architecture `project_id` 与
producer-emitted normalized Compose model 的 path/checksum。`verify-artifact` 只接受 v2，因为 v1 没有可脱离 target Compose binary 独立
验证的 normalized model。v1 manifest 仍由 legacy commands 读取；不会原地升级或推测缺失字段。

新增 `docker-release-state/v2`，在 v1 上增加 `staged_releases` receipts。读取合法 v1 state 时进行
deterministic in-memory migration并在下一次成功 mutation 后写出 v2；未知或 malformed state 拒绝。

`deploy` 是保留的 compatibility orchestration；对 v2 release 依次调用同一内部 stage、migrate、
activate 原语，对 v1 release 保留既有整体语义。新 action 可以通过最小权限 gate 独立授权。

## 安全、失败与回滚约束

- Artifact verification 的任何失败发生在 Docker/Compose/Secret/target facts 访问之前。
- Readiness 只能调用 capability/inspect/config 类 read-only adapter method。
- 每个 mutation phase 在执行前验证完整 release SHA、target identity、receipt 与 exact local image IDs。
- gate 不解释 shell，不接受调用方传入 profile/CLI path，grant 文件必须位于固定 root-owned path。
- 平台代码回滚使用 revert PR；已发布 artifact 不原地改写，只能重新生成新的 full-SHA release。
- Runtime rollback 不自动运行 PostgreSQL restore；database backup/restore 始终是独立人工授权。

## 非目标

- 不修改 NewEmaint 或其他应用仓库，不复制业务 artifact、target-candidate lock 或 Secret。
- 不操作 DockerLab/AppServer/production，不创建/restart VM/daemon，不切 image store，不 prune。
- 不运行真实业务 PostgreSQL migration/restore，不部署，不做 browser acceptance。
- 不修改 Gitea 权限、required CI、protected main 或自动 merge PR。
- 不增加 Compose 5.1.4 supported matrix row，不用放宽解析或版本比较绕过 readiness failure。

## 未决问题

没有会改变本地实现方向的合同问题。真实 disposable Docker E2E 需要后续精确授权；未获授权时
对应 AC-12 与 Compose 5.1.4 consumer evidence 保持 `NOT RUN / BLOCKED`。
