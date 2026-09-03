---
issue: 239
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/239
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - ci-change
depends_on:
  - 237
status: pending
branch: change/239-param-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Verification · company-delivery runtime 参数化

## 基线与范围

- Commit SHA: 待填写（逐 ticket 记录）
- 基线：`origin/main` = `2482584`（Merge PR #238，#237 deproject-company-delivery）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-239-param-company-delivery`）
- 本记录负责证明的 acceptance criteria: AC-1～AC-6（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.issue.read --project newemaint --number 75`（会话开始，2026-09-03） | `state: open`，`closed_at: null` | 「承接平台 company-delivery pilot 归属…（平台 #237）」；删除副本软依赖未满足 → plan T05 |
| `grep -rci newemaint codex/runtime/aisoft_company_delivery/` | 4 处 | `bundle.py` 1（`:33` `COMPATIBILITY_PATH`）、`contract.py` 2（`:49`、`:357`）、`collector.py` 1（`:350`）；`__init__.py`/`cli.py`/`secret_scan.py` 0 |
| `grep -rci NewEmaint company-delivery/ \| grep -v ':0$'` | 合计 9 | `compatibility/newemaint-company-pilot-v1.json` 1、`schema/inventory-v1` 3、`inventory-v2` 2、`inventory-v3` 2、`templates/handoff-manifest.example.json` 1（与 Issue 正文一致） |
| `grep -ci newemaint codex/runtime/tests/test_company_delivery.py` | 13 | fixture timer 名 ×9、pilot matrix 路径 ×3、方法名 ×1 |
| `cat company-delivery/VERSION`；`find company-delivery -type f \| wc -l` | `1.2.0`；19 | 与 #237 判定表一致 |
| `bash codex/tests/integration/test-company-delivery-real-release.sh`（默认调用） | NOT RUN | `NOT RUN: Issue #124 exact real-release regression requires explicit --execute.` |
| `bash codex/tests/smoke.sh`（pristine `origin/main` = `2482584` detached worktree） | PASS，rc=0 | `Ran 651 tests in 38.099s … OK` + `Codex platform static smoke checks passed.` |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery`（改动前） | 76 tests OK | #237 verification 同值 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

## 平台侧读取 compatibility matrix 的路径（AC-5）

待 T04 填写。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待填写 |
| AC-2 | NOT RUN | 待填写 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |
| AC-5 | NOT RUN | 待填写 |
| AC-6 | NOT RUN | 待填写 |

## 遗留风险与未完成项

待填写。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
