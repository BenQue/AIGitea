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
status: approved
branch: change/41
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## Live failure baseline

- PR #39 merged identity：`main@0396779c3566ba0dbd84da745e6c482fd65a2082`；Issue #35
  `verify-merged=PASS`。
- 修复后的 `git`-user doctor：`PASS`。首次 restart 后即时 healthz curl connection refused；脚本
  触发 restore 并返回 `BLOCKED_EXTERNAL`。
- 恢复后只读证据：`gitea.service=active/running`、`ExecMainStatus=0`、`healthz=pass`；live
  `/etc/gitea/app.ini` 与本次 `app.ini.pre` SHA-256 均为
  `ced87688df1158ae3e70a698a3ddf9da6a1b54c7359df1477f4faad4aa7d7841`，bytes restored=`yes`。
- service policy 仍为 `DRIFT`；不能把稍后健康写成 apply 成功或 deployed。

## Candidate verification

- focused shell regression：`PASS`；覆盖 transient health recovery、retry exhaustion + config restore、
  recovery restart 和 unsafe attempts。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest 及全部
  shell/integration mock regressions 通过。
- `bash -n`、ShellCheck、`git diff --check`：`PASS`；changed files 未加入 credential、PAT、
  password、`.env` 或其它 Secret material。
- live service apply/restart：`NOT RUN`，等待本 PR 人工合并。
- Gitea accounts/PAT/repository ACL/visibility/protection、`ci-bot` retirement、业务 VM/数据库、
  公司内网：`NOT RUN`。
