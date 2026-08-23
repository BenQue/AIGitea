---
issue: 146
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/146
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/146-loop-controller-pr-url
created: 2026-08-23
updated: 2026-08-23
---

# Verification

## 环境与版本

- 基线 `2745aeb`（含 #142、#143）
- worktree `/private/tmp/issue-146-loop-controller-pr-url`
- 无新增依赖；不涉及安装、不改 broker、不需重装

## 关于测试形态的说明（先说清楚，免得被读成比实际更强的证据）

Loop 无法端到端真跑：平台仓 profile 是 `implement_provider: none`。因此下面的 Controller 级证据来自 `test_controller.py` 的既有 fake 架子——**但 fake 的只是 git/gitea/provider 三个外部边界，文档写入是真的**：`self.repo` 是真实临时 git 仓库，`backfill_pr_number()` 真的解析真实 summary、真的改写文件，断言读的是磁盘上的内容。

## 逐条验收

### AC-1 `pr_url` 非空且等于 `<gitea_url 前缀>/pulls/<PR 号>`

`test_pr_url_and_status_are_written_when_the_pr_is_created`：Loop 跑完后从磁盘读回 summary，断言含

```
pr_url: http://gitea.test/owner/repo/pulls/3
```

`3` 是 fake Gitea 的 `create_pr` 返回号，前缀由 fixture summary 自己的 `gitea_url`（`http://gitea.test/owner/repo/issues/8`）推出——即 spec §5 裁决的路径。

### AC-2 summary `status` 与 Gitea 标签一致

同一条测试断言 summary 含 `status: pr-open\n`，且 `gitea.label_updates[-1]` 含 `pr-open`。这消除了问题陈述里那处记录分裂。

### AC-3 回填 commit 只含那一个文件，且负向可证

- `test_the_backfill_commit_carries_only_the_summary`：`git.commits` 恰好一条，路径元组恰好 `("docs/changes/8/00-summary.md",)`，subject 含 `#8` 与 `pr_url`；
- **真实 git 上的负向验证**（`LocalGitTests`，非 fake）：
  - `test_commit_paths_refuses_a_worktree_holding_anything_else`：工作树里多一个未声明文件时 `ProviderError`，且 `HEAD` 未移动；
  - `test_commit_paths_refuses_when_the_declared_path_did_not_change`：声明的路径没有改动时同样拒绝；
  - `test_commit_paths_commits_exactly_what_it_declared`：正常路径下 `git show --name-only` 恰好一个文件，事后 `git status --porcelain` 为空。

### AC-4 CI 轮询针对回填后的 HEAD

`test_ci_is_polled_against_the_head_the_backfill_produced`：断言 `gitea.status_queries[-1] == git.head_sha()`。

为此给 `FakeGitea.get_commit_status` 加了 `status_queries` 记录——此前没有任何测试关心「CI 证据属于哪个 commit」，而这正是 spec §3.1 指出的既有缺陷：Loop 宣布 CI 通过的那个 commit，会被之后的人工回填推翻。

`test_complex_loop_...` 的 push 计数从 2 改为 3，注释写明第三次就是回填推送。

### AC-5 幂等

`test_an_already_correct_summary_produces_no_commit_and_no_push`：第二次运行 `git.commits` 为空，summary 字节与第一次跑完后完全相同。以及 `test_documents.BackfillPrNumberTests.test_is_idempotent_like_the_url_form` 在库函数层逐字节比对。

### AC-6 三条 fail-closed 路径都升级，不崩溃不跳过

| 情形 | 测试 | 结果 |
|---|---|---|
| summary 缺 `pr_url` 键 | `test_a_summary_without_the_pr_url_key_escalates` | `NEEDS_HUMAN_DECISION`，评论含 `pr_url`，标签转 `awaiting-triage`，无 commit |
| 已有不同的 `pr_url` | `test_a_conflicting_pr_url_escalates_instead_of_being_overwritten` | 升级，且磁盘上原值 `pulls/99` **未被覆盖** |
| `commit_paths` 拒绝 | `test_a_refused_commit_escalates_rather_than_leaving_a_dirty_worktree` | 升级，评论含拒绝原因 |

#### 这条路径是被一个既有测试自己撞出来的

接入 Controller 后 `test_complex_loop_implements_each_frontier_ticket_before_pr` 变成 `NEEDS_HUMAN_DECISION`。原因不是实现错了，而是**那个 fixture 的 summary 根本没有 `pr_url` 键**——它不符合平台的 front matter 合同，而 #142 的闸门在真实仓库上会直接报出这种 summary。

处置：补齐 fixture（让它合规），并把这次意外固化成上表第一行那条**显式**测试。没有为了让它变绿而改判据。

### AC-7 不放宽 `validate_provider_commit`

- 代码层面：本变更**没有触碰** `validate_provider_commit` 一行；
- 测试层面：新增 `test_provider_commits_are_still_held_to_the_ticket_id_rule`，在真实 git 上确认一条缺 ticket id 的 provider commit 仍被 `#8 and T01` 规则拦下。

spec §2 记录了为什么不需要豁免：`provider_base_sha` 在**每轮开头**取值（`controller.py:185`），Controller 在第 N 轮末尾产生的 commit 位于第 N+1 轮 `base_sha` 之前，从来不在校验窗口内。Issue 正文把这两条列为「最硬的约束」，**那是我在开 Issue 时的误判**，spec §2 已公开更正——照着 Issue 走的人会去设计一套并不需要的豁免机制。

### AC-8 Codex 侧文档可被 grep 到，且表述为自动

```
$ grep -rn "pr_url" skill-for-codex/SKILL.md codex/skills/gitea-development-loop/SKILL.md
codex/skills/gitea-development-loop/SKILL.md:23: The controller opens the PR and then writes … That commit is the controller's, not yours: never write pr_url yourself …
skill-for-codex/SKILL.md:107: After it opens the pull request, the Controller writes … This is automatic — do not add a manual backfill step …
```

两处都明确写成「Controller 自动完成、不是人工步骤」，并说明失败会升级为 `NEEDS_HUMAN_DECISION`。这也补上了 #142 spec §2.6 那句不准确表述留下的真实缺口（Codex 侧此前对该步骤零描述）。

### AC-9 全量测试

```
$ PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests
Ran 506 tests in 27.683s
OK

$ bash codex/tests/smoke.sh
（exit 0）
```

506 = 合并前 479 + 本变更新增 27。会话内 `rg` 是 harness shim，按既有规避法在 `PATH` 前置了可执行 shim 后运行 smoke。

## 未能进一步核实

- **真实 Loop 的端到端运行**。平台仓 `implement_provider: none`，任何已接入项目要跑 Loop 都需先各自完成 provider acceptance matrix，不在本变更范围。外部边界（git/gitea/provider）因此是 fake 的；文档写入与 `LocalGit.commit_paths` 的 git 行为是真的。
- **`LocalGit.push()` 的 remote 解析**。它硬编码 `origin`，而 broker 依 manifest 的 `git_remote_name` 解析（NewEMaint 的平台 remote 是 `gitea`，`origin` 是 GitHub 镜像）。VM 上的 Loop checkout 通常直接 clone 自 Gitea，因此 `origin` 就是对的；但这个差异是既有的、独立于本变更的，spec §9 已列为范围外。**若要让 Loop 在 Mac 侧的 NewEMaint checkout 上跑，必须先确认这一条**——否则 change 分支会被推去 GitHub。

## 回滚

`git revert` 单个 commit：新增一个库函数、一个 `LocalGit` 方法、Controller 里一段接入代码、两处 Codex 文档。不涉及安装、不改 broker、不需重装。
