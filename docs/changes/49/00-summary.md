---
issue: 49
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/49
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Gitea 1.26.4 拒绝 bot user random-password flag 导致 service-account bootstrap 无法创建首个账号的问题
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
  - 46
status: pr-open
branch: change/49
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/50
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

PR #48 合并后，Issue #35 rollout 从 exact
`main@d3759c39d66bb60de1d783eac5181a4ee086036f` 恢复。manifest、merge identity、两次 service
policy、Gitea service/health 和 config service-user preflight 全部 `PASS`，但第一个
`aisoft-platform-manager` 创建被 Gitea 1.26.4 拒绝：`password can only be set for individual users`。

失败发生在账号写入完成前。读回确认 manager 仍为 404，managed credential root 为 mode 700 且
0 个文件；其余 declared accounts、PAT、仓库 ACL/visibility/protection 和 `ci-bot` 均未修改。

根因是 bootstrap 对 `--user-type bot` 同时传入 `--random-password`。Gitea bot 不使用密码登录，
`MustChangePassword=false` 是其内建行为；账号创建后由独立命令生成 manifest-declared 最小 scope PAT。
本 Change 只移除该 password flag，并强化回归测试，不改变 identity、scope、credential、OS user、
repository policy 或人工 merge gate。

## AI 判级

虽然实现为局部兼容性修复，但它位于认证、授权和平台账号 bootstrap 路径，按照 `AGENTS.md` 强制
归类为 `complex`。
