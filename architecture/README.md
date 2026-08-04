# AISoftPlatform architecture catalog V1

本目录是技术架构版本、profile、例外和项目 lock 有效性的唯一平台事实源。它只验证候选，
不会升级依赖、修改应用、部署、访问服务器或宣称 migration 完成。

## Canonical contract

- 所有输入仅接受 strict JSON；V1 明确拒绝 `.yaml`/`.yml`，没有 YAML parser。
- `catalog.json` 固定 component 的精确版本、状态、lifecycle、官方来源和 provenance 要求。
- `profiles/*.json` 的每个 slot 保留唯一 `preferred` component，并可由 profile owner 维护同
  category 的 closed `transitions` allowlist；delivery 能力仍由 #22/应用 Change 提供。
- 项目人工维护 `.aisoft/architecture.json`，提交生成的 `architecture.lock.json`。
- lock 不含生成时间或主机信息；相同输入会生成 byte-identical canonical JSON。
- Project 每个 slot 只能选择 preferred 或一个 allowlisted `supported`/`sunset` transition；
  transition 不是第四种永久 profile，也不表示 major migration 已完成。
- Transition 必须引用绝对 HTTPS migration Issue，并与唯一、未过期 exception 一一绑定；
  lock 固化 Issue、exception ID/expiry 与 catalog/profile/declaration checksums。
- `prohibited`、EOL、过期/超过 180 天或晚于 `migrate_by` 的 exception、mutable-only OCI 和
  lock drift 均 fail closed；没有 bypass flag。

## CLI

```bash
architecture/bin/aisoft-architecture validate \
  --catalog architecture/catalog.json \
  --profiles-dir architecture/profiles \
  --schema-dir architecture/schemas \
  --project architecture/templates/project-architecture.example.json

architecture/bin/aisoft-architecture lock \
  --catalog architecture/catalog.json \
  --profiles-dir architecture/profiles \
  --schema-dir architecture/schemas \
  --project .aisoft/architecture.json \
  --output architecture.lock.json

architecture/bin/aisoft-architecture explain \
  --catalog architecture/catalog.json \
  --component runtime.node.24
```

`--today YYYY-MM-DD` 只用于可复现的 lifecycle/边界测试。生产 CI 不应覆盖当天 UTC date。
CLI diagnostics 只返回 code、path、remediation，不回显输入值。

## 更新与例外

Catalog 更新必须建立 Issue、complex spec/plan、兼容证据、PR/CI 和人工合并。Security 更新可走
快速通道但不能绕过这些门；patch 每月复审，minor 每季度复审，major 永远是独立 Change。
例外必须有 owner、reason、risk、controls、创建/到期日和 migration Issue；transition Issue
必须是应用仓中真实可读的绝对 HTTPS URL，expiry 不得超过创建日起 180 天或 component
`migrate_by`，且到期当日即无效。Preferred 路径不需要例外，也没有 `--ignore-all`。

离线导入顺序：从官方 source 获取 versioned artifact 和 metadata，校验签名/checksum，获取
SBOM/provenance/OCI attestations，导入批准 mirror，再由人工 PR 更新 catalog/lock。任何 timer 或
自动 updater 均不得直接改 production lock。

## 状态边界

`architecture/reference/` 是 read-only dry-run evidence。NewEmaint reference 明确分为：

- `target-candidate/`：project ID `newemaint-target-candidate`，描述 preferred 目标；
- `current-transition/`：仅在全部真实 migration Issues、有效 exceptions 与 upstream support
  gates 满足后，才可用 project ID `newemaint` 生成；
- `gap-report.md`：记录 current facts、target 差异和 `BLOCKED_EXTERNAL`。

Target lock 不能复制或重命名为 current，也不是项目已迁移、已部署或已验收的证据。
Transition 不能规避 `prohibited`/EOL/digest/expiry/checksum。Issue #26 当前没有生成
`current-transition/`：NewEmaint migration Issues 未获创建授权，且官方政策已将 Next.js 14
标为 unsupported。实际采用必须在对应应用仓另建 Change。
