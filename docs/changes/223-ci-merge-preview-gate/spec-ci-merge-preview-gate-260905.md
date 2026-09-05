---
issue: 223
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/223
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/223-ci-merge-preview-gate
created: 2026-09-05
updated: 2026-09-05
---

# Spec：合并预览检查器、CI 参考模板与过期绿闸门的只读回读

## 目标与原因

让「两个 PR 各自绿、合并后主干红」这个结构性盲区在平台层面**可被机器发现**，
并把它的第二半——「base 前进后过期的绿仍可合并」——一并纳入同一次裁定。

两个缺口的归属按 2026-09-05 的平台裁定切开：

| 缺口 | 修法 | 本次变更做什么 |
|---|---|---|
| ① `pull_request` 跑 head 而非合并结果 | 项目仓各自的 workflow | 加只读检查 + 给出参考模板 |
| ② base 前进后过期的绿仍可合并 | Gitea 分支保护 `block_on_outdated_branch` | 加只读检查 + 写交接项，开关由人操作 |

平台不代改任何项目仓文件。

## Acceptance criteria

- [ ] AC-1 `aisoft-project-check.sh` 新增只读检查 `ci-merge-preview`：判定仓库在
      `pull_request` 上跑的是合并预览还是 PR head，不满足报 GAP。检查全程只读，不写任何文件。
- [ ] AC-2 `ci-merge-preview` 对 LocalWMS 合并后的真实 `.gitea/workflows/ci.yml` 判 PASS。
      判据识别的是机制而非某一种写法：运行时三方合并与 `refs/pull/N/merge` 两种形态都接受。
- [ ] AC-3 `ci-merge-preview` 对「`actions/checkout` 未指定合并预览、也没有任何运行时合并步骤」
      的 workflow 判 GAP，GAP 文案指名是哪个 workflow 文件。
- [ ] AC-4 仓库没有 workflow 目录、或没有任何 `pull_request` 触发且检出仓库的 workflow 时，
      `ci-merge-preview` 报 SKIP 并说明原因，不报 PASS 也不报 GAP。
- [ ] AC-5 `aisoft-project-check.sh` 新增只读检查 `ci-outdated-branch`：经 `main` 分支保护回读
      `block_on_outdated_branch`。适用范围由 governance manifest 的 `classification` 决定——
      `public-platform` 与 `internal-application` 必须为 `true`，否则 GAP；`public-test` 报 SKIP。
- [ ] AC-6 `ci-outdated-branch` 只在 `--remote` 下运行；未启用 `--remote` 报 SKIP，
      读取失败或 HTTP 非 200 报 GAP，HTTP 403 报 SKIP，与既有 `ci-context` 的失败语义一致。
- [ ] AC-7 `templates/project/ci/` 提供 CI workflow 参考与合并预览脚本参考。脚本在合并预览
      不存在或过期时**明确失败并说清原因**，不回退到 head；参考文件本身通过 `bash -n`
      与 ShellCheck（环境可用时）。
- [ ] AC-8 平台仓自身 `.gitea/workflows/ci.yml` 改为在 `pull_request` 上跑合并预览，
      且 workflow 名 `CI`、job key `verify`、事件 `pull_request` 三者逐字不变——
      required context `CI / verify (pull_request)` 不变，分支保护不需要任何改动。
- [ ] AC-9 `06-运维手册与踩坑集.md` 记录：本盲区的机理、两个缺口的分工、打开
      `block_on_outdated_branch` 后并行 PR 被串行化的代价与处置办法。
- [ ] AC-10 `bash codex/tests/smoke.sh` 全绿；新增的模板脚本进入 smoke 的 `bash -n`
      与 ShellCheck 清单。
- [ ] AC-11 verification 文档以显式交接项记录 7 个仍需人在 Gitea 界面打开
      `block_on_outdated_branch` 的仓库，写成**未执行**，不得写成已完成。

## 接口、数据与兼容性影响

**新增平台合同**：接入项目的 `aisoft-project-check.sh` 输出会多两行。既有项目会看到新的
GAP——这是裁定接受的代价（「能真正收口，代价是给既有项目增加一条 GAP」）。检查器只读，
不改任何项目仓文件，GAP 不阻塞任何既有流程。

**`ci-merge-preview` 的判据（本次新增的平台合同）**。仅判定「触发器含 `pull_request`
且存在 `actions/checkout` 步骤」的 workflow；其余 workflow 不判。满足下列任一形态即 PASS：

- 形态 A：`actions/checkout` 步骤声明 `ref:`，取值匹配 `refs/pull/.../merge`。
- 形态 B：该 workflow 中存在一个步骤，其 `run:` 内联执行了真实的 `git merge`，
  或调用了仓库内一个确实存在、且内容中含真实 `git merge` 的脚本。

两种形态下，承载合并预览的步骤都不得带 `continue-on-error: true`——一个可以静默失败的
预览不是闸门。

形态 B 是本平台已验证可行的那一种：LocalWMS Issue #193 的实现刻意避开 `refs/pull/N/merge`，
理由是该 ref 由 Gitea 后台在计算可合并性时刷新，新鲜度不由本次 CI 运行决定，
检出它可能得到对着旧 base 的合并结果。检查器必须同时接受两者。

**`ci-outdated-branch` 的适用范围**由 governance manifest 的 `classification` 推导，
不引入新的 manifest 字段，也不提供 per-repo 豁免——裁定是「全部」，不设开关。

**不变量**：required context 字符串不变；`gitea-governance.json` 不变；
broker 操作表不变；不新增 broker 操作。

## 风险与回滚约束

- **平台仓 CI 自伤**：AC-8 的改动在本 PR 的分支上就会被执行一次。若合并预览步骤在本平台
  runner 上跑不通，本 PR 自己会红。处置：回退 `.gitea/workflows/ci.yml` 这一处 hunk，
  在 verification 如实记录失败证据，AC-8 记为未达成，其余 AC 照常交付。
  合并前的失败只影响本 PR，不影响任何其他分支。
- **假 GAP**：判据过窄会把已修对的仓库判错。AC-2 用 LocalWMS 合并后的真实 workflow
  做 fixture 压住。
- **回滚**：本次变更全部是新增检查项、新增模板目录、一个 workflow 步骤与一段文档，
  `git revert` 单个 PR 即可完全回滚，无数据、无迁移、无部署。

## 非目标

- 不代改任何项目仓的 `.gitea/workflows/`。既有项目按各自节奏采纳。
- 不新增 broker `protection.set` 操作（那是 Issue #222 的范围）。
- 不由 AI 修改任何仓库的分支保护——`block_on_outdated_branch` 由人在 Gitea 界面操作。
- 不修改 `codex/config/gitea-governance.json`，不修改 `AGENTS.md`。
- 不修改 `aisoft_gitea_governance` 的 `desired_protection`。它当前对
  `block_on_outdated_branch` 采取「保留现值」，人打开之后不会被 reconcile 抹掉；
  把它写进 desired 是一条 mutation 路径，超出本次裁定，需要单独 Issue。
- 不声明任何部署、外部验收或生产就绪。

## 未决问题

无。
