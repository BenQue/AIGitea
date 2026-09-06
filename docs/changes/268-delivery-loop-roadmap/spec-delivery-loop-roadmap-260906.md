---
issue: 268
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/268
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/268-delivery-loop-roadmap
created: 2026-09-06
updated: 2026-09-06
---

# 平台流程收口与 NewEMaint 真实闭环路线图合同

## 目标与原因

把 2026-09-06 的完整性评估和用户确认的顺序转为可追踪路线图。先修复首发必需的平台流程，随后先完成公司内网 Gitea 与 AISoftPlatform 自身部署验收，再用 NewEMaint 的真实内网交付验证应用流程，最后抽取通用标准。后续的技术栈、基础设施、部署命令、数据迁移与回滚细节由项目自己的合同和版本化脚本规定。

## Acceptance criteria

- AC-1：plan 包含基线和发现 F1–F10 的去向；所有阶段有依赖、退出条件、责任仓库、任务模型与证据要求；改名全量延期。
- AC-2：明确首发前置的最小范围；公司内网 Gitea 与平台自身部署必须有独立先行阶段和现场退出条件，不依赖先搬运 NewEMaint 制品；NewEMaint 复用 #18/#43/#74；记录待决发布范围、release 身份、已有公司实例、非生产重复部署、故意失败、回滚、数据/文件恢复和生产验收。
- AC-3：给出可执行的调度协议、模型规则、单 Issue 文件所有权、状态台账、恢复方式、人工闸门；明确区分本 Issue 完成与整条路线图完成。
- AC-4：创建新的独立调度任务，采用 `gpt-5.6-sol` / `high`，提供准确文件路径和首轮工作，记录任务 ID 与可观察的启动回执。
- AC-5：本目录通过语义文档检查、判级字段验证与 diff 检查；verification 如实区分本次检查、前一轮证据、未运行的远端 CI/合并/部署。

## 多 Issue 模式的明确授权

本 spec 显式采用跨仓库 multi-Issue 模式，目标仅为 `admin/aisoft-platform` 和 `admin/NewEMaint`。路线图工作项 A1–D3 是排序与验收入口，不直接等于已经批准实施的 Issue，也不替代 `$triage → $to-spec → $to-tickets → $implement`。

调度者先核对开放 Issue 与既有合同，复用可覆盖的事项。只有存在独立、可验收且没有合适已有归属的工作时才新建 Issue。派生 Issue 必须写清来源 #268、本次调度任务、目标仓库、至少一条可衡量 AC 和真实 Issue 依赖，并在 summary 同步依赖。跨仓依赖用完整仓库名和 Issue 链接说明，避免数字冲突；遵循各仓现有 resolver 的字段格式。

每个 Issue 使用其 exact branch/docs/worktree tuple、唯一最终 PR 和批准合同。调度者维护顺序和证据，不写业务代码、平台 runtime 或替代实施者提交。子任务必须有明确文件/职责所有权，并知道其他任务也在工作，不能回退他人改动。

## 调度与模型合同

- 调度与复杂任务：`gpt-5.6-sol`，`high`。适用于跨仓架构、平台合同、CI/部署/回滚、安全、数据迁移、安装/权限差异定位和重要审查。
- 简单任务：`gpt-5.6-terra`，`high`。适用于已定合同内的有限文档修正、证据整理、机械同步和局部实现子任务。
- 模型选择与平台风险判级分开：脚本改动即使只有一行，也可能属于 complex Issue；可由 Terra 执行已确定的机械修复子任务，再由 Sol 核对合同与门禁。
- 模型不可用时明确报告，不静默换模型或降低 reasoning。子代理显式设置模型时使用不继承全部历史的上下文方式，并提供自足交接。
- 默认最多同时开展两个独立、无冲突的实施/分析子任务；同一 Issue 同时只有一个实施所有者。现场变更、权限和共享安装步骤串行。
- 不因等待合并而占用共享工作区反复改动；可以继续独立的只读调查和下一阶段合同准备，不能越过阶段执行闸门。

## 授权、接口、数据与兼容性影响

用户已批准本次路线图文档准备和调度启动。未来实现会改变的具体合同、权限、架构、数据和现场操作，仍在相应 Issue 给出可审阅结果后按现有规则确认。最终 PR 提交按 exact Issue/branch/manual 单独确认，manual merge 由人执行；merge 不授予部署权限。

本 Change 不修改 `AGENTS.md`、skills、controller、CI、部署脚本、manifest、凭据或现场服务，不启用 provider 或 routine merge。生效治理合同未来如需修改，必须独立受控步骤应用并停止，再由 fresh run 读取新合同。

NewEMaint 必须在已采纳的平台 pin 上判断是否有效，并单列相对最新平台的升级项。未重新验收的 source、lock 和制品不得仅为消除检查红项而改写。

## 风险与回滚约束

路线图修订可通过普通文档 revert 恢复；调度启动可停止新派发并保留子任务回执。已经创建的 Issue 不批量删除；重复项记录 duplicate-of 并按既有流程归并。现场失败、数据恢复与旧系统撤回属于项目合同，不由本路线图设计具体命令。

## 非目标

项目改名（包括展示名）、全平台参数化改造先行、通用部署引擎、Windows 方案实现、自动 merge/无人值守启用、实际公司部署以及本轮业务代码安全审计。

## 未决问题

本路线图交付无未决问题。后续决策按 plan 的决策表逐项产生具体候选并由所属合同处理，不阻止调度先做证据核对与合同草案。
