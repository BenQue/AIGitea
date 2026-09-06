---
issue: 270
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/270
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - deployment
depends_on:
  - 268
status: approved
branch: change/270-company-platform-bootstrap
created: 2026-09-06
updated: 2026-09-06
---

# 独立公司平台交付合同

## Problem Statement

公司 Gitea 与平台自身需要在任何 application release/matrix 之前建立独立可信的采用入口。已有实例必须先盘点，不能重复空白安装。开发权威和公司部署权威保持分离。

## Solution 与用户故事

1. 平台维护者从 approved、clean、完整 source SHA 构建独立、可复现的离线包。
2. 现场操作员在运行包内代码之前用独立批准的 handoff SHA-256 核验 archive；包内 manifest/payload 身份再闭合。
3. 盘点者只交付严格结构的脱敏状态，不传 hostname/IP、用户名、配置、credential path 或原始日志。
4. 操作员得到 first-install/adopt/adopt-with-remediation/controlled-upgrade/BLOCKED 的确定性决策与停止条件。
5. 公司审批者审阅 exact target/source/组件/动作/回退身份；平台 source 批准不等于现场批准。
6. 操作员为 repo bootstrap、protected main、required CI、Runner、one-shot inbound、canary 得到固定输入、no-op、负向验证及恢复入口。
7. 审核者可以区分命令合同通过、本地隔离测试、installed readback 和 company live 证据。
8. application 操作员继续使用未改变的 company-delivery 工具与合同。

## Implementation Decisions

- 新增 platform-bootstrap/v1，version 1.0.0，Python 标准库运行时和 CLI；scm-ci 是唯一角色。
- package 只含固定 allowlist 的确定性验证/采用/动作工具、严格 schema、模板及 runbook。没有 AI provider、开发凭据、项目 Secret、自动安装全部 installer 或 application artifact。
- 外部 handoff 绑定 archive SHA-256 与包内 manifest SHA-256；包内 manifest 绑定 source、审批引用与摘要、rollback、组件、逐文件摘要及规范化 payload 索引摘要。避免 archive 自包含自身摘要的循环。
- clean HEAD 必须等于批准记录里的完整 source SHA。按 git 跟踪文件的固定映射打包，拒绝 symlink、未知文件、路径穿越、重复 JSON key、未知字段、摘要/角色/版本/身份冲突；错误不回显输入内容。
- 审批记录是公司审批系统的脱敏引用，checksum 提供完整性，不替代签名或人类批准。构建不证明 main 已合并；生产额外核验 merge/CI/公司批准。
- inventory 使用 opaque SHA-256 identity、版本与枚举/布尔值，不主动读取现场。adoption-plan 绑定 inventory 与 handoff 摘要；known-version、backup/restore、负向权限和 no-AI 边界必须显式给出。controlled-upgrade 只产生停止决策。
- apply/readback/rollback 是版本化的固定动作合同入口：dry-run 产出可审阅 exact 请求；没有独立现场授权/执行绑定时 fail closed。现场 repo/权限/Runner/服务的具体身份与路径由后续 B1/B2 合同绑定，本 Issue 不运行现场动作。不得把 dry-run 或传入的 observation 写成已安装事实。
- 原 source SHA 与公司 approval/merge SHA 分栏；inbound 只接受 exact source 到非 main staging，正常 protected PR 流程由人合并，禁止 direct/force push、自动 merge 或 timer 自动 enable。
- source 变更授权仅限新 package/runtime/测试/runbook 与导航。不得修改当前 AGENTS.md、Agent/Controller、CI workflow、现有 installer、live manifest 或 company-delivery application 合同。

## Acceptance criteria

- AC-1：无 application 输入、相同输入 byte-identical archive；严格身份和摘要闭合。
- AC-2：verify-handoff、inventory、adoption-plan、apply/readback/rollback 入口可运行；采用分流与停止条件有回归。
- AC-3：scm-ci 组件 allowlist 无 AI/凭据/application；未知字段、敏感字段和 symlink fail closed。
- AC-4：repo/protection/required CI/Runner/inbound/canary 各有 exact 输入、no-op、负向/失败/恢复检查，现场执行需独立绑定。
- AC-5：本地两次构建/验证、checksum 和 identity 故意失败、rollback dry-run、targeted regression 通过。
- AC-6：runbook 所有 shell 命令块 <=50 行；source/local/installed/company live 分层；最终 AWAITING_PR_CONFIRMATION。

## Testing Decisions

最高测试缝为 public CLI 和 bundle/adoption/action 公共函数。用隔离 Git fixture 与严格 observation 测试外部行为，不连接公司、不安装/启动服务或读取 credential。现有 company-delivery 回归验证兼容性。遵循仓库 Python suite 与脚本 smoke 约束；失败保持真实状态。

## Out of Scope

company live apply、controlled upgrade 执行、Gitea 数据/账号/PAT/Secret 迁移、环境探测、部署、应用 release、provider、routine merge、全局 skills 安装；#268 A2 等其他 Issue 的修复。
