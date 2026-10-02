---
issue: 319
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/319
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 registry 故障时非零退出及正确诊断的既有合同；CI 变更触发强制 complex
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-registry-utf8-exit-261002.md
  spec: spec-registry-utf8-exit-261002.md
  plan: plan-registry-utf8-exit-261002.md
  verification: verification-registry-utf8-exit-261002.md
depends_on: []
status: spec-drafting
branch: change/319-registry-utf8-exit
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

macOS Bash 3.2 UTF-8 下中文标点读入变量名，nounset 与 EXIT trap 使 registry 停止时误报退出 0。

## 影响范围

仅 registry-preflight 参考脚本、对应 HTTP fixture 回归、本 Issue 合同及证据。

## 初步方案与建议

明确中文标点前的变量边界，复用 HTTP fixture，验证真实失败诊断、退出码和绿—红—绿。合同步骤独立停止，获批准后 fresh run 重读才能实施。

## 风险

- CI 变更强制 complex/manual。
- LC_ALL=C 不得替代 UTF-8 验收；Bash 3.2 nounset trap 保存 $? 仍可能为 0。
- macOS 验收不能由 Linux required CI 重放，需要 verification。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 registry 故障时非零退出及正确诊断的既有合同；CI 变更触发强制 complex
risk_flags:
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- fresh origin/main 5c2cd726c9aeaee9d17541d8feb049e33881bbac 仍含 4 处中文标点相邻变量引用。
- macOS Bash 3.2.57 C.UTF-8/en_US.UTF-8/zh_CN.UTF-8：健康 0，停止 fixture 后错误退出 0，stderr unbound variable；完整 fixture 在停止处失败。
- Linux Bash 5.3.9 C.UTF-8 改前 fixture PASS。
- Issue open/needs-analysis，无评论与开放 PR；main 禁 direct/force push，required CI 为 CI / verify (pull_request)。
- 已搜索现有脚本/测试/README/06/Git history，无已实施修复；无对应 CONTEXT.md、ADR 或 .out-of-scope 文件。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 会话、依赖与确认

- session: `01a0fc7b-adfe-72e3-ae7a-cf96038acc23`；worktree: `/private/tmp/issue-319-registry-utf8-exit`，已 claim。
- Policy: `manual`；depends_on: []（#318 是发现来源，非阻塞依赖）。
- `AWAITING_CONTRACT_CONFIRMATION`：未批准、未实施、未 push/PR/安装/部署。
- 本轮只准备合同/基线并停止；获人确认后只记录 approved 合同并停止；下一 fresh run 重读后实施。
- Matt triage 建议 `bug / ready-for-agent`。现有 broker 表没有 triage 投影 typed operation；extension.set 仅允许 area/、priority/。live triage 标签为 GAP，仅评论记录建议，不绕过 broker。
