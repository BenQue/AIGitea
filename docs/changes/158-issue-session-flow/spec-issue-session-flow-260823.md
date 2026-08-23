---
issue: 158
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/158
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/158-issue-session-flow
created: 2026-08-23
updated: 2026-08-23
---

# Spec

## 目标与原因

给「开 Issue 解决问题」这件事补上**会话这一层**的契约，并把它固化成一份可安装、可校验、
可版本化的 Claude 侧技能 `issue-session-flow`。

平台现有合同止于「Loop 开出最终 PR」。`03` §11 已确认没有任何组件能观察到合并，
因此合并之后的一切——终态标签、文档自查、worktree 清理、衍生 Issue、会话归档——
全部落在人和会话身上，而这一段此前没有任何书面清单。本变更补上它。

技能主干必须**通用**（适用于任何项目与任何 issue tracker），平台特有工具以适配层出现。
这样它在未接入 AISoft 平台的项目里依然可用，也不会把平台细节固化成不可迁移的假设。

**本 spec 明确授权**修改 `skill-for-claude/` 下的 Claude Agent 行为契约与其安装工具
（`AGENTS.md` 要求 Agent 行为变更须由 complex 变更映射的 spec 显式授权）。
授权范围仅限技能**源文件**与安装/漂移工具；不授权在本次运行中安装到 `~/.claude/skills/`，
也不授权修改 `AGENTS.md`、controller、CI 或部署脚本。

## Acceptance criteria

- [ ] **AC-1** `skill-for-claude/issue-session-flow/SKILL.md` 存在；YAML front matter 含合法
      `name: issue-session-flow` 与 `description`；description 同时覆盖「开 issue」「多个 issue」
      「调度」「PR 合并」「收尾」「归档」六类触发词。
- [ ] **AC-2** `skill-for-claude/` 为多技能布局（`skill-for-claude/<skill-name>/SKILL.md`）；
      迁移后的 `skill-for-claude/aisoft-platform/SKILL.md` 内容与迁移前逐字节一致，
      **除了**新增的指向 `issue-session-flow` 的交叉引用行。
- [ ] **AC-3** 在一个空的临时 HOME 上 `bash skill-for-claude/install.sh "$tmp_home"` 成功，
      产出 `$tmp_home/.claude/skills/aisoft-platform/`（含 `SKILL.md` 与 `references/`）
      与 `$tmp_home/.claude/skills/issue-session-flow/SKILL.md`；
      紧接着再执行一次，退出码 0 且安装树逐文件相同（幂等）；
      随后 `bash skill-for-claude/check-drift.sh "$tmp_home"` 无 `DRIFT` 输出且退出码 0。
- [ ] **AC-4** 对未安装的临时 HOME，`check-drift.sh` 输出 `NOT_INSTALLED` 且退出码 0；
      安装后任意修改一个已安装技能文件，`check-drift.sh` 输出含 `DRIFT` 且退出码 1。
- [ ] **AC-5** exact-managed-tree 语义保持：在某个受管技能目录内放入一个陌生文件后再次
      `install.sh`，该文件被 prune；`install.sh` 拒绝 symlink 形式的技能目标；
      **且**不触碰 `~/.claude/skills/` 下本仓库未声明的其它技能目录。
- [ ] **AC-6** `bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-7** `issue-session-flow/SKILL.md` 正文包含完整的 7 步收尾清单，并显式写明两个陷阱：
      (a) `git worktree remove` 前必须先离开该 worktree；
      (b) `host-access-broker.json` 中 `mac_checkout` 为 `null` 的项目不得拼路径，必须停下来问人。

## 接口、数据与兼容性影响

### 技能规定的会话模型（技能正文的规范内容）

**两种会话角色**：

| 角色 | 开在哪 | 必须做 | 禁止做 |
|---|---|---|---|
| 调度会话 | 这批 Issue 的相关项目 checkout | 拆分需求成 Issue、决定并行/顺序、派单、跟踪、收口 | 实现任何 Issue、建 change worktree、写实现代码 |
| Issue 会话 | 该 Issue 的目标项目 checkout | 一个 Issue 从 triage 到 PR 到收尾到归档 | 处理别的 Issue、合并 PR |

**调度会话的开启条件**（三选一，否则不开）：一个大阶段新任务需要拆成多个 Issue；
一次新生成了多个 Issue；需要处理多个已有 Issue。

**Issue 会话状态机**，用 `set_session_title` 对外可见：

```
#N slug · 进行中  →  #N slug · 待合并  →  （收尾）  →  归档
```

**「待合并」提示为固定格式**，PR 开完即输出，会话停在此处等人：

```
🔵 需要你合并 —— #N <标题>
PR:   <url>
变更: <一句话>
CI:   <读回的真实状态>
合并后回来说「合并了」，我做收尾并归档本会话。
```

**收尾清单 7 步**（人确认已合并后执行）：
1. 取回主干并确认 merge commit 真实存在（不接受口头结论作为证据）。
2. 平台项目：`mark-completed-issues.sh --repo <checkout> --project <id> --range <range>` **dry-run**，
   把逐 Issue 判定计划念给人。非平台项目：确认 Issue 已因 `Closes #N` 关闭。
3. 人点头后才加 `--apply` 写终态标签。终态判定取自文档，AI 不得二次判断。
4. 文档自查（平台项目 `check-change-documents`）。
5. 清理：先离开 worktree，再 `git worktree remove` 与删除本地分支。
6. 盘点衍生 Issue：有调度会话则回报，无则自建 Issue 与派单卡片。
7. `archive_session("self")` 归档本会话（工具自身会向人确认）。

**衍生 Issue 与琐事例外**：可顺手做的仅限「不改变外部行为 + 不需要独立验收标准 +
在本 PR 已触碰的文件内」；其余一律开新 Issue。该判据与平台 small 判级同源。

**顺序依赖**：依赖关系写进 Issue 正文，并由 Issue 会话抄进 summary front matter 的
`depends_on`，使依赖持久化在 Issue 上而非只活在调度会话的上下文里。

### 安装工具的接口变化

- `install.sh [target_home]` 与 `check-drift.sh [target_home]` 的位置参数与退出码语义不变
  （install 失败非 0；check-drift：`NOT_INSTALLED`→0，无漂移→0，有漂移→1）。
- 受管目标从单一路径 `~/.claude/skills/aisoft-platform` 变为**本仓库声明的每个技能目录**。
  每个技能目录内仍是 exact managed tree；`~/.claude/skills/` 本身不再被整体接管。
- `references/` 仍只来自 `skill-for-codex/references`（单一事实源），且仅安装给声明需要它的技能。

### 兼容性

- 已安装旧布局的机器：重装即收敛，无需人工清理（旧路径 `~/.claude/skills/aisoft-platform`
  在新布局下仍是同一个受管目录）。
- Codex 侧 `skill-for-codex/` 不受影响。

## 风险与回滚约束

- **prune 误删**：受管范围算错会波及用户自有技能。约束：只允许 prune 本仓库声明的技能目录**之内**的内容。
- **合并 ≠ 生效**：技能列表在会话启动时加载，须合并后跑 `install.sh` 并**新开会话**才生效。
- **触发漏命中**：靠 `aisoft-platform` 的交叉引用兜底，不靠 description 抢词。
- **回滚**：本变更只增删仓库内文件，`git revert` 单个 PR 即可完全回滚；
  已安装侧回滚为重跑上一版 `install.sh`。无数据迁移、无部署、无外部状态。

## 非目标

- 不修改 `AGENTS.md`、controller、CI 或部署脚本。
- 不在本次运行中安装技能到 `~/.claude/skills/`。
- 不实现自动开会话（`spawn_task` 只产出待点击卡片，这是刻意保留的人工闸门）。
- 不清理现存残留 worktree（分属各自 Issue）。
- 不改动 Codex 侧技能或 references 的单一事实源结构。

## 未决问题

无。
