---
issue: 101
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/101
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - credential-boundary
  - sync-runtime
  - ci-change
depends_on: []
status: approved
branch: change/101-sync-stat-portability
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | mapped complex contract、exact scope 与回滚/非目标 | - | completed |
| T02 | GNU-first/BSD-fallback runtime + portability/private-mode tests | T01 | completed |
| T03 | Mac/VM/full smoke、review、typed push、唯一 PR 与 final-head CI | T02 | in-progress |

## Expected touch points

- T01：`docs/changes/101-sync-stat-portability/`
- T02：`sync/inbound-sync.sh`、`sync/git-credential-token-file.sh`、
  `sync/tests/test-inbound-sync.sh`、`sync/tests/test-install.sh`
- T03：只更新 mapped Change docs 的实际证据与 PR URL；不修改 CI workflow 或 live 环境

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2 | fake GNU `stat -f` success/non-mode regression + 400/600 allow + 644/unparseable deny |
| AC-3 | `bash sync/tests/test-inbound-sync.sh`、`bash sync/tests/test-install.sh` on Mac and gitea-ci VM |
| AC-4 | `bash -n`、ShellCheck、`bash codex/tests/smoke.sh` |
| AC-5 | document resolver、branch/docs/PR readback、exact-head commit status |
| AC-6 | diff/scope review + live-state boundary audit |

## 部署与回滚

无部署。本 Change 不运行 `sync/install.sh` 对 live root、不开 timer、不执行真实同步。代码回滚为人工
revert 最终 PR；临时 HOME/repository/fixture 由 tests 自身清理。
