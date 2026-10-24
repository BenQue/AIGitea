---
issue: 430
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/430
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/430-greenfield-planning
created: 2026-10-24
updated: 2026-10-24
reason: 新增全新项目需求发现与滚动阶段规划的通用方法并衔接现有 Agent 治理入口
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-greenfield-planning-261024.md
  spec: spec-greenfield-planning-261024.md
  plan: plan-greenfield-planning-261024.md
  verification: verification-greenfield-planning-261024.md
route_provider: codex
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: grill-me, to-spec, to-tickets, implement, issue-session-flow
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
override_reason: ''
status: spec-drafting
pr_url: ''
---

# Summary：全新项目需求发现与滚动阶段规划

## 请求与当前授权

负责人于 2026-10-24 明确要求建立 complex Issue、完善 spec/plan 供确认，并自行交 Claude 侧结合内部材料深入评估。已认可的方向是：保留 Matt 与现有路线图为基线，按项目情况选择合适技能，**当前阶段详细，下一阶段有轮廓，远期保留方向**。

本轮授权仅为合同准备与 Issue 内容发布。尚未达到 `approved`，没有启动实施，没有安装或接入新技能包。路线图方向获得认可不等于本票实施合同已经批准。用户送审 Claude 的结果也不自动授予实施、最终 PR、合并或部署权限。

## 范围与方案

- 为 0→1 项目补充问题发现、最小项目简报、必要全局边界、浅层路线图、当前阶段展开、阶段结果核验与滚动调整。
- 方法单一来源拟放在 `skills/aisoft-platform/references/greenfield-planning.md`，内嵌最小模板；现有入口只加必要指针与职责说明。
- 项目规划资料归项目仓；Issue 仍是交付追踪与授权主键，Txx 仍是 Issue 内任务身份。阶段记录不复制 Issue 合同，不新增状态机或第三确认点。
- Matt 负责需求澄清与 Issue 规格/任务拆解；`issue-session-flow` 继续承担多 Issue 路线图、派单与收口；执行与完成核验按现行 provider 路由。
- 本票未来实施仅交付通用规则、文档衔接和版本化使用发布包；Spec Kit、GSD、gstack 仅为以后按能力缺口评估的候选，本票不安装、调用、pin、vendor 或接入。

## 归属与基线

- exact Issue：`admin/aisoft-platform#430`；exact branch：`change/430-greenfield-planning`。
- worktree：`/private/tmp/issue-430-greenfield-planning`。
- 唯一 writer session：`01a16e1b-1085-7712-b5a8-c100d9f74629`。
- 2026-10-24 broker fresh-fetch 后基线：`08aac8d5b9af4d334c53bcf34029870f09e50bf0`。
- #429 与 #417 是独立在途事项，不作为依赖，也不修改其文件、分支或 worktree。未来实施前重新读取 main 和使用发布包版本，避免版本号冲突。

## 实施分段与停点

合同拟定三个任务：T01 受控方法、入口与发布包变更；T02 fresh run 场景核验与隔离分发验证；T03 实际实现的独立审查与最终候选整理。全部尚未启动。

T01 涉及治理技能，须独立 commit 后 STOP，由 fresh run 重读获批合同和治理内容再继续。T02/T03 不增加运行时代码。最终 PR 仍在确认点 2 之前停止，之后由人合并。源码、隔离导出、真实安装、项目采用、部署与业务验收分别记录。

## AI 判级与路由

新增平台方法和 Agent 行为约束，属于 `platform / complex / add`；证据充分，不使用 small。当前合同准备 provider 是 `codex`，命中现行 R3 + G1，具体路由见 front matter。

Claude 本次是负责人组织的合同评估方，不因此更换实施 provider。若后来明确由 Claude 实施，按同一 route policy 显式重新解析并记录 provider 差异，最终审查改由未参与实现的另一方承担；不静默沿用 Codex 的技能展开值。

## 评估与待确认

当前没有需要重新询问的产品方向选择。Claude 可按 spec 的内部材料清单检查边界、可执行性和最小范围；发现真实缺口时回填本票合同，保留版本变化依据。

负责人确认的是本票完整 spec、plan 和 exact scope；确认前维持 `spec-drafting`。不将此前通用建议的模型评议当成本票内部合同审查或最终实现审查通过证据。
