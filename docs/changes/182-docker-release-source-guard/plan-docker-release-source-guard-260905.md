---
issue: 182
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/182
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - platform-governance
depends_on: []
status: approved
branch: change/182-docker-release-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | Issue 65 闸门收窄到发布语义面：豁免清单 + 过滤函数，两处断言共用 | - | done |
| T02 | `docker-release/install.sh` 接入共用 source guard，并恢复 `INSTALLERS` 覆盖 | T01 | done |
| T03 | `06` 踩坑 20 从「暂无闸门」改为已覆盖 | T02 | done |

T01 必须先落地：闸门不收窄时 T02 会让 `smoke.sh` 变红，两者合成一个 ticket 就无法单独
revert 治理判据。T01 单独落地时 `smoke.sh` 应保持绿（豁免清单当时还没有被任何 diff 命中），
这正是它可独立验收的证据。

## Expected touch points

- **T01** `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh`
- **T02** `docker-release/install.sh`、`codex/tests/test-installer-source-guard.sh`
- **T03** `06-运维手册与踩坑集.md`

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-installer-source-guard.sh` 的 `assert_provenance` 对 `docker-release/install` 断言 `matrix revision` 与 `schemas`，三条源状态各跑一次；`bash codex/tests/test-docker-release-install.sh` 覆盖幂等第二次运行 |
| AC-2 | 同一测试的 behind 分支：非零退出、`ERROR: docker-release/install: source checkout is 1 commit(s) behind origin/main`、`merge --ff-only` 补救提示、并断言 install root 完全不存在（零写入）；no-remote 分支断言警告后仍安装 |
| AC-3 | diff review：`docker-release/install.sh` 只 source `codex/lib/install-source-guard.sh` 并调用一次 `aisoft_install_source_guard`，无第二份实现 |
| AC-4 | `bash codex/tests/test-installer-source-guard.sh` 末行计数从 5 变 6；diff review 确认缺口注释已删 |
| AC-5 | 处理方式与理由写在 spec 的「Issue 65 证据闸门的处理方式与理由」一节；`bash codex/tests/smoke.sh` 退出码 0，其中包含 `test-docker-release-v2-lifecycle-e2e.sh` 的 preflight 断言 |
| AC-6 | diff review：踩坑 20 的 `docker-release/install` 条目改为 `matrix revision` + `schemas` 并给出目标端核对对象 |

每个 ticket 落地后跑一次 `bash codex/tests/smoke.sh` 全量；`docker-release` 的 pin 检查
在很靠后的 integration preflight 才会红，只跑单条测试看不出来。

## 部署与回滚

无部署影响。本次变更不安装、不部署、不触及任何主机。回滚为单提交 revert。
