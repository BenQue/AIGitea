---
issue: 184
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/184
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: []
depends_on: []
status: contract-drafting
branch: change/184-project-target-fail-closed
created: 2026-08-24
updated: 2026-08-24
---

# Spec：判级投影与收尾工具的目标仓库由 checkout 判定，不自洽即 fail-closed

## 目标与原因

让 `apply-classification-labels.sh` 与 `mark-completed-issues.sh` **不可能**在操作者没有明确
说出目标项目时，产出或写入一个针对另一个仓库的结论。

现状的失效模式是一个未经证据核对的默认值：判级值来自 `--repo`，Issue 读写来自 `--project`
的默认值 `aisoft-platform`，两者在漏传 `--project` 时指向不同仓库而无人核对。它把 #167 的
判级闸门变成假通过（证据见 summary 与 verification），而窗口在合并时永久关闭、没有 override。

修复的形状不是「加一个警告」而是**换掉证据来源**：`--repo` 的 Git remote 就是「这个 checkout
属于哪个仓库」的权威答案，也正是 Issue 将要被读写的那个仓库。目标因此被**推断**出来，
`--project` 从默认降级为覆盖，两者不自洽即停止。

## Acceptance criteria

- [ ] **AC-1**　漏传 `--project` 时，两个工具都不得产出针对另一个仓库的结论。目标 `project_id`
      由 `--repo` 的 Git remote URL 反查 host access manifest 得到；判级/收尾判据的来源
      （checkout）与 broker 调用的 `--project` 必须是同一个项目。回归测试断言 broker 收到的
      `--project` 等于推断值，且从未收到 `aisoft-platform`。
- [ ] **AC-2**　`--verify` 同受此保护。回归测试复刻真实世界的假通过形状：fixture checkout 的
      summary 声明 `platform`/`complex`；被误读的另一个项目的**同号** Issue 恰好带
      `type/platform` + `complexity/complex`；而目标项目的该 Issue 标签为空。断言
      `--verify`（不传 `--project`）**非零退出**且报 `projection-missing`，不得出现
      `result: "projected"`。
- [ ] **AC-3**　显式 `--project` 与 `--repo` 推断结果不一致时 fail-closed：非零退出、
      stdout 不产出任何 Issue 行、broker 一次都不被调用（读操作也不调用）。错误信息同时点名
      推断值与传入值。
- [ ] **AC-4**　目标无法确定（checkout 的 remote 不匹配 manifest 里任何项目，且未显式传
      `--project`）时同样 fail-closed，非零退出且不调用 broker；错误信息给出可执行补救，
      逐字包含 `--project`。
- [ ] **AC-5**　两个工具的每一行 JSON 输出都带 `project` 与 `repository` 字段，指名它在谈论
      哪个项目与哪个仓库；`--apply` 与 `--verify` 的输出行同样带这两个字段。
- [ ] **AC-6**　`--project <project_id>` 仍是权威覆盖：checkout 推断不出项目时（无 Gitea
      remote 的 clone、VM 上的工作副本），显式传入即可继续，并在输出中标明目标由操作者给出。
- [ ] **AC-7**　无行为回归。`apply-classification-labels.sh`：plan / `--apply` / `--verify`
      三个模式、四种 skip reason（`issue-closed`、`documents-unresolved`、
      `classification-incomplete`、`classification-missing`）、四种 verify 结果
      （`projected`、`projection-missing`、`projection-mismatch`、`projection-window-closed`）、
      `broker-operation-missing` 翻译、`--range` 解析、`--verify --apply` 互斥全部保持。
      `mark-completed-issues.sh`：#163 的 `deployment_lifecycle` 判定与 #172 的
      `project_id → repository` 反查方向全部保持。`bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-8**　`codex/tools/` 下带 `--project` 默认值的脚本核查结论写进 summary，
      并在 `03` 的相应段落里把新合同写清楚（不传 `--project` 时目标从哪里来）。

## 接口、数据与兼容性影响

**命令行合同（破坏性，故意）**

| | 变更前 | 变更后 |
|---|---|---|
| 不传 `--project`，checkout 可推断 | 静默使用 `aisoft-platform` | 使用推断出的项目 |
| 不传 `--project`，checkout 不可推断 | 静默使用 `aisoft-platform` | 非零退出，提示传 `--project` |
| 传 `--project` 且与推断一致 | 使用传入值 | 使用传入值（不变） |
| 传 `--project` 且与推断不一致 | 静默使用传入值 | 非零退出 |
| 传 `--project` 且 checkout 不可推断 | 使用传入值 | 使用传入值（不变） |

在平台仓自身调用（现有文档与 skill 里的全部无 `--project` 调用）推断结果就是
`aisoft-platform`，可观察行为不变。

**输出 schema（向后兼容的增量）**：每行新增 `project` 与 `repository` 两个字符串字段。
既有字段的名称、取值与出现条件不变；既有 `jq 'select(...) | ...'` 断言不受影响。

**新增文件**：`codex/tools/aisoft-project-target.sh`，被两个工具以「同目录优先，其次仓库布局」
的既有约定 source。它不是可执行入口，不进任何安装脚本（这两个工具本身也不安装，从 checkout 运行）。

**manifest 依赖**：`aisoft-project-target.sh` 读 host access manifest 的
`projects[].project_id` / `projects[].repository`，以及 governance manifest 的
`base_url` / `owner`（仅用于构造期望 remote URL）。解析顺序沿用既有三级：
`AISOFT_ACCESS_MANIFEST` / `AISOFT_GOVERNANCE_MANIFEST` 环境覆盖 → `<tool_dir>/../config/`
仓库布局 → `/usr/local/share/aisoft/` 扁平安装。读不到即报错，与 `mark-completed-issues.sh`
既有姿态一致（无法满足的前置条件是错误，不是静默跳过）。

**匹配规则**：期望 URL 为 `<base_url>/<owner>/<repository>.git`，与
`aisoft_host_access.broker._expected_git_url` 同一构造。checkout 的**全部** remote 的 fetch 与
push URL 参与匹配（`newemaint` / `sfm-digital-board` 的 Gitea remote 名为 `gitea` 而非
`origin`，只看 `origin` 会漏）。比较前两侧同样地去掉结尾的 `/` 与 `.git`。命中多于一个项目
时视为歧义并 fail-closed。

## 风险与回滚约束

- 只有 Gitea remote 才能推断。实测 `rsdesign-new` 的 checkout 只有 GitHub remote，
  从此需要显式 `--project rsdesign-new`。这是 fail-closed 的预期形态：在此之前它得到的是一个
  针对平台仓的**错误**结论，报错严格优于错答。
- 两个工具都是「操作者主动运行」的姿态，前置条件不满足即报错，本变更不改变这一点。
- 回滚：纯脚本与测试变更，`git revert` 单个 commit。无数据库迁移、无持久状态、无部署。

## 非目标

- 不改 broker、不新增 typed 操作、不改 manifest 内容。
- 不改判级规则、不改标签合同、不改 `--verify` 的四种结论语义。
- 不动 #172 建立的 `project_id → repository` 反查方向，也不重新引入 repository name 作为
  `--project` 的合法取值。
- 不处理 Issue #173：核查确认它与已合并的 #172 是同一缺陷，`main` 上已修复，属重复条目；
  本变更不改动其结论，也不代为关闭。
- 不修改 `mark-deployed-issues.sh`：它没有 `--project`，不存在本缺陷的形状。
- 不为推断不出项目的 checkout 增加任何猜测性回退（例如按目录名、按 `.aisoft/` 猜）。

## 未决问题

- 无。
