---
issue: 175
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/175
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写收尾路径的范围选取合同，让接受 --range 的两个治理工具在写入前报出实际解析的 commit 并交回一个不可移动的重跑选择器，同时改写 issue-session-flow 收尾第 2 步与 03 §11；属平台与 Agent 治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-pin-finishing-range-260824.md
  spec: spec-pin-finishing-range-260824.md
  plan: plan-pin-finishing-range-260824.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/175-pin-finishing-range
pr_url: ''
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

收尾第 2 步的 `--range 'origin/main~N..origin/main'` 把范围**锚在一个会移动的 ref 上**。
`origin/main~1` 不是在 `git.fetch.main` 那一刻求值的，而是在工具启动那一刻求值的；
两者之间只要有别的会话合并一次，范围就整体后移一个 merge，静默指向别人的 Issue。

`#167` 收尾时实测到了这一幕：`git.fetch.main` 取回时 `origin/main` = `770d527`（#167 的
merge），下一条 `mark-completed-issues.sh --range 'origin/main~1..origin/main'` 却返回
`{"issue":168,...}`——期间 PR #169（Issue #168）被合进 main，`origin/main` 变成 `5faffa7`，
`origin/main~1` 于是等于 `770d527`。钉死到 `770d527^..770d527` 才拿到正确的 `{"issue":167,...}`。

**窗口有两个，不是一个。** 这一点决定了修法：

1. `fetch` → 跑计划之间。`#167` 撞上的就是这一个。
2. 跑计划 → 跑 `--apply` 之间。合同要求先 dry-run、人点头后才 `--apply`，两条命令之间
   隔着一次人工确认，`origin/main` 有更长的时间移动。**把解析结果打印出来只能关掉第一个窗口**：
   `--apply` 那一次会把 `origin/main~1` 从头再解析一遍，人点头时看到的计划与实际写入的对象
   可以是两个不同的 Issue。

失败是静默的：写错的对象是别人刚合并的 Issue，而 `completed` 恰恰常常正是它该有的标签。
既有的「`deployed` 不降级为 `completed`」保护只在目标 Issue 已经是 `deployed` 时才拦得住。

## 影响范围

**接受 `--range` 的是两个工具，不是三个**（Issue 正文按三个描述，此处按仓库证据更正）：

| 工具 | `--range` | 锚 | 本次处置 |
|---|---|---|---|
| `codex/tools/mark-completed-issues.sh` | 有（L112-126） | 调用方给的 range | 改 |
| `codex/tools/apply-classification-labels.sh` | 有（L151-165） | 调用方给的 range | 改 |
| `codex/tools/mark-deployed-issues.sh` | **没有** | `MERGE_MESSAGE_FILE` 或 `git log -1 HEAD` | 不改，见下 |

`mark-deployed-issues.sh` 不接受任何选项。它是部署链路的 hook，在部署已 checkout 的那个
commit 上运行，`HEAD` 与 `MERGE_MESSAGE_FILE` 都已经是钉死的具体对象，不存在「两条命令之间
ref 移动」这件事——它根本没有第二条命令。而且它的姿态是「任何缺失前提都 warn + exit 0，
绝不让已成功的部署失败」，给它加一个需要人读的计划输出会直接违反那个姿态。所以 AC-4 的
一致处置在这里取「明确说明为何不改」这一支。

前两个工具的 `--range` 块是**逐字重复**的（同一段 awk、同一句注释），所以同一个缺陷长在两处。

## 初步方案与建议

- **AC-2 让瞄错在写入前可见**：`--range` 解析改成两段——先 `git log --format=%H` 拿到范围
  实际覆盖的 commit 列表，再逐个 commit 解析 `Closes #N` / `change/N-slug`。计划开头多输出
  一行 `{"selector":"range",...}`，含实际解析的 range 字面量、覆盖的每个 commit（sha +
  subject + 它产出的 Issue），每条逐 Issue 行再带上 `commit` 字段。不必另行 `git log` 反推。
- **AC-1 让锚不再移动**：同一行给出 `pinned`——一个由本次解析结果得到的**不可移动选择器**，
  内容就是 Issue 编号本身（两个工具本来就接受裸编号）。收尾合同改为「用 `--range` 跑计划，
  用计划回给的 `pinned` 编号跑 `--apply`」。Issue 编号是不可变的，第二个窗口因此关闭。
- **空范围不再伪装成「没给选择器」**：范围解析出 0 个 commit 时报自己的错，而不是复用
  `no Issue selector given`——那句话说的是「你没给」，实际是「你给了但它什么都没命中」，
  这正是瞄错的极端形态。
- **共享而不是抄第三遍**：新增 `codex/agent/change-merge-range.sh` 作为 sourced library，
  两个工具都从它取解析结果。抄第二遍已经让一个缺陷长在两处，抄第三遍会让修复也长在两处。

## 风险

- **改收尾合同 = 改 Agent 行为合同**，必须由 spec 明确授权；`skill-for-claude/` 改完要跑
  `install.sh` 才对已安装副本生效（既有 `check-drift.sh` 与 `test-install-claude-skills.sh`
  覆盖该机制，本次不改它）。
- **AC-3 划的两条线**：`mark-completed-issues.sh` 的终态判定合取（`required_docs` ∧
  `deployment_lifecycle`，#163）与 `apply-classification-labels.sh` 的判级取值来源
  （summary 的 `change_type` / `effective_complexity`，#160）和窗口姿态（closed 不补写、
  无 override，#167）**一个字节都不改**。本次只改「哪些 Issue 进入这个判定」，不改
  「进来之后怎么判、判完写什么」。
- **新增一行输出会改变现有调用方的解析**。逐 Issue 行的既有字段与语义不变，新增的是
  一行 `selector` 行与一个 `commit` 字段；按行 `jq -e 'select(.issue == N)'` 的既有断言
  不受影响（`selector` 行没有 `.issue`）。这一点在测试里钉住。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写收尾路径的范围选取合同，让接受 --range 的两个治理工具在写入前报出实际解析的 commit 并交回一个不可移动的重跑选择器，同时改写 issue-session-flow 收尾第 2 步与 03 §11；属平台与 Agent 治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: change`：收尾第 2/3 步的既有做法被改写（`--apply` 不再传 `--range`），
  两个工具的计划输出形状改变。不是恢复既有合同，也不是纯新增。
- 改 `skill-for-claude/issue-session-flow/SKILL.md` 即改 Agent 行为合同，改 `03` §11 即改
  平台流程合同——AGENTS.md 对 Agent 与平台治理变更一律强制 complex，不看范围大小。
- **不需要 `verification`**：按 `03` §「何时声明 `verification`」的判据（证据来源，#168），
  AC-1..AC-5 的全部证据都来自 diff review 与 required CI。移动 ref 这一幕可以在 fixture 仓
  里确定性复现（两次运行之间 `git commit --allow-empty` 一次，同一个 `--range` 命中不同
  Issue），不存在只能在真实环境执行或只能一次性观测到的证据。终态因此是 `completed`
  （本仓 `deployment_lifecycle: none`，#163）。

### 缺失的 acceptance criteria 或决策

- 无。AC-1..AC-5 由 Issue 正文给定。AC-4 所说的「三个接受 `--range` 的工具」与仓库证据
  不符——`mark-deployed-issues.sh` 不接受 `--range`；按 AC-4 允许的「明确说明为何某个不改」
  一支处置，理由见上表下方。
