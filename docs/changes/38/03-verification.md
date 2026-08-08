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

# Verification

## Live failure baseline

- Issue #35 exact merge identity：`main@69251fd4d07665385eb6d9142038848c2b9392d7`。
- service-policy pre-check：`DISABLE_REGISTRATION=false`、`DEFAULT_PRIVATE=last`，结果 `DRIFT`；
  `FORCE_PRIVATE=false`、`REQUIRE_SIGNIN_VIEW=false` 已符合合同。
- root doctor：exit 1，Gitea 1.26.4 拒绝 root；同一个 mode 600 candidate 由 `git` 运行 doctor：
  exit 0，28 checks 完成。
- candidate 未安装；`/etc/gitea/app.ini` 仍为 pre-check 原值；`gitea.service=active`、
  `healthz=pass`。evidence 目录只有 root-only `app.ini.pre`。

## Candidate verification

- service-policy focused shell regression：`PASS`；mock sudo 确认 doctor 使用 `-n -u git`，unsafe
  service user fail closed。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；214 个 Python unittest 通过，所有
  现有 shell/integration mock regressions 通过。
- `bash -n`、ShellCheck、`git diff --check`：`PASS`。
- changed files 未加入 credential、PAT、password、`.env` 或其它 Secret material：`PASS`。
- live service apply/restart：`NOT RUN`，必须等待本 PR 人工合并。
- Gitea accounts/PAT/repository ACL/visibility/protection、业务 VM/数据库、公司内网：`NOT RUN`。
