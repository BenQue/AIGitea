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
| T02 | missing+404、strict schema/auth/transport、present-account 与 ordering failing tests | T01 | completed |
| T03 | 最小 host-access audit compatibility implementation 与 targeted regression | T02 | completed |
| T04 | #213 audit replay、security/full smoke、semantic/Controller preflight、verification 与 PR candidate | T03 | completed |
| T05 | 独立复审 P1：repository/ACL/malformed/unknown 404 与 inventory schema/contradiction failing tests | T04 | completed |
| T06 | account-missing exact collaborator inventory evidence 与 generic 404 fail-closed implementation | T05 | completed |
| T07 | semantic contract 修订、全量回归、verification 与第二轮独立复审 candidate | T06 | completed |
| T08 | 第三轮复审：exact-200、username/duplicate/case-fold、pagination/oversize failing tests | T07 | completed |
| T09 | 专用 strict inventory request/parser 与 bounded pagination implementation | T08 | completed |
| T10 | semantic/verification 同步、全量本地闸门与第三轮独立复审 candidate | T09 | completed |
| T11 | 第四轮复审：lossless Link、canonical pagination metadata、response/audit resource bound failing tests 与 implementation | T10 | completed |
| T12 | spec/verification 同步、全量本地闸门与第四轮独立复审 candidate | T11 | completed |

## Expected touch points

- T01：`docs/changes/215-routine-missing-audit/`。
- T02：`codex/runtime/tests/test_host_access.py`。
- T03：`codex/runtime/aisoft_host_access/broker.py`。
- T04：本 Issue verification/plan/summary status；除必要 source/test/docs 外不扩范围。
- T05：`codex/runtime/tests/test_host_access.py` review negatives 与 ordering/call inventory。
- T06：`codex/runtime/aisoft_host_access/broker.py` bounded collaborator inventory helper/branch。
- T07：本 Issue summary/spec/plan/verification 与全量本地闸门；不触达 live/network。
- T08：`codex/runtime/tests/test_host_access.py` exact status/identity/pagination review matrix。
- T09：`codex/runtime/aisoft_host_access/broker.py` strict inventory transport/parser。
- T10：本 Issue summary/spec/plan/verification 与全量本地闸门；不触达 live/network。
- T11：`broker.py` lossless headers/strict Link parser/bounded read 与 `test_host_access.py` 第四轮复审矩阵。
- T12：本 Issue spec/plan/verification 与全量本地闸门；不触达 live/network。

## 数据库迁移

无。Gitea account/PAT/collaborator/protection mutation 均不在本计划执行。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2、AC-7 | `test_host_access.py` exact HTTP 200、identifier/duplicate/case-fold、50-item page/100-page bound、lossless Link/canonical URL-query/relation termination、ordering/call assertions |
| AC-3、AC-4 | 200 permission schema、inventory schema、non-200 success、repository/ACL/malformed/unknown 404、401/403/5xx/transport、Content-Length/bounded-read/audit-budget negatives |
| AC-5、AC-6 | present read/write/admin/owner；target Write/missing/schema；identity/scope/protection existing suites |
| AC-8 | targeted Python、routine/governance security suites、shell broker/bootstrap/rollback/install suites、full smoke |
| AC-9 | local/mock transport method/call inventory、diff review、Controller manual preflight；live audit 按约束 NOT RUN |

## 实施顺序

1. T01 完成 semantic mapping/check 并原子 commit。
2. T02 先增加能稳定复现 `RESPONSE_SCHEMA_INVALID` 的 missing+404 failing test，再补全部负向与 ordering matrix。
3. T03/T06/T09 将 absent evidence 收紧为 account missing + exact HTTP 200 bounded collaborator inventory；保持 present permission strict parser 与全部 hard gates。
4. T04 运行 targeted/security/shell/full smoke、semantic audit 与 Controller preflight；如实更新 verification。
5. 停在 `AWAITING_PR_CONFIRMATION`，输出唯一 manual PR title/body；未经确认不 push/create PR。
6. 独立复审 P1 后，在同一 branch 增加 T05/T06；T07 重跑完整闸门并停在第二轮独立复审，不恢复 PR 提交请求。
7. 第二轮复审 P1 后增加 T08/T09；T10 重跑全部本地闸门并停在第三轮独立复审，不恢复 PR 提交请求。
8. 第三轮复审 P1/P2 后增加 T11；T12 重跑全部本地闸门并停在第四轮独立复审，不恢复 PR 提交请求。

## 部署与回滚

无部署。Source 通过 revert #215 唯一最终 PR 回滚；本任务 live mutation 固定为 0。
