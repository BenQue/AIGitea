---
issue: 154
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/154
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: architecture catalog 与共享 profile 是平台事实源，新增组件条目并抬升 profile 版本改变项目声明合同
risk_flags:
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-catalog-fastify-kysely-260905.md
  spec: spec-catalog-fastify-kysely-260905.md
  plan: plan-catalog-fastify-kysely-260905.md
  verification: verification-catalog-fastify-kysely-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/154-catalog-fastify-kysely
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/247
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`architecture/catalog.json` 的 29 个组件里没有任何 `framework.fastify.` 或 `orm.kysely.` 条目，
因此 Fastify + Kysely 的 systemd 原生 Node 服务无法把这两个组件写进架构声明，它们的大版本跳跃
也不会在 architecture lock 里表现为 drift。

Issue 正文里的另外两项已经由其它变更解决，本次不处理：新 profile
`linux-node-systemd-postgres-v1` 已由 #150 交付；TypeScript sunset 已由 catalog
`toolchain.typescript.6` 与应用仓自己的升级解决。范围以 2026-09-05 平台裁定评论为准。

## 影响范围

- `architecture/catalog.json`：新增两个 preferred 组件条目，catalog revision 递增。
- `architecture/profiles/linux-node-systemd-postgres-v1.json`：1.0.0 升到 1.1.0，
  `required_components` 增加两个 slot，并改写声明「本 profile 没有 ORM/framework slot」的
  那条 `compatibility_rules`。
- catalog revision 递增引发的既有级联：四个 profile 的 `catalog_revision`、
  `architecture/fixtures/` 与 `architecture/templates/` 里的 `catalog_revision`、
  三份 `architecture/reference/` 声明与重新生成的 lock、
  `architecture/evidence/official-sources.md` 的新增证据段，以及测试与 smoke 里钉住的
  `--today` 与 `CATALOG_REVISION` 常量。这一级联由 `af575d9`、`6ca5acb`、`b2d3ddf`
  三次历史 revision bump 确立，不是本次新增的范围。
- 平台外：LocalWMS 的 `.aisoft/architecture.json` 现在钉 profile 1.0.0 与 catalog
  `2026.08.3`，本变更合并后它必须在自己的 Issue 里重新声明；本变更不代写。

## 初步方案与建议

按上游事实钉 preferred 版本，不从项目现状或目录名反推：Fastify 取官方 npm Registry 的
稳定 `latest` 5.12.3，Kysely 取 0.29.5。两者都只建 preferred 条目，不建 supported 或
sunset transition——Fastify v4 的官方 End of LTS 是 2025-06-30，已经过期，无法作为合法
transition；Kysely 是 0.x 且上游没有支持窗口表，凭空造一个 transition 会把平台没有的
承诺写进 catalog。

## 风险

- profile 版本从 1.0.0 抬到 1.1.0 会让所有钉 1.0.0 的既有声明报 `PROJECT_PROFILE_MISMATCH`。
  这是共享 profile 变更的固有代价，处置方式是目标仓各自开 Issue 重新声明。
- catalog revision 递增会让三份 reference lock 的 `catalog_sha256` 失效，必须用 CLI 重新
  生成而不是手改。
- `architecture/install.sh` 有 staleness 闸门（#171），合并后需要重装，属显式交接项。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: architecture catalog 与共享 profile 是平台事实源，新增组件条目并抬升 profile 版本改变项目声明合同
risk_flags:
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属强制 complex 类型；`risk_flags` 里的 `external-contract`
  与 `shared-core` 同为强制 complex 风险。
- `contract_effect: add`：catalog 新增组件、profile 新增必需 slot，都是对外部声明合同的
  增量，不是恢复或保持既有合同。
- `required_docs` 追加 `verification`：本次的核心验收是「用 LocalWMS 形状的候选声明实际
  跑通一次 validate」，候选声明是一次性工件、不进仓，required CI 无法重放这条证据。
  另有一条合并后重装 `architecture/install.sh` 的交接项同样只能记录在验证记录里。

### 缺失的 acceptance criteria 或决策

- 无。2026-09-05 的平台裁定评论已确定 profile 携带 framework/ORM slot，并划定实施边界。
