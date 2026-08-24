---
issue: 175
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/175
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: approved
branch: change/175-pin-finishing-range
created: 2026-08-24
updated: 2026-08-24
---

# Spec · 收尾路径的范围选取不再锚在会移动的 ref 上

## 目标与原因

收尾第 2 步用 `--range 'origin/main~N..origin/main'` 选取要写终态标签的 Issue。
`origin/main~N` 在**工具启动那一刻**求值，不是在 `git.fetch.main` 那一刻，也不是在人
点头那一刻。于是有两个窗口，任何一个里 `origin/main` 前进一次，范围就整体后移：

| 窗口 | 两端 | `#167` 是否实测到 |
|---|---|---|
| W1 | `git.fetch.main` → 跑计划 | 是。计划返回 `{"issue":168,...}` 而不是 167 |
| W2 | 跑计划 → 跑 `--apply` | 未实测。合同要求两者之间隔一次人工确认，窗口更长 |

写错既不报错也不易发现：错的对象是别人刚合并的 Issue，而 `completed` 恰恰常常正是它
该有的标签。目标是让**范围覆盖了哪些 merge** 这件事在 `--apply` 之前肉眼可查，并让
`--apply` 不再重新解析一个会移动的 ref。

本 spec 授权修改治理文件：`codex/tools/` 下两个工具、`codex/agent/` 新增一个 sourced
library、`skill-for-claude/issue-session-flow/SKILL.md` 与 `03` §11。

## Acceptance criteria

- [ ] **AC-1** 收尾路径上存在一条确定性做法，使范围覆盖哪些 merge 不依赖 `origin/main`
      在两条命令之间没有移动过。具体形态：接受 `--range` 的工具在计划输出里交回一个
      `pinned` 选择器，其内容是本次解析得到的 Issue 编号（不可变），收尾合同改为
      「用 `--range` 跑计划，用 `pinned` 的编号跑 `--apply`」；`issue-session-flow`
      收尾第 2、3 步与 `03` §11 同步改写。
- [ ] **AC-2** 计划输出能让人在 `--apply` 之前看出每个 Issue 是从哪条 commit 推导出来的，
      不必另行 `git log` 反推。具体形态：使用 `--range` 时先输出一行
      `{"selector":"range","range":<字面量>,"commits":[{"commit":<完整 sha>,"subject":<subject>,"issues":[N,…]}],"pinned":"N …"}`，
      且每条逐 Issue 行带 `commit` 字段指向产出它的那条 commit。
- [ ] **AC-3** 不改 `mark-completed-issues.sh` 的终态判定合取（`required_docs` ∧
      `deployment_lifecycle`，#163）与 `apply-classification-labels.sh` 的判级取值来源
      （summary 的 `change_type` / `effective_complexity`，#160）及窗口姿态（closed 不补写、
      无 override，#167）。不引入自动合并、自动写标签。逐 Issue 行的既有字段与语义不变。
- [ ] **AC-4** 三个工具得到一致处置：`mark-completed-issues.sh` 与
      `apply-classification-labels.sh` 同改；`mark-deployed-issues.sh` **不改**，并在
      `03` §11 与工具头部注释里写明理由（它不接受 `--range`，锚是部署已 checkout 的
      `HEAD` 或显式的 `MERGE_MESSAGE_FILE`，不存在第二条命令，且它的 hook 姿态是任何
      缺失前提都 warn + exit 0，不能引入需要人读的计划）。该「不接受 `--range`」的事实
      由测试钉住，防止日后被悄悄加上。
- [ ] **AC-5** `bash codex/tests/smoke.sh` 全绿，新行为有测试覆盖，其中包含一条在 fixture
      仓里确定性复现「两条命令之间 main 前进一次」的用例。

## 接口、数据与兼容性影响

**新增 sourced library** `codex/agent/change-merge-range.sh`，与既有 `gitea-token.sh`、
`gitea-label-manifest.sh` 同一约定：只被 source、不改调用方 shell 选项、数据走 stdout、
诊断走 stderr、按 same-directory-first 再 `../agent/` 解析。两个工具此前逐字重复的
`--range` awk 块由它取代——抄第二遍已经让一个缺陷长在两处。

**输出兼容性**：逐 Issue 行新增 `commit` 字段（仅 `--range` 路径有值，裸编号路径省略，
沿用既有「空值不输出该键」的 `emit` 约定）。新增的 `selector` 行没有 `.issue` 键，因此
既有的 `jq -e 'select(.issue == N) | …'` 断言不受影响。退出码语义不变。

**错误面**：`--range` 解析出 0 个 commit 时不再复用 `no Issue selector given`（那句话说
「你没给选择器」，与事实不符），改为自己的错误，指出该 range 命中 0 个 commit。

**不改 broker**：不新增、不修改任何 typed 操作。写路径仍是既有的
`gitea.issue.labels.set` 与 `gitea.issue.labels.classify`，参数不变。

## 风险与回滚约束

- 改 skill 源即改 Agent 行为合同，改完须跑 `skill-for-claude/install.sh` 才对已安装副本
  生效；drift 由既有 `check-drift.sh` / `test-install-claude-skills.sh` 覆盖，本次不改它们。
- `pinned` 是从本次解析得到的编号，不是从 Gitea 读的。若解析本身瞄错，`pinned` 会忠实
  地把错的编号钉住——所以 `commits` 行与 `pinned` 必须同时输出：前者是让人判断有没有
  瞄错的证据，后者只是把已经过目的结论固定下来。二者顺序不可颠倒。
- 回滚：本变更全部落在两个工具、一个新 library、一个 skill 与两份文档，无迁移、无部署、
  无 broker 变更，`git revert` 单个 merge 即可完全回滚。

## 非目标

- 不改判级投影的窗口姿态（#167 交付物），不补写已关闭 Issue。
- 不引入串行化并行会话的机制。本 Issue 只要求瞄错可见、锚点不移动。
- 不给 `mark-deployed-issues.sh` 增加 `--range` 或计划输出。
- 不改终态判定合取与判级取值来源（AC-3）。
- 不改 `--apply` 的写路径、退出码与 broker 参数面。

## 未决问题

无。
