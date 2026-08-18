---
issue: 128
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/128
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
depends_on:
  - 126
status: approved
branch: change/128-gitea-port-inventory-fix
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/129
created: 2026-08-18
updated: 2026-08-18
---

# Plan：Stage 10 固定端口 8888 与 inventory 兼容修复

## Ticket graph

| Ticket | blocked_by | 交付切片 | Acceptance criteria |
|---|---|---|---|
| T01 | [] | 锁定 Issue tuple、summary/spec/plan/verification 与 focused failing tests | AC-1–AC-9 |
| T02 | [T01] | 固定 8888 target；实现 systemd pair normalization 与 PostgreSQL template preflight | AC-1–AC-4, AC-6 |
| T03 | [T01] | 实现 legacy HTTP 固定 reason class、schema/validator no-echo 合同 | AC-5, AC-6 |
| T04 | [T02, T03] | 同步 1.1.1 version、transition/template/compatibility/README/runbook 与 package tests | AC-1, AC-6, AC-7, AC-9 |
| T05 | [T04] | 完整验证、双轴 review、verification、push、唯一 PR 与 CI handoff | AC-7–AC-9 |

## T01 — 合同与回归基线

**Touch points**

- `docs/changes/128-gitea-port-inventory-fix/*.md`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. 建立 readable tuple 与四份 mapped 文档，确认无 unresolved decision。
2. 为真实 Ubuntu pairs、3000 occupied/8888 free、8888 collision 与 legacy HTTP reason classes 增加 focused tests。
3. 保留现有 no-secret/no-raw assertions，并确保测试先能捕获 1.1.0 行为差异。

**验证**

```bash
PYTHONPATH=codex/runtime python3 -m unittest \
  codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests
```

## T02 — Fixed target 与 systemd normalization

**Touch points**

- `codex/runtime/aisoft_company_delivery/collector.py`
- `codex/runtime/aisoft_company_delivery/contract.py`
- `company-delivery/schema/inventory-v2.schema.json`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. 把 candidate Gitea port 固定为 8888；保持 legacy typed port 与 PostgreSQL 55432。
2. 增加 pair-level unit normalization，只接受 `not-found/inactive` 的窄等价映射。
3. 更新 optional tool/timer/candidate service consumer 与 runtime validator。
4. 为 PostgreSQL fixed template 增加只在 disabled/inactive 且其它 fixed facts 安全时成立的 preflight rule。

**验证**

```bash
PYTHONPATH=codex/runtime python3 -m unittest \
  codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests
```

## T03 — Legacy health 固定枚举

**Touch points**

- `codex/runtime/aisoft_company_delivery/collector.py`
- `codex/runtime/aisoft_company_delivery/contract.py`
- `company-delivery/schema/inventory-v2.schema.json`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. 将非 200 分组为固定 3xx/4xx/5xx reason；异常只为 request-failed。
2. 将 200 但 body 不满足 exact JSON/semver/size 的情况归为 response-invalid 或 sensitive-output-rejected。
3. 证明 raw body、header、status code、异常与 sentinel 不进入 inventory/CLI 输出。

**验证**

```bash
PYTHONPATH=codex/runtime python3 -m unittest \
  codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests.test_legacy_health_probe_is_bounded_strict_and_no_echo
```

## T04 — Portable operator 1.1.1 同步

**Touch points**

- `company-delivery/VERSION`
- `company-delivery/{README.md,runbook.md}`
- `company-delivery/compatibility/newemaint-company-pilot-v1.json`
- `company-delivery/schema/gitea-transition-v1.schema.json`
- `company-delivery/templates/*.json`
- `codex/runtime/aisoft_company_delivery/contract.py`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. 同步 operator/version/target exact const 和 matrix revision。
2. 更新 Stage 10 PASS 与 BLOCKED 说明，明确 1.1.0 evidence 不可复用。
3. 更新 deterministic bundle、tamper、transition 与 template fixtures。
4. 只修改 company-delivery owned 3000 references；保留平台本地 Gitea references。

**验证**

```bash
PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery
python3 -m json.tool company-delivery/compatibility/newemaint-company-pilot-v1.json >/dev/null
python3 -m json.tool company-delivery/schema/inventory-v2.schema.json >/dev/null
python3 -m json.tool company-delivery/schema/gitea-transition-v1.schema.json >/dev/null
```

## T05 — 完整验证与 PR handoff

**Touch points**

- `docs/changes/128-gitea-port-inventory-fix/verification-gitea-port-inventory-fix-260818.md`
- 仅在验证发现 in-scope 缺陷时修改 T02–T04 文件

**验证命令**

```bash
PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery
bash codex/tests/test-company-delivery.sh
bash codex/tests/smoke.sh
find codex company-delivery -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
git diff --check origin/main...HEAD
```

如 ShellCheck 可用，对本 Change 涉及的 shell harness 运行；本 Change 预计不修改 shell。随后运行：

- source/schema/runtime/tests 与 runbook/compatibility/templates 双轴一致性 review；
- no-secret/no-raw-output review；
- dual deterministic `build-bundle` archive SHA 对比；
- broker exact branch push、唯一 PR create/readback、protected main readback 与 CI follow。

## 回滚与停止条件

- 任一测试发现 8888 未成为唯一 company target、systemd rule 过宽、raw output 落盘或 1.1.0 receipt 可被误接收，
  停止 T05 并修复，不弱化断言。
- 本 Change 不执行公司 live action；source 回滚为最终 PR 的单一 revert。
- push/PR 后不合并、不生成公司 Stage00 包、不继续 Stage10 appserver；保持现场 1.1.0 SCM outcome=`BLOCKED`。
