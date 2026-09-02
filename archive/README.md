# 历史资料索引

本目录保存已经被当前平台合同替代、但仍有审计和设计追溯价值的资料。它们不是当前配置、命令、
权限或 live 环境的事实源；执行平台操作时从仓库根 [README](../README.md)、相关编号分册、
`architecture/README.md`、`docker-release/README.md` 和对应 Change verification 开始。

## 已归档资料

| 文件 | 历史范围 | 被替代原因 |
|---|---|---|
| [AISoft 平台全貌 v2（2026-07-11）](AISoft平台全貌-一页-v2-20260711.pdf) | 三道人工闸门、`gitea-ci` 同机 PM2/SQLite、`prod-sim` 早期设想 | v3 单一最终 PR 闸门、host-role 收口、独立 AppServer 与 Docker-first 合同已替代 |
| [10-AI Issue 判级与标签实施计划](10-AI-Issue判级与标签实施计划.md) | 2026-07-15 初始 16-label、Issue #8 试点实施步骤 | 当前 taxonomy、判级与 readable Change 合同已进入 README、03/04、AGENTS 和 runtime source |
| [11-Codex Loop runtime 实施计划](11-Codex-Loop运行时实施计划.md) | provider-neutral Loop 的首轮实现和试点计划 | 当前 controller/provider/Matt 边界已进入 04/08 与 versioned runtime source |
| [软件开发与自动化部署运维平台-方案设计](软件开发与自动化部署运维平台-方案设计.md) | 最初平台方案 | 后续 as-built 与 v3 分册替代 |
| [Spec 驱动工作流与绑定方案](Spec驱动工作流与Spec-Plan-Issue绑定方案.md) | 独立 spec PR 与早期三闸门模型 | small/complex 双路径和单一最终 PR 闸门替代 |
| [阶段 0–2.6 起步清单](阶段0-起步清单-OrbStack-Gitea-actrunner.md) | 早期 POC 建设步骤 | 当前编号分册与 Change evidence 替代 |
| [平台状态历史（截至 2026-09-02）](平台状态历史-20260902.md) | README §1 与 08 §4 中已完成的状态条目：v2 试点 #4、`prod-sim` 退役、legacy 制品收口、#21/#35 基线、Windows/内网目标设计、Docker release evidence、Codex/Claude adapter 试点 | 活文档只描述当前合同；已兑现的历史条目由 Issue #233 迁出 |

## 使用规则

- 历史资料中的路径、账号、端口、版本、Issue/PR 状态和命令均可能过时，使用前必须回到当前文档并
  做实时只读核对。
- `docs/changes/` 是当时 Change 的审计证据，不因本次归档批量改写。
- 需要恢复归档文件时优先使用 Git 历史或 `git mv`，不要复制成新的核心事实源。
