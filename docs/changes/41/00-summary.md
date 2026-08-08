---
issue: 41
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/41
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Issue 35 service-policy 在 Gitea restart 后只做一次即时 health 请求而误触发回滚的问题
risk_flags:
  - availability
  - platform-governance
  - deployment
  - rollback
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on:
  - 35
  - 38
status: approved
branch: change/41
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #38 / PR #39 合并后，Issue #35 rollout 从
`main@0396779c3566ba0dbd84da745e6c482fd65a2082` 恢复。Gitea service user doctor 已真实通过，
但 `restart_and_verify` 在 `systemctl restart` 后只执行一次即时 healthz 请求。Gitea 进程尚未 ready，
脚本即判定失败并恢复原始 config。

回滚后的只读核对证明：Gitea 为 `active/running`、`healthz=pass`，live `app.ini` 与本次
`app.ini.pre` SHA-256 完全相同。问题是 readiness 时间模型，不是配置、doctor、VM 或 Gitea
持续停机。

## 影响范围与方案

只修改 service-policy 的 restart/health 边界：默认最多 30 次、间隔 1 秒；每次同时要求 systemd
active 和 healthz 成功。attempts 只允许 1–60，interval 只允许 0 或 1 秒，确保总等待有硬上限。
预算耗尽后继续使用现有自动恢复；config、账号、PAT、仓库 ACL 和保护合同均不改变。

## AI 判级

这是恢复既有合同的局部 Bug 修复，但直接影响平台 service restart、健康判定和回滚，因此按
`AGENTS.md` 强制归类为 `complex`。
