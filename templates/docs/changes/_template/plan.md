---
issue: ISSUE_NUMBER
gitea_url: ISSUE_URL
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: complex
contract_effect: CONTRACT_EFFECT
confidence: CONFIDENCE
risk_flags: []
depends_on: []
status: contract-drafting
branch: change/ISSUE_NUMBER-SHORT-SLUG
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Implementation plan template

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 一个端到端可验证的垂直切片 | - | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。每个 ticket 都应可由 `$implement #N Txx` 独立执行和验证。
默认使用可独立验收的 vertical slice；只有无法逐片保持绿色的宽重构才按 expand → migrate batches → contract 建图。

## Expected touch points

- 按 ticket 列出预期文件或模块；这是范围提示，不授权扩大 spec。

## 数据库迁移

没有迁移时明确写“无”。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 待填写 |

## 部署与回滚

没有部署影响时明确写“无”。有部署影响时必须计划映射的 `verification` 文档、两次重复执行和一次故意失败回滚。
