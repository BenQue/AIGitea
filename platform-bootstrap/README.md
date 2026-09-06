# platform-bootstrap/v1

独立 SCM/平台离线交付合同，工具版本 `1.0.0`。不需要 application release 或 compatibility matrix。
`company-delivery/` 继续负责现有 application operator bundle；本入口不会安装全部八个 installer。

本版交付可执行的 builder、verify-handoff、inventory 校验、采用决策和动作请求/回读协议。
`apply` / `rollback --dry-run` 生成固定动作合同，**不执行现场安装或 API mutation**。
不带 `--dry-run` 返回 `SITE_EXECUTOR_NOT_BOUND`。后续 B1/B2 必须在独立部署合同中绑定实际
Gitea/Runner/服务执行器及身份，经过 source review、两次隔离执行、故意失败与恢复后才可现场执行。
本工具不会接受任意 shell、URL、credential path 或插件执行器作为绕过入口。

| 组件 allowlist | 交付内容 |
|---|---|
| handoff-verifier | Python 标准库 CLI、archive/manifest/payload 校验 |
| adoption-planner | 脱敏 inventory/target、采用决策、回退身份 |
| action-contracts | repo/protection/required CI/Runner/one-shot inbound/canary 固定动作协议 |

这些组件在 `scm-ci` 按需使用。包内无 AI/Claude/Codex、项目 Secret、实际 profile/凭据、Runner 二进制、
Gitea 数据库、application artifact、服务 unit 或自动安装器。运行时不需要网络或第三方 Python 库，要求 Python 3.10+。

## 信任与制品身份

批准记录绑定 source SHA、组件、scm-ci 与 rollback identity。builder 要求 clean repository 的 HEAD 完全相同，
只读取固定 allowlist 的 Git 跟踪文件；拒绝 symlink/hardlink、模式漂移和未知包文件。
输出 `platform-bootstrap.tar.gz`、`handoff.json`、`handoff.sha256`。同一批准记录原字节和 source 输入得到相同输出。

外部批准的 handoff SHA-256 → handoff 的 archive/manifest SHA-256 → bundle manifest 的逐文件/payload 索引摘要。
archive 无需且不能包含自身摘要；`bundle-manifest.json` 与外部 `handoff.json` 分担两层身份。
审批引用和 checksum 不代替签名或审批系统认证。`handoff.sha256` 随包携带仅便于搬运，不能作为独立信任起点。
在运行收到的包内代码前，先用已信任工具核验批准记录中的 digest。生产还须 independently 核验 source 已合并、
required CI、现场批准；builder 不把本地 clean commit 解释成已批准生产部署。

manifest 保留原始平台 source SHA；公司 PR 的 human merge SHA 在 observation 单独保存。
公司合并产生的新 SHA 不会改写原 source 或重构建冒充已验证 archive。

## 数据与证据

`schema/` 是标准 JSON Schema 2020-12 的闭合合同；Python 校验器实现本版使用的严格子集。
未知字段（含 Secret、raw log、URL、hostname、IP、username、credential path）、重复 key、非法枚举/identity 均拒绝。
模板里的重复数字 digest 是结构示例，`evidence_layer=local`，不构成公司事实。引用须用脱敏审批系统编号，
identity 必须从已批准的 canonical 资产记录计算 SHA-256；不要直接哈希低熵密码或把 hash 当匿名化保证。

`verify-inventory` 仅校验传入文档；`readback` 仅校验申报的 observation 与请求身份/验收检查关系，
输出明确为 `declared-observation-only`，不会主动检测主机或声称已执行现场动作。
完整采用分流、命令、动作协议和恢复边界见 [runbook](runbook.md) 与 [actions](actions.json)。
