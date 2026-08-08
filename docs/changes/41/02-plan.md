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

# Implementation plan

1. 保存 live baseline：doctor pass、restart 后即时 curl refused、自动 restore、live/pre checksum 相同、
   稍后 service active/health pass。
2. 先扩展 shell regression：mock health 前两次失败第三次成功；预算耗尽触发 restore 且恢复服务最终
   ready；非法 attempts 被拒绝。确认旧实现失败。
3. 为 `restart_and_verify` 增加 30×1 秒默认 readiness budget 和 60×1 秒硬上限；保留现有
   systemd/health 双检查与 restore 调用链。
4. 更新运维说明、Issue #35/#38 live evidence 和本 Change verification。
5. 运行 focused test、full smoke、`bash -n`、ShellCheck、diff/secret checks。
6. push `change/41`，创建 `Closes #41` PR；核对最终 head、statuses/Actions 后停在人工 merge gate。
7. 人工合并后从新的 exact `origin/main` SHA 恢复 Issue #35 rollout。

## 涉及文件

- `codex/tools/sync-gitea-service-policy.sh`
- `codex/tests/test-sync-gitea-service-policy.sh`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/38/03-verification.md`
- `docs/changes/41/{00-summary,01-spec,02-plan,03-verification}.md`

## 验证与回滚

本 PR 不运行 live service apply。测试通过只证明 bounded retry 候选；真实 config/restart/health
必须在人工合并后重跑。代码 revert 不删除两次 fail-closed attempt 已生成的 root-only backup。
