---
issue: 43
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/43
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - authentication
  - security
  - platform-governance
depends_on:
  - 35
  - 41
status: approved
branch: change/43
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标与 acceptance criteria

- [ ] **AC-1** bot create argv 必须包含 `--user-type bot` 和 `--random-password`，且完全不包含
  `--must-change-password`；依赖 Gitea 1.26.4 的 bot intrinsic `MustChangePassword=false`。
- [ ] **AC-2** 不改变 declared identities、PAT scopes、credential filename/mode、ownership markers、
  token identity/site-admin read-back 或 no-op/fail-closed 语义。
- [ ] **AC-3** focused shell test 显式读取 mock Gitea argv，证明 bot type/random password 存在、
  must-change flag 缺失，并继续证明 password/token 不进入 argv/stdout。
- [ ] **AC-4** full smoke、`bash -n`、ShellCheck、`git diff --check` 通过，不加入 Secret material。
- [ ] **AC-5** 最终 PR `Closes #43` 且只允许人工合并。合并前不创建 live account/PAT 或修改仓库
  ACL/visibility/protection；合并后重新核对 exact protected-main SHA 再启动全部 declared accounts。

## 非目标与回滚

不修改 service policy、Gitea 数据库 schema、manifest identities/scopes、仓库策略、Runner、业务 VM
或公司内网。代码回滚为 revert 本 Change；合并前没有账号/PAT mutation 可回滚。
