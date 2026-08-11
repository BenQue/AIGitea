---
issue: 89
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/89
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-artifact-deployment
depends_on: []
status: contract-drafting
branch: change/89-platform-repo-ci
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Plan

| Ticket | 内容 | 文件 | 验证 | 映射 AC |
|---|---|---|---|---|
| T01 | PR CI workflow | `.gitea/workflows/ci.yml` | python yaml 解析 + 字段断言 | AC-1 |
| T02 | 确认清单不动的契约依据并写入 spec | `spec` 文档 | `test_host_access` 两用例在清单先改时 PROTECTION_MISMATCH 复现记录 | AC-2 |
| T03 | 本地回归 | — | smoke 全绿（必要时按 #77 先例叠加 #82 修复验证） | AC-3 |
| T04 | 真实运行与保护翻转交接 | PR 本体 + verification | PR 触发 workflow 首跑；合并后人工从 status 读回 context 再 apply | AC-4、AC-5 |

回滚：删 workflow 文件 + revert 清单一行；VM 侧 `sudo apt-get remove -y ripgrep`。
