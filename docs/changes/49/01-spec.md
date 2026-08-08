---
issue: 49
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/49
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
  - 46
status: approved
branch: change/49
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与 acceptance criteria

- [ ] **AC-1** Gitea bot create argv 必须包含 `--user-type bot`，且不包含 `--password`、
  `--random-password`、`--must-change-password` 或任何其它 password flag。
- [ ] **AC-2** 账号创建后仍由独立 `generate-access-token` 命令生成 manifest-declared 最小 scopes；
  manager audit/mutation token 与 project-agent token 的角色、文件名和 scopes 不变。
- [ ] **AC-3** 保持 `sudo -n -u git` CLI 身份、caller-owned mode 700 temp/credential root、mode 600
  credential/markers、非 site-admin identity read-back、幂等与冲突 fail-closed。
- [ ] **AC-4** focused regression 必须先证明旧 argv 失败，再验证新 argv 无 password 字样；继续覆盖
  config service-user preflight、账号/PAT、no-op、undeclared identity 和 Secret 不进入 argv/stdout。
- [ ] **AC-5** full smoke、`bash -n`、ShellCheck、`git diff --check` 通过，不提交任何 credential、PAT、
  password、config content 或 `.env`。
- [ ] **AC-6** 最终 PR `Closes #49` 且只由人手工合并。合并前不再重试 live bootstrap、仓库策略或
  `ci-bot` retirement；合并后必须从新的 exact protected-main SHA 恢复 rollout。

## 非目标与回滚

不修改账号类型、PAT scopes、manifest、Gitea config/DB schema、仓库设置、Runner、业务 VM/数据库或
公司内网。代码回滚为 revert 本 Change；候选合并前没有新的 live mutation。现场保留 `ci-bot`，直到
每个项目真实正反向验证全部 `PASS`。
