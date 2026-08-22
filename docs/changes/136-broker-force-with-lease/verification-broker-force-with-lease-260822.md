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
status: pending
branch: change/136-broker-force-with-lease
pr_url:
created: 2026-08-22
updated: 2026-08-22
---

# Verification · `git.push.change` 改用 force-with-lease

## 环境与版本

- Commit SHA: 见最终 PR head。本文档随该 commit 一同写入，无法自引用。
- Base: `origin/main` = `97878f9`
- Artifact: source only。`/usr/local/libexec/aisoft/host-access-broker` **尚未重装**。
- Environment: Mac（`Darwin 25.5.0`），`git version 2.50.1 (Apple Git-155)`，Python 3.13。
- Worktree: `/private/tmp/issue-136-broker-force-with-lease`

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| git lease 语义探针（一次性 bare 仓库，见下节） | PASS | 四种行为全部实测确认 |
| `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access` | PASS | `Ran 81 tests ... OK`（改前 77，新增 4） |
| 反向验证：把 push argv 改回裸 `git push` 后重跑新用例 | PASS | `test_push_survives_main_advancing_and_a_rebase` 立即失败，证明用例非空转；随后已还原 |
| `bash codex/tests/smoke.sh` | PASS | `Ran 457 tests ... OK` / `Codex platform static smoke checks passed.` / `rc=0` |
| 两台主机重装 installed broker | NOT RUN | 需独立部署授权，不在本 PR 范围内 |
| 用 installed broker 实测复现路径 | NOT RUN | 依赖上一行 |

### git lease 语义探针（实现前提，T01）

在一次性 bare 仓库上用 `git 2.50.1` 实测，结论直接决定了实现形状：

| 场景 | lease 形式 | 实测结果 |
|---|---|---|
| 远端 ref 不存在，首次推送 | `refs/heads/X:`（空 expectation） | `* [new branch]` 创建成功 |
| 远端 ref 已存在，但 lease 声称不存在 | `refs/heads/X:` | `! [rejected] (stale info)` |
| lease sha 与远端一致，本地为非快进 | `refs/heads/X:<sha>` | `+ ...  (forced update)` 成功 |
| lease sha 与远端不一致 | `refs/heads/X:<sha>` | `! [rejected] (stale info)` |
| 裸 `git push`，本地为非快进 | —— | `non-fast-forward`，即 Issue 描述的死锁 |

两点由此确定：（一）空 expectation 是首推的显式解，且它把「我认为该分支还不存在」
也变成一条被校验的断言，不会在竞态下退化成无保护推送；（二）lease 命中时 force 必定成功，
所以推送失败中出现 `stale info` 只可能是租约不符，`REMOTE_BRANCH_MOVED` 的判据不会误吞凭据或网络故障。

## Acceptance criteria 结果

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 lease 形式，无裸 force | PASS | `test_push_uses_current_linked_worktree_and_exact_same_change_ref` 断言完整 argv 为 `git push --force-with-lease=refs/heads/change/70:<sha> origin refs/heads/change/70:refs/heads/change/70`，并断言 `--force`、`-f` 不在任何命令的 token 列表中；`test_newemaint_push_uses_manifest_gitea_remote` 同形 |
| AC-2 竞态拒绝且不覆盖 | PASS | `test_remote_branch_moved_after_the_lease_was_read_is_refused`：在 broker 的 `ls-remote` 返回之后、`push` 发出之前由第三方 clone 推动远端分支；断言 `REMOTE_BRANCH_MOVED`、远端 sha 仍等于第三方 HEAD、且 push 携带的正是移动前的 lease |
| AC-3 首次推送创建 | PASS | `test_readable_first_push_...` 断言 argv 为空 expectation `--force-with-lease=refs/heads/change/70-readable-change-name:`；`test_push_survives_main_advancing_and_a_rebase` 首推段在真实 bare 远端上创建分支并校验 sha |
| AC-4 既有约束不变 | PASS | `test_stale_base_branch_is_rejected_before_the_push_runs` 与 `test_merge_commit_is_rejected_before_the_push_runs`：各自断言错误码、断言**没有任何 `git push` 命令被发出**、断言远端分支未被创建。后者还先断言 merge 已让基线新鲜检查通过，确保咬住的确是 merge 规则而非前一条 |
| AC-5 复现路径 | PASS | `test_push_survives_main_advancing_and_a_rebase`：推送 → 推进远端 `main`（模拟他人 PR 合并）→ `BASE_BRANCH_STALE` → `git rebase origin/main` → 显式断言旧远端 sha **不是** rebase 后 HEAD 的祖先（确为非快进）→ 再推送 PASS 且远端 sha 等于 rebase 后 HEAD |
| AC-6 smoke 全绿 | PASS | `Ran 457 tests ... OK`，`rc=0` |

## 重复部署

- 第一次：NOT RUN
- 第二次：NOT RUN

installed broker 重装需独立部署授权。合并本 PR 后须在 **Mac 与 gitea-ci VM 两台**
重新安装并做 installed-byte readback，本修复才生效；source 合并不改变已安装字节。

## 故意失败与回滚

- 失败场景：NOT RUN
- 停止/回滚结果：NOT RUN
- 数据恢复验证：NOT RUN

回滚路径（未执行）：`git revert` 本 PR 后按同一 installer 重装两台主机，回到裸 push 行为。
无 schema、无数据面影响。

## 遗留风险与未完成项

- **本 PR 自身受该缺陷影响**：承载修复的分支要用当前仍有缺陷的 installed broker 推送。
  因此实现期间一次性推送，未做 `pr_url` 回填（回填需要第二次推送，而第二次推送正是会被互锁的动作）。
  summary 的 `pr_url` 保持为空，PR 编号以 Issue #136 的关联 PR 为准。
- **文档同步待独立治理变更**：`skill-for-claude/SKILL.md` 第 5 条仍指导 agent 在
  `BASE_BRANCH_STALE` 时停止当前 pass 并升级；`06-运维手册与踩坑集.md` 未记录
  `REMOTE_BRANCH_MOVED`。二者是 agent 行为/治理文档，按 `AGENTS.md` 必须由独立的、
  只修改治理合同的受控步骤应用，不能与本次 runtime 变更同 run 交付。
  现行指导在本变更之后仍然安全，只是偏保守。
- **未执行部署**：两台主机重装与 installed broker 的 typed canary 均为 NOT RUN。
