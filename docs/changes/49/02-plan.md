---
issue: 49
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/49
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
  - 46
status: approved
branch: change/49
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

1. 保存 PR #48 exact-main、service/config preflight、Gitea 版本与账号/credential 无半成品证据。
2. 先把 focused regression 改为拒绝 bot create argv 中所有 password 字样，并运行旧实现取得预期 red。
3. 只移除 `--random-password`，保持 bot type、CLI OS user、PAT、credential 与 read-back 逻辑不变。
4. 更新总纲、运维说明、Issue #35/#45 live evidence 和本 Change 四份文档。
5. 运行 focused test、full smoke、`bash -n`、ShellCheck、diff/secret checks。
6. push `change/49`，创建 `Closes #49` PR，核对 final head 与 remote CI 后停止在人工 merge gate。
7. 人工合并后从新的 exact `origin/main` 创建 manager 双 token 和 9 个 project-agent token，再逐仓库
   应用、读回、真实验证；全部项目通过前不退休 `ci-bot`。

## 涉及文件

- `codex/tools/bootstrap-gitea-service-account.sh`
- `codex/tests/test-bootstrap-gitea-service-account.sh`
- `README.md`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/45/03-verification.md`
- `docs/changes/49/{00-summary,01-spec,02-plan,03-verification}.md`
