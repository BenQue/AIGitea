---
issue: 45
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/45
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
  - 46
status: approved
branch: change/45
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与 acceptance criteria

- [ ] **AC-1** `GITEA_BIN` 继续由 caller 验证为可执行文件；受保护 `GITEA_CONFIG` 必须由
  `sudo -n -u git test -f` 和 `test -r` 验证。任一失败均在 credential directory、账号或 PAT
  mutation 前 fail closed，并给出不包含 Secret 的明确错误。
- [ ] **AC-2** 不修改 `/etc/gitea` owner/mode/ACL，不让 caller 读取 config，也不用 root 运行整个
  bootstrap。Gitea CLI 仍只以 OS user `git` 运行；token stdout redirection 仍发生在 caller-owned
  mode 700 temp directory。
- [ ] **AC-3** focused regression 构造 caller 不可读、mock `git` user 可读的 config，证明旧实现失败、
  修复后 `test -f/-r` 各执行一次，并继续覆盖账号创建、PAT、no-op、undeclared identity 与 Secret
  不进入 argv/stdout。
- [ ] **AC-4** 不改变 declared identities、PAT scopes、credential filename/mode、ownership markers、
  token identity/site-admin read-back 或 bot create argv。
- [ ] **AC-5** full smoke、`bash -n`、ShellCheck、`git diff --check` 通过，不加入 credential、PAT、
  password、config content 或其它 Secret material。
- [ ] **AC-6** 最终 PR `Closes #45` 且只允许人工合并。合并前不重试 live account/PAT 或仓库
  ACL/visibility/protection；合并后重新核对 exact protected-main SHA，再恢复 Issue #35 rollout。

## 非目标与回滚

不修改 service policy、Gitea config bytes/permissions、数据库 schema、manifest、仓库设置、Runner、
业务 VM、数据库或公司内网。代码回滚为 revert 本 Change；合并前没有 live account/PAT mutation，
无需数据回滚。
