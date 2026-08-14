---
issue: 116
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/116
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 治理 manifest（host-access-broker.json）声明变更，触发平台治理强制 complex；范围为两个项目条目各加一行 #73 既有 schema 字段
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-remote-name-declarations-260813.md
  spec: spec-remote-name-declarations-260813.md
  plan: plan-remote-name-declarations-260813.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/116-remote-name-declarations
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/117
created: 2026-08-13
updated: 2026-08-13
---

## 问题/需求总结

三仓对齐 Issue 逐仓处理启动时，Mac broker adoption 闸门实测：hsdb 全 PASS，而
rsdesign-new 与 sfm-digital-board 的 `mac.git.bind`/`host.onboarding.check` 均
`BLOCKED_EXTERNAL`——两仓 Mac checkout 的 `origin` 是 GitHub（与 NewEMaint 同布局），
manifest 未声明 `git_remote_name`，broker 按默认 `origin` 解析导致 URL 不匹配。

## 影响范围

仅 `codex/config/host-access-broker.json` 两个项目条目各加一行
`"git_remote_name": "gitea"`（#73 既有 strict schema 字段，NewEMaint 先例）。不改
broker runtime、不改其他项目条目、不动业务仓库。rsdesign-new Mac checkout 已本地补加
`gitea` remote（指向 governance 派生 URL；GitHub `origin` 未触碰）。

## 初步方案与建议

按 #73 机制声明；合并后人工重装（Mac sudo + VM orb sudo），复跑两仓 adoption 闸门
验收 PASS。

## 风险

- 极低：纯声明，schema 已存在校验（contract.py strict 字段集）；错误声明会被
  fail-closed 拒绝而非静默放行。回滚 = revert 单 PR + 重装。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 治理 manifest（host-access-broker.json）声明变更，触发平台治理强制 complex；范围为两个项目条目各加一行 #73 既有 schema 字段
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 修改 `codex/config/*` 治理 manifest → 强制 complex（03 §2）；但无 runtime/schema
  变更，spec/plan 按最小形态。

### 缺失的 acceptance criteria 或决策

- 无。

## 状态记录

- 2026-08-13：Issue #116 建立；manifest 两行声明 + 文档完成；测试与 smoke 待跑后推送
  开 PR。合并后需人工重装两端并复跑 adoption 闸门（AC-3，本 PR 外验收）。
