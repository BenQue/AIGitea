---
issue: 23
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/23
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 建立跨项目 machine-readable 技术架构目录、版本生命周期、例外和 fail-closed CI 合同
risk_flags:
  - security
  - shared-core
  - ci-change
  - external-contract
  - compatibility
  - migration
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
branch: change/23
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

## 问题/需求总结

正式项目和服务器缺少统一的 architecture profile、精确版本目录、EOL 证据、更新节奏与
例外到期机制，导致 Node/.NET/Prisma/EF Core/PostgreSQL/SQLite/Docker/OS 等由项目临时
选择。平台需要一个版本化、可离线验证、可生成 lock、能在 CI fail closed 的事实源。

## 影响范围

- 新增三类标准 profile 和 machine-readable component catalog。
- 项目提交 architecture declaration，CI 生成并校验 deterministic lock。
- 建立 preferred/supported/sunset/prohibited、版本 pin、review/EOL、例外与迁移 Issue 合同。
- 盘点正式项目/服务器并对 NewEmaint 生成 read-only gap/migration plan；不实施升级。
- 为 #22 提供 profile/catalog/lock identity；#23 不实现 OCI deploy runtime。

## 初步方案与建议

采用 JSON 作为 v1 canonical format，而不是 Issue 中的 YAML 示例：当前 runtime 为离线、
stdlib-first，仓库没有受治理的 YAML parser；JSON 可直接使用 stdlib、精确 canonicalize、
hash 和 JSON Schema，避免不同 YAML parser 的隐式类型差异。对人展示可由报告层生成，但 CI
只消费 canonical JSON。

Catalog 和 profiles 保存 component constraints 与官方 lifecycle 证据；项目声明只选择
profile 和例外，生成的 `architecture.lock.json` 固化解析结果与 checksums。版本升级不会由
validator 自动执行，仍需独立 Issue/PR/测试/部署 Gate。

## 风险

- 把“当前最新”写死而不记录官方支持期和 review date 会快速陈旧。
- 自动修改 lock/package/image/数据库会越过人工合并与迁移 Gate，本 Change 只 validate。
- 宽松 YAML、semver range 或 mutable OCI tag 会造成不同环境解析不一致。
- 全项目 inventory 可能触及凭据或业务数据；只读取版本/配置 metadata，不读取 Secret。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 建立跨项目 machine-readable 技术架构目录、版本生命周期、例外和 fail-closed CI 合同
risk_flags:
  - security
  - shared-core
  - ci-change
  - external-contract
  - compatibility
  - migration
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

- 新增跨项目共享治理、CI gate、外部 lifecycle 事实和兼容矩阵。
- 决策将约束 OS/runtime/framework/ORM/database/container tooling 与未来升级。
- 实际项目迁移具有独立 schema/deployment/rollback 风险，必须保持分离。

### 缺失的 acceptance criteria 或决策

- 无。具体 preferred/supported 数值由计划中的官方证据和兼容测试确定，不改变合同结构。
