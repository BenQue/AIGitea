---
issue: 184
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/184
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 平台治理工具的 --project 命令行合同改变（默认值移除、目标改由 checkout 推断、不自洽即 fail-closed），触及判级投影与收尾两条治理路径
risk_flags: []
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-project-target-fail-closed-260824.md
  spec: spec-project-target-fail-closed-260824.md
  plan: plan-project-target-fail-closed-260824.md
  verification: verification-project-target-fail-closed-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/184-project-target-fail-closed
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/188
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`codex/tools/apply-classification-labels.sh:47` 的 `project="aisoft-platform"` 是一个
**从不与任何证据核对的默认值**。漏传 `--project` 时判级值来自 `--repo` 指向的目标仓
checkout，Issue 状态、标签读回与写入却落在**平台仓**，脚本从不核对两者是否指向同一个仓库。

结果不是崩溃，而是一个自洽、格式完好、但针对另一个仓库的结论。真实影响是 #167 的判级闸门
被反转：`--verify` 是唯一能区分「已投影」与「从没投影过」的检查，而窗口在合并时永久关闭。

2026-08-24 实测的两个方向（完整命令与输出见映射的 verification）：

- **假失败**：`--verify 73 --repo <LocalWMS>` 报 `projection-window-closed`（「判级已永久丢失」），
  而 LocalWMS #73 实际带着 `type/docs` + `complexity/small`，投影完全正确。
- **假通过**：`--verify 1 11 57 --repo <LocalWMS>` 退 0、三行全部 `result: "projected"`，
  而这三条 LocalWMS Issue 上 `type/*` 与 `complexity/*` **一个都没有**。它读的是平台仓同号
  Issue，那三条恰好带 `type/platform` + `complexity/complex`——平台仓里最常见的一对组合。

假通过这个方向才是致命的：它让「进入待合并前必须读回 `projected`」这道硬闸门，在判级根本没
投影的情况下干净通过，而且一旦 PR 合并，窗口就永久关上、没有 override。

## 影响范围

- `codex/tools/apply-classification-labels.sh`：读与写两个模式全部中招。
- `codex/tools/mark-completed-issues.sh:33`：**同一形状**的未核对默认值。它写生命周期标签
  （`gitea.issue.labels.set --lifecycle completed`），比本 Issue 的读更危险——漏传 `--project`
  会把目标仓的收尾判定写到平台仓的同号 Issue 上。一并修。
- `codex/tools/mark-deployed-issues.sh`：**不在此列**。它没有 `--project`，目标仓库由部署钩子的
  `GITEA_OWNER`/`GITEA_REPO` 环境变量给出，不存在「默认值 vs `--repo`」这对不自洽的来源。
- `codex/tools/` 下其余脚本：`grep -rn -- '--project)' codex/tools/` 只命中上面两个，核查完毕。
- 项目面：manifest 里 10 个项目，除 `aisoft-platform` 自己以外的 9 个全部中招；
  `aisoft-platform` 恰好等于那个默认值，所以在平台仓上一直是对的——这正是它长期隐身的原因。

## 初步方案与建议

`--repo` 已经指向一个具体 checkout，而它的 Git remote 就是「这个 checkout 属于哪个仓库」的
权威答案——也正是 Issue 将要被读写的那个仓库。方向因此是把目标**推断**出来而不是**默认**出来：

1. 新增被两个工具共享的 `codex/tools/aisoft-project-target.sh`，从 `--repo` 的 remote URL 反查
   host access manifest 的 `projects[]`，得到 `project_id` 与 `repository`。
2. 移除 `project="aisoft-platform"` 默认值。`--project` 从「默认」降级为「覆盖」。
3. 推断值与显式 `--project` 不一致 → fail-closed，非零退出、不产出任何 Issue 行、不发生任何写。
4. 两者都无法确定 → fail-closed，错误信息给出可执行补救（传 `--project <project_id>`）。
5. 每一行输出带上 `project` 与 `repository`，让「在谈论哪个仓库」不再需要靠人回忆。

命名空间仍然只认 broker 的 `project_id`，不回退 #172 建立的 `project_id → repository` 反查方向。

## 风险

- **推断失败面**：只有 GitHub remote 而没有 Gitea remote 的 checkout（实测 `rsdesign-new` 属于
  这一类）推断不出项目，需要显式 `--project`。这是 fail-closed 的预期形态，不是回归——
  在此之前它得到的是一个针对平台仓的错误结论。
- **新增 manifest 依赖**：`apply-classification-labels.sh` 此前不读任何 manifest，现在需要
  host access manifest 与 governance manifest（后者只取 `base_url`/`owner` 构造期望 URL）。
  沿用 `mark-completed-issues.sh` 已有的三级解析顺序（环境覆盖 → 仓库布局 → 扁平安装）。
- **调用方影响**：现有文档/skill 里不带 `--project` 的调用只在平台仓自身使用，推断会给出
  `aisoft-platform`，行为不变；在别的仓上它们本来就是错的。
- **回滚**：纯脚本变更，`git revert` 单个 commit 即可，无迁移、无状态、无部署。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 平台治理工具的 --project 命令行合同改变（默认值移除、目标改由 checkout 推断、不自洽即 fail-closed），触及判级投影与收尾两条治理路径
risk_flags: []
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- AGENTS.md：「Agent 或平台治理变更一律按 complex 处理」。本变更改的是判级投影与收尾这两条
  治理路径的执行工具，落在该强制规则内。
- `03` §4：`type/platform`（改变平台行为或治理合同）强制 complex。
- `contract_effect: change`：`--project` 的默认值被移除，命令行合同对既有调用方发生可观察的
  改变——此前不传即静默使用 `aisoft-platform`，此后不传要么由 checkout 推断、要么报错。
  这是外部契约变更，本身也强制 complex。
- `required_docs` 含 `verification`（`03` §3）：AC-2 的核心证据是真实系统上的一次性观测——
  LocalWMS #1/#11/#57 在改动前假通过、改动后不再假通过。这属于「改动前才观测得到的基线」与
  「required CI 不跑的跨仓命令」，diff review 与 CI 都无法复现。

### 缺失的 acceptance criteria 或决策

- 无。Issue #184 已给出 AC-1..AC-8，spec 逐条落成可测形式。
