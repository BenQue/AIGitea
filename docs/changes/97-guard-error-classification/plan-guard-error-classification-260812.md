---
issue: 97
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/97
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - operations
depends_on:
  - 96
  - 101
status: ready-for-review
branch: change/97-guard-error-classification
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 六类 permission/malformed reason 与无泄漏 tests | #96 test baseline | completed |
| T02 | 06 §1 探针身份与安全解释 | T01 | completed |
| T03 | Mac/VM/full smoke、两轴 review、typed push 与 stacked PR | T02、#101 CI | in-progress |

## Expected touch points

- `codex/tools/verify-host-role.sh`
- `codex/tests/test-host-role-guard.sh`
- `06-运维手册与踩坑集.md`
- `docs/changes/97-guard-error-classification/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2 | targeted unreadable/malformed tests for profile/schema/catalog + marker leak check |
| AC-3 | existing targeted guard suite + full smoke |
| AC-4/6 | static diff + standards/spec review |
| AC-5 | `bash -n`, ShellCheck, Mac/VM targeted, `bash codex/tests/smoke.sh` |

## 部署与回滚

无部署或 live install。PR 依赖 #96/#101，保持 stacked ancestry；依赖合并后 diff 只保留 #97
内容。回滚为人工 revert；任何 installed guard 回退/重装需另行授权。
