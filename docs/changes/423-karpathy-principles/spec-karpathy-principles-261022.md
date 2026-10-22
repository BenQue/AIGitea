---
issue: 423
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/423
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/423-karpathy-principles
git_scope:
  - 08-双工具共存与实施.md
  - docs/changes/423-karpathy-principles/plan-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/proposals/engineering-principles.patch
  - docs/changes/423-karpathy-principles/spec-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/summary-karpathy-principles-261022.md
  - docs/changes/423-karpathy-principles/verification-karpathy-principles-261022.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/engineering-principles.md
  - skills/issue-session-flow/SKILL.md
  - usage/CONTRACT.md
  - usage/bundle.json
created: 2026-10-22
updated: 2026-10-22
---

# 研究与 Spec：Karpathy 工程原则的平台适配

## 目标与原因

交付编程思想的纲领性指导，减少 AI 擅自假设、过度设计、顺手改动和无效验证。原则正文不承载具体开发方案，不规定阶段、命令、工具、模型、任务拆分或固定检查表；本 Issue 的实施计划只说明如何交付这份指导文件。

## 上游研究与平台差距

2026-10-22 读取 [上游仓库](https://github.com/multica-ai/andrej-karpathy-skills)，固定 commit `2c606141936f1eeef17fa3043a72095b4765b9c2`。
已读 [SKILL.md](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md)、CLAUDE.md、EXAMPLES.md、Cursor rule 和 plugin.json。
它是社区整理的行为指南，plugin 版本字段为 1.0.0；不是执行引擎，也没有效果评测套件。README 与元数据声明 MIT，所读完整树未见独立 LICENSE 文件；本提案只自行表述思想，不 vendor 上游正文。

| 上游思想 | 平台现有覆盖 | 本次补强 |
|---|---|---|
| 编码前思考 | triage、spec 的未决问题、approved | 先查事实，区分重要假设与人工决策；已授权低风险细节不反复提问 |
| 简单优先 | 合同范围、ADR D9 治理预算 | 功能/依赖/配置/抽象须有当前需求依据，保留安全可靠性 |
| 精准改动 | 单写者、只提交当前任务文件 | 检查每个改动块的必要性，完整修复，禁止顺手整理 |
| 目标驱动 | AC、Txx、验证、NOT RUN | 验证必须能区分目标的正确与错误行为，按风险取适当证据 |

不能机械照抄的例子：EXAMPLES.md 的排序测试只检查 score，没有断言同分元素顺序，不能证明它声称的 tie-break 修复；“无效数据出现后才加验证”的示例建议不能替代真实输入边界分析。
这说明要采用原则并校验其适用条件，不能把示例代码当平台验收标准。

## 方案与决策

采用“现有共享技能 + 一份参考文档”，复用 `skills.manifest` 与 usage bundle 的三端落点。不增新技能名、插件、vendor pin 或安装器。
拒绝全局安装上游插件（多一份行为来源，且只解决部分工具）与把全文追加到 AGENTS.md（违反精简和单一来源目标）。
具体候选见 [治理 patch](proposals/engineering-principles.patch)，基线 `58b06590c1539ffdeb8af9e0d5a95b78090edb6b`；patch 使用零上下文格式（应用/反向检查加 `--unidiff-zero`），已按负责人本轮的纲领性定位收紧，仍只改六份治理文字；发布登记由 T01 用既有工具生成。

## Acceptance criteria

- [ ] AC-1：一份纲领性原则被三个技能入口与使用合同引用，正文不变成开发步骤或固定检查表；隔离发布包导出三端技能/reference，符合各自 manifest 声明。
- [ ] AC-2：先查事实、重要假设显式；合同内低风险可逆决定自主推进，只有实质决策歧义阻塞依赖操作，不增加确认点。
- [ ] AC-3：不为假想需求增加复杂度，不删必要安全/可靠性校验；每处改动关联验收或必要的兼容/安全要求，同时完整修复。
- [ ] AC-4：表达可验证目标、可靠缺陷证据、验证判别力与风险匹配的原则；不强制所有任务采用固定测试顺序，既有硬门与停止规则保留。
- [ ] AC-5：下列六场景桌面评审和既有文档、技能、发布包检查及 smoke 通过；静态或桌面结果不冒充真实模型效果。
- [ ] AC-6：固定思想来源，发布历史只追加；治理受控应用后停止，fresh run 重读并验证，未参与实现的另一提供者独立审查。

## 六场景与反例

| 场景 | 预期行为 | 必须拒绝的反例 |
|---|---|---|
| 已批准的一行文案改动 | 修改并做适当差异检查 | 追加多轮确认或为文案新增运行时测试 |
| 依赖版本可从 lock 查询 | 自主只读核实再决定 | 猜版本或把查询问题交给用户 |
| 导出数据的范围/敏感字段未定 | 先澄清关键合同，只继续独立工作 | 擅自导出全部字段 |
| 单一计算需求 | 使用已有模式完成当前功能 | 预建策略框架、插件系统、无需求的配置 |
| 修复空输入错误 | 复现、完整修复并针对性验证 | 夹带全文件格式化或只掩盖报错 |
| 外部输入或权限失败 | 保留必要校验，负例确能失败 | 用“更简单”删除校验，或断言无关条件冒充通过 |

## 精确授权目标（确认合同后生效）

- `skills/aisoft-platform/references/engineering-principles.md`、`skills/aisoft-platform/SKILL.md`
- `skills/aisoft-matt-workflow/SKILL.md`、`skills/issue-session-flow/SKILL.md`
- `usage/CONTRACT.md`、`08-双工具共存与实施.md`、`usage/bundle.json`
- `docs/changes/423-karpathy-principles/`；按 03 §7 维护 `docs/governance/review-evidence-index.md` 的本 Issue 审议记录。本批不登记路线图，精确路径以 front matter 的 git_scope 为准。

## 接口、数据与兼容性影响

无 API/schema/runtime/依赖变化。发布包新增 minor 版本（当前 1.13.0，候选 1.14.0；如 main 前进按既有 release 规则顺延），不修改历史 release。
既有项目继续 pin 旧包；三端导出能力不等于全局安装或真实 provider-session 行为改善。本 Issue 不产生项目采用/E2E 事件，不改已有 E2E 行。

## 风险与回滚约束

未应用提案可丢弃；source 合并后经新 Issue/PR revert 本批治理文字并追加修正版发布包，不重写历史版本。项目 pin 不自动前移。

## 非目标

不改根 AGENTS.md/CLAUDE.md、路由、模板、runtime/test 代码、CI/安装/部署脚本、broker/权限/凭据、外部技能原文；不安装、部署、自动合并或更新项目。

## 未决问题

无。2026-10-22 负责人确认：“确认，按 #423 的方案启动实施”，并明确这是纲领性的编程思想指导，完成后须在 Claude Code 审议。该补充收紧文案定位，不增加开发方法或 runtime 范围。
