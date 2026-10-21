# AISoftPlatform 术语表

本表解释既有术语；权限、状态转换与验收规则以链接的合同为准。

| 术语 | 定义 | 合同来源 |
|---|---|---|
| Issue | 需求、缺陷或平台变更的唯一追踪主键 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| Change | 同一 Issue 的分支、语义文档、worktree 和唯一最终 PR 所组成的交付单元 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 语义文档 | summary 的 documents 映射所解析出的 summary、spec、plan、verification 等文档 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 路由合同 | 一条 Issue 怎么开发由确定性的表决定，不由模型自由决定；与执行引擎分离 | [ADR 0002](docs/adr/0002-deterministic-development-flow.md) |
| 路由表 | `aisoft-platform` 技能的 `references/route-policy.md`：判级结果到路由卡的唯一映射，只钉必用与禁用技能 | [路由表](skills/aisoft-platform/references/route-policy.md) |
| 路由卡 | summary front matter 的 `route:` 块（process、tier、effort、skills、method、verify、review、confirm），确认点 1 显示为「路由」行；人可覆盖并写 `override_reason` | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| process | 路由卡的开发路径：`awaiting-triage`、`small-direct`、`complex-development`、`complex-production` | [路由表](skills/aisoft-platform/references/route-policy.md) |
| tier / effort | 模型档位（standard、frontier、max）与推理强度（medium、high、max）；合同只写档位，型号按工具映射 | [双工具](08-双工具共存与实施.md) |
| `change_control` | 仓库的交付阶段：`development` 的 complex 变更用 Issue 正文的验收标准与合成 `T01`，缺省 `production` 要求 spec/plan | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 合成 T01 | development complex 不写 plan，把 Issue 正文的全部验收标准当作一个 ticket `T01` 实现 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 确认点 1 / 确认点 2 | 两个人工确认：合同/启动确认（持久化 `approved`）与提交唯一最终 PR 前确认；都不授权合并或部署 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 执行引擎 | 把路由卡执行到 PR 候选的程序；VM 上的版本已退出，今后只在 Mac 上分阶段重建，产出止于 PR 候选 | [ADR 0002](docs/adr/0002-deterministic-development-flow.md) |
| 交叉审核 | 平台仓 complex 变更在确认点 2 前由未参与实现的另一方提供者对候选 head 只读审查 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| Controller | 已退出：VM 上加载合同、选择任务并管理远端交付状态的编排程序；现由会话按两个确认点执行 | [编排](04-Agent编排与定时任务.md) |
| Provider | 执行实现的模型工具（Claude Code、Codex；项目使用层另有 Cursor） | [双工具](08-双工具共存与实施.md) |
| Frontier ticket | Ticket graph 中前置依赖均已完成、当前可执行的任务 Txx | [编排](04-Agent编排与定时任务.md) |
| approved | 合同与启动已获批准的 Issue 状态 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| AWAITING_PR_CONFIRMATION | 已备好最终 PR 候选、等待提交确认的持久状态 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| READY_FOR_REVIEW | 最终 PR 已完成要求的验证，等待人工审阅及合并的状态 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| source / local / CI / installed / live | 分别指源码、局部执行、持续集成、实际安装与现场运行的证据层次 | [总纲](README.md) |
| Matt snapshot | 按上游 release 固定 tag、commit、完整技能目录和 manifest 的快照 | [双工具](08-双工具共存与实施.md) |
| 现行合同 / 来历 | 分册体例：开头一段说本册现在管什么，文末一张表记哪个 Issue 在哪个合并里带来了什么 | [总纲](README.md) |
