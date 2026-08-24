---
issue: 163
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/163
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - deployment-boundary
depends_on: []
status: approved
branch: change/163-declare-deployment-lifecycle
created: 2026-08-24
updated: 2026-08-24
---

# Spec：给「有没有应用部署链路」一个仓库级声明

## 1. 目标与原因

让「声明 `verification` 但不经过应用部署链路」的变更有一条确定性路径到达明确终态。

今天的判定点只有一个条件（`required_docs` 是否含 `verification`），它被迫同时回答两个问题：
「这次变更欠不欠验证记录」与「这次变更走不走应用部署链路」。第二个问题不是变更的属性，
是仓库的属性——`aisoft-platform` 里没有任何变更走应用部署链路。缺这一维的后果已经落地：
#138、#146、#148 三个已合并 closed Issue 至今一个标签都没有。

本 spec 把第二个问题移出判级产物，交给 governance manifest 的仓库条目回答一次。

## 2. Acceptance criteria

映射关系：Issue 正文 AC-1 → 本文 AC-1/AC-2/AC-3；AC-2 → AC-6；AC-3 → AC-7；AC-4 → AC-8。

- [ ] **AC-1 声明存在且被 schema 接住**：`codex/config/gitea-governance.json` 的
      `aisoft-platform` 条目含 `"deployment_lifecycle": "none"`；
      `aisoft_gitea_governance.contract` 接受该键、把它读进
      `RepositoryContract.deployment_lifecycle`，并拒绝取值集合以外的字符串。
      未声明该键的仓库条目继续通过校验，取缺省 `application-deploy`。
- [ ] **AC-2 判定变成合取**：`mark-completed-issues.sh` 仅在
      「`required_docs` 含 `verification`」**且**「项目未声明 `deployment_lifecycle: none`」
      时跳过并给出 `requires-deployment`。两个条件都取自仓库证据，
      工具不新增任何接受终态、部署与否或 `deployment_lifecycle` 取值的命令行参数。
- [ ] **AC-3 新路径写 `completed` 并说明依据**：`required_docs` 含 `verification`
      且项目声明 `none` 时，工具输出 `action: "set-completed"` 且
      `reason: "no-deployment-chain"`；`--apply` 时经 broker
      `gitea.issue.labels.set --lifecycle completed` 写入。
- [ ] **AC-4 缺省与既有行为逐条不变**：未声明 `deployment_lifecycle` 的项目，
      三种输入（不含 verification / 含 verification / 无映射文档）的计划与写入
      与本变更前完全一致。
- [ ] **AC-5 manifest 读不到是错误，不是静默跳过**：manifest 文件不存在或不是合法 JSON 时，
      工具以非零退出并说明；manifest 里查不到该项目条目时同样非零退出。
      `--apply` 与 dry-run 两种模式都如此。声明缺失不属于此列（走 AC-4 缺省）。
- [ ] **AC-6 文档与工具一致**：`03` §11 的判定依据改写为合取并说明哪些仓库有链路；
      `02` §9 指回该声明；`skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步
      说明判定同时取自文档与 manifest；`classification.py` 的 `route()` 注释与
      `test_change_control.py` 中陈述旧双重语义的 docstring 同步更新。
      按上述任一文档执行，得到的结论与工具实际行为一致。
- [ ] **AC-7 #138/#146/#148 有明确处置**：结论为补写 `completed`，
      依据是 `aisoft-platform` 声明 `none` 使 `deployed` 不可达；
      执行由人显式运行本工具，默认只出逐 Issue 计划（无 `--apply` 时不发生任何 broker 调用），
      可拒绝。summary 记录该结论与「为何这与 #160 的 closed-Issue 姿态不矛盾」。
- [ ] **AC-8 全绿且新路径有测试**：`bash codex/tests/smoke.sh` 全绿；
      AC-1..AC-5 每条都有断言覆盖，且新用例在没有真实 Gitea、真实 broker 与真实 Issue 的
      前提下运行。

## 3. 接口、数据与兼容性影响

### 3.1 manifest 仓库条目（新增可选键）

```json
{ "name": "aisoft-platform", "...": "...", "deployment_lifecycle": "none" }
```

| 取值 | 含义 |
|---|---|
| `application-deploy` | `02` §9 的应用部署链路会在健康检查成功后写 `deployed`。**缺省**。 |
| `none` | 没有那条链路，`deployed` 不可达，`completed` 是唯一终态。 |

缺省取 `application-deploy`：更严的一档，使既有仓库行为完全不变，
也保证「读不到声明」永远不会意外放宽。与 #148 的 `change_control` 缺省 `production` 同一条规则。

`deployment_lifecycle` 是**收窄声明**，只影响合并后的终态记账。它不改变 CI、
不触发或抑制任何部署、不改变分支保护，也不改变 `required_docs` 该不该含 `verification`。

### 3.2 `mark-completed-issues.sh`

manifest 位置按既有的两条解析姿态，不新增第三条规则：

1. `AISOFT_GOVERNANCE_MANIFEST`（`aisoft_loop/change_control.py` 已定义的同一个环境变量）
2. `<tool_dir>/../config/gitea-governance.json`（仓库布局优先，与本文件解析 `PYTHONPATH` 的注释同构）
3. `/usr/local/share/aisoft/gitea-governance.json`（扁平安装）

输出 schema 不变，仍是每行一个 JSON 对象；新路径复用既有的 `reason` 键。
既有调用方（`issue-session-flow` 收尾第 2/3 步）的命令行不变。

### 3.3 兼容性

- 未声明该键的九个仓库：schema 校验、计划与写入逐条不变。
- 已合并的历史 change 文档：不读、不改、不迁移。
- broker：不新增 typed 操作，不改参数；写入仍是既有的
  `gitea.issue.labels.set --lifecycle completed`，操作表停在 30。

## 4. 风险与回滚约束

- 回滚 = revert 本 PR。manifest 少一个可选键、工具回到单条件判定，无数据迁移、
  无外部状态需要撤销。已经写进 Gitea 的 `completed` 标签不会被 revert 撤回，
  但那正是 `03` §11 要求的终态，不需要撤。
- 本变更不部署、不迁移、不改 CI，因此 `required_docs` 不含 `verification`
  （沿用模板「部署或迁移再追加 verification」的作者规则）。
  AC-8 的证据写在 plan 的「测试与验收映射」与 PR 正文里。
- 合并后有两个显式的人工步骤，都不是本 PR 的交付物，也都不阻塞终态判定在平台 checkout 上生效：
  重装 governance manifest（影响扁平安装）与重装 Claude skills（消除 `check-drift` 漂移）。

## 5. 治理文件修改授权

按 `AGENTS.md`「只有 complex 变更映射的 spec 明确授权时，才能修改 Agent 行为、
controller、CI/部署脚本或其他治理文件」，本 spec 授权且仅授权以下修改：

- `codex/config/gitea-governance.json`：仅给 `aisoft-platform` 条目增加
  `deployment_lifecycle` 一个键，不动任何其它字段或仓库。
- `codex/runtime/aisoft_gitea_governance/contract.py`：仅接住并校验该键。
- `codex/tools/mark-completed-issues.sh`：仅改终态判定条件与 manifest 解析。
- `03` §11、`02` §9、`skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步：
  仅同步判定依据的陈述。
- `classification.py` 的 `route()` 注释、`test_change_control.py` 的用例 docstring：
  仅同步陈述，**不改 `route()` 的任何行为**。

不授权修改 `AGENTS.md`、controller、CI/部署脚本、broker 操作表、标签 manifest
与 analyzer 判级判据。

## 6. 非目标

- 不改 `apply-classification-labels.sh` 与 `gitea.issue.labels.classify`（#160 交付物）。
- 不引入自动部署、自动合并，或任何在人之外自动推进终态的组件。
- 不给 `mark-deployed-issues.sh` 增加对称的拒绝逻辑：它是应用仓库 workflow 里的
  best-effort 部署钩子，`deployment_lifecycle: none` 的仓库根本没有能调用它的 workflow。
  真需要那道防线时另开 Issue。
- 不改「何时该声明 `verification`」的作者规则、summary/verification 模板与
  `gitea-analyze-change` 的 analyzer 指引。本变更解耦的是**终态判定**，
  不是 `required_docs` 的填写规则。
- 不补写、不迁移、不重命名任何历史 change 文档或分支。

## 7. 未决问题

无。
