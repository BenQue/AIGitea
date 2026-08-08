---
issue: 45
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/45
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 service-account bootstrap 以普通 caller 检查 root:git Gitea config 而在 mutation 前误阻塞的问题
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
  - 46
status: approved
branch: change/45
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

PR #44 合并后，Issue #35 rollout 从 exact `main@3b01e29dad23e6d78d83c48014d69ea78a37a83e`
继续。service policy 与 manifest 均 `PASS`，但第一个账号 bootstrap 在任何 mutation 前返回
`BLOCKED_EXTERNAL: Gitea binary or config is unavailable`。

真实 config 为 root:git 保护的 `/etc/gitea/app.ini`；普通运维 caller `benque` 不应拥有遍历或读取
权限，而实际 Gitea CLI 命令已经通过 `sudo -n -u git` 运行。旧脚本却先以 caller 执行 `-f`，把正确
的权限隔离误判为 config 不存在。credential root、账号和 PAT 均未创建。

本 Change 只让实际 Gitea OS user `git` 通过 `sudo -n` 验证 config 存在且可读；caller 仍验证 binary
可执行性并独占 credential root、临时目录、stdout redirection 和 mode 600 token 文件。不修改任何
账号、scope、manifest、仓库策略或 OS 文件权限。

实现期间 exact main 暴露两个与本 Change 无关的既有 full-smoke 静态门禁漂移；Issue #46 / PR #47
已独立修复并由人合并。当前候选以 `main@dd9675d10778daa0fb4ce6609494559ed24647e6` 为基线，不能用
Issue #46 的修复掩盖本 Change 自身 focused/full-smoke 结果。

## AI 判级

这是局部兼容性修复，但位于认证、授权和平台账号 bootstrap 路径，按照 `AGENTS.md` 强制归类为
`complex`。
