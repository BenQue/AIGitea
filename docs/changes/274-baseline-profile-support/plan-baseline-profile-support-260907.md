---
issue: 274
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/274
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
  - external-contract
depends_on: []
status: approved
branch: change/274-baseline-profile-support
created: 2026-09-07
updated: 2026-09-07
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | closed/canonical profile、digest binding、v2 identity/schema/verify 最小闭环及拒绝测试 | - | complete |
| T02 | profile-driven fixed probes、动态判定、supplement 与 external-interface/hyphen-free fixture | T01 | complete |
| T03 | 发布 schema/README、完整回归、verification 与最终 source candidate | T02 | complete |

每个 ticket 属于 #274；默认不建子 Issue。T01/T02 的中间状态必须保持 v1 测试绿色。

## Expected touch points

- T01：`codex/runtime/aisoft_company_baseline_v2.py`、`codex/runtime/tests/test_company_baseline_v2.py`。
- T02：同上，完成所有 host-probe seam 与 decision semantics。
- T03：`company-delivery/baseline/profile-v1.schema.json`、`inventory-v2.schema.json`、`README.md`、本 Issue verification。
- 明确不修改：`codex/runtime/aisoft_company_baseline.py`、`inventory-v1.schema.json`、`blocked-envelope.example.json`、governance/host-access manifests、skills、installer、CI。

## 数据库迁移

无。测试不连接数据库，现场不执行 SQL。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | v1 exact SHA-256 回归 + 既有 `test_company_baseline.py` |
| AC-2/AC-3 | v2 unit tests：canonical/digest/schema/identity relation 与恶意输入拒绝 |
| AC-4/AC-5 | 注入 FakeHost：exact argv/HTTP/storage allowlist、external listener、loopback PostgreSQL、bounded errors |
| AC-6 | adopt/remediation/BLOCKED、freshness、manual evidence、backup/restore tests |
| AC-7 | CLI subprocess、published schema byte comparison、Secret/unknown/tamper tests |
| AC-8 | diff review、`git diff --check`、verification 的 installed/live NOT RUN |
| 全部 | targeted v1/v2 unittest；完整 runtime unittest；semantic document checker；shell smoke（仅在 shell/shared runtime 受影响时） |

## 部署与回滚

无部署。source 可普通 revert；v1 未改，不需要迁移历史回执。NewEMaint #79 只能在本 Issue 稳定 merged source 后消费 v2，仍需其独立 live gate。
