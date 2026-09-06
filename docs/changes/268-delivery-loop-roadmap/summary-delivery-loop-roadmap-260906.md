---
issue: 268
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/268
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 跨仓库交付路线图和调度合同规划，限定为文档与会话交接，不授权后续运行时变更。
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-delivery-loop-roadmap-260906.md
  spec: spec-delivery-loop-roadmap-260906.md
  plan: plan-delivery-loop-roadmap-260906.md
  verification: verification-delivery-loop-roadmap-260906.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/268-delivery-loop-roadmap
pr_url:
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

用户已确认：暂缓项目改名。先完成必要的平台流程收口，公司内网 Gitea 与 AISoftPlatform 自身部署是第一个真实交付闭环，验收通过后才能开展 NewEMaint 应用部署，最后依据实例完善通用 onboarding 和部署流程。建立独立调度任务跟踪执行，复杂任务使用 `gpt-5.6-sol` / `high`，简单任务使用 `gpt-5.6-terra` / `high`。

平台当前开发链已有实际 PR/CI 证据，交付链仍存在阶段依赖、首次安装、跨 Gitea 制品身份和已有实例接管的断点。NewEMaint 已有 DockerLab 历史验收和公司部分部署线索，当前公司现场的正式验收记录尚未闭合。

## 影响范围

本 Change 只增加本目录四份语义文档并交接调度任务。平台仓与 NewEMaint 的后续实施均另行立项或复用已有 Issue，不混入本分支。

路线图事实源为映射的 [plan](plan-delivery-loop-roadmap-260906.md)，授权范围为 [spec](spec-delivery-loop-roadmap-260906.md)。当前阶段台账由新调度任务维护；每项实际进展须链接到对应 Issue、PR、SHA 和验收记录。后续改变路线图合同本身时，走新的平台 Change 并引用本路线图。

本 Issue 完成表示路线图发布与调度建立，**不表示阶段 A/B/C/D 已完成**。它的最终 PR 不关闭 NewEMaint 的待办事项。

## 初步方案与建议

1. A：修复首发必需的流程矛盾和工具问题，将公司 SCM/平台自身交付与应用制品交付分开形成可执行路径。
2. B：先在公司内网完成已有 Gitea 实例接管/必要部署，以及 AISoftPlatform 仓库、治理、所需工具/runtime 的安装与平台自身闭环验收。
3. C：Gate B 通过后，再完成 NewEMaint 准入、非生产验证、应用发布和实际业务验收。
4. D：复盘 B/C 的实证，将通用规则收敛回已有 onboarding/runbook/模板/检查器，技术与环境细节仍归项目。

不以通用接入重构、routine merge、无人值守 Agent、Windows 参考实施或项目改名作为 NewEMaint 首发前置条件。

## 风险

- 将历史已测 release 与最新 main 混同，或将不同 source/installed/CI/live 证据互相代替。
- 把路线图方向确认扩大为具体安全决策、生产操作或最终 PR 授权。
- 为等待“完整平台”无限增加首发前置事项；或反向以首发为由跳过必要恢复、安全和现场验收。
- 调度任务跨仓实施、多个任务共写同一 Issue，导致提交和证据无法追溯。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 跨仓库交付路线图和调度合同规划，限定为文档与会话交接，不授权后续运行时变更。
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 平台治理与跨仓库调度规划按现行合同判为 complex，不因本次只写文档而降级。
- 基线评估及新任务创建包含一次性观察，不能只由 diff/CI 重放，因此要求 verification。
- 本次用户确认覆盖路线图制定和调度建立；各阶段的实际变更仍各有合同。

### 缺失的 acceptance criteria 或决策

本次路线图交付无阻塞决策。NewEMaint 发布范围、目标版本、现场窗口及身份策略等是后续阶段必须解决的决策，详见 plan，不假装已获批准。
