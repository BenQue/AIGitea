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
status: pr-open
branch: change/43
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/44
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## Live compatibility baseline

- PR #42 merged identity：`main@ec5fce7f4e944c961b58b6373fb9023755ab964f`。
- installed binary：Gitea `1.26.4`。`admin user create --help` 支持 `--user-type bot`；binary string
  存在 `must-change-password flag can only be set for individual users`。
- `admin user generate-access-token --help` 支持 `--username`、`--token-name`、`--scopes` 和 `--raw`。
- Issue #35 service account/PAT：`NOT RUN`；预检发生在第一个账号 mutation 前。

## Candidate verification

- focused bootstrap shell regression：`PASS`；旧实现因 argv 包含 must-change flag 失败，修复后证明
  bot/random-password 存在、must-change flag 缺失、Secret 不进入 argv/stdout。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest 及全部
  shell/integration mock regressions 通过。
- `bash -n`、ShellCheck、`git diff --check`：`PASS`；changed files 未加入 credential、PAT、
  password、`.env` 或其它 Secret material。
- PR #44 初始 head `7f12a911957d6a0dcb1544dd0b05ac23d197162f`：`open`、
  `mergeable=true`、`merged=false`；metadata 回填后必须重新读回 final head。
- live account/PAT/ACL/visibility/protection：`NOT RUN`，等待本 PR 人工合并。
