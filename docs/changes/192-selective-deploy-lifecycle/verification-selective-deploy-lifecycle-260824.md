---
issue: 192
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/192
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
status: pending
branch: change/192-selective-deploy-lifecycle
created: 2026-08-24
updated: 2026-08-24
---

# Verification · 三档 `deployment_lifecycle`

## 基线与范围

- Commit SHA：`change/192-selective-deploy-lifecycle`
- 基线：`origin/main` = `eda2aeb`
- 环境：Mac 交互会话，worktree `/private/tmp/issue-192-selective-deploy-lifecycle`；
  只读访问 LocalWMS checkout `/Users/benque/Projects/LocalWMS`（`origin/main` = `bc95326`）
  与 Gitea（broker `gitea.issue.read`，只读）。
- 本记录负责证明的 acceptance criteria：AC-1 ～ AC-9 全部。
- 本次**不部署、不迁移**，按 `03` §3 删除 `## 部署验收` 整节。

## 为什么这次声明了 `verification`

按 `03` §3 的证据来源判据，决定性的证据有两类，required CI 一条都不跑：

1. **跨 5 个仓库的扫描**（下方「否掉的两条候选判据」），它决定了方案选型；
2. **改动前旧工具在真实 checkout 上的输出**——本次改的就是这个工具，合并后无法重放。

本仓库声明 `deployment_lifecycle: none`，所以声明 `verification` 不会让本 Issue 卡住
（下方第 1 行实测：`set-completed` / `no-deployment-chain`）。这本身就是 §3 那句承诺
在本仓库一侧成立的一次现场演示。

## 执行结果

### 一、否掉的两条候选判据（跨仓库扫描，改动前）

要区分「声明了 `verification` 且这次确实部署了」与「本次不部署」，需要一个**本次变更部不
部署**的机读来源。两个看起来现成的候选被实测否掉：

| 候选 | 命令 | 结果 |
|---|---|---|
| verification 文档的 `## 部署验收` 小节（`03` §3 规定不部署时整节删除） | 对平台仓 + `~/Projects/{LocalWMS,NewEmaint,HSDB,SFMDigitalBoard,rsdesign-new}` 的全部 `verification*.md` / `03-verification.md` 跑 `grep -q '^##[[:space:]]*部署验收'` | **零命中**。该小节是 #168 才写进模板的，历史文档一份都没用；真部署的变更（LocalWMS #7 `native-systemd-deployment`）用的是自己的 `## 1. 硬验收 …` 编号标题 |
| summary front matter 的 `risk_flags` | 对同一批仓库的全部 summary 提取 `risk_flags` 并计数 | **不是封闭词表**。平台仓 32 种、NewEmaint 50 余种；`deployment` / `deployment_work` / `deployment-contract` / `ci-deployment` / `implicit-main-push-deploy` 并存，HSDB 与 SFMDigitalBoard 整体用 snake_case。任何字面匹配都会漏 |

结论：现有仓库证据里没有可靠的「本次部不部署」来源，Issue 方向 1 的字面实现不可行；
硬造一个新 front matter 键则只有终态工具一个消费者，等于「人工传入的终态判断」换个写法。
判据因此改在**仓库属性**上——把「有没有链路」收紧成「链路覆盖不覆盖每一次 merge」。

### 二、缺口在真实仓库里已经发生（改动前，只读）

对 LocalWMS 全部**声明了 `verification` 的已合并 Issue** 逐条读回 Gitea 标签
（broker `gitea.issue.read`，只读）：

```
#  1 closed TERMINAL ['completed']      #  5 closed TERMINAL ['completed']
#  6 closed TERMINAL ['completed']      #  7 closed TERMINAL ['completed']
# 11 closed TERMINAL ['completed']      # 12 closed TERMINAL ['completed']
# 13 closed NO-TERMINAL []              # 16 closed TERMINAL ['completed']
# 23 closed NO-TERMINAL []              # 26 closed TERMINAL ['completed']
# 27 closed TERMINAL ['completed']      # 28 closed TERMINAL ['completed']
# 29 closed NO-TERMINAL []              # 34 closed NO-TERMINAL []
# 35 closed NO-TERMINAL []
```

15 个里 **5 个 closed 之后一个标签都没有**（#13、#23、#29、#34、#35）——#138/#146/#148
的失败模式在缺省档仓库上原样复现。另外 10 个拿到了 `completed`，而改动前的工具对它们
**全部判 `skip`**（下一节第一行），也就是说那 10 个标签是绕过这条判定写上去的：
等待没有终点时，人不会等，只会绕过去。这同时否掉了 Issue 方向 3。

### 三、真实 checkout 上的改动前后对比（AC-9）

同一条命令，同一个 LocalWMS checkout，同一批 Issue，**全程计划模式、不带 `--apply`、
不写任何 Issue**（`broker.log` 语义上的等价物：命令输出里 `applied` 恒为 `false`）：

```bash
codex/tools/mark-completed-issues.sh --repo /Users/benque/Projects/LocalWMS 1 7 12 16 34
```

| | 改动前（`origin/main` = `eda2aeb` 的工具） | 改动后 |
|---|---|---|
| #1 / #7 / #12 / #16 / #34 | `skip` · `requires-deployment` | `set-completed` · `deployment-not-guaranteed` |

改动前 detail：`required_docs contains verification and LocalWMS has an application
deployment chain, so this change ships …`
改动后 detail：`… LocalWMS's application deployment chain covers only some merges:
nothing guarantees one will ever ship this Issue and write deployed, so completed is
written now and a deployment that does ship it replaces completed with deployed`

### 四、三档 + 非法取值的判定矩阵（真实 checkout，本 Issue 自己）

`--repo` 指向本 worktree（`origin` 指向平台仓，project 由 checkout 判定），
Issue #192 的映射 summary 声明了 `verification`。改声明只改一份 manifest **副本**
（`AISOFT_GOVERNANCE_MANIFEST` 覆盖），`codex/config/gitea-governance.json` 一个字节都没动。

| # | 声明 | 工具 | 结果 |
|---|---|---|---|
| 1 | `none`（真 manifest） | 新 | `set-completed` · `no-deployment-chain` |
| 2 | `application-deploy-selective` | 新 | `set-completed` · `deployment-not-guaranteed` |
| 3 | `application-deploy-selective` | 旧 | `skip` · `requires-deployment`（新取值被当成「有链路」吞掉，退出码 0） |
| 4 | `application-deploy` | 新 | `skip` · `requires-deployment`，detail 写明「deploys every merge」 |
| 5 | `ship-it-later`（非法） | 新 | `ERROR: mark-completed: unsupported deployment_lifecycle …: ship-it-later`，**退出码 1** |
| 6 | `ship-it-later`（非法） | 旧 | `skip` · `requires-deployment`，**退出码 0**——一个拼错的声明读起来像一次决定 |

第 3、6 行是本次改动必要性的直接证据：旧工具对新取值和对拼错的取值给出**完全相同**的
输出，而那正是「跳过、等一个不会到来的部署」。

### 五、测试（AC-1 ～ AC-4、AC-6）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -p 'test_deployment_lifecycle.py'` | `Ran 7 tests … OK` |
| 2 | `bash codex/tests/test-mark-completed-issues.sh` | `mark-completed tests passed` |
| 3 | **红/绿对照**：把 `codex/tools/mark-completed-issues.sh` 换成 `origin/main` 的版本后重跑第 2 条 | **退出码 1**（`set -e` 在断言处中止，无输出）；换回后再跑 → passed。新增断言非空转 |
| 4 | `bash -n codex/tools/mark-completed-issues.sh` | 退出码 0 |
| 5 | `shellcheck codex/tools/mark-completed-issues.sh` | 无告警 |
| 6 | `bash codex/tests/smoke.sh` | `Ran 527 tests … OK` + `Codex platform static smoke checks passed.` |

### 六、范围（AC-5）

```
$ git diff --stat origin/main -- codex/config/gitea-governance.json
（无输出）

$ git status --porcelain
 M 02-CI与自动部署流水线.md
 M 03-Issue-Spec-Plan与单闸门开发流程.md
 M codex/runtime/aisoft_gitea_governance/contract.py
 M codex/runtime/tests/test_deployment_lifecycle.py
 M codex/tests/test-mark-completed-issues.sh
 M codex/tools/mark-completed-issues.sh
 M skill-for-claude/issue-session-flow/SKILL.md
?? docs/changes/192-selective-deploy-lifecycle/
```

没有任何仓库的实际声明被改动；broker、CI workflow、`AGENTS.md`、
`codex/config/*` 全部未触碰，因此**不需要重装 broker**。

**`templates/docs/changes/_template/verification.md` 被有意留着不改。** 它那句
「`deployment_lifecycle: none` 的仓库照样到 `completed`」在新规则下仍然成立；而模板是
vendored 到各接入项目的副本，改它会让所有下游仓库的 `aisoft-project-check.sh`
`change-templates` 立刻变红（LocalWMS #78 就是这么被触发的）。为一句仍然正确的话换取
一轮全下游 GAP 是亏本交易。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 三档 + 新缺省 + 非法值 fail closed | 通过 | 五-1（`test_three_declarable_lifecycles`、`test_default_is_the_self_healing_option`、`test_every_declared_lifecycle_round_trips`、`test_invalid_deployment_lifecycle_is_rejected`） |
| AC-2 三档各自的终态分支 | 通过 | 四-1/2/4 实测 + 五-2 的 `#192` 段（explicit / selective / undeclared 三组断言，且 undeclared 与 selective 逐字段相等） |
| AC-3 未知取值报错退出 | 通过 | 四-5（退出码 1）+ 五-2（计划、`--apply`、非 verification Issue 三种模式各一次） |
| AC-4 不含 `verification` 的 Issue 判定不变 | 通过 | 五-2 中 `#501` 在三档下均 `set-completed` 且**不带** `reason`；五-6 的既有断言全部保留 |
| AC-5 manifest 数据零改动 | 通过 | 六 |
| AC-6 测试覆盖 + smoke 全绿 | 通过 | 五-1/2/3/6 |
| AC-7 §3 那句对三档都成立并说明理由 | 通过 | `03` §3 改写 + §11 新增「『跳过等待』必须有一个会到来的写入者（#192）」一节；四-1/2/4 是三档各自的现场 |
| AC-8 `02` §9 与 skill 文字一致 | 通过 | `02` §9 新增「有这条链路，也不等于它覆盖每一次 merge」；`skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步改写。**注意**：`~/.claude/skills/` 下的已安装副本不由本 PR 更新（未经授权不安装全局 skills） |
| AC-9 真实非部署变更的改动前后对比 | 部分通过，见下 | 三 |

### AC-9 的诚实边界

Issue 正文写的是「声明 `verification` → 合并 → 拿到终态标签」的**完整**闭环。本 PR 走通了
其中可在本仓库内走通的部分：

- **本仓库一侧（`none` 档）完整成立**：本 Issue 自己声明了 `verification`，四-1 实测判为
  `set-completed`，合并后收尾即可拿到 `completed`。
- **缺省档一侧只走到「判定」为止**：三的对比证明同一批真实 Issue 的判定从 `skip` 变成
  `set-completed`，但真正把标签写上去要在 LocalWMS 自己的 Issue 与会话里做（跨仓写入不属
  本 Issue 范围，且本次全程未带 `--apply`）。

因此**开一个 LocalWMS 衍生 Issue**：用本次修好的判定回填那 5 个没有终态标签的已合并
Issue，并撤销 #78 记录的那次「被迫不声明 `verification`」的规避。本 PR 合并前不做。

## 遗留风险与未完成项

- **窗口内的 `completed` 会先于部署出现**。已论证自愈（`mark-deployed-issues.sh` 重写整个
  生命周期维度）且不可反向覆盖（broker `REQUEST_DENIED`）。**未实测**：本次没有真实部署可
  触发这条 hook，两条依据都来自代码与既有测试（`codex/tests/test-mark-deployed-issues.sh`
  钉住 hook 姿态，broker 侧由 `_set_issue_lifecycle` 的 guard 保证）。
- **已经 `deployed` 的 Issue 再跑收尾**会得到 broker `REQUEST_DENIED` → 工具报
  `broker-refused` 且退出码 1。这是既有行为、也是守卫在起作用，但读起来像故障。本次
  按 spec 非目标未改（会改动 broker 文案或新增标签读取，两者都超出本 Issue）。
- **没有任何仓库声明 `application-deploy`**，所以「等待有终点」那一档目前只有测试覆盖，
  没有生产实例。谁是「合并即部署」需要各自的证据，另开 Issue。
