---
issue: 282
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/282
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
depends_on: []
status: approved
branch: change/282-ufw-format-compat
created: 2026-09-10
updated: 2026-09-10
---

# 实施计划

| Ticket | blocked_by | 交付 | 验收 |
|---|---|---|---|
| T01 | [] | v2解析/版本/schema和合成测试 | AC-1/2/3 |
| T02 | [T01] | 指南、全部回归及证据 | AC-4 |

## Touch points

codex/runtime/aisoft_company_baseline_diagnostics_v2.py；company-delivery/baseline/diagnostics-v2.schema.json；codex/runtime/tests/test_company_baseline_diagnostics_v2.py；company-delivery/baseline/DIAGNOSTICS-V2.md；本目录。

## 验证命令

PYTHONPATH=codex/runtime:. python3 -B -m unittest codex.runtime.tests.test_company_baseline_diagnostics_v2

PYTHONPATH=codex/runtime:. python3 -B -m unittest codex.runtime.tests.test_company_baseline_diagnostics_v2 codex.runtime.tests.test_company_baseline_diagnostics_v1 codex.runtime.tests.test_company_baseline_v2 codex.runtime.tests.test_company_baseline

PYTHONPATH=codex/runtime:. python3 -B -m aisoft_loop.cli check-change-documents --repo /private/tmp/issue-282-ufw-format-compat

最后 git diff --check，检查 allowlist，原子本地 commit，停止在 AWAITING_PR_CONFIRMATION。无部署。

T01/T02 已完成本地实现与验证；实际结果见映射 verification。
