# 平台级 E2E 验收表

- 依据：[ADR 0002](../adr/0002-deterministic-development-flow.md)「重开条件」、[整改路线](remediation-roadmap.md)第二轮退出条件 1
- 建立：2026-10-20（Issue #389）
- 用法：活文档。一个项目每完成一次端到端演练或采用一个新的发布包版本，追加一行；不改写已有行。证据只写链接与编号，读回正文留在项目仓的 verification 里。

## 覆盖阶段

一条完整链是：**构建 → 发布制品 → test 部署 → 健康端点返回精确 release SHA → 同版本重跑 noop → 回滚 → 再部署**。`database restore` 与生产单独列出，未做就写进「未覆盖」。

## 验收记录

| 项目 | 发布包版本 | 日期 | 覆盖阶段 | 证据 | 未覆盖 |
|---|---|---|---|---|---|
| NewEMaint（#279 M1 最小部署链演练） | 1.2.0（NewEMaint #297 pin） | 2026-10-20 | 构建、发布、test 部署、健康 SHA、同版本 noop、回滚到上一版本、再部署；数据表与 uploads 卷保留核对 | NewEMaint PR 308（`docs/changes/279-m1-test-deploy-drill/` 的 verification，合并 `f4617aae`）；GitHub run 39118940079；Release 416386339；公司 Gitea run 6（activated）/ 10（healthy-noop）/ 13（再部署） | database restore（manual-only，NOT RUN）；生产；业务表 0 行与 uploads 空卷，保留只证明不丢表、卷未重建 |
