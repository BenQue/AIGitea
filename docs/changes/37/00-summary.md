---
issue: 37
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/37
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 Docker 29 containerd 与 classic image store 实际 save archive 的 identity 和 OCI index metadata 兼容缺口
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
status: approved
branch: change/37
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

NewEmaint protected `main@ee4f6a1205a5df1603568e455e158c460b675a89` 在获准的本地
disposable Docker 29.7.1 builder 上生成真实 offline bundle 后，现有
`docker-release/v1` preflight 暴露两个稳定缺口：

- containerd image store 的 `docker image inspect .Id` 可以是 OCI index digest，而 Docker
  archive `manifest.json[].Config` 记录的是 image config digest；现有 validator 错误地要求两者
  byte-identical。
- classic image store 生成的 Docker 29 OCI `index.json` 可以把完整 transport name 写入
  `io.containerd.image.name`，而 `org.opencontainers.image.ref.name` 只保留 tag；现有 validator
  把后者单独当作完整 reference allowlist 输入并拒绝合法 archive。

两个失败都发生在 DockerLab 部署前。DockerLab 仍是 0 images、0 containers、0 volumes、
0 build cache，NewEmaint 未部署；静态修复和 platform E2E 不能替代目标部署、数据库、健康或浏览器验收。

## 影响范围

- 澄清 Registry manifest/index digest、local inspect identity、archive config digest 与 OCI
  descriptor/annotation 的关系。
- 更新 offline archive fail-closed validator、negative fixtures、真实 Engine harness、compatibility
  matrix 和文档。
- 保持 release SHA、Registry digest、runtime/transport tag、Compose、architecture lock、migration
  ordering 和 target state machine 的既有所有权。
- 为 NewEmaint 后续采用新平台 release contract 提供确定性 producer/consumer 规则；本 Change
  不修改 NewEmaint、DockerLab target 或数据库。

## 初步方案与建议

不把 OCI index digest、image manifest digest 和 config digest 合并成一个字段。Manifest 中
`image_id` 继续表示目标 daemon 对 exact runtime reference 的 inspect identity；archive validator
根据真实 archive graph 验证该 identity：classic 可直接等于 Docker manifest Config digest，
containerd 则必须等于 allowlisted OCI top-level descriptor digest，并沿 descriptor → manifest →
config 验证 Docker manifest Config。OCI annotation 只作为 reference binding，完整 name 与 tag-only
表达必须先规范化并互相一致，任何额外 repository/tag/name 继续拒绝。

真实 E2E 的 producer archive matrix 与 consumer deploy capability 分开记录。修复 archive parser
不自动把 classic target row 提升为 `supported`；只有独立 consumer `load`、Compose、identity、health
和 cleanup 达到 #27 同级证据后才能改 matrix。

## 风险

- 宽松接受 OCI annotations 可能让额外 tag/name 混入 archive；必须从 exact
  `transport_reference` 派生唯一允许的 full name 与 tag，并验证 descriptor graph 无歧义。
- 错把 index digest 当作 config digest，或反向只认 config digest，会造成 producer/consumer image
  identity 漂移；positive 与 negative fixtures 必须覆盖两种 store。
- 真实 Docker 测试只能使用另行批准的 disposable 环境；不得 restart VM/service、切换既有 daemon
  store、prune 或触碰 DockerLab target。未获授权的动作保持 `NOT RUN / BLOCKED`。
- Fake/static/archive parser PASS 不是 NewEmaint build、DockerLab deploy、database migration、health、
  browser acceptance 或 rollback PASS。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 Docker 29 containerd 与 classic image store 实际 save archive 的 identity 和 OCI index metadata 兼容缺口
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

- 修改跨项目 Docker release archive validation 和真实 image-store compatibility evidence。
- 错误实现可能把 manifest 外 image/tag 带入目标 daemon，或在 migration/up 前接受错误 identity。
- 本 Change 涉及共享核心、外部制品合同、CI/E2E、部署门禁和回滚边界，强制为 complex。

### 缺失的 acceptance criteria 或决策

- 无设计方向未决项。任何需要 restart/service/store switch 的真实 E2E 都是单独授权 Gate；缺少授权
  时相关行必须保持 `NOT RUN / BLOCKED`，不影响先完成合同、fixtures 和 read-only artifact validation。
