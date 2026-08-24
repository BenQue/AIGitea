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

# Implementation plan：deployment_lifecycle 声明与合取判定

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | manifest schema 接住 `deployment_lifecycle`，`aisoft-platform` 声明 `none`，Python 侧断言到位 | - | pending |
| T02 | `mark-completed-issues.sh` 解析 manifest，判定改为合取，新增 `no-deployment-chain` 路径 | T01 | pending |
| T03 | `test-mark-completed-issues.sh` 覆盖新路径、缺省不变与 manifest 缺失报错 | T02 | pending |
| T04 | 文档与陈述同步：`03` §11、`02` §9、issue-session-flow skill、`classification.py` 注释、`test_change_control.py` docstring | T02 | pending |

T01 先行，因为 T02 的判定依赖 schema 已经接受该键——否则任何加载 manifest 的 Python
路径都会因 `_exact_keys` 拒绝未知键而失败。T03/T04 都只依赖 T02 的最终行为。

## Expected touch points

**T01**
- `codex/runtime/aisoft_gitea_governance/contract.py`：新增 `DEPLOYMENT_LIFECYCLES`
  与缺省常量（放在 `CHANGE_CONTROL_PHASES` 旁边，manifest schema 的取值集合只此一处）；
  `RepositoryContract` 新增 `deployment_lifecycle: str = "application-deploy"`；
  `_exact_keys(..., optional={"change_control", "deployment_lifecycle"})`；
  逐值 `_require`；构造 `RepositoryContract` 时带上。
- `codex/config/gitea-governance.json`：`aisoft-platform` 条目加一行。
- `codex/runtime/tests/test_gitea_governance.py`：接受/拒绝/缺省三条断言。

**T02**
- `codex/tools/mark-completed-issues.sh`：
  - manifest 解析块，紧跟既有的 broker 与 `PYTHONPATH` 解析（同一条「仓库布局优先，
    其次扁平安装」姿态，前面再加 `AISOFT_GOVERNANCE_MANIFEST` 覆盖）。
  - 一次 `jq` 读出该项目条目是否存在、以及它是否声明 `none`；
    条目缺失或 manifest 不可读 → `fail`。
  - `requires-deployment` 分支收紧为合取；新增分支输出
    `action: set-completed` + `reason: no-deployment-chain` + `detail`。
  - shell 侧只比较 `none` 这一个值，缺省名字不在 shell 里出现——缺省只在
    `contract.py` 定义一次，不产生第二份副本。

**T03**
- `codex/tests/test-mark-completed-issues.sh`：fixture manifest（两个仓库条目：
  一个声明 `none`、一个不声明）+ `AISOFT_GOVERNANCE_MANIFEST` 指过去；
  沿用既有的 mock broker 与 fixture 仓库，不接触真实 Gitea。

**T04**
- `03-Issue-Spec-Plan与单闸门开发流程.md` §11
- `02-CI与自动部署流水线.md` §9
- `skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步
- `codex/runtime/aisoft_loop/classification.py` `route()` 注释
- `codex/runtime/tests/test_change_control.py` 对应用例 docstring

`codex/tests/smoke.sh` 无需改动：新测试文件不新增，`bash -n`/shellcheck/`unittest discover`
的既有注册已经覆盖本变更触及的全部文件。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `codex/runtime/tests/test_gitea_governance.py`：声明被读进 `RepositoryContract`、非法取值被 `ContractError` 拒绝、未声明的仓库取缺省 |
| AC-2 | `test-mark-completed-issues.sh`：声明 `none` 的项目 + 含 verification → 不再出现 `requires-deployment`；未声明的项目 + 含 verification → 仍然 `requires-deployment`。并 review 工具的参数解析未新增开关 |
| AC-3 | `test-mark-completed-issues.sh`：计划里 `action == "set-completed"` 且 `reason == "no-deployment-chain"`；`--apply` 后 broker.log 含 `--lifecycle completed` 与该 Issue 号 |
| AC-4 | `test-mark-completed-issues.sh` 既有全部用例保持不改而通过（501/502/503、range、无选择器） |
| AC-5 | `test-mark-completed-issues.sh`：manifest 指向不存在的文件 / 非法 JSON / 查不到项目条目，三种情况均非零退出且有说明 |
| AC-6 | review：按 `03` §11、`02` §9、skill 第 3 步各自的表述推演一遍三行判定表，结论与工具一致；`rg` 确认不再有陈述旧单条件语义的注释 |
| AC-7 | 在本分支对 #138/#146/#148 跑一次 dry-run（不带 `--apply`，无 broker 调用），逐 Issue 计划贴进 PR；结论与依据写在 summary |
| AC-8 | `bash codex/tests/smoke.sh` |

## 部署与回滚

无部署。回滚 = revert 本 PR：manifest 少一个可选键、工具回到单条件判定，
无数据迁移、无外部状态需要撤销。

合并后有两个显式的人工步骤，均不属于本 PR 交付物，也都不阻塞平台 checkout 上的收尾：

1. `codex/install-vm.sh` / 相应安装脚本重装 governance manifest —— 只影响扁平安装读到的副本。
2. `bash skill-for-claude/install.sh` —— 消除 `check-drift.sh` 报出的 issue-session-flow 漂移。
