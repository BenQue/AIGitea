---
issue: 51
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/51
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - platform-governance
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

# Implementation plan

1. 保存 PR #50 exact-main、双路径 OrbStack、service policy、账号/PAT 半状态与 HTTP 403 证据。
2. 只对 Issue #35 marker 管理的 manager 用专用 CLI 精确恢复，验证 active/non-admin/token identity。
3. 先扩展 mock 复现 MustChangePassword 403，覆盖 policy unset、marker、恢复、no-op 与冲突 fail closed，
   取得旧实现 red。
4. 在 bootstrap 中加入 exact username policy unset 与 mode 600 marker，不改变 create/PAT/credential 合同。
5. 更新总纲、运维说明、Issue #35/#49 verification 和本 Change 四份文档。
6. 运行 focused test、full smoke、`bash -n`、ShellCheck、diff/Secret checks。
7. push `change/51`，创建 `Closes #51` PR，核对 final head/remote CI 并停止在人工 merge gate。
8. 人工合并后从新的 exact main 幂等恢复 manager，创建其余 9 个 agents/PAT，再逐仓库授权和验证；
   全部项目 PASS 前保留 `ci-bot`。

## 涉及文件

- `codex/tools/bootstrap-gitea-service-account.sh`
- `codex/tests/test-bootstrap-gitea-service-account.sh`
- `README.md`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/49/03-verification.md`
- `docs/changes/51/{00-summary,01-spec,02-plan,03-verification}.md`
