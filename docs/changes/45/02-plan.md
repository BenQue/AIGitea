---
issue: 45
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/45
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
  - 46
status: approved
branch: change/45
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

1. 保存 exact merged source、service policy PASS、caller config access failure 与账号/PAT 无 mutation 证据。
2. 先扩展 bootstrap regression：caller 无法读取 config、mock `git` user 的 `test -f/-r` 成功；确认
   旧实现 fail closed。
3. 分离 binary 与 config preflight；config 只通过 `sudo -n -u git test -f/-r` 验证，不改变其余
   账号、PAT、credential 和 Secret 逻辑。
4. 更新总纲、运维说明、Issue #35/#43 live evidence 和本 Change verification。
5. 若 exact main 自身 full smoke 失败，独立治理且等待人工合并；随后只以新 protected-main baseline
   更新本分支，再运行 focused test、full smoke、`bash -n`、ShellCheck、diff/secret checks。
6. push `change/45`，创建 `Closes #45` PR；核对 final head、statuses/Actions 后停在人工 merge gate。
7. 人工合并后从新的 exact `origin/main` SHA 创建 manager 双 token 和 9 个 project-agent token，随后
   再逐仓库应用 Issue #35 策略。

## 涉及文件

- `codex/tools/bootstrap-gitea-service-account.sh`
- `codex/tests/test-bootstrap-gitea-service-account.sh`
- `README.md`
- `06-运维手册与踩坑集.md`
- `docs/changes/35/03-verification.md`
- `docs/changes/43/03-verification.md`
- `docs/changes/45/{00-summary,01-spec,02-plan,03-verification}.md`
