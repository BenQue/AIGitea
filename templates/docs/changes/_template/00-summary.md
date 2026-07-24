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
  - 00-summary.md
confidence: CONFIDENCE
override_reason: ''
depends_on: []
status: analyzed
branch: change/ISSUE_NUMBER
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
  - 00-summary.md
confidence: CONFIDENCE
override_reason: ''
```

### 判级证据

- CLASSIFICATION_EVIDENCE

### 缺失的 acceptance criteria 或决策

- 无；如有则逐项列出。

`## AI 判级` YAML 使用 analyzer 的唯一字段集合和顺序。`small` 的
`required_docs` 只能是 `00-summary.md`；`complex` 必须依次包含
`00-summary.md`、`01-spec.md`、`02-plan.md`，部署或迁移再追加
`03-verification.md`；unresolved 只保留 `00-summary.md`。
