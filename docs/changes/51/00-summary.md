---
issue: 51
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/51
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 将 live Gitea 1.26.4 bot 的 must-change-password 精确恢复纳入可审计幂等 bootstrap
risk_flags:
  - authentication
  - authorization
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
  - 43
  - 45
  - 49
status: pr-open
branch: change/51
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/52
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

PR #50 合并后，Issue #35 rollout 从 exact
`main@04ab0cce79166ff202318ed48d9b6851b132c511` 恢复。首个 manager bot 与 audit PAT/marker 已创建，
但 token identity 返回 HTTP 403 `You must change your password`；其余 9 个 project agents 尚未开始。

live Gitea 1.26.4 的 create 命令拒绝 bot 的 password/must-change-password flags，但实际创建结果仍为
MustChangePassword=true。通过专用 `admin user must-change-password --unset aisoft-platform-manager`
精确恢复后，manager 为 `active=true`、`is_admin=false`，现有最小 scope audit PAT identity `PASS`，
且没有设置密码。

本 Change 把该专用恢复步骤纳入 bootstrap，并以 mode 600 ownership marker 记录完成状态：marker 缺失
时恢复一次，存在时必须类型、mode 和内容精确匹配，幂等重跑不重复数据库 mutation。其它 identity、
PAT、credential 与 repository policy 合同不变。

## AI 判级

虽然是局部兼容性修复，但位于认证、授权和平台账号 bootstrap 路径，按照 `AGENTS.md` 强制归类为
`complex`。
