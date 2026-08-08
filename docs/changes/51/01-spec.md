---
issue: 51
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/51
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - platform-governance
depends_on:
  - 35
  - 43
  - 45
  - 49
status: approved
branch: change/51
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与 acceptance criteria

- [ ] **AC-1** 对 manifest-declared 且有 Issue #35 ownership marker 的 exact username，bootstrap 在 PAT
  identity 前执行 `admin user must-change-password --unset <username>`；禁止 `--all`，不设置密码。
- [ ] **AC-2** 成功后写 exact managed root 下 mode 600
  `<username>.must-change-password-unset-by-issue-35` marker，内容绑定 issue、username 与 policy。
- [ ] **AC-3** marker 已存在时必须是非 symlink regular file、mode 400/600、内容精确匹配；任何冲突在
  PAT 生成或读取前 fail closed。有效 marker 使第二次运行不再执行数据库 policy mutation。
- [ ] **AC-4** marker 缺失但账号/account marker 已存在时必须支持一次恢复，覆盖当前 live manager
  半状态；恢复后现有 token identity 必须为 exact username 且非 site-admin。
- [ ] **AC-5** 保持 bot create 无任何 password flag、`sudo -n -u git`、最小 PAT scopes、mode 600
  credential、token ownership marker、Secret 不进入 argv/stdout 和 undeclared identity fail closed。
- [ ] **AC-6** focused red/green、full smoke、`bash -n`、ShellCheck、`git diff --check` 通过；最终 PR
  `Closes #51` 且只由人合并。合并前不创建其余 agents 或修改仓库策略/`ci-bot`。

## 非目标与回滚

不设置账号密码，不修改 site-admin、PAT scopes、manifest、Gitea config/DB schema、仓库权限、业务 VM、
数据库或公司内网。代码可 revert；已恢复的 manager 不回设 MustChangePassword，也不删除账号/PAT。
