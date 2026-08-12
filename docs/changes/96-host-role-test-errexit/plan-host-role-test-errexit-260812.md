---
issue: 96
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/96
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
  - security
depends_on: []
status: ready-for-review
branch: change/96-host-role-test-errexit
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 跨 Bash 版本稳定的 host-role tests、明确失败输出与双端/CI 证据 | - | completed |

## Expected touch points

- `codex/tests/test-host-role-guard.sh`
- `codex/tests/test-install-host-role.sh`
- `docs/changes/96-host-role-test-errexit/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2/3 | targeted tests + source review |
| AC-4 | Mac `bash -n` + two targeted tests |
| AC-5 | VM Bash 5.3 + two targeted tests |
| AC-6 | full smoke + PR final-head status readback |

## 部署与回滚

无部署。回滚为人工 revert 最终 PR；required-context 三件套继续由后续独立 Issue 处理。
