# ADR-0004：离线 provenance 与不可变 identity

- 状态：Accepted
- 日期：2026-08-02
- 补充：ADR-0006 的 as-built 版本例外明确不适用于按 digest 固定的 component；
  不可变身份与 provenance 要求不变。

生产依赖必须先在联网 staging 从官方 source 取得 versioned artifact、checksum/signature、SBOM
和 provenance，再导入批准的内网 mirror。OS 使用 release/build/checksum，packages 使用 exact
version 与 lock，CI actions 使用 full commit SHA，OCI 同时保留可读 tag 和 `sha256` digest。

Catalog/lock 只保存脱敏 artifact identity，不保存 registry credentials。Validator 无网络调用，
不会 pull、升级或修改 production。Mirror import、签名验证和实际部署由独立运维/应用 Change
执行并保留 rollback evidence。
