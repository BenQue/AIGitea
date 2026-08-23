---
issue: 150
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/150
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - deployment-boundary
  - platform-governance
depends_on: []
status: approved
branch: change/150-systemd-native-profile
pr_url:
created: 2026-08-23
updated: 2026-08-23
---

# Spec：systemd 原生 Node 服务 profile 与 `systemd-native/v1`

## 目标与原因

让「Linux + Node 服务、systemd 直管、无容器、无前端框架、查询层不限定 Prisma」这一形态能够在平台 architecture 合同中被如实声明并 lock，从而解除 LocalWMS 在 project-align checklist 第 6 行的阻塞，同时不放松任何 fail-closed 规则。

`required_components` 不允许省略是刻意设计：它保证 lock 描述的是真实形态。因此缺口的唯一正确解法是新增 profile 与新增枚举取值，而不是给 validator 加逃生口、给项目发 exception，或让项目套用最接近的 profile。

## Acceptance criteria

- [ ] `architecture/profiles/linux-node-systemd-postgres-v1.json` 存在，含 `profile_id`/`version`/`catalog_revision`/`status`，并通过 `architecture/schemas/profile-v1.schema.json` 与 `validate_profile` 的语义校验。
- [ ] profile 的 `required_components` 只覆盖 `os`/`runtime`/`package-manager`/`database`/`toolchain` 五个 slot，不含 container、OCI、proxy、ORM、framework、frontend 任一 category。
- [ ] `delivery_contract` 枚举在 `project-architecture-v1.schema.json` 与 `profile-v1.schema.json` 中同时包含 `systemd-native/v1`，两份 schema 校验通过。
- [ ] 形如 LocalWMS 的候选声明（Ubuntu 24.04 + Node 24 + npm 11 + PostgreSQL 18 + TypeScript，`delivery_contract: systemd-native/v1`）跑 `aisoft-architecture validate` 得 `valid: true`。
- [ ] 同一候选跑 `aisoft-architecture lock` 连续两次输出 byte-identical，且 `validate --lock` 无 drift。
- [ ] 既有三个 profile、`architecture/fixtures/` 全部 valid/invalid fixture、`architecture/reference/` 三份已提交 lock 交叉校验保持通过。
- [ ] runbook §4 与 §9 说明新取值的适用条件与共用/不适用的验收步骤。

## 接口、数据与兼容性影响

- **新增（向后兼容）**：两处枚举各追加一个取值；追加不会使任何既有声明失效。既有 profile 的 `delivery_contracts` 不变，因此既有项目不能因为本变更改用 `systemd-native/v1`。
- **不变**：catalog（不新增 PostgreSQL 17）、`validator.py`/`lockfile.py` 逻辑、lock schema（其 `delivery_contract` 本就是自由 string）、既有三个 profile 的 `version`。
- **下游边界**：`aisoft_release` 要求 release lock 的 `delivery_contract` 等于 docker-release 取值，systemd-native lock 因此进不了 Docker release/transport/offline bundle 路径，无需额外开关。
- **消费者**：`codex/tools/aisoft-project-check.sh` 的 `delivery-profile` 检查读的是目标仓 `AGENTS.md` 的交付形态段落，不校验枚举字面量，故无需改动即可接受 systemd 原生项目。

## 风险与回滚约束

- 回滚 = revert 本 PR。新增文件与两处枚举追加都是纯增量，revert 后既有 profile、fixture、reference lock 全部回到当前状态。
- 一旦有项目提交了引用 `systemd-native/v1` 的 lock，revert 会让该项目的声明失效——因此第一个消费者（LocalWMS）必须在本 PR 合并之后才提交自己的声明。
- 本变更不部署、不改任何目标机、不授予部署能力：profile 名称与 delivery contract 都只表达 delivery ownership（ADR-0003）。

## 非目标

- 不给 catalog 增加 PostgreSQL 17；LocalWMS 侧升级到 18 对齐 preferred。
- 不在本仓库创建 LocalWMS 的 `.aisoft/architecture.json`。
- 不修改 validator/lockfile 语义，不引入任何 bypass flag。
- 不实现 systemd 部署脚本；本变更只定义合同。

## 未决问题

- 无。
