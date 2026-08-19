---
issue: 130
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/130
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
depends_on: []
status: approved
branch: change/130-greenfield-legacy-decouple
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/131
created: 2026-08-19
updated: 2026-08-19
---

# Plan：greenfield legacy decoupling

## Ticket graph

| Ticket | blocked_by | 垂直切片 | Acceptance criteria |
|---|---|---|---|
| T01 | [] | readable tuple、mapped docs 与 RED zero-call/version-boundary tests | AC-1–AC-10 |
| T02 | [T01] | inventory v3 collector/validator/schema/CLI candidate-only flow | AC-1–AC-3, AC-6 |
| T03 | [T02] | transition v2、candidate-only post-install/non-interference contracts | AC-3–AC-6 |
| T04 | [T03] | operator 1.2.0、templates/matrix/runbook/bundle consistency | AC-7, AC-8, AC-10 |
| T05 | [T04] | full verification、双轴 review、PR/CI handoff | AC-8–AC-10 |

## T01 — 合同与 RED 回归

**Touch points**

- `docs/changes/130-greenfield-legacy-decouple/*.md`
- `codex/runtime/tests/test_company_delivery.py`

**工作与验证**

1. 锁定 v3/v2/1.2.0 和 candidate-only acceptance mapping。
2. 增加 runner/http spy，断言 SCM preflight/post-install 对 legacy 为 zero-call。
3. 增加旧 inventory v2/transition v1 拒绝、legacy CLI 参数拒绝和 candidate collision tests。

```bash
PYTHONPATH=codex/runtime python3 -m unittest \
  codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests
```

## T02 — Inventory v3 candidate-only flow

**Touch points**

- `codex/runtime/aisoft_company_delivery/{collector.py,contract.py,cli.py}`
- `company-delivery/schema/inventory-v3.schema.json`
- `company-delivery/templates/inventory.example.json`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. 删除 SCM collector 的 legacy port requirement、Docker discovery 与 legacy HTTP path。
2. 输出 `greenfield-isolated-install-v1` candidate/automation-only SCM object。
3. 新增 inventory v3 loader/schema，明确拒绝 v2 active input。
4. 保留 candidate ports/resources/services/automation 的 exact preflight/post-install rules。

## T03 — Transition v2 与 post-install

**Touch points**

- `codex/runtime/aisoft_company_delivery/{contract.py,cli.py}`
- `company-delivery/schema/gitea-transition-v2.schema.json`
- `company-delivery/templates/gitea-transition.example.json`
- `codex/runtime/tests/test_company_delivery.py`

**工作**

1. transition v2 只接受 `greenfield-isolated-install|BLOCKED`，删除 legacy baseline/equality fields。
2. Stage50 prerequisite 改为 `candidate-post-install-health`。
3. 旧 `verify-legacy-health` 明确为历史 compatibility，不进入 v2 flow。
4. 验证 inventory/handoff/package checksums、fixed target/stage/automation 继续 fail closed。

## T04 — Portable 1.2.0 同步

**Touch points**

- `company-delivery/VERSION`
- `company-delivery/{README.md,runbook.md}`
- `company-delivery/compatibility/newemaint-company-pilot-v1.json`
- `company-delivery/schema/*.json`
- `company-delivery/templates/*.json`
- `codex/runtime/aisoft_company_delivery/contract.py`
- package/smoke tests

**工作**

同步 operator/version/matrix/contracts/templates/runbook，更新 deterministic fixtures；保留历史 schema 文件仅作历史
解析证据，不允许 active 1.2.0 verifier 接受旧 receipt。

## T05 — 验证与 PR handoff

```bash
PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery
bash codex/tests/smoke.sh
find codex company-delivery -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
git diff --check origin/main...HEAD
```

另外执行 strict JSON parse、zero-legacy-call review、candidate fail-closed review、operator/schema/template/matrix/runbook
一致性检查与两次 deterministic fake bundle checksum 对比。Controller 完成 broker push、唯一 PR create/readback、
protected main readback与 CI follow；不合并、不生成公司候选包、不执行任何 company stage。

## 回滚与停止条件

- 任一 legacy Docker/API call、旧 receipt active acceptance、candidate rule 放宽或 raw/sensitive output 为阻断缺陷。
- 普通测试失败在本 Issue 内修复；合同扩张、需要公司事实、破坏性/安全决策或三次同因失败升级给人。
- source 回滚是最终 PR 的单一 revert；公司环境无 live rollback，因为所有公司动作均 `NOT RUN`。
