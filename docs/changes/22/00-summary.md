---
issue: 22
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/22
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将新 Linux 项目的默认交付目标改为可离线验证的 Docker release contract，并保持 PM2 legacy 兼容
risk_flags:
  - security
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
  - rollback
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on:
  - 23
status: approved
branch: change/22
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

## 问题/需求总结

平台目前只有 PM2/tar.gz 的 Linux as-built，无法把 OCI image、Gitea Container
Registry、完全离线 bundle、digest promotion、migration 和 Compose rollback 固化为跨项目
合同。新 Linux 项目需要在受控 builder 一次构建，测试与生产仅消费同一 immutable digest，
目标机不得现场 build、安装依赖或访问公网。

## 影响范围

- Linux 默认交付方向从“整体去 Docker 化”改为 Docker-first；PM2 保留为 legacy adapter。
- 新增 release manifest/schema、Registry/offline transports 和确定性 deploy runtime。
- 对接 #23 的 architecture profile/catalog lock；本 Issue 不决定 Node/PostgreSQL 等版本。
- 对接 #21 的 host-role 语义；`scm-ci` 可以 build/publish，不能运行业务容器。
- NewEmaint 仅获得消费模板，应用实现与真实部署仍走独立 Change。

## 初步方案与建议

建立深模块 `aisoft_release`，只暴露 `verify`、`deploy`、`status`、`rollback`。Release
bytes 由完整 Gitea merge SHA、image digests、Compose checksum、architecture lock checksum 和
migration identity 唯一确定；环境 profile 只持有目标路径、transport、Compose project、
host role 和外置 Secret 路径。

Registry 与 offline bundle 是同一 manifest 的两个 transport，不是两套部署流程。所有验证
在 migration/容器替换前完成；应用 rollback 不自动执行 PostgreSQL restore。

## 风险

- Docker daemon 是高权限边界；应用容器不得挂载 socket，调用方不能传任意 shell。
- migration 成功后 image rollback 不一定能撤销数据变化，破坏性 migration 必须停止。
- #23 未完成前，版本/profile 合法性没有权威事实源，因此 #22 的 final review 受
  `depends_on: [23]` 阻断。
- 本地 fake Docker 通过不等于 Registry、公司网络、AppServer 或生产验收。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将新 Linux 项目的默认交付目标改为可离线验证的 Docker release contract，并保持 PM2 legacy 兼容
risk_flags:
  - security
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
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

- 修改共享平台默认部署合同、OCI 制品、CI、Secret、migration 和 rollback 边界。
- 同时支持在线 Registry 与完全离线传输，但必须保持一个可验证 release identity。
- 首个消费项目跨仓实施，平台 candidate 不能代替应用和环境验收。

### 缺失的 acceptance criteria 或决策

- 无。版本目录由 #23 提供；真实主机、凭据和维护窗口属于后续环境 Gate。
