---
issue: 136
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/136
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
depends_on: []
status: contract-drafting
branch: change/136-broker-force-with-lease
pr_url:
created: 2026-08-22
updated: 2026-08-22
---

# Implementation plan · `git.push.change` 改用 force-with-lease

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 用真实 bare 远端验证 git 的 lease 语义（空 expectation 创建、租约不符拒绝、租约命中强推非快进），作为实现前提 | - | done |
| T02 | `ls-remote` 解析同时带回 object id 并校验，`git.push.change` 改用 `--force-with-lease` | T01 | done |
| T03 | lease 拒绝映射为 `REMOTE_BRANCH_MOVED`，其余非零返回仍为 `HOST_COMMAND_FAILED` | T02 | done |
| T04 | 四条真实远端回归测试 + 三处既有 argv 断言更新 | T02, T03 | done |

T01 是独立的一次性探针，不留在仓库里；其结论写入本文档与 verification。

## Expected touch points

- T02：`codex/runtime/aisoft_host_access/broker.py`
  —— `_remote_change_names` → `_remote_change_heads`（返回 `(ChangeName, sha)`，
  object id 复用既有 `COMMIT_SHA_RE` 校验）；`git.push.change` 的 argv 构造。
- T03：`codex/runtime/aisoft_host_access/broker.py`
  —— 新增模块级 `LEASE_REJECTION_MARKERS` 与 `_push_leased()`。
- T04：`codex/runtime/tests/test_host_access.py`
  —— 新增 `_remote_backed_change_worktree` / `_remote_backed_runner` 夹具与四个用例；
  更新 `test_push_uses_current_linked_worktree_and_exact_same_change_ref`、
  `test_newemaint_push_uses_manifest_gitea_remote`、
  `test_readable_first_push_is_allowed_but_conflicting_remote_name_is_rejected` 的 stub 前缀匹配与 argv 断言。

范围提示，不授权扩大 spec：不触碰 typed 操作清单、manifest、CLI、installer 与治理文档。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 lease 形式 | `test_push_uses_current_linked_worktree_and_exact_same_change_ref`（断言完整 push argv 等于带 lease 的形式，并断言 `--force`/`-f` 不在任何命令的 token 列表中）、`test_newemaint_push_uses_manifest_gitea_remote` |
| AC-2 竞态拒绝 | `test_remote_branch_moved_after_the_lease_was_read_is_refused`（在 broker 的 `ls-remote` 返回之后、`push` 发出之前由第三方推动远端分支；断言错误码、远端 sha 未被覆盖、且 push 携带的正是移动前的 lease） |
| AC-3 首次推送 | `test_readable_first_push_is_allowed_but_conflicting_remote_name_is_rejected`（断言空 expectation argv）、`test_push_survives_main_advancing_and_a_rebase` 的首推段（真实 bare 远端上分支被创建） |
| AC-4 既有约束不变 | `test_stale_base_branch_is_rejected_before_the_push_runs`、`test_merge_commit_is_rejected_before_the_push_runs`（各自断言错误码、无 `git push` 命令发出、远端分支未被创建） |
| AC-5 复现路径 | `test_push_survives_main_advancing_and_a_rebase`（推送 → `main` 前进 → `BASE_BRANCH_STALE` → rebase → 再推送成功；显式断言旧远端 sha 不是 rebase 后 HEAD 的祖先） |
| AC-6 全量绿 | `bash codex/tests/smoke.sh` |

测试策略：新增用例使用**真实 bare 仓库**作为远端，只把会走网络的 `fetch`/`push`/`ls-remote`
重定向到该 bare 路径，manifest 的 remote URL 校验仍看到 `http://gitea-ci.orb.local:3000/...`。
这样 lease 的判定权留在 git 自己手里；argv 断言只能证明「我们传了什么」，证明不了「git 会怎么做」。

## 部署与回滚

**有部署影响。** source 合并不改变 installed broker 的字节，
本修复在 Mac 与 gitea-ci VM 重装 `/usr/local/libexec/aisoft/host-access-broker` 之前不生效。
重装需要独立部署授权，不在本 PR 范围内，由映射的 `verification` 文档承载
两次幂等执行与一次故意失败回滚的证据。终态为 `deployed` 而非 `completed`。

回滚：`git revert` 本 PR 后按同一 installer 重装两台主机，回到裸 push 行为；无数据面影响。
