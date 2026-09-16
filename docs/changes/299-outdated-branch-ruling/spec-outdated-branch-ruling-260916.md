---
issue: 299
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/299
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-change
depends_on: []
status: approved
branch: change/299-outdated-branch-ruling
created: 2026-09-16
updated: 2026-09-16
---

# 裁决合同：受保护 main 的 block_on_outdated_branch 与合并预览重叠

## 目标与原因

给「`block_on_outdated_branch` 与项目侧合并预览重叠、多 PR 并行时每次合并级联变基」一个平台级
裁决，并把裁决、理由与残余风险固化到 `06` 踩坑集与检查器语义里，让后续项目不再逐个重议。

## 证据（裁决依据，取证于 2026-09-16）

| 项 | 事实 | 出处 |
|---|---|---|
| 踩坑 22 原始事故 | 2026-08-29 LocalWMS `main` `d5a9222` push CI job 823 红：两个 PR 各把同一计数常数 74→75，文本相同、干净合并，真值 76，阻塞所有后续 PR。当时 LocalWMS `block_on_outdated_branch: False`，CI 检出 PR head | #223 summary 与 Issue 评论「溯源补充」 |
| #223 裁定 | 2026-09-05：缺口①走检查器+模板，缺口②平台仓与全部 internal-application 打开开关；「接受并行 PR 串行化的成本」；那一轮平台仓同时 3 个 PR | #223 评论「平台裁定（2026-09-05）」 |
| 当前开关状态 | aisoft-platform / LocalWMS / NewEMaint `true`（2026-09-05 23:07 更新）；SFMDigitalBoard `true`（2026-08-08 建仓即是） | `gitea.protection.read` 四仓读回 |
| 检查器现行语义 | `check_outdated_branch`：范围 `public-platform` + `internal-application`；`true` PASS；`false` 或键缺失 GAP；`public-test` SKIP；不在 manifest GAP；403 SKIP；未 `--remote` SKIP | `codex/tools/aisoft-project-check.sh` 第 924–964 行；`codex/tests/test-project-check.sh` 第 831–879 行 |
| Gitea 1.26.4 能力 | `BranchProtection` 唯一相关字段 `block_on_outdated_branch`；手动更新端点 `POST /repos/{owner}/{repo}/pulls/{index}/update?style=merge\|rebase`；仓库选项 `allow_rebase_update` 只决定按钮风格；无自动更新、无 merge queue | `GET /api/v1/version`、`swagger.v1.json` |
| broker 能力 | 有 `gitea.protection.read`（无参数、manager-audit、只读）；`gitea.pull.update` 只改 title/body；没有 update-branch 或 protection.set 操作 | `codex/config/host-access-broker.json` |
| runner 并发 | `capacity: 1`，级联重跑串行排队 | `01` §4.1 |
| push-main CI | NewEMaint 与 LocalWMS 的 ci.yml 有 `push: branches: [main]` 且已接合并预览；平台仓 ci.yml 只有 `pull_request` | 三仓 `main` 的 `.gitea/workflows/ci.yml` |
| 今天的代价 | NewEMaint 开放 PR #114/#119/#121/#123/#125/#126，base 全部 `f57c1a2`；PR #119 一天变基 3 次 | Issue #299 正文；`gitea.pulls.read --state open` |

## 三个选项的后果

- **A 关闭**：级联变基归零。代价：重新接受缺口②——合并预览是运行那一刻的三方合并，base 之后前进
  没有任何东西让它重跑，过期的绿仍可合并；事故形态与踩坑 22 相同。兜底是 push-main CI 红即回滚，
  NewEMaint/LocalWMS 有这条兜底，**平台仓没有**（加 push 触发是另一条 CI 变更，需另行授权）。
  检查器 `ci-outdated-branch` 从「要求 true」改为「读回并报告」：`true` 仍 PASS，`false`/缺失改为
  SKIP 并写明 #299 裁决与残余风险，不再报 GAP；范围、403、不在 manifest 的分支不变。
- **B 保留并写规程**：缺口②继续被堵死。代价原样：每次合并后其余 PR 各重跑一轮 CI，单 runner 串行。
  规程要点：合并者按依赖顺序排队，用 Gitea「更新分支」按钮而不是让 Issue 会话变基；**merge 风格**
  更新对会话无害（本地分支是远端的祖先，`git.fetch.change` 后可 fast-forward）；**rebase 风格**会重写
  远端 head，会话下次 `git.push.change` 撞 `REMOTE_BRANCH_MOVED`。检查器不变。
- **C 保留并自动化**：Gitea 没有内建能力，需要新建自动化（push-main 触发的 workflow 或调度任务，
  对每个开放 PR 调 `pulls/{index}/update`），并配一个能写 head 分支的身份与新的 broker typed 操作。
  级联 CI 消耗不减反增（每次 main 前进自动重跑全部开放 PR），单 runner 队列被放大。
  这是 broker/治理变更，超出本 Issue 的可测验收标准 3 所假设的「补一条自动化」；若选 C，本 Issue
  只记录裁决并另立 Issue 实施。

## 裁决（确认点 1，2026-09-16）

**A 的分仓变体**：`internal-application` 关闭 `block_on_outdated_branch`；`aisoft-platform` 保留 `true`。
B 与 C 为否定裁决，理由与残余风险记入 `06` 踩坑 29。

## Acceptance criteria

- [ ] AC-1：裁决、理由、否定裁决（B/C）与残余风险写进 `06-运维手册与踩坑集.md` 新条目（踩坑 29，
  回指踩坑 22；踩坑 22 的对策列加一句收窄指针）。
- [ ] AC-2：`aisoft-project-check.sh --remote` 对 `internal-application` 的 `block_on_outdated_branch=false`
  与键缺失不再报 `ci-outdated-branch` GAP，改为带 #299 说明的 SKIP；对 `public-platform` 仍报 GAP；
  `true` 一律 PASS；`public-test`、不在 manifest、403、未 `--remote` 四条分支行为不变。
  `codex/tests/test-project-check.sh` 对应用例更新并全部通过；`bash codex/tests/smoke.sh` 通过。
- [ ] AC-3：负责人在 Gitea 界面切换三个 `internal-application` 后，会话用 `gitea.protection.read`
  读回四仓的 `block_on_outdated_branch`，结果写进 verification 并评论到本 Issue。切换前后各读一次。
- [ ] AC-4：平台 required CI 全绿；不改任何项目仓的 `.gitea/workflows/*`；不改平台仓 ci.yml。

## 接口、数据与兼容性影响

- `aisoft-project-check.sh` 是所有接入项目共用的只读检查器；选 A 改变 `ci-outdated-branch` 的
  PASS/GAP 语义，接入项目下次 `project-align` 读到的结论随之变化。输出行格式与检查 id 不变。
- 无数据迁移、无 broker 操作变更、无 Actions workflow 变更。
- 分支保护开关本身由人在 Gitea 界面操作；本变更不含 `protection.set`。

## 风险与回滚约束

- 源码改动可用受治理 revert 恢复。开关切换的回滚是再切一次界面并读回。
- 选 A 后一旦再次发生踩坑 22 形态的事故，回滚路径是把开关重新打开并 revert 本次检查器改动。

## 非目标

- NewEMaint #120（`$GITHUB_SHA` 误用）。
- 任何项目仓的 CI 改动；平台仓 ci.yml 加 push 触发（若需要，另立 Issue）。
- 新增 broker typed 操作（`protection.set`、update-branch）。

## 未决问题

- 无。三选一已于 2026-09-16 确认点 1 裁决。
