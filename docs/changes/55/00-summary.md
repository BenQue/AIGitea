---
issue: 55
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/55
change_type: docs
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 回填已完成的 Issue #35 本机 Gitea rollout 证据与生命周期
risk_flags: []
required_docs:
  - 00-summary.md
confidence: high
override_reason: ''
depends_on:
  - 35
  - 51
status: pr-open
branch: change/55
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/56
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #35 已在本机 OrbStack/Gitea 完成真实 rollout 并标记 `deployed`，但 protected `main` 文档仍停留
在 Issue #51 合并前的 partial/blocking 状态。本 Change 只回填已存在的 Issue 评论、manager audit 与
root-protected evidence，不改变任何运行时合同或外部状态。

## 验收

- README 将 Gitea 身份/可见性更新为已验证状态。
- Issue #35 verification 记录 exact main、账号/PAT、仓库策略、真实 project-agent validation、
  `ci-bot` collaborator retirement、service/health、evidence/rollback 与明确 `NOT RUN` 边界。
- Issue #51 verification 记录 PR 合并和 live bootstrap 结果。
- `git diff --check` 与平台 static smoke 通过；最终 PR 仅由人手工合并，合并后无需部署并标记
  `completed`。

## 非目标

不修改脚本、manifest、Gitea config、账号/PAT、仓库 ACL/visibility/protection、业务 VM/数据库或
公司内网。`ci-bot` 账号与 legacy credential 不在本 Change 删除范围。
