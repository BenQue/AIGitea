---
issue: 299
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/299
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 平台级治理裁决，改动受保护 main 的分支保护合同、共享检查器 aisoft-project-check.sh 的语义与运维手册，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-outdated-branch-ruling-260916.md
  spec: spec-outdated-branch-ruling-260916.md
  plan: plan-outdated-branch-ruling-260916.md
  verification: verification-outdated-branch-ruling-260916.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/299-outdated-branch-ruling
pr_url:
created: 2026-09-16
updated: 2026-09-16
---

## 问题/需求总结

受保护 `main` 的 `block_on_outdated_branch: true`（#223 于 2026-09-05 裁定打开）与项目侧合并预览
（#223 缺口①，NewEMaint/LocalWMS 已接入）在功能上重叠：两者都想保证「合并时验的是与 base 当前
尖端合并后的树」。前者的代价在多 PR 并行时被放大——admin/NewEMaint 2026-09-16 同时开放 6 个 PR、
当天合并 5 次，每次合并后其余 PR 全部过期，PR #119 一天被迫变基 3 次，每次一轮约 5 分钟
`CI / verify (pull_request)`。NewEMaint 负责人倾向选项 A（关闭开关）。

本 Issue 是**平台级裁决**：A（关闭）/ B（保留并写成合并规程）/ C（保留并自动化更新分支）三选一。
裁决与残余风险无论选哪个都要落到 `06` 踩坑集，不能只留在 Issue 评论。

## 影响范围

- `06-运维手册与踩坑集.md` 踩坑 22：补记本次裁决、理由与残余风险（三个选项都要写）。
- 选 A 时：`codex/tools/aisoft-project-check.sh` 的 `check_outdated_branch`（第 924–964 行）与
  `codex/tests/test-project-check.sh` 第 831–879 行对应用例；Gitea 界面开关由负责人人工切换，
  会话只用 `gitea.protection.read` 读回并写进 verification 与 Issue 评论。
- 选 B 时：`03`/`06` 增写合并串行化规程（合并者用 Gitea「更新分支」按钮，一批 PR 按依赖排队）。
- 选 C 时：需要新的自动化（Gitea 1.26.4 没有内建「base 前进后自动更新 PR 分支」），
  实际是一个新的 broker typed 操作或 Actions workflow，范围超出本 Issue 的可测验收标准 3 所假设的
  「补一条自动化」，见 spec 的证据。
- 不改任何项目仓的 `.gitea/workflows/*`；NewEMaint #120 不在范围。

## 初步方案与建议

把三个选项的证据与后果摆给负责人在确认点 1 裁决，会话不替他选。证据要点：

1. 踩坑 22 的原始事故是 2026-08-29 LocalWMS `main` `d5a9222` push CI job 823：两个 PR 各把同一条
   计数常数从 74 改成 75，文本相同、干净合并、真值 76，主干红并阻塞所有后续 PR。当时 LocalWMS
   `block_on_outdated_branch: False`、CI 检出的是 PR head。#223 裁定两个缺口一起堵并明确
   「接受并行 PR 串行化的成本」；那一轮平台仓同时有 3 个 PR。
2. 当前读回：aisoft-platform / LocalWMS / NewEMaint 三仓 `block_on_outdated_branch: true`
   （2026-09-05 23:07 切换），SFMDigitalBoard 自 2026-08-08 建仓即为 `true`。
3. `ci-outdated-branch` 现行语义：对 `public-platform` 与 `internal-application` 读
   `/branch_protections/main`，`true` 才 PASS，`false` 或键缺失都是 GAP，`public-test` SKIP，
   不在 manifest 为 GAP，403 为 SKIP。基线 `test-project-check.sh` 58 例全绿。
4. Gitea 1.26.4 swagger：`BranchProtection` 只有 `block_on_outdated_branch` 一个相关字段；
   更新分支只有手动端点 `POST /repos/{owner}/{repo}/pulls/{index}/update?style=merge|rebase`；
   仓库选项 `allow_rebase_update` 只决定按钮用 rebase 还是 merge。没有仓库级或保护级的
   「base 前进后自动更新开放 PR」，也没有 merge queue。选项 C 不是一个开关，而是新自动化。
5. runner `capacity: 1`（`01` §4.1）。级联重跑不管是人按按钮还是自动化触发，
   都在同一条串行队列里排队：N 个开放 PR 每次合并额外消耗 (N−1) 轮 CI。
6. 选 A 的兜底「合并后主干 CI 红即回滚」依赖 `push: branches: [main]` 触发的 CI：
   NewEMaint 与 LocalWMS 都有；平台仓自己的 `.gitea/workflows/ci.yml` 只有 `pull_request`，
   平台仓在 A 下没有这条兜底，除非另行授权加 push 触发。

## 风险

- A：重新接受缺口②。合并预览是运行那一刻的结果，base 之后前进则过期的绿仍可合并；
  事故形态与踩坑 22 完全相同（文本相同、语义冲突的常数断言）。兜底是 push-main CI 红即回滚，
  平台仓目前没有这条兜底。
- B：串行化成本原样保留，只是把「谁按更新」从 Issue 会话挪到合并者；rebase 式更新会重写远端
  head，Issue 会话下次 `git.push.change` 会撞 `REMOTE_BRANCH_MOVED`（`06` §1.0）；merge 式更新
  会把 `main` 的 merge commit 带进 change 分支。
- C：级联 CI 消耗不减反增（每次 main 前进自动重跑全部开放 PR），单 runner 队列被放大；
  需要新的 typed 操作与写 head 分支的身份，是 broker 治理变更，超出本 Issue 范围。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 平台级治理裁决，改动受保护 main 的分支保护合同、共享检查器 aisoft-project-check.sh 的语义与运维手册，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述「平台级裁决」，改动对象是分支保护合同与 `codex/tools/aisoft-project-check.sh`
  共享检查器：AGENTS.md 把 CI/治理与共享核心组件一律列为 complex。
- 选 A 的可测验收标准 2 要求 Gitea 界面人工切换后读回 `gitea.protection.read`，证据只能在真实
  环境一次性观测，按 `03` §3 判据声明 `verification`。
- 三个选项都要求把否定裁决写进 `06` 踩坑集，这是治理文档改动。

### 缺失的 acceptance criteria 或决策

- 无。A/B/C 已于 2026-09-16 确认点 1 裁决，见下。

## 裁决（确认点 1，2026-09-16）

负责人选定 **A 的分仓变体**：`internal-application`（NewEMaint、LocalWMS、SFMDigitalBoard）关闭
`block_on_outdated_branch`，`ci-outdated-branch` 对 internal-application 读到 `false` 改报带裁决说明的
SKIP；`aisoft-platform` 保留 `true`、检查器仍要求 `true`（平台仓 ci.yml 只有 `pull_request` 触发，
没有 push-main CI 兜底，且并行度低）。B、C 作为否定裁决与残余风险一并写进 `06` 踩坑 29。
Gitea 界面开关由负责人人工切换，会话只读回。已启动 Development Loop（manual PR）。
