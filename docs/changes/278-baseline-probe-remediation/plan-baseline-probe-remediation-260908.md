---
issue: 278
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/278
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
depends_on: []
status: approved
branch: change/278-baseline-probe-remediation
created: 2026-09-08
updated: 2026-09-08
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | v2 2.0.1 兼容层：小写 Gitea version、`enabled-runtime` GAP、2.0.0 verifier compatibility 与 published schema | - | completed |
| T02 | diagnostics/v1 collector、closed schema 与安全负向测试 | T01 | pending |
| T03 | exact-commit review bundle builder、操作说明、manifest/digest/profile drift tests | T02 | pending |
| T04 | targeted/full regression、NewEMaint profile 的本地 review bundle、verification 与最终 source candidate | T03 | pending |

所有 ticket 属于 #278，不创建子 Issue。每个 ticket 的中间提交必须保持 v1 exact bytes 与已完成的 earlier tests 绿色。

## Expected touch points

- T01：`codex/runtime/aisoft_company_baseline_v2.py`、`codex/runtime/tests/test_company_baseline_v2.py`、`company-delivery/baseline/inventory-v2.schema.json`。
- T02：`codex/runtime/aisoft_company_baseline_diagnostics_v1.py`、`codex/runtime/tests/test_company_baseline_diagnostics_v1.py`、`company-delivery/baseline/diagnostics-v1.schema.json`。
- T03：`company-delivery/baseline/prepare-diagnostics-bundle.py`、`company-delivery/baseline/DIAGNOSTICS.md`，并由 T02/T03 tests 覆盖。
- T04：`company-delivery/baseline/README.md`、本 Issue verification；review bundle 只写到 `/private/tmp`，不提交项目 profile 或现场 evidence。
- 明确不修改：`codex/runtime/aisoft_company_baseline.py`、`company-delivery/baseline/inventory-v1.schema.json`、governance/host-access manifests、installer、skills、CI、NewEMaint 或任何现场文件。

## 数据库迁移

无。实现和测试不连接数据库；诊断 collector 不包含 SQL、`psql`、backup 或 restore 接口。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/AC-2/AC-3 | `test_company_baseline_v2.py`：2.0.0/2.0.1 envelope、真实小写版本 fixture、畸形版本、`enabled-runtime` GAP 与未知状态 BLOCKED |
| AC-4/AC-5/AC-6/AC-7 | diagnostics unit/CLI tests：binding、selected properties、config boolean projection、UFW success/permission/error、closed receipt |
| AC-8 | command/http/path static allowlist、subprocess fake、Secret sentinel across stdout/stderr/schema/error；源码审查确认无 shell/sudo/HTTP/SQL/log/env/raw output |
| AC-9 | disposable Git fixture 与 project profile fixture：exact commit materialization、mode/hash manifest、existing dir/canonical/profile/object drift 拒绝 |
| AC-10 | targeted unittest 连续两次；完整 runtime unittest；`bash codex/tests/smoke.sh`；semantic document checker；`git diff --check`；review bundle readback |

预期命令：

```bash
PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_baseline codex.runtime.tests.test_company_baseline_v2 codex.runtime.tests.test_company_baseline_diagnostics_v1
PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests
bash codex/tests/smoke.sh
PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .
git diff --check
```

## 部署与回滚

无部署。T04 只在开发侧 `/private/tmp` 生成 review bundle 并验证后保留给人工审阅；不拷贝到或执行于公司服务器。source 回滚为最终 PR revert，现场没有本 Issue 引入的状态可回滚。PR 固定 `manual`，提交与合并分别受人工闸门控制。
