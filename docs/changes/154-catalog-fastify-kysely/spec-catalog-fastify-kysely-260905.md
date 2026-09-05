---
issue: 154
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/154
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - shared-core
depends_on: []
status: contract-drafting
branch: change/154-catalog-fastify-kysely
created: 2026-09-05
updated: 2026-09-05
---

# Spec: catalog 补 Fastify 与 Kysely，systemd 原生 profile 升到 1.1.0

## 目标与原因

让 architecture 声明能覆盖 Fastify 与 Kysely。今天两者都不在 catalog 里，systemd 原生
profile 也没有对应 slot，结果是这两个组件的大版本跳跃不会在 architecture lock 里表现为
drift——等于平台对它们没有治理。只补 catalog 而不给 profile 加 slot 无法解决问题，声明侧
仍然拿不到它们；2026-09-05 的平台裁定据此要求两件事一起做。

## 上游事实与版本裁定

版本只取上游事实，不从目录名或任何项目的现状反推（onboarding runbook §9）。
2026-09-05 从官方 npm Registry 与官方文档读回：

| 组件 | 裁定版本 | 上游依据 | 支持窗口 |
|---|---|---|---|
| Fastify | 5.12.3 | npm Registry `dist-tags.latest` 为 5.12.3，发布日 2026-09-04 | 官方 LTS 表：v5.0.0 发布于 2024-09-17，End of LTS 为 TBD；主版本自发布起至少 6 个月支持，并在下一个主版本发布后再获 6 个月安全更新 |
| Kysely | 0.29.5 | npm Registry `dist-tags.latest` 为 0.29.5，发布日 2026-08-10，`engines.node` 为 `>=22.0.0` | 上游未发布固定支持窗口表，因此 `support_end`、`eol`、`migrate_by` 一律为 null，表示未知而非无限支持 |

两条都只建 preferred 条目，不建 transition：

- Fastify v4 的官方 End of LTS 是 2025-06-30，已经过期。`sunset` 状态要求同时声明
  `migrate_by` 与 `eol`，而一个已过期的 EOL 只会 fail closed，做不成合法 transition。
- Kysely 是 0.x 且上游没有支持窗口表。为它编一个 transition 等于把平台没有拿到的上游
  承诺写进 catalog。

两者都不进 `PACKAGE_RELEASE_CONTRACTS`。那个受治理 npm snapshot 集合目前只含 Next.js、
React 与 Prisma，扩充它要改 validator 这一共享核心，超出本次裁定边界。

## Acceptance criteria

- [ ] AC-1 `architecture/catalog.json` 新增 `framework.fastify.5`（5.12.3，preferred）与
      `orm.kysely.0-29`（0.29.5，preferred），两条的 `provenance.evidence` 都写明上游
      支持窗口依据。
- [ ] AC-2 catalog `revision` 按既有规则递增到 `2026.09.0`，`published_at` 与 `review_by`
      同步更新。
- [ ] AC-3 `architecture/profiles/linux-node-systemd-postgres-v1.json` 版本升到 1.1.0，
      `required_components` 增加这两个 slot，并改写声明本 profile 没有 ORM/framework slot
      的那条 `compatibility_rules`。
- [ ] AC-4 既有三个 profile 的 `required_components` 一个组件都不增删，
      `architecture/fixtures/` 下既有 fixture 的组件集合、profile 归属与预期结论全部不变；
      只有 catalog revision 这一机械字段随之更新。
- [ ] AC-5 三份 `architecture/reference/` lock 由 CLI 重新生成，重复生成 byte-identical。
- [ ] AC-6 用 LocalWMS 形状的候选声明跑通一次 `aisoft-architecture validate`，输出
      `"valid":true`、profile `linux-node-systemd-postgres-v1`、catalog revision `2026.09.0`，
      并包含两个新组件。
- [ ] AC-7 `bash codex/tests/smoke.sh` 全绿，architecture 单测全绿。
- [ ] AC-8 `architecture/install.sh` 合并后重装写成验证记录里的显式交接项。

## 接口、数据与兼容性影响

catalog revision 是 profile 与项目声明共同比对的字段：`validate_profile` 在
`catalog_revision` 不等时报 `PROFILE_CATALOG_MISMATCH`，`validate_project` 报
`PROJECT_CATALOG_MISMATCH`，lock 里还固化了 `catalog_sha256`。因此一次 revision 递增
必然带动四个 profile、`architecture/fixtures/` 与 `architecture/templates/` 里的
`catalog_revision`、三份 reference 声明与 lock，以及测试与 smoke 里钉住的 `--today` 与
`CATALOG_REVISION` 常量。这一级联在 `af575d9`、`6ca5acb`、`b2d3ddf` 三次历史 revision
bump 里逐字出现过，是既有规则；裁定里的「既有三个 profile 与 fixtures 不受影响」按
AC-4 理解为组件语义不变，不是文件零 diff。

profile 从 1.0.0 抬到 1.1.0 会让所有钉 1.0.0 的既有声明报 `PROJECT_PROFILE_MISMATCH`。
今天唯一这样的声明在 LocalWMS，处置方式是它自己开 Issue 重新声明，本变更不代写、也不
读写该仓任何文件之外的东西。

## 风险与回滚约束

- 回滚方式是 revert 唯一最终 PR 并重跑同一套验证集，没有其它路径。
- `architecture/install.sh` 的 staleness 闸门（#171）意味着已安装的 CLI 在合并后会与仓库
  不一致，必须重装；这不是本次 PR 内的动作。
- 不改 `codex/runtime/aisoft_architecture/` 下任何 validator/lock 逻辑，不动 schema。

## 非目标

- 不新增 profile，不改既有三个 profile 的 `required_components`。
- 不代 LocalWMS 写 `.aisoft/architecture.json`。
- 不扩 `PACKAGE_RELEASE_CONTRACTS`，不改 validator 或 schema。
- 不处理 Issue 正文里已由其它变更解决的 profile 新增与 TypeScript sunset 两项。
- 不动 `docker-release/`，它的 `matrix_revision` 是独立工件，历史 catalog revision bump
  从未触碰过它。

## 未决问题

无。
