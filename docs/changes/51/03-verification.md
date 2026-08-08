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

# Verification

## Live failure and bounded recovery

- PR #50：`merged=true`；head `6d6c173000300750a52bacb7ed016344f47a0d9e`，protected-main
  merge commit `04ab0cce79166ff202318ed48d9b6851b132c511`，ancestry `PASS`。
- sandbox probe at `2026-08-08T09:42:56Z`：orbctl/DNS/HTTP 失败；host probe at
  `2026-08-08T09:43:44Z`：OrbStack/VM/DNS/HTTP 200/orb exec 全部通过。结论
  `SANDBOX_PATH_BLOCKED`；没有启动或重启 VM。
- exact-main/manifest/`verify-merged`、两次 service policy、Gitea active/health 均 `PASS`；bootstrap
  前 10 个账号均 404，managed credential root mode 700 且 0 个文件。
- 首个 manager bot 与 audit token/markers 创建后，identity HTTP 403，消息为必须改密。credential root
  只出现 manager account marker、audit token 与 token marker，均 mode 600；其余 agents 未创建。
- 只对 marker 管理的 `aisoft-platform-manager` 执行专用 `must-change-password --unset` 后，读回
  `active=true`、`is_admin=false`、audit token identity `PASS`；没有设置密码。
- Context7 上游源码测试预期 bot 自动为 false，但 live 1.26.4 行为相反；实现以 live 证据和该版本专用
  CLI 为准，并保留这种差异说明。

## Candidate verification

- red regression：mock bot 创建后保持 must-change 状态；旧实现没有 policy marker，focused test 按预期
  exit 1。
- green focused regression：正常创建、现有 account/token 半状态恢复、mode 600 policy marker、第二次
  no-op 不重复 policy mutation、不安全 marker mode fail closed、config preflight、最小 PAT、Secret
  不进入 argv/stdout与 undeclared identity 均 `PASS`。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest、全部 shell/
  installer/mock/integration harness 与 static checks 通过，末行
  `Codex platform static smoke checks passed.`，exit 0。
- `bash -n`、ShellCheck、`git diff --check` 与 changed-file Secret filename scan：`PASS`。
- PR #52 initial head `743d9790287af1cc4d5a8fb4bb6160f31edea548`：`open`、
  `mergeable=true`、`merged=false`。metadata 回填会产生 final head，人工审核只认最终远端 SHA。

## Live / external boundary

manager mutation PAT、9 个 project agents/PAT、仓库授权、visibility/protection、真实项目验证和
`ci-bot` retirement：`NOT RUN`，等待 PR #51 人工合并。业务 VM/数据库和公司内网：`NOT RUN`。
