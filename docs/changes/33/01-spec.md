---
issue: 33
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/33
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
depends_on: []
status: approved
branch: change/33
pr_url:
created: 2026-08-06
updated: 2026-08-06
---

# Spec

## 目标与原因

将平台 Next.js 安全基线提升到 `16.3.0`，将 Prisma CLI、Client 与 PostgreSQL adapter 同步提升
到 `7.9.1`，同时保留 React/ReactDOM `19.2.8`。通过离线、可复现的 npm stable-release
snapshot 使 catalog fail closed，避免下游被要求消费已进入安全公告影响范围或内部不一致的包。

## Acceptance criteria

- [ ] **AC-1** `framework.next.16` 精确固定 `next@16.3.0`，记录 stable channel、精确 Registry
  URL、integrity 与 `2026-08-03` 发布日期；证据记录 Node `>=20.9.0` 和 React/ReactDOM
  `^19.0.0` peer compatibility。
- [ ] **AC-2** `orm.prisma.7` 精确固定 `prisma`、`@prisma/client`、`@prisma/adapter-pg`
  `7.9.1`，三个 packages 的 snapshot 版本完全一致，并记录各自 Registry URL、integrity 与
  `2026-07-27` 发布日期。
- [ ] **AC-3** React/ReactDOM 保持 `19.2.8`；Linux profile 同时表达 Next.js 16.3、React 19.2.8、
  Prisma 7.9.1 与 Node 24 compatibility，且不引入 Canary、Experimental、`latest` 或范围。
- [ ] **AC-4** Validator/tests 拒绝旧 Next.js/Prisma catalog 版本、缺失或多余 package、Prisma
  三包版本不一致、package/channel 使用可变 dist-tag、semver range、Canary/预发布、非精确
  Registry URL、future metadata 与过期 project/lock。
- [ ] **AC-5** Catalog、全部 profiles、templates/fixtures、NewEmaint target declaration 与所有
  committed reference locks 的 revision/version/source checksums 一致；locks 由 canonical CLI
  重建且重复生成 byte-identical。
- [ ] **AC-6** 在 disposable temp workspace 中安装四个 exact packages，并在最小 Prisma 7
  PostgreSQL schema/config 上完成 `prisma validate` 与 `prisma generate`；现有 architecture、
  Linux/Windows/SQLite、Docker release、offline 与 full smoke tests 继续通过。
- [ ] **AC-7** 文档明确 NewEmaint #52 的迁移顺序和边界：只能在本 PR 人工合并后消费受保护
  `main` 的精确 SHA，同时更新 Next.js/Prisma packages 与 application lockfile，再独立执行
  audit/build/browser；合并前该 SHA 为 `BLOCKED_EXTERNAL`，不得以 branch head 伪装 merge commit。

## 接口、数据与兼容性影响

Catalog V1 的现有可选 `package_release` 字段继续保持 schema-compatible，但 semantic validator
从 React 单一特例扩展为三个受治理 component 的 package-set contract：

- `framework.next.16`：只能包含 `next`；
- `frontend.react.19`：只能包含 `react`、`react-dom`；
- `orm.prisma.7`：只能包含 `prisma`、`@prisma/client`、`@prisma/adapter-pg`。

每个 package version 必须与 component exact version 相同。Scoped package Registry URL 使用
percent-encoded package name，lock 仍只固化 component identity 与 source checksum，不复制 npm
metadata。无 schema、数据库、API 或部署格式迁移。

## 风险与回滚约束

Validator 扩展可能使旧 catalog/lock 立即失败，这是预期的 fail-closed 行为；所有仓库内标准
reference 必须同 PR 更新。回滚只能通过 revert 本最终 PR 回到先前 catalog revision，不能在
新 revision 下恢复 `16.2.11`/`7.8.0` 或放宽 validator。不得运行 `prisma db push`、migration、
数据库连接、Docker/server/Secret 操作或自动合并。

## 非目标

- 不修改 NewEmaint package.json/package-lock、schema、source、Dockerfile、服务器或数据库。
- 不处理 NewEmaint 的 `sharp`、`xlsx` 或其它 application-owned security findings。
- 不引入联网 validator、自动 dependency updater、可变 dist-tag、Canary/Experimental 或范围。
- 不声称 NewEmaint #52 已解除安全 Gate、完成 browser/Docker/deployment/migration 或生成 current lock。

## 未决问题

无。最终 merge SHA 由人工合并事件产生，是验收外部门禁而非实现决策。
