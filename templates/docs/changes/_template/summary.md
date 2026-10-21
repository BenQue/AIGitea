---
issue: ISSUE_NUMBER
gitea_url: ISSUE_URL
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: EFFECTIVE_COMPLEXITY
contract_effect: CONTRACT_EFFECT
reason: CLASSIFICATION_REASON
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-SHORT-SLUG-YYMMDD.md
route:
  process: ROUTE_PROCESS
  tier: ROUTE_TIER
  effort: ROUTE_EFFORT
  skills: ROUTE_SKILLS
  method: ROUTE_METHOD
  verify: ROUTE_VERIFY
  review: ROUTE_REVIEW
  confirm: 2
confidence: CONFIDENCE
override_reason: ''
depends_on: []
status: analyzed
branch: change/ISSUE_NUMBER-SHORT-SLUG
pr_url:
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

<!-- WRAPPER_CONDITIONAL:
When assessed_complexity == needs-human-decision, delete every
`effective_complexity:` key from both the front matter and the `## AI 判级`
YAML block before writing the document. Otherwise require exactly one safe
value: small or complex. Do not leave an empty key or placeholder behind.
-->

## 问题/需求总结

<!-- depends_on: a bare number always means an Issue in this repository. A
cross-repository dependency may only use a reference that the platform governance
manifest authorizes for this repository; never substitute a foreign bare number or
clear a dependency to bypass a gate. -->

## 影响范围

## 初步方案与建议

## 风险

## AI 判级

```yaml
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: EFFECTIVE_COMPLEXITY
contract_effect: CONTRACT_EFFECT
reason: CLASSIFICATION_REASON
risk_flags: []
required_docs:
  - summary
confidence: CONFIDENCE
override_reason: ''
```

### 判级证据

- CLASSIFICATION_EVIDENCE

### 缺失的 acceptance criteria 或决策

- 无；如有则逐项列出。

`## AI 判级` YAML 使用 analyzer 的唯一字段集合和顺序。
`required_docs` 使用语义角色：`small` 和 unresolved 只包含 `summary`；
`complex` 必须依次包含 `summary`、`spec`、`plan`；当本次变更的验收证据不能由
diff review 与 required CI 复现时，再追加 `verification`（判据见 `03` §3
「何时声明 `verification`」）。追加它表示这次变更**欠一份验证记录**，不表示
这次变更要部署——部署与迁移必然需要它，但不是只有它们需要。`documents`
把每个角色映射到同目录的 `<role>-<short-slug>-<YYMMDD>.md`；所有角色共用
2–4 词短 slug。
`route:` 是路由卡：判级之后查 `aisoft-platform` 技能的 `references/route-policy.md`
逐格填写（取值闭集与 `process` 和 `effective_complexity` 的对应都以那张表为准），
同一段写进判级评论并在确认点 1 展示。人覆盖任何一格时把哪一格、为什么写进
`override_reason`。
