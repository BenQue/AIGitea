---
name: issue-session-flow
description: Use when 开 Issue 解决问题、需要把一个大阶段任务拆成多个 Issue、一次新生成了多个 Issue、要同时处理多个已有 Issue、PR 已开等人合并、人说「合并了」之后要收尾、或要清理并归档一个已完成的会话。触发词：开 issue、新会话、调度会话、派单、并行、顺序、依赖、待合并、合并了、收尾、清理 worktree、归档会话、衍生 issue。
---

# Issue 会话编排

一个 Issue 一个会话；会话开在该 Issue 的**目标项目**里；PR 开完停在人的合并闸门；人合并后收尾并归档。

**核心事实**：没有任何自动组件处在能观察到「PR 被合并」的位置上。合并之后的一切——终态标签、文档自查、worktree 清理、衍生 Issue、会话归档——只有会话主动做才会发生。忘了就是永远不做。

## 何时开调度会话

只有这三种情形，其余一律直接开 Issue 会话：

- 一个大阶段新任务，需要拆成多个 Issue
- 一次新生成了多个 Issue
- 需要处理多个已有 Issue

调度会话开在**这批 Issue 的相关项目**里，只协调不实现：不建 change worktree、不写实现代码、不碰任何 Issue 的分支。

## 两种会话

|  | 调度会话 | Issue 会话 |
|---|---|---|
| 开在 | 相关项目 checkout | 该 Issue 的目标项目 checkout |
| 做 | 拆分、派单、跟踪、收口 | 一个 Issue 从头到尾 |
| 不做 | 实现任何 Issue | 处理别的 Issue、合并 PR |

## 派单

`spawn_task({title, prompt, tldr, cwd})` 产出的是**待点击的卡片**，人点了才开出会话。这是刻意保留的人工闸门，不要绕过，也不要因为「反正要开」就自己在本会话里动手。

- `cwd` = 目标项目的本地 checkout。接入 AISoft 平台的项目从 `codex/config/host-access-broker.json` 的 `projects[].mac_checkout` 读。
- **`mac_checkout` 是 `null` 或查不到 → 停下来问人。不要拼路径、不要从别的项目类推。**
- `prompt` 必须自包含：新会话没有本会话的上下文。至少写清 Issue 号、目标项目、可测验收标准、依赖的 Issue、以及回报地址（本调度会话的 session id）。

**并行**：一次把所有卡片派出去。
**顺序**：只派当前无阻塞的。依赖写进 **Issue 正文**，再由 Issue 会话抄进 summary front matter 的 `depends_on`——依赖必须落在 Issue 上，不能只活在调度会话的上下文里（会话会被压缩，Issue 不会）。前置 Issue 完成时用 `send_message` 回报，调度会话再派下一张。

## Issue 会话的状态

用 `set_session_title` 让状态在会话列表里一眼可见：

```
#N slug · 进行中   →   #N slug · 待合并   →   （收尾）   →   归档
```

## 待合并：固定格式，会话停在这里

PR 开完立刻输出下面这个块，然后**停止**——不要接着做别的，更不要自己合并：

```
🔵 需要你合并 —— #N <标题>
PR:   <url>
变更: <一句话>
CI:   <读回的真实状态，不是推测>
判级: <apply-classification-labels.sh --verify N 的真实读回>
合并后回来说「合并了」，我做收尾并归档本会话。
```

`判级` 一行是**合并前的最后一道自查**，必须填 `codex/tools/apply-classification-labels.sh --verify N`
的真实读回，不是印象。**不是 `projected` 就不要进入待合并**——合并把 Issue 转成 closed，
判级投影的窗口随之永久关闭，之后没有任何工具会补写 `type/*` 与 `complexity/*`（#167）。
读到 `projection-missing` 就回去跑 `--apply`；读到 `broker-operation-missing` 就是本机 broker
操作表陈旧，两台重装后重跑，不要往权限方向查。未接入平台的项目跳过这一行。

## 收尾（人确认已合并后，7 步）

1. 取回主干，确认 merge commit **真实存在**。人说「合并了」不是证据，`git log` 才是。
2. 终态标签先 **dry-run**：接入平台的项目跑 `codex/tools/mark-completed-issues.sh --repo <checkout> --project <id> --range <range>`，把逐 Issue 判定计划念给人。未接入的项目：确认 `Closes #N` 已把 Issue 关掉。同时对本 Issue 跑一次 `codex/tools/apply-classification-labels.sh --verify N`（**用编号，不用 `--range`**）：报 `projection-window-closed` 说明合并前那一步漏了，如实报给人并按 `03` §11 记录，**不补写、不加 override**。

   念计划前先读第一行 `{"selector":"range",…}`：`commits` 是这个 range 实际覆盖的 merge，
   逐 Issue 行的 `commit` 是产出它的那条。**核对它就是第 1 步认定的那个 merge**；
   不是就说明范围瞄错了，重跑之前不要往下走。`origin/main~N` 在工具启动那一刻求值，
   不是在你 fetch 那一刻——`#167` 收尾时它就静默指向了别人刚合并的 Issue（#175）。
3. 人点头后才加 `--apply`，**并且用计划回给的 `pinned` 编号，不再传 `--range`**：
   `codex/tools/mark-completed-issues.sh --repo <checkout> --project <id> --apply <pinned>`。
   人点头与你敲 `--apply` 之间 `origin/main` 还会移动，同一个 `--range` 第二次解析可以
   落到另一个 Issue 上；Issue 编号不会移动。**终态判定取自文档与 manifest**：summary 的
   `required_docs` 含不含 `verification`，以及该项目在 `gitea-governance.json` 里有没有声明
   `deployment_lifecycle: none`（没有部署链路 → `completed` 是唯一终态）。两个条件都由工具
   读取，不要自己判断该写 `completed` 还是 `deployed`。
4. 文档自查：接入平台的项目跑 `check-change-documents --repo <checkout>`。
5. 清理：**先离开 worktree**，再 `git worktree remove <path>` 与 `git branch -d change/N-slug`。站在 worktree 里删自己脚下的目录会失败。
6. 盘点衍生 Issue：有调度会话就 `send_message` 回报，没有就自己开 Issue 并派卡片。
7. `archive_session("self")` 归档本会话。

`archive_session` 清理的是 CCD 自己管的 `.claude/worktrees/`，**不是**你手建的 change worktree。第 5 步不能省。

## 衍生 Issue 与琐事例外

会话中途发现新问题，默认开新 Issue。可以顺手做的**仅限**同时满足三条：不改变外部行为、不需要独立验收标准、在本 PR 已经触碰的文件内。

一句话判据：**它需要写验收标准吗？需要就是新 Issue。** 这与平台 small 判级同源，不是新规则。

## Red Flags —— 出现这些念头说明正在偏离

- 「顺便在这个会话里把 #M 也做了」
- 「PR 开完了，我接着把下一件事做了」
- 「人说合并了，那就直接 `--apply`」
- 「判级投影回头再补」→ 窗口在合并时关闭，没有回头
- 「计划里那个编号不是我的 Issue，大概是范围多带了一个」→ 是范围瞄错了，不是多带
- 「worktree 先留着，说不定还用得上」
- 「这个小改动不值得开 Issue」→ 它需要验收标准吗？
- 「会话先留着，回头一起归档」

## Common Mistakes

| 做法 | 后果 |
|---|---|
| 一个会话处理多个 Issue | 分支/worktree 串台，PR 范围失控，无法单独 revert |
| 会话开在平台仓却改目标项目 | 改动落错仓库，或落进别的 change 分支 |
| PR 开完继续往下做 | 越过人的唯一交付闸门 |
| 跳过第 1 步直接 `--apply` | 未合并的 Issue 被写成终态 |
| `--apply` 仍然传 `--range` | 人点头之后 `origin/main` 又前进一次，写到别人刚合并的 Issue 上——而 `completed` 恰恰常常正是它该有的标签，所以不报错也看不出来（#175） |
| 不清理 worktree | 残留累积——本机曾同时残留三个已合并 change 的 worktree |
| 只在上下文里记依赖 | 会话一压缩，顺序关系就丢了 |
| 靠印象填 `cwd` | 会话开在错误目录，或开在根本不存在的路径上 |

## 平台适配

- **接入 AISoft 平台的项目**：Issue/PR/push 走 broker typed 操作；命名元组、AI 判级、语义文档合同见 `aisoft-platform` skill。
- **未接入的项目**：用该项目自己的 tracker 与 `git`/`gh` 等价物。会话模型、待合并格式、收尾 7 步不变。
