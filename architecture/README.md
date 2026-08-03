# AISoftPlatform architecture catalog V1

本目录是技术架构版本、profile、例外和项目 lock 有效性的唯一平台事实源。它只验证候选，
不会升级依赖、修改应用、部署、访问服务器或宣称 migration 完成。

## Canonical contract

- 所有输入仅接受 strict JSON；V1 明确拒绝 `.yaml`/`.yml`，没有 YAML parser。
- `catalog.json` 固定 component 的精确版本、状态、lifecycle、官方来源和 provenance 要求。
- `profiles/*.json` 组合兼容 component 与 delivery contract；delivery 能力仍由 #22/应用 Change
  提供。
- 项目人工维护 `.aisoft/architecture.json`，提交生成的 `architecture.lock.json`。
- lock 不含生成时间或主机信息；相同输入会生成 byte-identical canonical JSON。
- `preferred`/`supported` 可被 profile 接受；`sunset` 必须有 migration Issue；`prohibited`、
  EOL、过期例外、mutable-only OCI 和 lock drift 均 fail closed。

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
例外必须有 owner、reason、risk、controls、创建/到期日和 migration Issue；到期当日即无效，
没有 `--ignore-all`。

离线导入顺序：从官方 source 获取 versioned artifact 和 metadata，校验签名/checksum，获取
SBOM/provenance/OCI attestations，导入批准 mirror，再由人工 PR 更新 catalog/lock。任何 timer 或
自动 updater 均不得直接改 production lock。

## 状态边界

`architecture/reference/` 是 read-only dry-run evidence。其 declaration/lock 是目标候选，gap
报告描述当前差异；它们不是项目已迁移、已部署或已验收的证据。实际采用必须在对应应用仓
另建 Change。
