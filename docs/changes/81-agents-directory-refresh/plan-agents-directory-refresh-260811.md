---
issue: 81
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/81
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/81-agents-directory-refresh
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | 重写「## 目录」小节为当前结构完整索引 | `AGENTS.md` | `rg` 逐项比对 AC-1 清单；目视比对 `ls` 输出 | AC-1、AC-2 |
| T02 | 变更范围与合同断言验证 | — | `git diff`（唯一 hunk 在 §目录）；`bash codex/tests/smoke.sh` exit 0 | AC-3、AC-4 |

回滚：单 commit revert 即恢复原目录节；无状态、无部署影响。
