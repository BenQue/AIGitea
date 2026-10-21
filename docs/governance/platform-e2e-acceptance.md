# 平台级 E2E 验收表

- 依据：[ADR 0002](../adr/0002-deterministic-development-flow.md)「重开条件」、[整改路线](remediation-roadmap.md)第二轮退出条件 1
- 建立：2026-10-20（Issue #389）
- 用法：活文档。一个项目每完成一次端到端演练或采用一个新的发布包版本，追加一行；不改写已有行。「工具」列是 #408 补的，已有行按当时会话补填，推定的标 `*`。证据只写链接与编号，读回正文留在项目仓的 verification 里。

## 覆盖阶段

一条完整链是：**构建 → 发布制品 → test 部署 → 健康端点返回精确 release SHA → 同版本重跑 noop → 回滚 → 再部署**。`database restore` 与生产单独列出，未做就写进「未覆盖」。

## 验收记录

| 项目 | 工具 | 发布包版本 | 日期 | 覆盖阶段 | 证据 | 未覆盖 |
|---|---|---|---|---|---|---|
| NewEMaint（#279 M1 最小部署链演练） | Claude* | 1.2.0（NewEMaint #297 pin） | 2026-10-20 | 构建、发布、test 部署、健康 SHA、同版本 noop、回滚到上一版本、再部署；数据表与 uploads 卷保留核对 | NewEMaint PR 308（`docs/changes/279-m1-test-deploy-drill/` 的 verification，合并 `f4617aae`）；GitHub run 39118940079；Release 416386339；公司 Gitea run 6（activated）/ 10（healthy-noop）/ 13（再部署） | database restore（manual-only，NOT RUN）；生产；业务表 0 行与 uploads 空卷，保留只证明不丢表、卷未重建 |
| NewEMaint（#313 公司 test 数据库恢复演练） | Claude | 1.2.0（NewEMaint main pin） | 2026-10-21 | database restore：一键部署备份（run 13）在一次性隔离容器恢复，32 张表行数与数据哈希、表结构、枚举、迁移清单与备份和源库一致，演练容器已删除 | NewEMaint PR 322（`docs/changes/313-test-db-restore-drill/` 的 verification，合并 `dfe04df`）；AC-1–AC-4、AC-6 PASS，AC-5 隔离比对被无关容器的重启循环误判为 FAIL，负责人以回执判过并记录例外 | 生产恢复（NOT RUN）；业务表几乎为空，耗时与体量不能外推到生产；未恢复到正式 test 库；uploads 不在范围 |

## 采用记录

项目采用或升级一个发布包版本时追加一行（#402 起）；`--project-status` 写采用 PR 合并后在项目 `main` 上的读回。

| 项目 | 工具 | 发布包版本 | 采用 Issue | 采用 PR | `--project-status` |
|---|---|---|---|---|---|
| HSDB | Claude | 1.8.0 | HSDB #70 | HSDB PR 71（合并 `673cadb`） | main `673cadb` 上 `aisoft bundle status` 四项 PASS（1.8.0）；`check-change-documents` gap=0 |
| LocalWMS | Claude | 1.8.0 | LocalWMS #335（含 CI checkout，complex） | LocalWMS PR 336（合并 `6e143fe`） | main `6e143fe` 上 `aisoft bundle status` 四项 PASS（1.8.0）；`check-change-documents` gap=0；workflow 无 `uses:` |
| SFM | Claude | 1.8.0 | SFMDigitalBoard #184 | SFMDigitalBoard PR 185（合并 `799bf12`） | main `3bb6b78`（含 PR 185 与 187）上 `aisoft bundle status` 四项 PASS（1.8.0）；`check-change-documents` gap=1，全是旧编号目录与旧四文档（R12 LEGACY 范围） |
| SFM（Cursor 落点，平台 R15 的 Cursor 使用层首次验收） | Cursor（本机 `cursor-agent`，Claude 驱动） | 1.8.0 | SFMDigitalBoard #186 | SFMDigitalBoard PR 187（合并 `3bb6b78`；`docs/changes/186-cursor-landing/` 的 verification；fresh Cursor 会话读到平台技能） | 采用分支四项 PASS，`--capabilities` 的 Cursor 行 PASS；main `3bb6b78` 上 `aisoft bundle status` 四项 PASS（1.8.0） |
