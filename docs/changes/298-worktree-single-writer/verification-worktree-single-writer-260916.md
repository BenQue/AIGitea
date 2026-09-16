---
issue: 298
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/298
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - agent-governance
  - platform-governance
depends_on: []
status: verified
branch: change/298-worktree-single-writer
created: 2026-09-16
updated: 2026-09-16
---

# Verification · change worktree 单写者归属

## 基线与范围

- Commit SHA: `e6830e0ad5af5063b65e42e8d8fe5f4c95203e93`（T04 完成时）
- 基线：`origin/main` = `9a2fa118bb86860372e6c90e08c917641aeba563`
- 环境: Mac，`/private/tmp/issue-298-worktree-single-writer`，Python 3.14.4，源码树直跑，
  **未重装 broker**
- 本记录负责证明的 acceptance criteria：AC-3（本机真实 worktree 的只读扫描）与
  AC-2/AC-4 在未重装前提下对真实 manifest、真实项目、真实远端的一次执行。
  AC-1、AC-5、AC-6 由 required CI（`codex/tests/smoke.sh`）复现，此处只记结果。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（改动前基线） | **PASS** | `Ran 922 tests ... OK` / `Codex platform static smoke checks passed.` / `exit=0` |
| `bash codex/tests/smoke.sh`（改动后） | **PASS** | `Ran 960 tests in 90.819s` / `OK` / `Codex platform static smoke checks passed.` / `SMOKE_EXIT=0` |
| `python3 -m unittest discover -s codex/runtime/tests -t codex/runtime` | **PASS** | `Ran 960 tests in 90.650s` / `OK`（基线 922，本次新增 38） |
| `python3 -m unittest tests.test_worktree_owner` | **PASS** | `Ran 32 tests` / `OK` |
| `python3 -m unittest tests.test_host_access` | **PASS** | `Ran 192 tests` / `OK`（基线 186） |
| broker 契约 `validate`（源码树） | **PASS** | `{"contract_version": "host-access-broker/v1", "merge_operation_count": 1, "operation_count": 36, "project_count": 6, "status": "PASS"}` |
| 已安装 vs 源码 `operations` 计数 | **PASS** | `source=36 installed=36 unchanged=True`——本次不动 typed 操作集合 |
| 真实 broker：错误会话 id 推送 | **PASS（fail closed）** | `{"code": "WORKTREE_OWNER_MISMATCH", "message": "worktree is owned by session cc4a92-issue-298, not not-the-owner; ...", "status": "BLOCKED_EXTERNAL"}`，`exit=20` |
| 真实 broker：完全不带会话 id 推送 | **PASS（fail closed）** | `{"code": "WORKTREE_OWNER_MISMATCH", "message": "AISOFT_SESSION_ID is not set; this worktree is owned by session cc4a92-issue-298 ...", "status": "BLOCKED_EXTERNAL"}`，`exit=20` |
| 上面两次拒绝之后远端分支仍不存在 | **PASS** | `git ls-remote --heads origin 'refs/heads/change/298-*' \| wc -l` = `0`——拒绝确实发生在任何网络写之前 |
| `scan-worktrees --repo /Users/benque/MyDocs/AISoftPlatform`（只读） | **PASS** | 见下方原文；`exit=0` |
| 归属标记不进工作树 | **PASS** | claim 之后 `git status --porcelain` 只有源码改动，无 `aisoft-owner.json` |
| smoke 新守卫反向验证 | **PASS** | 把 `### change worktree 的单写者归属（#298）` 改成 `### change worktree 的归属` 后守卫块变红，复原后回绿 |
| installer 计数守卫反向验证 | **PASS** | 把 `expected_runtime_modules + 2` 改回 `+ 1` 后 `test-installer-source-guard.sh` 报 `FAIL: level/install-vm: expected 'source runtime modules: 30'`，复原后回绿 |
| 两台重装 | **NOT RUN** | 需要 sudo，不由本会话执行；见「遗留风险与未完成项」 |

首次跑改动后 smoke 时红在 `release evidence boundary: current file set differs from the fixed
baseline`。**这不是本次改动造成的**：`check-release-evidence-boundary.py` 的 `disk_files()`
直接走文件系统、不读 `.gitignore`，把本会话手工跑 `python3 -m unittest`（未带 `-B`）留下的
`codex/runtime/aisoft_release/__pycache__/*.pyc` 算进了「当前文件集」。定位方式是打印
`disk_files(root) - set(baseline_files(root))`，结果 12 项全是 `.pyc`。删掉 `__pycache__`
后该检查单独跑 PASS，完整 smoke `SMOKE_EXIT=0`。上表记的是清理之后那一次。

本机真实扫描原文：

```text
PASS: change/298-worktree-single-writer [unpushed] /private/tmp/issue-298-worktree-single-writer
      head=e6830e0ad5af5063b65e42e8d8fe5f4c95203e93 last_push=- session=cc4a92-issue-298
      never pushed through the broker
result: worktrees=1 pass=1 gap=0
```

本机当时只有这一个 change worktree；CCD 自己的 `clever-jennings-cc4a92` 站在
`claude/clever-jennings-cc4a92` 上，不是 `change/` 分支，因此被正确排除。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 合同文档写死单写者归属并含 Red Flag | **PASS** | `03` 新增 `### change worktree 的单写者归属（#298）`，含 🚩 Red Flag；两份 `issue-session-flow` 各加规则、Red Flag 与 Common Mistakes 行；`06` 新增踩坑 28。smoke 字面量守卫钉住全部三样并已反向验证 |
| AC-2 可机读标记 + fail closed 独立 code | **PASS** | 标记在 `$(git rev-parse --git-dir)/aisoft-owner.json`；四种拒绝各有独立 code（`WORKTREE_UNCLAIMED` / `WORKTREE_CLAIM_INVALID` / 两种 `WORKTREE_OWNER_MISMATCH`），无一复用 `WORKTREE_DIRTY`；单测 `test_every_ownership_refusal_has_its_own_code_and_pushes_nothing` 断言四种情形下均无 `git push` 且远端 SHA 为空；真实 broker 两次执行见上表 |
| AC-3 只读扫描命令 PASS/GAP | **PASS** | `scan-worktrees` 真实执行见上；`test_every_reason_is_reported_and_only_three_are_gaps` 用真实 git 构造六种状态；`test_the_scan_writes_nothing` 断言扫描既不修标记也不给未 claim 的 worktree 补一份 |
| AC-4 返回体含两个 40 位 SHA | **PASS** | `test_push_returns_both_shas_and_records_the_landed_push`：首推 `previous_head` 为 `null`、`pushed_head` 匹配 `^[0-9a-f]{40}$` 且等于本地 HEAD；二推 `previous_head` 等于首推的 `pushed_head`。`test_a_failed_push_is_never_recorded_as_landed` 断言失败路径不写台账 |
| AC-5 跨会话改写有 smoke 覆盖（按 2026-09-16 合同修订） | **PASS** | `test_a_second_session_cannot_push_from_the_worktree_it_wandered_into`：B 在 A 的 worktree 里 rebase 后以自己的身份推 → `WORKTREE_OWNER_MISMATCH`，远端仍是 A 推上去的 SHA。`test_a_rewrite_by_someone_else_is_detectable_in_the_push_return`：B 改写后 A 推送 → 推送发生，但 `pushed_head` ≠ A 核验过的 SHA 且 `previous_head` 等于它，改写确定性可检出 |
| AC-6 不阻断自身 rebase-重推 | **PASS** | `test_the_owner_still_rebases_and_repushes_without_reclaiming`：`BASE_BRANCH_STALE` → `git.fetch.main` → 本地 rebase → 重推全绿，`previous_head` 指向 rebase 前的 SHA，标记的 `session` 未变，全程没有重新 claim |

## 遗留风险与未完成项

- **两台重装 NOT RUN**。运行中的 broker 读 `/usr/local/lib/aisoft-host-access/`，合并后必须在
  Mac 与 gitea-ci VM 各执行一次 `sudo bash codex/install-host-access-broker.sh`，闸门才对真实
  push 生效（`06` 踩坑 20 的既定形态）。需要 sudo，由人执行。本记录里所有 broker 证据都来自
  **源码树 runtime**（`codex/tools/host-access-broker.sh` 检测到源码树时优先用源码 manifest 与
  源码 runtime），不证明已安装 broker 的行为。
- **对既有在途 change worktree 是一次 flag day**。重装之后，没有归属标记的 change worktree
  推送会被 `WORKTREE_UNCLAIMED` 拒绝。拒绝信息直接带 claim 命令，补一次即可。本机当时只有
  本变更自己这一个 change worktree（扫描结果 `worktrees=1`），影响面为零。
- **归属机制是协作式的，不是安全边界**。同机同用户下，B 能读到的标记 B 也能改写或伪造。
  本次覆盖的是**意外**跨 worktree 改写，不防御蓄意 agent；这一条已写进 spec 的非目标。
- **闸门不覆盖「别人改写 HEAD 之后你自己推」**，这是 2026-09-16 合同修订的结论而非缺陷：
  该情形的检出依赖调用方真的去核对 `pushed_head`。合同文档已把这一步写成步骤而非建议，
  smoke 钉住了那句话，但「人/agent 是否真的照做」不是代码能保证的。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
