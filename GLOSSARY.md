# AISoftPlatform 术语表

本表解释既有术语；权限、状态转换与验收规则以链接的合同为准。

| 术语 | 定义 | 合同来源 |
|---|---|---|
| Issue | 需求、缺陷或平台变更的唯一追踪主键 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| Change | 同一 Issue 的分支、语义文档、worktree 和唯一最终 PR 所组成的交付单元 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| 语义文档 | summary 的 documents 映射所解析出的 summary、spec、plan、verification 等文档 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| Controller | 加载合同、选择任务、验证提交并管理远端交付状态的确定性编排程序 | [编排](04-Agent编排与定时任务.md) |
| Provider | 在 Controller 给定范围内执行实现、测试和本地提交的模型适配器 | [双工具](08-双工具共存与实施.md) |
| Frontier ticket | Ticket graph 中前置依赖均已完成、当前可执行的任务 Txx | [编排](04-Agent编排与定时任务.md) |
| approved | 合同与启动已获批准的 Issue 状态 | [流程](03-Issue-Spec-Plan与单闸门开发流程.md) |
| AWAITING_PR_CONFIRMATION | 已备好最终 PR 候选、等待提交确认的持久状态 | [编排](04-Agent编排与定时任务.md) |
| READY_FOR_REVIEW | manual PR 已完成要求的验证，等待人工审阅及合并的状态 | [编排](04-Agent编排与定时任务.md) |
| source / local / CI / installed / live | 分别指源码、局部执行、持续集成、实际安装与现场运行的证据层次 | [总纲](README.md) |
| Matt snapshot | 按上游 release 固定 tag、commit、完整技能目录和 manifest 的快照 | [双工具](08-双工具共存与实施.md) |
