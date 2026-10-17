---
issue: 366
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/366
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - cross-module
depends_on:
  - 364
status: analyzed
branch: change/366-agents-contract-slim
created: 2026-10-17
updated: 2026-10-17
---

# #366 计划

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 分析、迁移对照表、新 AGENTS.md 预览与三份映射文档 | - | in-progress |
| T02 | macOS canonical 测试临时目录取 resolve()；本机 smoke 只剩 0 个失败 | T01 | pending |
| T03 | 治理文本一次性应用：新 AGENTS.md、03/04 迁入细则、13 个文件删 #327 段落、准入问题、测试与 smoke 注释、路线状态；smoke 全绿后本地 commit 并 STOP | T02 | pending |
| T04 | fresh run 重读治理文件后：判级投影、PR 候选，等第二次确认 | T03 | pending |
