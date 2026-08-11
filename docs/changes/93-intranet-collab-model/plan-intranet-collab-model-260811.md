---
issue: 93
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/93
change_type: docs
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment-contract
depends_on: []
status: contract-drafting
branch: change/93-intranet-collab-model
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | 13 §0 总纲 + §1 拓扑 + §3 manifest 字段 + §7 PRD 限定 + §11/§12.2 备选化 | 13 | `rg` 关键串与反向串 | AC-1/2/3 |
| T02 | 14 C-13/C-14 + Linux 分流说明 | 14 | `rg 'C-13\|C-14'` | AC-4 |
| T03 | 07 §1 核心决策 + §2 图边 | 07 | `rg` + mermaid 边检查 | AC-2/5 |
| T04 | 回归 | — | smoke 全绿 | AC-6 |

回滚：三文件单 commit revert。
