---
issue: 12
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/12
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-deployment
  - repository-settings
  - destructive-operations
depends_on: []
status: contract-ready
branch: change/12
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Spec

## 目标与原因

让合批 PR 在部署成功后为全部关联 Issue 正确回写 `deployed`，让新接入仓库默认在合并后删除远端源分支，并把本地 worktree/branch 清理脚本纳入版本控制、修复 Bash 3.2 空数组回归。三个动作共同完成“合并后收尾”，但必须维持部署成功事实、标签三维合同和删除安全边界。

## Acceptance criteria

- [ ] AC-1：deployed 工具从 merge commit body 中提取所有独立成行、大小写规范的 `Closes #<正整数>`，去重且保持出现顺序；无匹配时才回退 subject 的 `change/N`。
- [ ] AC-2：每个 Issue 回写后保留全部 `type/*`、`complexity/*` 和非生命周期标签，移除其它生命周期标签并增加 `deployed`；label ID 从 API 读回，不硬编码。
- [ ] AC-3：token 只通过环境和 curl stdin config 使用，不出现在 argv、stdout、stderr；缺 token、无匹配或 API 失败均输出脱敏告警并以 best-effort 语义结束，不把已成功部署改判失败。
- [ ] AC-4：仓库设置工具只处理显式 `GITEA_URL/GITEA_OWNER/GITEA_REPO`，把 `default_delete_branch_after_merge` 设置为 `true` 并 GET 读回；`--disable` 可将其恢复为 `false`。
- [ ] AC-5：版本化 cleanup 工具在 macOS Bash 3.2 的空 `REMOVE` + `--apply --branches` 路径继续执行分支清理；默认 dry-run、`git branch -d`、禁止 force、跳过脏/未合并/活跃 worktree 的既有红线保持不变。
- [ ] AC-6：临时仓库和 mock API 回归覆盖合批 Issue、标签保留、fallback、API failure、设置 enable/disable、cleanup 空数组和无凭据泄漏。
- [ ] AC-7：新项目接入 runbook 明确复制 deployed 工具、在健康检查成功后调用、启用 merge 后删源分支，并要求各应用通过自己的 PR 采用。

## 接口、数据与兼容性影响

- deployed 工具环境合同：

  ```text
  GITEA_URL
  GITEA_OWNER
  GITEA_REPO
  GITEA_TOKEN
  ```

  默认读取 `git log -1 --format=%B HEAD`；测试可通过 `MERGE_MESSAGE_FILE` 注入固定输入。

- repository settings 工具复用同一组环境变量，并支持 `--disable` 回滚。
- cleanup 工具 CLI 保持：

  ```text
  <repo> [--remote NAME] [--branches] [--min-age MINUTES] [--apply]
  ```

- 不修改任何数据库、应用 schema 或 artifact。

## 风险与回滚约束

- deployed 回写失败时应用已部署，不执行应用回滚；保留告警并由人修正记账。
- repository setting 回滚运行同一脚本 `--disable` 并读回 `false`。
- cleanup 删除只允许 `git worktree remove` 的干净已合并路径和 `git branch -d`；Git 自身最后一道合并检查不得绕过。
- 应用仓库采用本工具必须走独立 PR；本平台 PR 不直接改变其 workflow。

## 非目标

- 不删除任何现有远端或本地分支。
- 不清理当前用户工作区、`.DS_Store` 或遗留 worktree。
- 不因 deployed 回写失败回滚已成功应用部署。
- 不把所有 Gitea 仓库作为隐式批量目标。
- 普通 implementation worker 永远不得编辑本运行 governing `AGENTS.md`。

## 未决问题

无。
