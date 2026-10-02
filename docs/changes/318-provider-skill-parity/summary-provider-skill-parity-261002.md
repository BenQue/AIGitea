---
issue: 318
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/318
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
reason: 恢复两端既有会话合同，但会修改 Agent 技能、共享治理指导与合同测试，命中强制 complex 的平台治理规则。
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-provider-skill-parity-261002.md
  spec: spec-provider-skill-parity-261002.md
  plan: plan-provider-skill-parity-261002.md
  verification: verification-provider-skill-parity-261002.md
override_reason: ''
status: approved
branch: change/318-provider-skill-parity
created: 2026-10-02
updated: 2026-10-02
pr_url:
---

## 问题/需求总结

用户要求审查近期 Claude Code 调整对 Codex 的影响，并确保后续项目能通过相同 AISoftPlatform 合同开发与维护。远端与本地 main 均为 `480d1d262c3e915f546049ede3f34ad7d3362f50`。本机 Codex 原有两项漂移、Claude 一项漂移已通过稳定源安装修齐，两端 `CLEAN`；Codex Matt v1.2.2 的 35 个技能快照校验 PASS。

用户已于 2026-10-02 明确回复“确认”，批准本 spec/plan 启动。T01 独立应用四份治理指导后停止（`dc77c93`）；T02 fresh run 读取更新规则，补强测试并验证（`b780eab`）。本地治理差异已修齐，当前准备唯一最终 PR candidate；尚未 push 或创建 PR。

## 影响范围

Codex `issue-session-flow`、`aisoft-platform`、两侧共享 onboarding reference、08 分册与现有会话合同测试。5 个明确目标文件，见 spec。CLAUDE 导入的 AGENTS 共享合同保持原样。

## 初步方案与建议

已恢复既有两确认点、projected 判级、exact merge/pinned 收尾、两条 backfill 路径，并补齐共享指导。12 个合同测试覆盖 27 个负向变异；targeted 38 与 C locale 完整 smoke 978 均 PASS；两侧临时安装 CLEAN、三份 references byte-identical。两工具共享行为语义，保留各自调用语法。

## 风险

这是 Agent 执行指导修订，必须 complex contract/start 确认。source/local/installed/live 分层验收；一侧真实项目验收不能替代另一侧。既有开放 #308/#316/#317 不在此 Issue 实现。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复两端既有会话合同，但会修改 Agent 技能、共享治理指导与合同测试，命中强制 complex 的平台治理规则。
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

- source 差异均来自当前仓库逐行比对，详见 verification 的行号与基线。
- 虽为恢复既有合同，Agent/平台治理为强制 complex；不是 small 文档例外。
- 采用默认 production route，四份语义角色显式映射；verification 保存安装前状态与 overlay 的先红后绿证据。

### 缺失的 acceptance criteria 或决策

验收标准已完整；用户已经明确确认本 spec/plan 启动，授权收据为 evidence/contract-start-authorization.json。最终 PR 提交仍未获确认。

## 本地结果与提交候选

- source T01：`dc77c93b3c92534b3f1e796dce896ea15fc43e56`，仅四份治理指导；已停止受控应用步骤。
- source T02：`b780eabb293fb000b36c0b7e01a74b44f3b2547d`，仅 SessionContractTests，类外 AST unchanged。
- source/local：修订、fresh read、targeted 38、C locale full smoke 978、静态/负向覆盖与 staged install 均 PASS。
- 判级：#318 `type/platform + complexity/complex`，verify 读回 `projected`，当前 lifecycle approved。
- Policy manual；最终 PR 提交尚未授权，进入 `AWAITING_PR_CONFIRMATION`。
- installed：本机稳定 480d1d2 在前次同步后 CLEAN；本 Issue 候选尚未全局安装，合并后 exact main 才安装/fresh adoption。
- remote PR/CI/merge、真实 provider matrix 与 deploy：NOT RUN。默认 UTF-8 fixture #319 FAIL 与既有 SHA 指导歧义 #320 独立记录。
