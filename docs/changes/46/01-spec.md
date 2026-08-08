---
issue: 46
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/46
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
  - compatibility
  - artifact
  - platform-governance
depends_on:
  - 27
status: approved
branch: change/46
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与 acceptance criteria

- [ ] **AC-1** smoke 必须要求 compatibility matrix 只有两个 exact row IDs，防止重复、缺失或隐式
  新增 row 绕过 committed policy。
- [ ] **AC-2** containerd row 必须是 exact `image_store=containerd`、`status=supported`，且 evidence
  精确绑定 `kind=real-e2e`、`issue-27-containerd-a75181cd7209` 与
  `docs/changes/27/03-verification.md`。
- [ ] **AC-3** classic row 必须是 exact `image_store=classic`、`status=rejected`、`evidence=null`；
  不因修复 stale assertion 把 classic 写成 supported。
- [ ] **AC-4** 不修改 compatibility matrix、schema、runtime、Docker harness 或 Issue #27 evidence。
- [ ] **AC-5** `gitea-platform-ops` skill 必须把既有逐仓库 `ci-bot` retirement gate 明确绑定到
  `gitea-governance.sh retire-shared-bot`；不得减少 project-agent 的 private read、Issue/comment/
  label、feature push、PR、main denial 证据。
- [ ] **AC-6** 旧 image-store assertion 对 exact main 稳定退出 1；修复后又精确定位 skill command
  name gate；两处修复后 216 Python tests、全部 shell/static smoke、`bash -n`、ShellCheck 与
  `git diff --check` 通过。
- [ ] **AC-7** 最终 PR `Closes #46` 且只允许人工合并；不得借此执行 Docker、VM、业务部署或公司
  内网 mutation。

## 回滚

代码回滚为 revert 本 Change。回滚只会恢复两个已证明无法满足的旧静态门禁，不会改变任何
runtime/VM/制品状态。
