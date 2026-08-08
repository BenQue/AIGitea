---
issue: 41
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/41
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - availability
  - platform-governance
  - deployment
  - rollback
depends_on:
  - 35
  - 38
status: pr-open
branch: change/41
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/42
created: 2026-08-08
updated: 2026-08-08
---

# Spec

## 目标

让 service-policy 在 Gitea restart 后等待一个明确、有限的 readiness window，避免瞬时 connection
refused 被误判为持续故障，同时保留预算耗尽后的自动 config restore 和二次健康验证。

## Acceptance criteria

- [ ] **AC-1** `GITEA_HEALTH_ATTEMPTS` 默认 30，只接受整数 1–60；
  `GITEA_HEALTH_INTERVAL_SECONDS` 默认 1，只接受 0 或 1。非法值在 restart/config install 前
  fail closed。
- [ ] **AC-2** 每次 attempt 都同时要求 `systemctl is-active --quiet gitea.service` 和
  `healthz` curl 成功；任一不满足则在预算内等待下一次，不把单次 connection refused 当最终失败。
- [ ] **AC-3** readiness 成功立即返回；预算耗尽返回失败并触发现有原始 config restore。恢复后的
  restart 使用相同有界 readiness 逻辑。
- [ ] **AC-4** focused shell test 覆盖前两次 health 失败、第三次成功；并覆盖预算耗尽后恢复原始
  config、恢复 restart 最终健康以及非法 attempts fail closed。
- [ ] **AC-5** full smoke、`bash -n`、ShellCheck 和 `git diff --check` 通过，不打印 config/PAT/
  password/Secret。
- [ ] **AC-6** 最终 PR `Closes #41` 且只允许人工合并。合并前不恢复 Issue #35 的账号、PAT、ACL、
  visibility 或 protection apply；合并后从新的 exact protected-main SHA 重新运行 service policy。

## 兼容性与非目标

现有命令行参数和 Issue #35 manifest 不变，只增加两个有界环境参数。不会修改 Gitea 数据库、
Runner、业务 VM、应用、公司内网或 `ci-bot`；不会把一次稍后成功的 health 解释为此前 apply 成功。

## 回滚

合并前 live config 已由前一次脚本恢复为 pre bytes。代码回滚为 revert 本 Change；service-policy
运行时回滚继续恢复 evidence 中的 `app.ini.pre`，并使用同一 readiness budget 验证恢复后的服务。
