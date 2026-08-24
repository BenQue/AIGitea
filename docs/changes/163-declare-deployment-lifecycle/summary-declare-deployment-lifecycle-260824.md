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
status: pr-open
branch: change/163-declare-deployment-lifecycle
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/166
created: 2026-08-24
updated: 2026-08-24
reason: 改动 governance manifest 的仓库条目 schema 与合并后终态判定规则，触及部署边界与治理写路径，属平台治理变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-declare-deployment-lifecycle-260824.md
  spec: spec-declare-deployment-lifecycle-260824.md
  plan: plan-declare-deployment-lifecycle-260824.md
---

## 问题/需求总结

`03` §11 规定 `completed` 与 `deployed` 是互斥终态、二者必居其一。声明了 `verification`
的平台变更一个都到不了：

- `mark-completed-issues.sh` 见到映射 summary 的 `required_docs` 含 `verification` 就
  `skip / requires-deployment`（`mark-completed-issues.sh:157`）。
- `deployed` 只由应用部署链路在健康检查成功后经 `mark-deployed-issues.sh` 回写（`02` §9）。
  平台仓库没有那条链路——它本身就是链路——所以没有任何组件会写。

现场证据（2026-08-23 经 broker `gitea.issue.read` 读回，三者均已合并且 closed）：

| Issue | `required_docs` 含 verification | 标签 |
|---|---|---|
| #138 broker-issue-comments-read | 是 | `[]` |
| #146 loop-controller-pr-url | 是 | `[]` |
| #148 declare-change-control | 是 | `[]` |

对照 #152、#158、#160（`required_docs` 不含 `verification`）都拿到了 `completed`。
所以这不是偶发遗漏，而是**声明 verification 就必然卡住**。

根因是**一个谓词被要求回答两个问题**。`classification.py` 的 `route()` 注释把这笔账写得很清楚：

> `required_docs` 含 verification 同时承载着「该变更要部署，终态是 deployed 而非 completed」
> 这一既有语义（见 mark-completed-issues.sh）。

两个问题是：

1. **这次变更欠不欠一份验证记录？** —— 是变更本身的属性，`required_docs` 回答得了。
2. **这次变更走不走应用部署链路？** —— **不是变更的属性，是仓库的属性**。
   `aisoft-platform` 里没有任何一个变更走应用部署链路，`deployed` 在这个仓库上结构性不可达；
   `NewEMaint` 里则确实有。

缺的正是第 2 个维度：判定点只能看 `required_docs`，看不到仓库有没有那条链路。

## 影响范围

判定路径（改既有语义，不新增自动化）：

1. `codex/config/gitea-governance.json` —— `aisoft-platform` 条目新增
   `"deployment_lifecycle": "none"`。这是**唯一**声明处；其余仓库不声明，按缺省
   `application-deploy` 保持今天的行为，一个字节都不改。
2. `codex/runtime/aisoft_gitea_governance/contract.py` —— manifest schema 侧接住新键：
   `DEPLOYMENT_LIFECYCLES` 取值集合、`RepositoryContract.deployment_lifecycle`
   （默认 `application-deploy`）、`_exact_keys` 的 `optional` 集合。
   与 #148 给 `change_control` 加键的做法逐行同构。
3. `codex/tools/mark-completed-issues.sh` —— 判定从单条件变成合取：
   `skip / requires-deployment` 仅当 `required_docs` 含 `verification`
   **且**该项目声明了部署链路；声明 `none` 时 `deployed` 不可达，`completed` 是唯一终态，
   工具照常出计划并写入，`reason` 记为 `no-deployment-chain`。
4. 测试：`codex/tests/test-mark-completed-issues.sh` 补 fixture manifest 与三条新用例；
   `codex/runtime/tests/test_gitea_governance.py` 钉住 schema 的接受/拒绝与缺省。

合同文档（本变更授权修改，见 spec §5）：

5. `03-Issue-Spec-Plan与单闸门开发流程.md` §11 —— 判定依据改写为合取，并新增
   「哪些仓库有部署链路」小节。
6. `02-CI与自动部署流水线.md` §9 —— 补一句指回声明，说明没有链路的仓库不会有人写 `deployed`。
7. `skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步 —— 「终态判定取自文档」
   补成「取自文档与项目的 manifest 声明」。
8. `codex/runtime/aisoft_loop/classification.py` 的 `route()` 注释与
   `codex/runtime/tests/test_change_control.py` 的用例 docstring —— 二者都陈述了旧的
   双重语义，行为不变但陈述必须跟上，否则下一个读者会照旧的说法继续设计。

**不改动**：`apply-classification-labels.sh` 与 `gitea.issue.labels.classify`（#160 交付物，
Issue 明确列为范围外）、`mark-deployed-issues.sh`、analyzer 判级判据、
`required_docs` 何时该含 `verification` 的作者规则与模板、broker typed 操作表、
标签 manifest、CI 与部署脚本、`AGENTS.md`。不引入自动部署或自动合并。

## 初步方案与建议

**判定依据放进 governance manifest，而不是判级产物。** 理由是上面那条：
「走不走部署链路」是仓库属性。放进 summary front matter 等于让每个作者在每次变更上
重新回答同一个问题，答错一次就复现本 Issue；放进 manifest 只回答一次，而且
`gitea-governance.json` 本来就是每仓库交付属性的唯一声明处（#148 的 `change_control`
就在隔壁）。

判定变成合取，两个条件都取自仓库证据、都不接受人工传入：

| `required_docs` 含 verification | 项目 `deployment_lifecycle` | 终态 |
|---|---|---|
| 否 | 任意 | `completed`（既有行为，不变） |
| 是 | `application-deploy`（缺省） | 跳过，等部署链路写 `deployed`（既有行为，不变） |
| 是 | `none` | `completed`，`reason: no-deployment-chain`（新路径） |

manifest 位置沿用本工具已有的两条解析姿态，不新增第三条规则：
`AISOFT_GOVERNANCE_MANIFEST`（`change_control.py` 已经定义的同一个环境变量）→
仓库布局 `codex/config/gitea-governance.json` → 扁平安装
`/usr/local/share/aisoft/gitea-governance.json`。仓库布局优先，意味着从平台 checkout 跑
收尾时合并即生效，不必等两台重装。

**manifest 读不到时报错、不静默跳过。** 这是 `mark-completed-issues.sh` 头部已经写死的姿态：

> a prerequisite it cannot satisfy is an error, because silently doing nothing
> would read as "every Issue was already correct".

读不到 manifest 就无法判断 `deployed` 可不可达，此时沉默跳过恰恰是本 Issue 要修的那个 bug。
但**声明缺失不是错误**：manifest 能读、条目里没有这个键，就是按缺省
`application-deploy` 处理——与 #148 的 default-by-omission 同一条规则。

### AC-3：#138 / #146 / #148 的处置

**结论是补写 `completed`**，依据是 `aisoft-platform` 声明 `deployment_lifecycle: none`，
`deployed` 在该仓库上不可达，因此 `completed` 是唯一可能的终态——这不是一次新的人工判断，
而是本变更那张表的第三行。执行路径就是本变更修好的工具，由人显式运行：

```bash
codex/tools/mark-completed-issues.sh --repo <checkout> 138 146 148   # 逐 Issue 计划
codex/tools/mark-completed-issues.sh --repo <checkout> --apply 138 146 148
```

默认只出计划、不做任何写入（无 `--apply` 时连 broker 都不会被调用），人看完可以拒绝。
与 #160 确立的姿态相容。

**这与 #160「已关闭的 Issue 不补写」不矛盾，两者管的是不同维度**，值得写清楚，
否则下一个读者会以为平台有两条互相打架的规则：

- #160 拒绝补写的是 `type/*` 与 `complexity/*`。理由是 `list-issues` 只请求 `state=open`，
  检索缺口只存在于 open Issue 上，判级事实又已经不可变地躺在合并后的 summary 里——
  补了不增加信息。
- 生命周期终态相反：`completed` 按定义只可能写在**已经合并、因而已经关闭**的 Issue 上。
  `mark-completed-issues.sh` 从 #115 起就只在 closed Issue 上工作，这是它的正常模式，
  不是例外。拒绝写 closed Issue 等于拒绝写终态。

## 风险

- **扁平安装读到旧 manifest**：VM 侧从 `/usr/local/share/aisoft/gitea-governance.json`
  读，重装前该文件没有新键 → 回落到缺省 `application-deploy` → 继续跳过。
  这是安全方向的失败（不会误写终态），且平台 Issue 的收尾按 `issue-session-flow` 一律在
  平台 checkout 上跑、命中仓库布局优先。缓解：spec 把「重装 governance manifest」列为
  合并后的显式可选步骤，与 `06` 踩坑 20 的 broker 重装同一类。
- **误声明 `none` 会静默放行**：某个真有部署链路的应用仓库若被错误声明为 `none`，
  它的 Issue 会在部署之前就被写成 `completed`。缓解三层：缺省是保守的一档、
  `contract.py` 逐值校验拒绝非法取值、声明是显式的一行 manifest diff 会被 review 看见。
  本变更只声明 `aisoft-platform` 一个仓库。
- **已安装 skill 漂移**：改了 `skill-for-claude/issue-session-flow/SKILL.md` 之后，
  本机 `~/.claude/skills/` 里的副本要到人跑 `skill-for-claude/install.sh` 才更新。
  缓解：`check-drift.sh` 能报出来；PR 正文列为合并后步骤。测试用临时 HOME，不受影响。
- **文档说法漂移**：`classification.py` 与 `test_change_control.py` 里陈述旧双重语义的注释
  若不同步更新，读者会照旧说法继续设计。缓解：本变更把这两处一并改掉，行为不动。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改动 governance manifest 的仓库条目 schema 与合并后终态判定规则，触及部署边界与治理写路径，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - deployment-boundary
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「CI/制品/部署/回滚，以及 Agent 或平台治理变更一律按 complex 处理」——
  本变更改的正是合并后终态记账规则与部署边界的判定依据。
- `contract_effect: change`：`mark-completed-issues.sh` 的 `requires-deployment` 分支已经存在，
  本变更改变它的触发条件，不是恢复或新增一条独立契约。
- 触及共享核心组件：`gitea-governance.json` 的仓库条目 schema 由全平台的
  `aisoft_gitea_governance.contract` 校验，`aisoft_host_access` 也消费同一个契约。
- 触及 Agent 行为契约 `skill-for-claude/issue-session-flow/SKILL.md`，
  须由本 spec 显式授权（`AGENTS.md` 治理文件条款）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文 AC-1..AC-4 完整且可测；AC-3 要求的「处置结论 + 依据」由本文档
  「AC-3」小节给出，执行由 `mark-completed-issues.sh` 的既有 dry-run/`--apply` 两段式承载。
