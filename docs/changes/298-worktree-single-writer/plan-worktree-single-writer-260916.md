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
status: contract-drafting
branch: change/298-worktree-single-writer
created: 2026-09-16
updated: 2026-09-16
---

# Plan · change worktree 单写者归属

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 归属标记 schema 与 claim 命令：写入、幂等、显式交接，附单测 | - | pending |
| T02 | `git.push.change` 归属闸门四个 code、返回体两个 SHA、推送后更新标记，附 broker 单测 | T01 | pending |
| T03 | 只读扫描命令：枚举本机 change worktree，PASS/GAP 与 reason 分类，附单测 | T01 | pending |
| T04 | 合同文档与 Red Flag：`03`、两份 `issue-session-flow`、`06` 踩坑，附 smoke 文本守卫 | - | pending |
| T05 | 全量 smoke 与 verification 记录：本机真实扫描、候选 broker 验收、未执行项 | T02, T03, T04 | pending |

T04 不依赖任何代码 ticket，可与 T01–T03 并行推进；T05 是收口，必须最后跑。

## Expected touch points

- **T01**：`codex/runtime/aisoft_loop/`（新模块，归属标记读写）、`codex/runtime/aisoft_loop/cli.py`
  新增 `claim-worktree` 子命令、`codex/runtime/tests/`（新测试文件）。
- **T02**：`codex/runtime/aisoft_host_access/broker.py` 的 `_git` 与 `_push_leased`、
  `codex/runtime/tests/test_host_access.py`。
- **T03**：`codex/runtime/aisoft_loop/cli.py` 新增 `scan-worktrees` 子命令、同一新模块、单测。
- **T04**：`03-Issue-Spec-Plan与单闸门开发流程.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `codex/skills/issue-session-flow/SKILL.md`、`06-运维手册与踩坑集.md`、`codex/tests/smoke.sh`。
- **T05**：`docs/changes/298-worktree-single-writer/verification-worktree-single-writer-260916.md`。

范围提示，不授权扩大 spec。明确不碰：`codex/config/host-access-broker.json`、
`codex/tests/test-host-access-broker.sh` 的 `operation_count`、任何项目仓。

## 实现注意

- **标记路径**用 `git rev-parse --git-dir` 解析，不要拼 `.git/`：linked worktree 的 `.git` 是文件。
- **不要把标记放进工作树**：`git.push.change` 在读标记之前先跑 `git status --porcelain`，
  工作树内的新文件会先触发 `WORKTREE_DIRTY`。
- **闸门位置**在 `broker.py:3231` 那一段既有 `git.push.change` 前置校验之内、
  `self.credentials.resolve(...)` 之前，保证拒绝时不解析凭据、不发起网络写。
- **`previous_head` 已经在手边**：`_git` 里为 `--force-with-lease` 读出的 `remote_sha`
  就是该分支上一次 push 的远端 SHA，空串表示远端此前无该分支，返回时映射为 `null`。
- **`last_push_head` 只在推送成功后写**：`_push_leased` 返回 0 之后才更新标记，
  失败路径一律不写，避免把没推上去的 SHA 记成已推送。
- **06 踩坑编号是跨 PR 共享的可变状态**：写之前先读当前最大编号；并行 PR 撞号由合并者改号。
- **smoke 文本守卫用 `grep -Fq` 钉死字面量**，与该文件既有 802–815 行的写法一致；
  加守卫之后必须反向验证一次（删掉被钉的短语确认变红），否则守卫等于没加。
- **`AISOFT_SESSION_ID` 只从 `os.environ` 读**，不进 argparse、不进 manifest。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 合同文档与 Red Flag | `bash codex/tests/smoke.sh` 中新增的 `grep -Fq` 守卫；diff review 读 `03` 与两份 SKILL.md |
| AC-2 闸门四个 code | `python3 -m unittest codex.runtime.tests.test_host_access`：四个情形各一条断言 code |
| AC-3 只读扫描命令 | 新增单测断言 PASS/GAP 与 reason 分类；`verification` 记录本机真实一次只读执行 |
| AC-4 返回体两个 SHA | broker 单测断言成功返回含 40 位 lowercase `pushed_head` 与 `previous_head`（首推为 `null`） |
| AC-5 跨会话改写 fail closed | broker 端到端测试：A claim、B 改写 HEAD、A push 断言 `WORKTREE_OWNER_MISMATCH` 稳定；B 以自身身份在 A 的 worktree push 同样断言 fail closed |
| AC-6 不阻断自身 rebase-重推 | 扩展既有 `test_push_survives_main_advancing_and_a_rebase`：claim 之后走 fetch → rebase → 重推全绿，且不要求重新 claim |
| 回归 | `bash codex/tests/smoke.sh` 全量绿 |

## 部署与回滚

本次 PR 不部署。**但合并后需要一次非本 PR 范围的运维动作**：在 Mac 与 gitea-ci VM 两台各执行
`sudo bash codex/install-host-access-broker.sh`，否则运行中的 broker 仍读旧代码，闸门不生效
（`06` 踩坑 20 的既定形态）。该命令需要 sudo，由人执行，会在 PR 正文与收尾报告里显式点名。

不重装也能验收 broker 侧行为：直接用源码树跑
`PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate`
以及 `codex/tools/host-access-broker.sh`（它在检测到源码树时优先用源码 manifest 与源码 runtime）。

回滚：`git revert` 本次 merge commit 后两台重装即回到无闸门行为。归属标记留在各 worktree 的
git dir 内，对 Git 与工作树无副作用，不需要清理。
