---
issue: 320
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/320
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修正 Agent 平台治理指导的 push SHA 比较锚歧义，强制 complex 且 manual
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-push-head-anchor-261002.md
  spec: spec-push-head-anchor-261002.md
  plan: plan-push-head-anchor-261002.md
  verification: verification-push-head-anchor-261002.md
depends_on: []
status: pr-open
branch: change/320-push-head-anchor
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/322
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

首次 push 与合法 PR summary 回填、范围内 CI 修复的后续 push 共用旧比较锚，指导有歧义；未证明 runtime 故障。

## 影响范围

只修 03、08、Codex/Claude issue-session-flow 与两侧复合 aisoft-platform PR 路径文字。

## 初步方案与建议

首次 push 比对确认候选；后续 push 比对该次 fresh 验证 exact head。只改治理合同的独立步骤应用后停止，fresh run 重读并验证。

## 风险

- 合法新 head 不能绕过 fresh diff/合同验证；任何非本会话改写或 head 不匹配仍停止。
- source/local 场景验证不证明真实模型、installed 或 remote 事件成功。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修正 Agent 平台治理指导的 push SHA 比较锚歧义，强制 complex 且 manual
risk_flags:
  - agent-governance
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

- Issue #320 live read：open/needs-analysis，comments=[]，没有合同批准；open PR=[]。
- fresh broker git.fetch.main 后 origin/main=5c2cd726c9aeaee9d17541d8feb049e33881bbac，含 #318 PR #321 合并。
- 03 §1、08 §3 与两侧 session skill 沿用确认点2旧 SHA；两侧复合 skill 明确合法 summary-only 回填与追加 push。
- 无 .out-of-scope 记录；全文搜索未找到区分首次与后续比较锚的已有等价指导。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 会话与授权

- session：`01a0fc7b-c01c-71f2-954c-6a87dabb4a87`；worktree：`/private/tmp/issue-320-push-head-anchor`。
- Policy：manual；用户已确认合同/启动；PR/push/merge/install/deploy 均未授权。
- 依赖：无；#318 已在 main，仅作事实基线，不代改其合同。
- 本轮按已批准合同执行独立 T01，仅应用治理源并停止；T02 留待 fresh run。

## 最终 PR 候选（提交前验证记录）

提交前状态 `AWAITING_PR_CONFIRMATION`；Policy manual；T01/T02 source/local验证完成。首次push仍以最终候选fresh验证exact head为锚；后续summary-only回填和范围内CI修复刷新该次验证head并读回。17合成场景、38定向、完整smoke 978 runtime tests PASS，双轴review各0发现；首次sandbox失败保留。Classification actual verify projected: platform/complex。用户现已确认提交，唯一PR #322已创建；真实首次/summary-only后续push的pushed_head均与各自验证锚相同。required CI正在运行，尚不写PASS；无安装/部署授权，canonical triage projection GAP保留。
