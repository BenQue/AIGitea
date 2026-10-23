---
issue: 427
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/427
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
  - cross-module
depends_on: []
branch: change/427-workflow-route-review
created: 2026-10-23
updated: 2026-10-23
reason: 修复共享路由和审查范围合同并补直接必要的执行适配，涉及共享核心与 Agent 治理
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-workflow-route-review-261023.md
  spec: spec-workflow-route-review-261023.md
  plan: plan-workflow-route-review-261023.md
  verification: verification-workflow-route-review-261023.md
route_provider: codex
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, implement, issue-session-flow
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
override_reason: '用户要求保持现有 provider 默认；F1 修复前本票显式采用既有 Codex 默认 implement 与 issue-session-flow，替换 R3 字面列出的 executing-plans 与 verification-before-completion；其余路由格不变，随本票确认点 1 一并呈交'
status: approved
pr_url:
---

# Summary：F1/F6 与必要流程适配

## 问题/需求总结

用户于 2026-10-23 明确确认 #427 合同并启动 T01：保持现有技能默认分工和两个确认点；T01 提交后停止并交接 fresh run，后续在本次批准范围内继续，不重复请求启动确认。批准对象是准备提交 `5b16b9a706e9e79fc69dff27a119b9b4ca351954` 中的四份合同文档。

F1：路由表 R2–R5 的全局技能义务与 provider 默认不一致。F6：Matt implement 先 review 后 commit，而 code-review 读取提交 diff，可能漏掉本票未提交实现。必要关联范围仅 F2 的 Txx/SP 执行兼容、F3 的局部与整批审查区分、F5 的执行与 finding 证据。F4 保持禁用原版 implement-spec 写入编排。

## 影响范围

- exact Issue：`admin/aisoft-platform#427`；exact branch：`change/427-workflow-route-review`。
- worktree：`/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review`；唯一 writer session：`01a16423-3e17-73b0-a723-76adc045218e`。
- fresh source base / change_base：`dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`（2026-10-23 broker fetch/readback）；主仓 main 干净。
- 只改平台共同规则、窄范围本地适配及其 fixture/发行记录；精确路径在 spec.git_scope。无业务项目写入、全局安装、部署或数据迁移。
- 保持 Codex complex → Matt、Claude/Cursor complex → SP；small → small-direct + 针对核验。production/development 文档要求、风险判级、R1–R5 顺序、两确认点、人合并均不改变。

## 初步方案与建议

单一规则源导出具体技能；新合同显式 provider；Txx 为唯一任务身份，Task N 是机器生成执行视图；ticket 开始前固定 BASE，本地候选提交后固定 HEAD 并查遗漏；审查与修复均绑定实际范围。复用现有 summary/plan/verification，不维护第二份人工计划或审查数据库。

T01 治理受控应用后停止；fresh run 重读相同批准合同再执行 T02–T05，不另加人工确认。T02 路由、T03 Txx/frontier/恢复、T04 F6、T05 发布一致性与验证，详见映射 plan。

本票执行 provider 为 Codex。上方 route 为针对已知 F1 的显式、可审核映射，理由见 override_reason，不把 R3 字面义务与 Codex 默认强行叠加。后续实现用的模型按现有 frontier/max 档位；最终独立评议延续用户要求，优先 Claude Code Fable 5 / high，实际型号/配置/回执写 verification。模型不可用时不得假称已经完成该评议。

## 风险

- 不把目录/字符串检查当 provider 实际执行；Codex 会话可见 SP 6.4.2 与平台 v7.0.0 分开验明。
- 文件路径只帮助判范围，不证明语义归属；机器候选校验不得声称发现全部未保存或 ignored 成果。
- 治理更新后同一会话不能继续按自己新写的规则执行 runtime。
- 当前 typed broker 未暴露 triage category/state mutation；不能借 lifecycle/extension 或直连 API 伪造投影。语义 triage 结论记录为 bug / ready-for-agent，标签投影实际状态在 verification 记录；不增设批准、不扩 broker 权限。
- 第一阶段只证明 source/local 兼容；真实项目试点、安装与默认切换不在本票。不得将 NOT RUN 写为 PASS。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复共享路由和审查范围合同并补直接必要的执行适配，涉及共享核心与 Agent 治理
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
  - cross-module
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: '用户要求保持现有 provider 默认；F1 修复前本票显式采用既有 Codex 默认 implement 与 issue-session-flow，替换 R3 字面列出的 executing-plans 与 verification-before-completion；其余路由格不变，随本票确认点 1 一并呈交'
```

### 判级证据

- route-policy R2–R5 与默认入口表；现 contract.validate_route 只校验键/闭集/语法，不校验 provider 技能语义。
- Matt v1.3.1 implement 第 13/15 行与 code-review 第 21/23 行：审查顺序、提交 diff、空 diff 失败。
- SP v7 task-start 调用 task-brief 只识 Task N；task-done 的 complete 不等于平台 AC/依赖/HEAD 证明。
- 新能力和共享治理修正强制 complex；不能因修改量小降级。
- 当前 open Issue 查重仅 #417（凭据轮换），无本需求重复票；不存在 .out-of-scope 文件。

### 缺失的 acceptance criteria 或决策

无方向性未决；AC-1–AC-8 与技术选择已写入 spec。确认点 1 已通过；triage 标签投影缺口如实记录，不作为新增人确认点。

## 来源与状态

来源是用户认可的最终方案与当前源码核实，合同中已自包含全部实施决定，不依赖外部研究附件才能执行。方案评议：Claude Code `claude-fable-5 --effort high`，session `2dab0571-22c1-466e-84a6-b1ca2540e121`，SUPPORT。被审候选 SHA256：`edcc92c21327a9a2cc9c54d908570312b33960cd8a4115c0ade3ef2370f61a2c`。这是研究方案评议，不是 #427 实现审查。

2026-10-23：确认点 1 已通过；T01 已独立治理提交并 STOP，用户明确 fresh run 接续。T02–T04 已完成实现与固定 HEAD 双轴复核；T05 正在完成 1.16.0 源分发、完整 smoke 与 Claude Code Fable 5/high 终审。
最终仍停在 AWAITING_PR_CONFIRMATION；本次不 push/PR/merge，不安装或部署。逐票 BASE、原始证据与 findings 见 verification。

当前执行状态：`IMPLEMENTING`（T05）。用户已批准唯一一行旧入口 fixture 范围补正（35→36项），正在沿用原批准完成验证与指定 Claude 终审，尚未到确认点2。
