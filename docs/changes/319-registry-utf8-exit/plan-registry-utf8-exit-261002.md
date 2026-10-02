---
issue: 319
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/319
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: approved
branch: change/319-registry-utf8-exit
created: 2026-10-02
updated: 2026-10-02
---

# #319 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T00 | 分析、UTF-8 改前证据和可审阅 complex 合同 | - | completed |
| T01 | 修复 UTF-8 诊断边界，并用 HTTP fixture 证明成功/故障/恢复行为 | T00 | completed |
| T02 | 完成跨 Bash/UTF-8、语法、ShellCheck、完整 smoke 与审查证据 | T01 | completed |

T00 blocked_by: []。T01 blocked_by: [T00]。T02 blocked_by: [T01]。合同批准步骤只记录 approved 并停止，不和 runtime 实施放在一个 run。ticket 均在 #319，不建子 Issue。

## Expected touch points

- T01：`templates/project/ci/registry-preflight.sh`（6 处变量边界）、`codex/tests/test-registry-preflight.sh`（诊断行为断言）。复用 fake-npm-registry.py，保持 fixture 接口。
- T02：本目录 mapped summary/plan/verification 与脱敏 evidence；不得改已确认 AC。

## 数据库迁移

无。

## 测试与验收映射

| AC | Ticket | Verification |
|---|---|---|
| AC-1 | T01 | diff review 6 处边界、bash -n、ShellCheck |
| AC-2 | T01 | 同一 HTTP fixture 的 healthy/stop/recover/HTTP500/notpackument/tarball404/config，检查退出码、stage、标记、diagnostics |
| AC-3 | T02 | macOS C.UTF-8/en_US.UTF-8/zh_CN.UTF-8 三组 `/bin/bash codex/tests/test-registry-preflight.sh`；Linux C.UTF-8 同命令 |
| AC-4 | T02 | `/bin/bash -n templates/project/ci/registry-preflight.sh codex/tests/test-registry-preflight.sh`；`shellcheck` 同文件；默认 UTF-8 `bash codex/tests/smoke.sh`；required PR CI 独立读取 |

Linux 使用现有 gitea-ci/coder，从本 worktree 只读挂载 `/mnt/mac/private/tmp/issue-319-registry-utf8-exit` 执行；仅启动测试 fixture 临时进程/目录/端口，不操作正式服务。完整 smoke 失败应真实归因，不删除测试或弱化 AC。

## Review 与 PR 候选

审查文件范围、UTF-8 正式证据、无 credential/真实 registry/locale workaround。原子 commit subject 带 `#319 T01` 或 `#319 T02`。

本地全部完成后用 `apply-classification-labels.sh --repo <worktree> --verify 319` 读回 type/complexity，只有 projected 才进入 AWAITING_PR_CONFIRMATION。一次确认绑定 #319、change/319-registry-utf8-exit、manual；确认后才 broker push、对比 pushed_head、唯一 PR 与 CI，停 READY_FOR_REVIEW 等人 merge。

## 部署与回滚

无部署。回滚修复 commit 经独立 PR。人 merge 后证明 exact merge 位于 origin/main，pinned terminal reconciliation、文档检查、精确 worktree/分支清理后归档；验收未完成不写 completed。
