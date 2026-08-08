---
issue: 38
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/38
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - platform-governance
  - deployment
  - rollback
depends_on:
  - 35
status: approved
branch: change/38
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标

恢复 Issue #35 已批准的 service-policy contract：root 继续负责受保护 config 和 systemd 生命周期，
而 Gitea CLI doctor 必须以实际 Gitea service OS identity 读取 candidate 并连接现有数据目录/数据库。

## Acceptance criteria

- [ ] **AC-1** `GITEA_SERVICE_USER` 默认精确为 `git`；只接受安全的本地用户名格式。live apply 时该
  用户必须存在，异常在 candidate install/restart 前 fail closed。
- [ ] **AC-2** candidate config 保持 mode 600，其临时目录保持 mode 700；live doctor 前仅把这两个
  临时对象的 owner 交给 Gitea service user，不改变 `/etc/gitea/app.ini`、backup 或 evidence owner。
- [ ] **AC-3** doctor 必须经 `sudo -n -u "$GITEA_SERVICE_USER"` 执行；不得再次以 root 直接启动
  Gitea binary。config install、restart、health 和 rollback 的 root 边界保持不变。
- [ ] **AC-4** shell regression test 使用 mock sudo 证明每次 candidate doctor 都携带
  `-n -u git`，并证明 unsafe service user 在 doctor/restart 前被拒绝。
- [ ] **AC-5** focused test、full `codex/tests/smoke.sh`、`bash -n`、ShellCheck（若可用）和
  `git diff --check` 通过；测试不得打印 config Secret 或任何 PAT。
- [ ] **AC-6** 最终 PR `Closes #38` 且只允许人工合并。合并前不得用本分支执行 live config apply；
  合并后必须重新核对 exact protected-main SHA，再恢复 Issue #35 rollout。

## 兼容性与非目标

命令行参数保持兼容，只增加可选的 `GITEA_SERVICE_USER`/`SUDO_BIN` 环境覆盖；默认 live 行为匹配
当前 `gitea-ci` 的 `git` systemd user。不会创建或修改 Gitea 用户/PAT、仓库协作者、visibility、
branch protection、Runner、业务 VM、数据库或公司内网。不会删除 Issue #35 已生成的 pre-backup。

## 回滚

合并前没有 live mutation。代码回滚为 revert 本 Change；Issue #35 的 service-policy rollback 仍
使用 `/var/lib/aisoft/backups/gitea-policy/.../app.ini.pre` 恢复原始 bytes/owner/mode 并重启验证。
