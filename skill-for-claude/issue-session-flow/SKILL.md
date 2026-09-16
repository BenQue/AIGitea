---
name: issue-session-flow
description: Use when 开 Issue 解决问题、需要把一个大阶段任务拆成多个 Issue、一次新生成了多个 Issue、要同时处理多个已有 Issue、准备提交最终 PR、manual PR 等人合并、routine-auto 继续硬门、merge 后收尾、或要清理并归档一个已完成的会话。触发词：开 issue、新会话、调度会话、派单、并行、顺序、依赖、准备 PR、待合并、合并了、收尾、清理 worktree、归档会话、衍生 issue。
---

# Issue 会话编排

一个 Issue 一个会话；会话开在该 Issue 的**目标项目**里。默认人工确认只有两处：确认合同并启动 Development Loop；提交唯一最终 PR 前确认。manual PR 等人合并；eligible routine-auto 在提交确认后继续 CI 与最终硬门。merge 后终态、文档、本地清理与归档按确定性流程完成，不再询问。

**核心事实**：manual 路径由会话在人确认 merge 后主动收尾；routine-auto 成功后同一会话立即收尾。两条路径都必须完成终态标签、文档自查、worktree/本地分支清理并归档，但不为这些确定性动作增加确认点。

## 何时开调度会话

只有这三种情形，其余一律直接开 Issue 会话：

- 一个大阶段新任务，需要拆成多个 Issue
- 一次新生成了多个 Issue
- 需要处理多个已有 Issue

调度会话开在**这批 Issue 的相关项目**里，只协调不实现：不建 change worktree、不写实现代码、不碰任何 Issue 的分支。

## change worktree 的单写者归属

**一个 change worktree 的写者是且只是该 Issue 的会话。** 别的会话发现它需要变基、需要修冲突、
需要重跑验收时，只能**通知**那个会话或**交回**给它，不得代劳——哪怕改动本身是对的。`git rebase`
/ `git commit` / `git checkout` 都不经过 broker，代劳的那一笔在平台侧零感知、零记录。

建完 worktree 立刻 claim，此后每次调 broker 推送都带同一个会话 id：

```bash
AISOFT_SESSION_ID=<本会话 id> PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli \
  claim-worktree --branch change/N-short-description --worktree /private/tmp/issue-N-short-description
```

**push 之后核对返回体的 `pushed_head`** 是否等于你在确认点 2 核验过的那个 SHA——这是一个步骤，
不是一句建议。闸门只拦得住「别人以自己的身份推你的分支」；「别人改写了 HEAD 而你自己去推」它
放行，因为身份仍然是你。不等即被改写，停下来查清楚再决定，不要继续往 PR 走。

怀疑本机有人串台时，只读扫描一次（不写任何东西）：

```bash
PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli scan-worktrees --repo <checkout>
```

`rewritten`、`unclaimed`、`claim-invalid` 计入 GAP；`ahead` 与 `unpushed` 是实现期常态，照列不计。

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

## 开放 Issue 清扫

调度会话的第二项职责。每次被唤醒时，以及一批 Issue 派单完成之后，清扫一次开放 Issue。
清扫只做判定与派单，不实现任何 Issue。

**枚举**：一次 `gitea.issue.list --state open`（#222）。它分页取全、排除 pull request、
不带正文，每条给 `number`/`title`/`state`/`labels`，够直接做查重比对；正文按号用
`gitea.issue.read` 取。读到 `REQUEST_DENIED` 是本机 broker 操作表陈旧，两台重装后重跑，
不要往权限方向查。

**入口标签**：新建的 Issue 由 `gitea.issue.create` 在创建的同一次写入里带上入口标签，取值是
`needs-analysis` 或 `triage/needs-triage`。更早立的 Issue 可能一个标签都没有；清扫遇到时用
`gitea.issue.labels.set --number N --lifecycle needs-analysis` 补写。

**逐条判定表**，固定六列，一条 open Issue 一行：

| # | 标题 | 归属仓 | 重复于 | 判定 | 下一步 |
|---|---|---|---|---|---|
| N | 一句话 | 平台仓 / 项目仓 | - | 可派单 | `spawn_task` |
| N | 一句话 | 项目仓 | #M | 重复 | 关闭，并注明保留哪一条 |
| N | 一句话 | 平台仓 | - | 阻塞于 #M | 前置合并后再派 |
| N | 一句话 | 平台仓 | - | 待裁决 | 进入下面的汇总 |

判定只有这四种取值。**「先放着」不是判定**——它正是让开放 Issue 堆积起来的那个动作。

**需裁决项汇总**，一行一条，固定写三段：

```text
需裁决（n 条）
- #N <一句话问题> —— 选项 A：<后果> / 选项 B：<后果>；不裁决的后果：<一句话>
```

人裁决之前不要替它选一个默认值，也不要把待裁决的 Issue 派出去。

## Issue 会话的状态

用 `set_session_title` 让状态在会话列表里一眼可见：

```
#N slug · 待启动 → 进行中 → 待提交PR → manual: 待合并 / routine: 硬门 → 收尾 → 归档
```

## approved 之后默认自主推进

确认点 1 通过后，直到确认点 2 之前不再增加询问：读证据与判级、补齐合同文档、合同内实现与本地原子
commit、测试与普通修复、必需的更宽闸门、判级投影；确认点 2 通过后同样不再询问 push、唯一最终 PR
与 PR CI 修复。ticket、测试命令、commit、CI 重试都不是确认点；合同里已定的选择不再重问。

## 只在这些情况暂停

- 合同冲突，或实现必须扩范围
- 破坏性迁移
- 新的安全/权限/架构决策
- 任何直接生产动作
- 外部依赖缺失：凭据、服务、权限
- 验证不可靠：环境不可达、结果不可复现
- 同一根因连续三次失败

宿主弹出的 sandbox/网络授权是执行许可，不算新决策。暂停时报告真实 blocker 并等人，不自行决定。

## 确认点 1：合同/启动

triage、判级与路由要求的 semantic docs 完整后，输出 exact Issue 合同并询问是否启动 Development
Loop。确认后持久化 `approved`；它只授权合同内实现、测试和修复，不授权提交 PR、merge 或 deploy。

## 确认点 2：准备提交最终 PR

本地验证完成后进入 `AWAITING_PR_CONFIRMATION`；重复 poll 不调用 provider、不 push、不建 PR。
manual 与 routine-auto 都必须输出 branch、policy、真实验证、判级和未执行项。manual 明确“CI 修复后停在
`READY_FOR_REVIEW` 等人合并”，且不得包含自动合并 marker。routine-auto 必须逐字包含：

```text
当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，允许受控自动合并。
```

routine 授权绑定 exact Issue、branch 与 policy，不绑定确认时 SHA；实际 merge 必须钉住最终 40 位
lowercase SHA。部署不在本次授权内。routine hard gate 失败零 merge POST、零权限降级、零 fallback。
manual PR 在 required CI 全绿后停在 `READY_FOR_REVIEW` 等人 merge；routine `AUTO_MERGED` receipt
直接进入收尾，不再询问第三次。

`判级` 一行是**合并前的最后一道自查**，必须填 `codex/tools/apply-classification-labels.sh --verify N`
的真实读回，不是印象。**不是 `projected` 就不要进入待合并**——合并把 Issue 转成 closed，
判级投影的窗口随之永久关闭，之后没有任何工具会补写 `type/*` 与 `complexity/*`（#167）。
读到 `projection-missing` 就回去跑 `--apply`；读到 `broker-operation-missing` 就是本机 broker
操作表陈旧，两台重装后重跑，不要往权限方向查。未接入平台的项目跳过这一行。

## 收尾（manual 确认已合并，或 routine receipt 后自动执行）

1. 取回主干，确认 merge commit **真实存在**。人说「合并了」不是证据，`git log` 才是。
2. 终态标签先 **dry-run**：接入平台的项目跑 `codex/tools/mark-completed-issues.sh --repo <checkout> --project <id> --range <range>`，验证逐 Issue 判定计划。未接入的项目确认 `Closes #N` 已把 Issue 关掉。同时对本 Issue 跑一次 `codex/tools/apply-classification-labels.sh --verify N`（**用编号，不用 `--range`**）：报 `projection-window-closed` 说明合并前那一步漏了，如实记录并按 `03` §11 处置，**不补写、不加 override**。

   念计划前先读第一行 `{"selector":"range",…}`：`commits` 是这个 range 实际覆盖的 merge，
   逐 Issue 行的 `commit` 是产出它的那条。**核对它就是第 1 步认定的那个 merge**；
   不是就说明范围瞄错了，重跑之前不要往下走。`origin/main~N` 在工具启动那一刻求值，
   不是在你 fetch 那一刻——`#167` 收尾时它就静默指向了别人刚合并的 Issue（#175）。
3. merge receipt 已提供终态 mutation 权限；验证计划瞄准第 1 步的 exact merge 后直接加 `--apply`，
   **并且用计划回给的 `pinned` 编号，不再传 `--range`**：
   `codex/tools/mark-completed-issues.sh --repo <checkout> --project <id> --apply <pinned>`。
   人点头与你敲 `--apply` 之间 `origin/main` 还会移动，同一个 `--range` 第二次解析可以
   落到另一个 Issue 上；Issue 编号不会移动。**终态判定取自文档与 manifest**：summary 的
   `required_docs` 含不含 `verification`，以及该项目在 `gitea-governance.json` 里的
   `deployment_lifecycle`——只有 `application-deploy`（合并即部署）会让计划显示 `skip
   requires-deployment` 去等一次必然到来的部署，`none` 与缺省的 `application-deploy-selective`
   都当场到 `completed`（#192）。两个条件都由工具读取，不要自己判断该写 `completed` 还是
   `deployed`；计划里出现你不认识的 `reason` 时读 `detail`，它写着依据。
4. 文档自查：接入平台的项目跑 `check-change-documents --repo <checkout>`。
5. 清理：**先离开 worktree**，再 `git worktree remove <path>` 与 `git branch -d change/N-slug`。站在 worktree 里删自己脚下的目录会失败。
6. 盘点衍生 Issue：有调度会话就 `send_message` 回报，没有就自己开 Issue 并派卡片。
7. 报告 exact merge/receipt、终态、文档检查、worktree/本地分支清理与未执行项，然后直接执行
   `archive_session("self")`。任何确定性收尾失败都必须保留会话并报告真实 blocker，不得伪报已归档。

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
- 「我顺手把别人那个 worktree 变基一下，反正 main 已经前进了」→ 那是别人的证据链，通知或交回
- 「推完了，PR 建出来就行」→ 先核对返回体的 `pushed_head` 是不是你核验过的那个 SHA
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
| 进别人的 change worktree 代劳变基或修冲突 | 冲突解决无归属，验收证据来源不可分辨，错误跟着对方的 PR 直达唯一交付闸门（#298） |
| 推送后不核对 `pushed_head` | 跳过了中途改写唯一确定性可检出的时刻，PR 带着没读过的内容进入 review |
| 只在上下文里记依赖 | 会话一压缩，顺序关系就丢了 |
| 靠印象填 `cwd` | 会话开在错误目录，或开在根本不存在的路径上 |

## 平台适配

- **接入 AISoft 平台的项目**：Issue/PR/push 走 broker typed 操作；命名元组、AI 判级、语义文档合同见 `aisoft-platform` skill。
- **未接入的项目**：用该项目自己的 tracker 与 `git`/`gh` 等价物。会话模型、待合并格式、收尾 7 步不变。
