---
issue: 271
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/271
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
depends_on:
  - 268
status: approved
branch: change/271-company-platform-baseline
created: 2026-09-06
updated: 2026-09-06
---

# 只读基线验证

## 基线与范围

- source 基线：`2a012bd832926b210581e84fbfd74b180490ca15`。
- 开发侧 broker protection read：main 禁止 direct/force push；人工 admin merge；required `CI / verify (pull_request)`。不代表公司状态。
- 公司 current：BLOCKED_EXTERNAL；所有现场采集和 mutation：NOT RUN。

## 执行结果

本地实现和测试待执行。
