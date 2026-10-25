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
updated: 2026-10-25
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
status: approved
pr_url: ''
---

# Summary：全新项目需求发现与滚动阶段规划

## 请求与当前授权

负责人于 2026-10-24 明确要求建立 complex Issue、完善 spec/plan 供确认，并自行交 Claude 侧结合内部材料深入评估。已认可的方向是：保留 Matt 与现有路线图为基线，按项目情况选择合适技能，**当前阶段详细，下一阶段有轮廓，远期保留方向**。

负责人于 2026-10-25 明确确认本票修订合同，授权提交修订、同步 Issue 并读回核对，设为 approved 后启动 T01；治理文件提交后立即停止，由 fresh run 在同一合同授权内继续。确认点 2 前不 push、不建 PR。修订原固定为 `a847e70889e0abcd3cd565620e38e13372c2eec5`，获准恢复后对应 `561f87cda4ac44c2794b494dd15c56a9dbf3a2dd`（diff 逐字相同），完整正文同步后逐字读回一致，远端与本地均已投影 approved；这项授权不包含安装新技能包、合并或部署。

## 范围与方案

- 为 0→1 项目补充问题发现、最小项目简报、必要全局边界、浅层路线图、当前阶段展开、阶段结果核验与滚动调整。
- 方法单一来源放在 `skills/aisoft-platform/references/greenfield-planning.md`，内嵌最小模板；现有入口只加必要指针与职责说明。
- 项目规划资料归项目仓；Issue 仍是交付追踪与授权主键，Txx 仍是 Issue 内任务身份。阶段记录不复制 Issue 合同，不新增状态机或第三确认点。
- Matt 负责需求澄清与 Issue 规格/任务拆解；`issue-session-flow` 继续承担多 Issue 路线图、派单与收口；执行与完成核验按现行 provider 路由。
- 本票仅交付通用规则、文档衔接和版本化使用发布包；Spec Kit、GSD、gstack 仅为以后按能力缺口评估的候选，本票不安装、调用、pin、vendor 或接入。

## 归属与基线

- exact Issue：`admin/aisoft-platform#430`；exact branch：`change/430-greenfield-planning`。
- worktree：`/private/tmp/issue-430-greenfield-planning`。
- 唯一 writer session：`01a16e1b-1085-7712-b5a8-c100d9f74629`。
- 2026-10-24 broker fresh-fetch 后基线：`08aac8d5b9af4d334c53bcf34029870f09e50bf0`。
- #429 与 #417 不作为本票依赖，也不修改其文件、分支或 worktree。T01 前 broker fresh-fetch main 得到 `2454b0c2519b0145aca4f1d289efb09ed8ac46d8`（RELEASE_BASE），最新发布包仍为 1.16.0，本批 NEXT_MINOR 固定为 1.17.0，RELEASE_DATE 为 2026-10-25。
- fresh main 相对原始基线只增加 #429 的外部技能版本核对代码/测试、其合同和审查索引；未改变 T01 方法、路由或发布包输入，但完整 smoke 的来源检查会拒绝落后 main 的分支；先前“可留待 T03 整合”的判断已被实际检查否定。负责人已明确允许恢复：三笔未推送提交已重放到已核对 main，diff 逐字一致；当前 change_base/RELEASE_BASE 均为该 main，已重新建立 T01 回执，原回执与首次失败作为历史保留。新旧 SHA 对应表见 verification。

## 实施分段与停点

T01、T02、T03 均已完成。T01 交付通用方法、入口与 1.17.0 发布包，治理提交后停止；T02 经 fresh run 完成 S1–S11、三端隔离导出、完整 smoke 和两轴审查。原基线恢复与每票开始/完成回执详见 verification，原始合同语义和 writer 保持不变。

Claude Opus 5.5 / high 对 R1 候选给出 PASS、2 条 Low；范围内修正入口写入归属与过时证据索引后，1.17.0 同版本重发，746 项 runtime 测试及完整 smoke、12 份三端导出和 42 个链接均通过。治理修复 `a6d0a733407815c98fda765cd36045a0ee14a782` 后再次停止；本轮 fresh run 复审得到两轴及 Claude R2 全部 PASS，F1/F2 fixed，residual/new 均 0。

当前只回填完成证据和审查索引，不再修改发布成员。最终仅证据 HEAD 的只读复核回执归同一 Issue，完成核对后给出 `AWAITING_PR_CONFIRMATION` 候选。确认点 2 前不 push、不建 PR，之后仍由人合并。真实安装、项目采用、CI、部署与 UAT 均未执行；不把 source/local 与隔离导出结果提升为这些结果。

## AI 判级与路由

新增平台方法和 Agent 行为约束，属于 `platform / complex / add`；证据充分，不使用 small。实施 provider 是 `codex`，命中现行 R3 + G1，具体路由见 front matter。

Claude 承担负责人组织的合同评估与最终独立审查，实施 provider 仍为 Codex。若后来明确由 Claude 实施，按同一 route policy 显式重新解析并记录 provider 差异，最终审查改由未参与实现的另一方承担；不静默沿用 Codex 的技能展开值。

## 评估与确认

Claude 已完成两轮内部评估。2026-10-25 负责人要求按评估意见直接修订，Claude 会话据此在本 worktree 起草修订（只改本票四份文档，owner marker 与实施 provider 不变），交回 owner 会话审阅；修订映射见 verification「合同修订」行。负责人随后明确选择补跑 grill-me，并要求已有结论直接沿用、只问修订后尚未明确的决策。owner 会话已按平台 pin 的 grill-me → grilling 核对决策树，新增待决项为 0；来源和逐项沿用记录见 verification「grill-me 补跑记录」。没有豁免或改写 route.skills；负责人现已最终确认完整合同。

负责人确认的是本票完整 spec、plan 和 exact scope（13 个文件、12 条 AC、T01–T03）。Codex 先固定修订并回填 Issue，fresh-read 一致后设置 approved，再准备 T01。不将此前通用建议的模型评议当成本票内部合同审查或最终实现审查通过证据。
