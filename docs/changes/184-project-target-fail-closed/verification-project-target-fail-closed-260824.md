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
status: verified
branch: change/184-project-target-fail-closed
created: 2026-08-24
updated: 2026-08-24
---

# Verification：目标仓库由 checkout 判定

## 基线与范围

- Commit SHA: `e4c92bc`（rebase 后的实现 commit；本记录在其之上）
- 基线：`origin/main` = `c0c0c4c`（`platform(ops): 把 installer 的 source provenance 与
  staleness 闸门抽成共用库 (#171)` (#185)）
- 环境：Mac（darwin 25.5.0），真实 Gitea `http://gitea-ci.orb.local:3000`，
  已安装 broker `/usr/local/libexec/aisoft/host-access-broker`，真实 checkout
  `/Users/benque/Projects/LocalWMS`
- 本记录负责证明的 acceptance criteria：AC-1 ~ AC-8。其中 AC-1/AC-2 的核心证据是**改动前
  才观测得到的**真实系统状态（LocalWMS Issue 的真实标签，以及未修复工具在其上的假通过），
  required CI 与 diff review 都不能复现，因此本次声明 `verification`（`03` §3 第二行）。

## 执行结果

### 一、改动前的基线观测（真实系统，不可重放）

| Command / check | Result | Evidence |
|---|---|---|
| `host-access-broker --project localwms --operation gitea.issue.labels.read --number 1 / 11 / 57` | PASS（读取成功） | 三条均为 `[]`——LocalWMS #1/#11/#57 上没有任何 `type/*` 或 `complexity/*` 标签 |
| 同上，`--project aisoft-platform` | PASS | 三条均为 `["complexity/complex","type/platform"]` |
| LocalWMS 三条 Issue 的映射 summary | PASS | `change_type: platform` / `effective_complexity: complex`（与平台仓那对标签**恰好相同**） |
| **未修复工具** `apply-classification-labels.sh --verify 1 11 57 --repo <LocalWMS>` | **FALSE PASS，退出码 0** | 三行全部 `"result":"projected"`，`detail` 为 `Issue #N carries the classification its merged summary declares`。#167 的闸门在三条从未投影的 Issue 上干净通过 |
| **未修复工具** `--verify 73 --repo <LocalWMS>` | **FALSE ALARM，退出码 0** | `"reason":"projection-window-closed"`，`Observed: type=type/platform complexity=complexity/complex`；而 LocalWMS #73 真实标签是 `["completed","complexity/small","type/docs"]`，投影完全正确 |
| **未修复工具** `mark-completed-issues.sh --repo <LocalWMS> 73`（plan） | 输出**无法分辨目标** | `{"issue":73,"action":"set-completed","applied":false}`——同一行输出在目标是 LocalWMS 还是 aisoft-platform 时逐字相同。这是 AC-5 的依据 |

> `mark-completed-issues.sh --apply` **未在真实系统上执行**：它是写操作，会把终态生命周期标签
> 写到 Issue 上。写路径的证据由 fixture 回归测试提供（下节），真实系统只跑了 plan。

### 二、改动后的真实系统对比（同一台机器、同一条命令）

| Command / check | Result | Evidence |
|---|---|---|
| `apply-classification-labels.sh --verify 1 11 57 --repo <LocalWMS>`（不传 `--project`） | **PASS，退出码 1** | 三行 `"project":"localwms","repository":"LocalWMS"`，`reason: projection-window-closed`，`Observed: type=<none> complexity=<none>`——与真实标签一致。假通过消失 |
| `--verify 73 --repo <LocalWMS>` | **PASS，退出码 0** | `"project":"localwms"`，`"result":"projected"`，`change_type: docs` / `complexity: small`——与真实标签一致。假失败消失 |
| `--verify 1 --repo <LocalWMS> --project aisoft-platform` | **PASS，退出码 1** | `ERROR: apply-classification: --project aisoft-platform does not match the project this checkout belongs to: /Users/benque/Projects/LocalWMS has the Git remote of localwms. Refusing to report on one repository's Issues from another repository's change documents`；stdout 为空 |
| `--verify 167 --repo <本地路径 clone>`（无 Gitea remote，不传 `--project`） | **PASS，退出码非 0** | `ERROR: apply-classification: cannot determine the target project from …: none of its Git remotes matches a project in …/host-access-broker.json. Pass --project <project_id> to name the target explicitly` |
| 同一 clone `--verify 167 --project aisoft-platform` | **PASS，退出码 0** | `{"issue":167,"project":"aisoft-platform","repository":"aisoft-platform",…,"result":"projected"}`——显式覆盖在判不出时仍然可用 |
| `mark-completed-issues.sh --repo <LocalWMS> 73`（plan，不传 `--project`） | **PASS，退出码 0** | `{"issue":73,"project":"localwms","repository":"LocalWMS","action":"set-completed","applied":false}` |
| `mark-completed-issues.sh --repo <平台 checkout> 175`（plan） | **PASS，退出码 0** | `{"issue":175,"project":"aisoft-platform","repository":"aisoft-platform",…}`——平台仓自身行为不变 |

### 三、回归测试（先看着它红）

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-apply-classification-labels.sh`（工具换回 `c0c0c4c` 的未修复版本） | **RED，退出码 1** | 新断言不是空转的 |
| `bash codex/tests/test-apply-classification-labels.sh`（修复版本） | PASS，退出码 0 | `apply-classification tests passed` |
| `bash codex/tests/test-mark-completed-issues.sh`（未修复版本） | **RED，退出码 1** | 同上 |
| `bash codex/tests/test-mark-completed-issues.sh`（修复版本） | PASS，退出码 0 | `mark-completed tests passed` |
| `bash codex/tests/smoke.sh` | PASS，退出码 0 | `Ran 520 tests … OK` + `Codex platform static smoke checks passed.`（含新库的 `bash -n` 与 ShellCheck） |

### 四、同形状核查（AC-8）

| Command / check | Result | Evidence |
|---|---|---|
| `grep -rn -- '--project)' codex/tools/` | PASS | 只命中 `apply-classification-labels.sh` 与 `mark-completed-issues.sh`，两个都已修 |
| `grep -n -- '--project' codex/tools/mark-deployed-issues.sh` | PASS（无输出） | 它没有 `--project`，目标仓库由部署钩子的 `GITEA_OWNER`/`GITEA_REPO` 给出，不存在本缺陷的形状 |
| Issue #172 / #173 关系核查 | PASS | #172 已 closed 并由 PR #176 合并，`main` 上 `mark-completed-issues.sh` 已从 `project_id` 反查 `repository`；#173 报告的是同一个缺陷，属重复条目。本变更不改动其结论，也未代为关闭 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 二节全部四条真实系统命令的输出 `project` 均等于 checkout 判定值；测试断言 broker 只收到 `--project fixture-project` / `--project no-deploy-project`，从未收到 `aisoft-platform` |
| AC-2 | PASS | 一节的假通过（退 0、三行 `projected`）在二节同一条命令上变为退 1、`projection-missing` 语义（Issue 已关闭故报 `projection-window-closed`，`Observed: type=<none>`）。fixture 侧由 Issue 601 复刻同一形状并断言 `projection-missing` + 非零退出 |
| AC-3 | PASS | 二节第三行；fixture 侧对 plan / `--apply` / `--verify` 三个模式各断言：非零退出、stdout 为空、`broker.log` 行数为 0 |
| AC-4 | PASS | 二节第四行，错误信息逐字含 `--project`；fixture 侧三个模式同样断言不调用 broker |
| AC-5 | PASS | 二节每一行输出都带 `project` 与 `repository`；一节最后一行给出改动前「同一输出无法分辨目标」的对照 |
| AC-6 | PASS | 二节第五行（clone + 显式 `--project` 仍可用）；`mark-completed` 的全部既有用例现在都走这条路径 |
| AC-7 | PASS | 三节：两个专项测试的既有断言全部保留且通过，`smoke.sh` 520 项全绿 |
| AC-8 | PASS | 四节 |

## 遗留风险与未完成项

- `mark-completed-issues.sh --apply` 未在真实系统上执行（写操作）。写路径的目标选择由 fixture
  回归测试覆盖：`--project no-deploy-project` 出现在 mock broker 日志中，`aisoft-platform` 从未出现。
- 只有 GitHub remote 而没有 Gitea remote 的 checkout 判定不出项目，必须显式传 `--project`。
  这是设计内的 fail-closed 形态，已写进 `03` 与 `06` 踩坑 21。
- 本次没有对**历史上已经被误判**的 Issue 做任何回填。已关闭 Issue 的投影窗口按 #160 永久关闭，
  本变更不引入 override；LocalWMS #1/#11/#57 的判级仍然只存在于其合并后的 summary 中。
  该结论现在由工具如实报出（`projection-window-closed`，`Observed: type=<none>`），而不再被
  假通过掩盖。
- 判级投影（`--apply`）本次未对本 Issue #184 执行，它在开 PR 之后、合并之前由会话按平台合同完成。
