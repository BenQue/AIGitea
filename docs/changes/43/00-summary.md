---
issue: 43
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/43
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Gitea 1.26.4 拒绝 bot user 显式 must-change-password flag 导致 service-account bootstrap 无法开始的问题
risk_flags:
  - authentication
  - security
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on:
  - 35
  - 41
status: approved
branch: change/43
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

PR #42 合并后，Issue #35 service policy 已从
`main@ec5fce7f4e944c961b58b6373fb9023755ab964f` 真实应用成功。账号 bootstrap 前的 live binary
预检发现：Gitea 1.26.4 的 bot 用户天然 `MustChangePassword=false`，但 compiled validation 明确拒绝
对 bot 显式传入 `--must-change-password=false`。当前 merged 脚本会在第一个账号创建前停止。

本 Change 只移除该不兼容 flag；保留 `--user-type bot`、`--random-password`、最小 PAT scopes、
mode 600 credential、ownership marker、site-admin negative read-back 和所有 Secret 边界。尚未创建任何
Issue #35 service account 或 PAT。

## AI 判级

虽然是单行兼容性修复，但它位于认证和平台账号 bootstrap 路径，按照 `AGENTS.md` 强制归类为
`complex`。
