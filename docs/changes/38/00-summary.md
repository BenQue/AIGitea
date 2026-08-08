---
issue: 38
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/38
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Issue 35 service-policy live apply 在配置写入前因 Gitea doctor 被错误地以 root 运行而停止的问题
risk_flags:
  - security
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
status: pr-open
branch: change/38
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/39
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #35 / PR #36 已人工合并到受保护 `main@69251fd4d07665385eb6d9142038848c2b9392d7`。
post-merge live rollout 的 service-policy pre-check 正确发现 registration/default-private drift；但
`sync-gitea-service-policy.sh` 整体要求 root，同时直接以 root 调用
`gitea doctor check --all`。Gitea 1.26.4 因此在 candidate 安装和 restart 之前 fail closed。

同一个 candidate 以 systemd 的 Gitea service user `git` 运行 doctor 返回 `0`。live
`/etc/gitea/app.ini` 未修改，Gitea 保持 `active` 且 `healthz=pass`。本 Change 只修复 doctor 的
有效 OS identity，不改变 Issue #35 的 Gitea 账号、PAT、仓库、visibility 或保护合同。

## 影响范围

- `sync-gitea-service-policy.sh` 的 candidate owner/mode 和 doctor effective user。
- service-policy shell regression test、运维说明及 Issue #35 post-merge evidence。
- 人工合并后 Issue #35 rollout 的恢复闸门。

## 方案

保持 config backup/install、systemd restart、health check 和 rollback 由 root 管理；仅将 mode 600
candidate 及其 mode 700 临时目录交给显式、受校验的 `GITEA_SERVICE_USER`，默认 `git`，再通过
`sudo -n -u` 运行 doctor。非法用户名、不存在的 live user 或不可用的 sudo 必须在安装 candidate
前停止。测试使用受控 mock sudo 证明 doctor 的 effective-user argv 和 fail-closed 行为。

## AI 判级

虽然这是恢复既有合同的局部 Bug 修复，但它修改平台治理和 Gitea restart/rollback 路径；按照
`AGENTS.md` 的强制规则，effective complexity 为 `complex`。
