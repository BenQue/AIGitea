# AISoftPlatform architecture catalog V1

本目录是技术架构版本、profile、例外和项目 lock 有效性的唯一平台事实源。它只验证候选，
不会升级依赖、修改应用、部署、访问服务器或宣称 migration 完成。

## Canonical contract

- 所有输入仅接受 strict JSON；V1 明确拒绝 `.yaml`/`.yml`，没有 YAML parser。
- `catalog.json` 固定 component 的精确版本、状态、lifecycle、官方来源和 provenance 要求。
- React preferred entry 还固定 `react`/`react-dom` 同版本的 npm stable-release snapshot、精确
  Registry URL 和 integrity；validator 拒绝未被该 snapshot 覆盖的版本、Canary/Experimental、
  `latest`、范围和两包版本不一致，且不会在 lock 生成时访问网络。
- `profiles/*.json` 的每个 slot 保留唯一 `preferred` component，并可由 profile owner 维护同
  category 的 closed `transitions` allowlist；delivery 能力仍由 #22/应用 Change 提供。
- 项目人工维护 `.aisoft/architecture.json`，提交生成的 `architecture.lock.json`。
- lock 不含生成时间或主机信息；相同输入会生成 byte-identical canonical JSON。
- Project 每个 slot 只能选择 preferred 或一个 allowlisted `supported`/`sunset` transition；
  transition 不是第四种永久 profile，也不表示 major migration 已完成。
- Transition 必须引用绝对 HTTPS migration Issue，并与唯一、未过期 exception 一一绑定；
  多个 component 可共享一个逐项列明范围的 umbrella Issue，但每个 component 仍保留自己的
  exception。lock 固化 Issue、exception ID/expiry 与 catalog/profile/declaration checksums。
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
快速通道但不能绕过这些门；patch 每月复审，minor 每季度复审，major 必须进入应用仓的 complex
Change。多个相互依赖 major 可以由一个 umbrella Change 统一治理，但必须逐 component 记录
compatibility、test、exception/expiry 与 rollback，不能把“部分完成”报告成整套迁移完成。
例外必须有 owner、reason、risk、controls、创建/到期日和 migration Issue；transition Issue
必须是应用仓中真实可读的绝对 HTTPS URL，expiry 不得超过创建日起 180 天或 component
`migrate_by`，且到期当日即无效。Preferred 路径不需要例外，也没有 `--ignore-all`。

离线导入顺序：从官方 source 获取 versioned artifact 和 metadata，校验签名/checksum，获取
SBOM/provenance/OCI attestations，导入批准 mirror，再由人工 PR 更新 catalog/lock。任何 timer 或
自动 updater 均不得直接改 production lock。

## 状态边界

`architecture/reference/` 是 read-only dry-run evidence。NewEmaint reference 明确分为：

- `target-candidate/`：project ID `newemaint-target-candidate`，描述 preferred 目标；
- current lock：本 Change 不生成；NewEmaint 实际采用 supported/preferred bytes 后，才可用
  project ID `newemaint` 在应用 Change 中生成；
- `gap-report.md`：记录 current facts、target 差异、umbrella tracking 与未执行边界。

Target lock 不能复制或重命名为 current，也不是项目已迁移、已部署或已验收的证据。
Transition 不能规避 `prohibited`/EOL/digest/expiry/checksum。Issue #26 明确采用 target-only
验收；NewEmaint [#52](http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/52) 是唯一 umbrella
migration tracking Issue，但它不授权实施，也不能让 unsupported Next.js 14 进入 current lock。
