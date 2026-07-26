---
issue: 19
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/19
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
depends_on: []
status: implemented
branch: change/19
pr_url:
created: 2026-07-26
updated: 2026-07-26
---

# Spec

## 目标与原因

为已合并且明确无需部署的变更提供准确终态，消除 closed Issue 继续保留
`pr-open` 或被误标 `deployed` 的二选一错误，同时保持 type、complexity 和
lifecycle 三维标签合同、受保护 `main` 与人工合并闸门不变。

## Acceptance criteria

- [ ] AC-1：`codex/config/gitea-labels.json` 新增唯一 `completed` 标签，描述明确限定
  “最终 PR 已合并且无需部署”，规范标签总数为 17。
- [ ] AC-2：runtime 和 Gitea adapter 把 `completed` 识别为生命周期终态；任一 Issue
  仍只能有一个 lifecycle，且 resolved lifecycle 仍必须有唯一 complexity。
- [ ] AC-3：dependency readiness 接受 closed + `completed` 或 closed + `deployed`，
  但 open Issue 或仅有 `pr-open` 仍保持等待。
- [ ] AC-4：`mark-deployed-issues.sh` 会移除 `completed` 并写入唯一 `deployed`，
  同时保留 type、complexity 和非 managed labels。
- [ ] AC-5：README、01/03/04/09 分册、global AGENTS 和 onboarding skill 对 17 标签、
  八个 lifecycle、`completed`/`deployed` 选择规则保持一致；历史实施计划不得被改写成
  当时已有 `completed`。
- [ ] AC-6：mock label sync 第一次创建 17 个、第二次创建 0 个；Python/shell 回归、
  `bash -n`、ShellCheck、`bash codex/tests/smoke.sh` 全部通过。
- [ ] AC-7：本 PR 合并后，当前 Gitea 创建并读回 `completed`，#1、#3–#7、#11–#13、
  #17 均读回 `type/platform`、`complexity/complex`、`completed`，且无其它 lifecycle。
- [ ] AC-8：迁移失败时不删除 Issue、不改变 Issue open/closed 状态、不修改 PR 或
  `main`；可按迁移前读回快照恢复每个 Issue 的原标签集合。

## 接口、数据与兼容性影响

- `LIFECYCLE_LABELS` 增加 `completed`；所有 managed-label 校验自动纳入该标签。
- dependency 的完成判据从 closed + `deployed` 扩展为 closed +
  (`completed` 或 `deployed`)。
- `deployed` 仍是部署验证证据；`completed` 只表示合并且无需部署。
- 现有 `mark-deployed-issues.sh` 文件名、环境变量和默认行为保持兼容。
- 标签 manifest 是 canonical source；各接入仓库仍须独立 provision 和读回。

## 风险与回滚约束

- `completed` 和 `deployed` 必须互斥；任何包含两者的 desired labels 都应在 HTTP
  mutation 前失败。
- live 迁移只能在本 PR 合并后执行，先保存 issue number 与原标签名称的脱敏快照。
- 代码回滚使用 Gitea PR revert；标签目录中的 `completed` 可保留为未使用标签，或在
  确认没有 Issue 引用后由人删除。
- Issue 标签回滚使用迁移前快照逐项恢复，不改变 Issue state、评论、PR 或 commit。

## 非目标

- 不自动合并 PR，不增加第二个人工审批闸门。
- 不把 `Closed`、本地测试通过或 synthetic 验证等同于部署成功。
- 不修改应用仓库现有部署 workflow；应用采用新标签时仍需自己的 PR。
- 不扫描或批量修改其它 Gitea 仓库。

## 未决问题

无。
