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
depends_on:
  - 101
status: ready-for-review
branch: change/96-host-role-test-errexit
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/100
created: 2026-08-12
updated: 2026-08-12
---

# Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 跨 Bash 版本稳定的 host-role tests、明确失败输出与双端/CI 证据 | - | completed |
| T02 | test-only 复核后续 GNU/BSD 可移植性失败；若需 runtime 则停止并升级 | #101 | blocked / escalated |

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
| AC-7 | Mac/VM stat 实证、run #405 日志与 diff 复核；不注入 fake stat，不改 sync runtime |

## 部署与回滚

无部署。回滚为人工 revert 最终 PR；required-context 三件套继续由后续独立 Issue 处理。
PR #100 的远端 CI 需等待 #101 以独立 PR 合并后重跑，本 Change 不复制该 runtime 修复。
