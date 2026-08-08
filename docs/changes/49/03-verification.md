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
status: pr-open
branch: change/49
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/50
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## Live failure baseline

- PR #48：`merged=true`；head `cb27a9c07f8260f653886daf3b5363bce9ca3b3a`，protected-main
  merge commit `d3759c39d66bb60de1d783eac5181a4ee086036f`，ancestry `PASS`。
- exact merged source 的 manifest validate、`verify-merged`、两次 service-policy check、Gitea
  systemd active/health HTTP 200 与 config service-user preflight 均 `PASS`。
- 正确 manifest 路径读回的 1 个 manager 与 9 个 project agents 在 bootstrap 前均为 HTTP 404；legacy
  credential mode 600 且 admin marker 唯一。
- 首个 manager bootstrap 被 Gitea 1.26.4 返回 `password can only be set for individual users`。
  失败后 manager 仍为 HTTP 404，managed credential root 为 mode 700 且 0 个文件；PAT、ACL、
  visibility、protection 与 `ci-bot` 均未修改。
- OrbStack 双路径结论仍为 `SANDBOX_PATH_BLOCKED`：sandbox path 失败，host path 上 VM、DNS、HTTP、
  orb exec 通过；没有重启 VM。

## Candidate verification

- Context7 official Gitea source 与 live `gitea version 1.26.4` CLI help 共同确认：bot 内建
  `MustChangePassword=false`；密码参数只适用于 individual user，PAT scopes 仍支持 read/write 分类。
- red regression：只修改测试后，旧实现因 create argv 含 `--random-password` 按预期退出 1，并输出
  `bot create argv must omit all password flags`。
- green focused regression：`bash codex/tests/test-bootstrap-gitea-service-account.sh` 为 `PASS`；create
  argv 保留 `--user-type bot` 且不含任何 password 字样，config `test -f/-r`、账号/PAT、no-op、
  undeclared identity、mode 600 credential 与 Secret 不进入 argv/stdout 均继续覆盖。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest、全部 shell/
  installer/mock/integration harness 与 static checks 通过，末行
  `Codex platform static smoke checks passed.`，exit 0。
- `bash -n`、ShellCheck、`git diff --check` 与 changed-file Secret filename scan：`PASS`。
- PR #50 initial head `a9323e0bf2a83f374d1c4c313156a2c53bd340de`：`open`、
  `mergeable=true`、`merged=false`。本次 metadata 回填会产生 final head，required CI 与人工审核必须
  只认最终 SHA。

## Live / external boundary

账号/PAT、仓库授权、visibility/protection、真实项目正反向验证和 `ci-bot` retirement：`NOT RUN`，
必须等待 PR #49 人工合并并从新的 exact protected-main SHA 恢复。业务 VM/数据库和公司内网：
`NOT RUN`，不在本 Change 范围。
