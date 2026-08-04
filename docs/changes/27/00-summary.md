---
issue: 27
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/27
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 docker-release offline transport 对 RepoDigests 的错误依赖，并以内容身份和真实 image-store E2E 建立可移植门禁
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
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on: []
status: spec-drafting
branch: change/27
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

## 问题/需求总结

Issue #22 的 offline transport 在 `docker image load` 后继续按 registry
`name@sha256:...` inspect，并要求 `RepoDigests` 包含该引用。Docker 官方 contract 只承诺
`save/load` 保存 images 与 tags；Moby classic/containerd exporter 对 canonical digest
reference 的处理也不能保证目标 daemon 恢复 registry digest name。首个消费项目因此可能在
archive checksum 完整时仍得到 dangling image，或在 Compose `--pull never` 前失败。

## 影响范围

- 明确定义 registry digest、transport tag、local runtime tag 与 content image ID 四类身份。
- 升级 offline bundle 子合同、release manifest image fields、Compose validation 和 Docker
  adapter/preflight；不改变 release SHA、architecture lock 或 migration state machine 的所有权。
- 增加 Engine/Compose/image-store capability detection 和真实 containerd/classic E2E 证据矩阵。
- 更新 NewEmaint consumer fixture；不修改 NewEmaint 应用代码或运行环境。

## 初步方案与建议

Registry digest 继续是发布来源身份，image config ID 是两种 transport 的共同内容身份。
受控 producer 给每个 service 创建 release-scoped transport/runtime tag，并按 tag 执行
`docker image save`；archive、inventory、manifest 和 Compose checksums 将这个可变别名绑定到
固定 release/image ID。Offline consumer load 后按 runtime tag inspect image ID/platform，不再
依赖 `RepoDigests`。Registry consumer pull digest、验证 RepoDigest/image ID 后创建同一个本地
runtime tag；两条路径最终由 Compose `--pull never` 启动同一 image ID。

Runtime 在 load/migration/container mutation 前只读检测 Engine、Compose 和 image store。
只有 committed compatibility matrix 中有真实 E2E evidence 的组合可执行；classic 未达到同级
证据时明确拒绝，不依据 Engine major 或偶然 RepoDigest 猜测支持。

## 风险

- Local tag 本身是 mutable，不能成为信任根；必须同时由 release SHA、manifest/archive
  checksum、registry digest、image ID 和 post-start container image ID 约束。
- Capability detection 错判会在不支持的 daemon 上执行 load；unknown/ambiguous output 必须
  fail closed，不能把 Engine 29 等同于 containerd store。
- 真实 E2E 需要隔离的 Docker daemons。不得切换、重启或清理现有 daemon；缺少获准的 disposable
  环境时保持 `BLOCKED_EXTERNAL / NOT RUN`。
- Fake adapter 通过不等于真实 `save/load`、Registry、AppServer 或 production 通过。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 docker-release offline transport 对 RepoDigests 的错误依赖，并以内容身份和真实 image-store E2E 建立可移植门禁
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
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改跨项目 release schema、OCI/offline artifact identity、Docker mutation preflight 和
  Compose runtime reference。
- 错误实现可能加载或启动与 release manifest 不同的 image，影响 migration/rollback 安全。
- 验收包含真实 Docker image-store E2E，必须与 fake adapter 证据分开。

### 缺失的 acceptance criteria 或决策

- 无设计未决项。Disposable Docker E2E 环境是显式外部授权 Gate；未授权时不得把相关 AC
  写成 PASS，也不得修改现有 daemon 来绕过。
