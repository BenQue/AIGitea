---
issue: 106
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/106
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 Agent 行为（aisoft-project-align 对齐入口）与平台治理工具（aisoft-project-check 确定性检查器），属于 Agent/平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-behavior
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-project-align-capability-260812.md
  spec: spec-project-align-capability-260812.md
  plan: plan-project-align-capability-260812.md
confidence: high
override_reason: ''
depends_on: []
status: spec-review
branch: change/106-project-align-capability
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

用户 2026-08-12 决策：初始化新项目与更新已接入项目是同一操作——「把项目对齐到平台
当前合同」，应做成一个幂等能力而非两个技能。当前 onboarding-runbook 覆盖首次接入，
存量仓库回补靠人工记忆逐项核对；平台合同演进（#75 命名、#91 指针、#87 技能纳管）后
没有确定性手段回答「某项目是否仍与当前合同对齐」。

## 影响范围

仅平台仓库：复合技能 `aisoft-platform` 新增共享 reference（对齐 checklist 入口）、两侧
SKILL.md 入口指针、`codex/tools/` 新增只读检查器与配套测试、runbook 增加「初始化=对齐」
声明。不修改任何业务仓库、平台 AGENTS.md、broker、labels/governance manifest、CI。

## 初步方案与建议

1. 对齐入口：`skill-for-codex/references/project-align.md` 共享 reference，定义幂等对齐
   语义（核对→缺口走该仓独立 Issue/小 PR→复检至全 PASS；已对齐仓库重跑为 no-op）。
   checklist 每项只指向 runbook 章节、`templates/` 路径或工具命令，不复制合同正文。
   Claude 侧安装与 check-drift 按既有 references/*.md 迭代自动覆盖。
2. 检查器：`codex/tools/aisoft-project-check.sh`，六项检查（指针节、语义模板、
   architecture lock、24 标签读回、CI context、delivery profile 声明），逐项
   `PASS:`/`GAP:`/`SKIP:` 输出，退出码可 gate；本地检查零网络零凭据，远程读回仅在
   显式提供 `AGENT_ENV_FILE` 时执行（复用 sync-gitea-labels.sh 凭据模式）。
3. 顺序（Issue 既定）：本变更先固化 spec/plan 与 checklist 草案；NewEMaint 人工对齐
   （NewEMaint 侧独立 Issue）验证 checklist 后，反馈回灌再实施技能入口与检查器
   （实现可派 Codex，#101 已关闭、前置解除）。

## 风险

- checklist 与 runbook 语义漂移——以「只指向不复制」原则约束，测试断言 reference 不含
  合同正文串。
- 指针节比对语义过严或过松——以 `templates/project/AGENTS.md` 模板注释为准（前两节
  逐字节一致、后两节在位），NewEMaint 人工对齐负责验证该语义并回灌。
- 全部为新增/文档型变更，单 PR revert 即可回滚；检查器只读，无远程 mutation。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 Agent 行为（aisoft-project-align 对齐入口）与平台治理工具（aisoft-project-check 确定性检查器），属于 Agent/平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-behavior
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- Issue 明确预期 complex/platform；范围为新增技能入口 + 平台检查器，触发「Agent 或
  平台治理变更一律 complex」强制规则（AGENTS.md 强制风险规则、03 §2）。
- 修改治理文件（技能源、runbook）需 complex spec 显式授权；spec §治理授权列出精确
  文件清单。

### 缺失的 acceptance criteria 或决策

- NewEMaint 人工对齐验证（NewEMaint 侧独立 Issue，尚未建）是 T03/T04 实施前置；其
  反馈可能修订 checklist 措辞与 pointer-sections 比对语义，但不改变本 spec 的能力边界。

## 状态记录

- 2026-08-12：判级评论已发（Issue #106 comment 2991）；spec/plan 完成，进入
  spec-review，待人复核后按 plan 推进 T02 外部验证与 T03/T04 实施。标签投影
  （complexity/complex + type/platform + spec-drafting）属 controller/projector 职责，
  Mac 会话 broker 无标签 typed 操作，未在本会话执行。
- 2026-08-12（晚）：人工复核 spec 通过；NewEMaint #65/PR #66 人工合并，T02 外部闸门
  清除。实战反馈回灌：pointer-sections 放宽后两节标题要求（参照实现纯新增结构获
  合并背书）、labels-readback 增加受管命名空间冲突检测（实测 12 个 manifest 外标签、
  其中 4 个冲突）、delivery-profile 改为事实命中型检查。T01/T03/T04 待实施
  （检查器实现可派 Codex）。
