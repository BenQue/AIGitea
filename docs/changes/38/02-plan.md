---
issue: 38
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/38
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - platform-governance
  - deployment
  - rollback
depends_on:
  - 35
status: approved
branch: change/38
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

1. 保存 Issue #35 post-merge live evidence：root doctor exit 1、同 candidate 的 `git` doctor exit 0、
   live config 未变、service active、health pass。
2. 先扩展 shell regression，要求 doctor 通过 mock sudo 的 `-n -u git` 路径运行，并新增 unsafe
   service user negative test；确认旧实现失败。
3. 在 `sync-gitea-service-policy.sh` 中校验 service user/sudo，收紧 candidate owner/mode，并仅对
   doctor 降权；保留 root install/restart/rollback。
4. 更新运维文档、Issue #35 live evidence 和本 Change verification。
5. 运行 focused test、full smoke、`bash -n`、ShellCheck、diff/secret checks。
6. push `change/38`、创建 `Closes #38` PR，核对最终 head/remote CI 后停在人工 merge gate。
7. 人工合并后只从新的 exact `origin/main` SHA 恢复 Issue #35 service-policy rollout。

## 涉及文件

- `codex/tools/sync-gitea-service-policy.sh`
- `codex/tests/test-sync-gitea-service-policy.sh`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/38/{00-summary,01-spec,02-plan,03-verification}.md`

## 验证与回滚

本 PR 不运行 live service apply。测试通过只证明代码候选；真实 restart/health 必须在人工合并后
重新执行。回滚不删除 backup，代码 revert 与已有 `app.ini.pre` 恢复路径相互独立。
