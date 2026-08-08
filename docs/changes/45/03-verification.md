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
status: pr-open
branch: change/45
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/48
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## Live failure baseline

- PR #44 已人工合并到 `main@3b01e29dad23e6d78d83c48014d69ea78a37a83e`；merged source manifest
  validate 与 service policy check 均 `PASS`。
- 账号 bootstrap 在第一个 mutation 前返回 config unavailable：caller `benque` 无法遍历 root:git
  `/etc/gitea/app.ini`，旧脚本以 caller 执行 `-f`。credential root 不存在，10 个 declared accounts
  的 API read-back 均为 404，PAT 未生成。
- service policy 保持两次连续 `PASS`；Gitea active/health pass。仓库 ACL/visibility/protection、
  `ci-bot` retirement、业务 VM/数据库和公司内网均未修改。

## Candidate verification

- Issue #46 / PR #47 已人工合并；`change/45` 通过 `git merge --ff-only origin/main` 从
  `3b01e29dad23e6d78d83c48014d69ea78a37a83e` 更新到
  `dd9675d10778daa0fb4ce6609494559ed24647e6`，本地 Issue #45 修改文件与该 fast-forward 无重叠。
- red/green focused regression：旧实现因 caller config check 返回 `BLOCKED_EXTERNAL`；修复后 caller
  不可读场景通过，并读回 `git` user 的 `test -f/-r` 各一次。
- focused bootstrap shell regression：`PASS`；账号创建、PAT、no-op、undeclared identity、bot argv、
  mode 600 credential 与 Secret 不进入 argv/stdout 均继续通过。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest、全部
  shell/installer/mock/integration harness 与 static checks 通过，末行
  `Codex platform static smoke checks passed.`，exit 0。
- `bash -n`、ShellCheck、`git diff --check`：`PASS`；changed files 未加入 credential、PAT、password、
  config content、`.env` 或其它 Secret material。
- PR #48 initial head `1b777b4acbcf4b80797c0929476f4eae74a1fc3c`：`open`、
  `mergeable=true`、`merged=false`；metadata 回填将产生 final head，必须重新读回。
- remote status/Actions、live account/PAT/ACL/visibility/protection：`NOT RUN`。

## 合并与后续边界

PR merge 必须由人执行。候选测试不授权读取 `/etc/gitea/app.ini`、创建 live account/PAT、改变仓库
策略、退休 `ci-bot` 或连接公司内网；只有合并后的 exact protected-main source 才能恢复 Issue #35
rollout。

## 合并后读回

- PR #48 已由人合并；head `cb27a9c07f8260f653886daf3b5363bce9ca3b3a`，protected-main merge
  commit `d3759c39d66bb60de1d783eac5181a4ee086036f`，且 head 为 main ancestor。
- exact merged source 的 config `sudo -n -u git test -f/-r` preflight 已通过，证明 Issue #45 目标完成。
- 随后的账号创建进入 Gitea CLI 后被另一个独立兼容性问题阻止：bot user 不接受
  `--random-password`。失败没有创建账号或 PAT；Issue #49 负责修复，不回写或扩大 Issue #45 合同。
