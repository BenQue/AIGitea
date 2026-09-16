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

# Spec · change worktree 单写者归属

## 目标与原因

给 change worktree 建立**单写者归属**：一个 change worktree 的写者是且只是该 Issue 的会话。
让「HEAD 在会话核验之后被第三方改写」从事后人工发现，变成推送时会停下的事件，并让推送方能够
在推送之后确定性地看出中途是否被改写。

原因见 summary：`git rebase` / `git commit` / `git checkout` 不经过 broker，`git.push.change`
现有的 cwd 校验（`broker.py` 的 `_validated_project_worktree` 只比对 `git-common-dir`）对
「同一仓库的另一个 worktree」天然放行，因此并发 agent 改写他人分支 HEAD 时平台侧零感知。

## 归属标记

位置：该 worktree 的 git dir 下的 `aisoft-owner.json`，即
`$(git rev-parse --git-dir)/aisoft-owner.json`。对 linked worktree 解析为
`<common-dir>/worktrees/<name>/aisoft-owner.json`，每个 worktree 各一份，互不共享。

选择 git dir 而不是工作树内的路径，是因为工作树内的任何文件都会进入 `git status --porcelain`，
而 `git.push.change` 在读标记之前就会因为它报 `WORKTREE_DIRTY`。

内容是单个 JSON object，字段固定：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 `1` |
| `issue` | Issue 编号，与分支编号一致 |
| `branch` | exact `change/N-short-description` |
| `session` | 创建会话 id，非空字符串 |
| `worktree` | 创建时的 worktree 绝对路径（realpath） |
| `created` | 创建时间 |
| `last_push_head` | 最近一次成功 broker push 的 40 位 lowercase SHA；从未推送为 `null` |
| `last_push_at` | 最近一次成功 broker push 的时间；从未推送为 `null` |

前六个字段由 claim 命令写入，后两个由 broker 在每次成功推送后更新。

## 调用方身份的载体（决策）

同机同用户下没有 OS 级隔离：任何写在磁盘上的凭证，进入该 worktree 的第二个会话同样读得到。
因此唯一能区分两个会话的载体是**调用方自己的进程环境**。

取 `AISOFT_SESSION_ID` 环境变量作为调用方身份，由会话在调用 broker 时显式带上：

```bash
AISOFT_SESSION_ID=<本会话 id> /usr/local/libexec/aisoft/host-access-broker \
  --project <项目> --operation git.push.change --branch change/N-slug
```

它不是 broker 的 typed 参数：给既有操作增删参数是破坏性变更（`06` 踩坑 26），会让全部既有
调用方当场 `ARGUMENT_MISMATCH`。环境变量既不进 `arguments` 集合，也不进 manifest，
`operation_count` 与 `[.operations[].name]` 因此完全不变。

## Acceptance criteria

- [ ] **AC-1 合同文档写死单写者归属**：`03` 与两份 `issue-session-flow/SKILL.md` 明确写死
      change worktree 的写者是且只是该 Issue 的会话；其它会话发现它需要变基时只能通知或交回，
      不得代劳。两份 skill 各含一条对应的 Red Flag 条目。
- [ ] **AC-2 标记存在且 broker 据此 fail closed**：change worktree 内存在上节定义的可机读归属
      标记；`git.push.change` 读取它，并在下列情形拒绝推送，每种给一个独立且不误导的错误码：

      | 情形 | code |
      |---|---|
      | 标记缺失 | `WORKTREE_UNCLAIMED` |
      | 标记不是合法 JSON 或字段不合规 | `WORKTREE_CLAIM_INVALID` |
      | 标记的 issue/branch 与本次推送的分支不一致 | `WORKTREE_OWNER_MISMATCH` |
      | `AISOFT_SESSION_ID` 缺失或与标记的 `session` 不一致 | `WORKTREE_OWNER_MISMATCH` |

      四个 code 都不复用 `WORKTREE_DIRTY` 与 `TARGET_MISMATCH`。拒绝发生在解析凭据之前，
      不产生任何网络写操作。
- [ ] **AC-3 只读扫描命令**：提供一条只读命令，枚举本机该项目的全部 change worktree，
      对每条报告 worktree 路径、分支、归属标记状态、当前 HEAD、`last_push_head` 及其关系
      分类，整体输出 `PASS` 或 `GAP`，全程不做任何写操作（不写标记、不 fetch、不 push）。
- [ ] **AC-4 推送返回体带两个 SHA**：`git.push.change` 成功时的返回体包含 `pushed_head`
      （本次推送的 40 位 lowercase SHA）与 `previous_head`（该分支上一次 push 的 SHA；
      远端此前不存在该分支时为 `null`），使调用方能在推送后确定性地与自己核验过的 SHA 比对。
      既有返回字段一个不删、一个不改名。
- [ ] **AC-5 smoke 覆盖跨会话改写**（2026-09-16 修订，见下节）：构造「B 站在 A 的
      worktree 里以自己的身份 push」的用例，断言 fail closed 且 code 稳定
      （`WORKTREE_OWNER_MISMATCH`）、远端仍是 A 推上去的那个 SHA；并构造「B 改写 HEAD
      之后 A 推送」的用例，断言推送发生，且返回体使改写**确定性可检出**
      （`pushed_head` 不等于 A 核验过的 SHA，`previous_head` 等于 A 上一次推送的 SHA）。
- [ ] **AC-6 不阻断单会话自身的 rebase-重推**：`BASE_BRANCH_STALE` 的既定处置
      （`git.fetch.main` → 本地 `git rebase origin/main` → broker 重推）在归属机制下仍然走得通，
      由一条端到端测试断言，且该路径不要求会话在 rebase 之后重新 claim。

## 扫描命令的 GAP 判定口径（决策）

每条 worktree 行给一个 `reason` 分类：

| reason | 含义 | 计入 GAP |
|---|---|---|
| `clean` | HEAD 等于 `last_push_head` | 否 |
| `ahead` | HEAD 是 `last_push_head` 的后代 | 否 |
| `unpushed` | `last_push_head` 为 `null`，该分支从未经 broker 推送 | 否 |
| `rewritten` | HEAD 既不等于也不是 `last_push_head` 的后代 | **是** |
| `unclaimed` | 没有归属标记 | **是** |
| `claim-invalid` | 标记不合法，或与所在分支不一致 | **是** |

`ahead` 与 `unpushed` 仍然列出（Issue 要求的列表口径是「HEAD 与最近一次 push 的 SHA 不一致」），
但不改变整体判定。理由：实现期间有未推送的本地 commit 是常态，若它一律报 GAP，这条命令在整个
实现期都是红的，读者会被训练成忽略它——那恰好毁掉它要提供的那一个信号。

## 合同修订：AC-5 前半与 AC-6 互斥（2026-09-16）

实现 T02 时发现，AC-5 原文的前半「A 的 worktree 被 B 改写 HEAD 之后 A 尝试 push 要
fail closed」与 AC-6「不要求会话在 rebase 之后重新 claim」**不能同时成立**。

实测证据（T02 完成后对真实 Git 与真实 broker 代码路径跑的一次探针）：

```text
A's push SUCCEEDED
  A verified      : 51c8bc374c465a757ad7c389781380ae2b409b55
  actually pushed : dcb645c1afde5ea2b4a0b8e27c2bb19382a38ea7
  previous_head   : 51c8bc374c465a757ad7c389781380ae2b409b55
```

根因：B 的改写与 A 自己的 rebase 在 HEAD 上留下的形状完全相同——HEAD 不再是
`last_push_head` 的后代——而闸门只看身份，两种情况下身份都是 A。要在推送时分开它们，
必须索要一个「A 本人打算改写」的信号，而 AC-6 恰好禁止索要那个信号。

处置（项目负责人 2026-09-16 裁决，选项 A）：**闸门只回答「谁能写」，改写的检出交给
返回体与扫描命令**。两条检出路径都已经实现并测过：推送后 `pushed_head` 与调用方核验过的
SHA 不符即是改写；推送前 `scan-worktrees` 把同一状态报成 `rewritten`。

被否决的两个选项与否决理由：在 `git.fetch.main` 上记「改写意图」再于推送时校验，会让一个
只读操作开始写本地状态，并对「不经 broker fetch 直接 rebase」产生误拒；一律要求非后代
HEAD 重新 claim 则直接违反 AC-6 字面。

代价必须写进合同文档：**检出只在有人真的去看的时候才成立**。因此 `03` 与
`issue-session-flow` 必须把「push 之后核对 `pushed_head`」写成一个步骤，而不是一句建议。

## 接口、数据与兼容性影响

- **broker typed 操作集合与参数集合不变**：不新增操作、不给既有操作增删参数。
  `codex/config/host-access-broker.json` 的 `operations` 与
  `codex/tests/test-host-access-broker.sh` 的 `operation_count == 36` 保持不变。
- **返回体只增字段**：既有消费者按键取值，新增 `pushed_head` / `previous_head` 不破坏它们。
- **对既有在途 change worktree 是一次 flag day**：闸门上线后，没有标记的 worktree 推送被拒。
  `WORKTREE_UNCLAIMED` 的 message 必须直接给出 claim 命令。
- **生效需要两台重装**：broker 运行时读 `/usr/local/lib/aisoft-host-access/`，合并后要在 Mac 与
  gitea-ci VM 各跑一次 `sudo bash codex/install-host-access-broker.sh`。重装之前仓库里的新行为
  对真实 push 不生效。重装需要 sudo，由人执行，不在本次 PR 的范围内。

## 风险与回滚约束

- 回滚方式：`git revert` 本次 merge commit 后在两台重装，即回到无归属闸门的行为；归属标记留在
  各 worktree 的 git dir 里，不影响 Git 本身，也不需要清理。
- 闸门必须 fail closed 且零降级：拒绝时不得回落到「警告后照推」。
- 拒绝必须发生在任何网络写之前，避免推送成功后才报错这种更坏的中间态。

## 非目标

- **不防御蓄意改写**：同机同用户下，B 能读到的标记 B 也能改写或伪造。本次是协作式护栏，
  目标是让**意外**跨 worktree 改写变成会停下的事件。防御蓄意 agent 需要 OS 级隔离，不在本次范围。
- 不改 `git rebase` / `git commit` / `git checkout` 本身，也不给它们加包装层。
- 不引入后台守护进程、文件锁或定时扫描；扫描命令是人和会话按需调用的只读工具。
- 不改 NewEMaint 或任何项目仓；本次只改平台仓。
- 不在本次 PR 内执行两台重装。

## 未决问题

无。两处设计决策（调用方身份的载体、扫描命令的 GAP 判定口径）已在上文给出取值与理由，
随合同一并确认。
