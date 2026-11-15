---
issue: 448
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/448
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 终态生命周期写入改为同时清除 triage 状态标签，改变既有 broker 操作的可观察语义，触及两种访问来源共用的 broker 核心与发布包成员
risk_flags:
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-terminal-clears-triage-state-261114.md
  spec: spec-terminal-clears-triage-state-261114.md
  plan: plan-terminal-clears-triage-state-261114.md
  verification: verification-terminal-clears-triage-state-261114.md
route_provider: claude
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/448-terminal-clears-triage-state
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/449
created: 2026-11-14
updated: 2026-11-15
---

## 索引

- Issue：http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/448
- 状态：见 front matter `status`；PR：见 `pr_url`
- 文档：见 front matter `documents`。需求、范围、验收与风险只写在 spec，本文件不重复。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 终态生命周期写入改为同时清除 triage 状态标签，改变既有 broker 操作的可观察语义，触及两种访问来源共用的 broker 核心与发布包成员
risk_flags:
  - shared-core
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `_replace_issue_label_dimensions` 只替换调用方点名的维度，其余标签按 id 原样带过；三个写者（lifecycle、classify、extension）都不含 `triage/*`，`triage/needs-triage` 只在 `gitea.issue.create --entry-label` 写入一次。
- 修法改变 `gitea.issue.labels.set` 写终态时的可观察结果（多移除一组标签、遇 `triage/wontfix` 拒写），是 `contract_effect: change`，强制 complex。
- `ProjectSourceBroker` 继承 `HostAccessBroker`，broker.py 是使用发布包 exact 成员：共享核心与项目侧外部契约同时受影响。
- 存量清理的读回与 installed 层重装证据不能由 diff review 与 required CI 重放，故声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无；四个待定问题的推荐答案写在 spec「方案与决策」，经确认点 1 定案。
