---
issue: 215
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/215
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 213
status: approved
branch: change/215-routine-missing-audit
created: 2026-08-27
updated: 2026-08-27
---

# routine missing audit 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | #215 mapped summary/spec/plan/verification、fresh #213 baseline 与 manual/read-only 边界 | - | completed |
| T02 | missing+404、strict schema/auth/transport、present-account 与 ordering failing tests | T01 | pending |
| T03 | 最小 host-access audit compatibility implementation 与 targeted regression | T02 | pending |
| T04 | #213 audit replay、security/full smoke、semantic/Controller preflight、verification 与 PR candidate | T03 | pending |

## Expected touch points

- T01：`docs/changes/215-routine-missing-audit/`。
- T02：`codex/runtime/tests/test_host_access.py`。
- T03：`codex/runtime/aisoft_host_access/broker.py`。
- T04：本 Issue verification/plan/summary status；除必要 source/test/docs 外不扩范围。

## 数据库迁移

无。Gitea account/PAT/collaborator/protection mutation 均不在本计划执行。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2、AC-7 | `test_host_access.py` missing-account 404 + ordering + inventory assertions；canonical read-only audit replay |
| AC-3、AC-4 | 200 malformed/extra/non-string/unknown 与 401/403/5xx/transport parameterized negatives |
| AC-5、AC-6 | present read/write/admin/owner；target Write/missing/schema；identity/scope/protection existing suites |
| AC-8 | targeted Python、routine/governance security suites、shell broker/bootstrap/rollback/install suites、full smoke |
| AC-9 | transport method/call inventory、live audit read-only receipt、diff review、Controller manual preflight |

## 实施顺序

1. T01 完成 semantic mapping/check 并原子 commit。
2. T02 先增加能稳定复现 `RESPONSE_SCHEMA_INVALID` 的 missing+404 failing test，再补全部负向与 ordering matrix。
3. T03 只在 account 明确 missing + exact 404 分支投影 absent evidence；保持 200 strict parser 与全部 hard gates。
4. T04 运行 targeted/security/shell/full smoke、semantic audit 与 Controller preflight；如实更新 verification。
5. 停在 `AWAITING_PR_CONFIRMATION`，输出唯一 manual PR title/body；未经确认不 push/create PR。

## 部署与回滚

无部署。Source 通过 revert #215 唯一最终 PR 回滚；本任务 live mutation 固定为 0。
