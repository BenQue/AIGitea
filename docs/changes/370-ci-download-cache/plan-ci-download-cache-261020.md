---
issue: 370
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/370
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/370-ci-download-cache
created: 2026-10-20
updated: 2026-10-21
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | PAT helper 脚本缓存与重试，gates 测试补命中/驱逐场景 | - | done |
| T02 | `ci.yml` 改用手写本地 checkout 并传缓存目录（治理文件单独 commit） | T01 | done |
| T03 | `01` §4 as-built 与回滚；runner 两次真实运行写进 verification | T02 | pending |

## Expected touch points

- T01：`codex/tests/test-gitea-pat-helper-linux.sh`、`codex/tests/test-gitea-pat-helper-linux-gates.sh`
- T02：`.gitea/workflows/ci.yml`
- T03：`01-基础设施-VM-Gitea-Runner.md`、本目录 verification

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1 | PR CI 第二次运行日志：checkout 来源、`TOOLCHAIN_CACHE_HIT`、`GO_MODULE_CACHE_HIT` |
| AC2 | `bash codex/tests/test-gitea-pat-helper-linux-gates.sh`（命中、驱逐、校验和、路径四场景）；Linux 容器篡改模块后 `go mod verify` 拒绝 |
| AC3 | PR CI 两次运行（填充、命中）摘录；`bash codex/tests/smoke.sh`、ShellCheck |

## 部署与回滚

无应用部署，无站点前置。回滚见 spec。
