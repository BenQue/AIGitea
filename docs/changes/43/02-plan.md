---
issue: 43
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/43
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - authentication
  - security
  - platform-governance
depends_on:
  - 35
  - 41
status: approved
branch: change/43
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

1. 保存 installed Gitea 1.26.4 binary help 与 compiled rejection read-only evidence。
2. 先扩展 bootstrap regression，要求 bot argv 完全不含 must-change flag；确认旧实现失败。
3. 从 bot create 命令移除单个不兼容 flag，不改变其它账号/PAT/Secret 逻辑。
4. 更新运维文档、Issue #35/#41 live evidence和本 Change verification。
5. 运行 focused test、full smoke、`bash -n`、ShellCheck 和 diff/secret checks。
6. push `change/43`，创建 `Closes #43` PR；核对 final head/remote CI 后停在人工 merge gate。
7. 人工合并后从新的 exact main SHA 创建 manager 双 token 和 9 个 project-agent token。

## 涉及文件

- `codex/tools/bootstrap-gitea-service-account.sh`
- `codex/tests/test-bootstrap-gitea-service-account.sh`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/41/03-verification.md`
- `docs/changes/43/{00-summary,01-spec,02-plan,03-verification}.md`
