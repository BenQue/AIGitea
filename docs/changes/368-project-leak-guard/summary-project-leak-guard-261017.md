---
issue: 368
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/368
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增smoke硬门检查项目名渗入，属于CI与平台治理变更
risk_flags:
  - ci
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-project-leak-guard-261017.md
  spec: spec-project-leak-guard-261017.md
  plan: plan-project-leak-guard-261017.md
confidence: high
override_reason: ''
depends_on:
  - 366
status: analyzed
branch: change/368-project-leak-guard
pr_url:
created: 2026-10-17
updated: 2026-10-17
---

## 问题/需求总结

整改路线 R2。ADR 0001 D3 规定项目名只能出现在白名单位置，但没有机器检查；现存 37 个文件 222 处命中。本票新增棘轮式守卫：已有命中记入基线，新增渗入让 smoke 失败。

## 影响范围

新增检查器、基线、单元测试，smoke 增加一行调用；更新整改路线。不改 runtime 产品代码。

## 初步方案与建议

见 mapped spec。

## 风险

误报会挡住正常 PR；白名单与匹配规则写在 spec 中并由单测覆盖。基线次数是跨 PR 共享状态，只在命中增加时失败，减少时不失败，降低并行冲突。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增smoke硬门检查项目名渗入，属于CI与平台治理变更
risk_flags:
  - ci
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 新增 smoke 硬门属于 CI 变更，强制 complex。
- 证据可由 diff review 与 required CI 复现，不声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。
