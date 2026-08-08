---
issue: 61
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/61
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
  - deployment
depends_on:
  - 35
  - 51
  - 55
status: implementing
branch: change/61
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## 实时只读 baseline

- `git fetch origin --prune` 后 protected `origin/main` =
  `9f4d5fbf6daea50138f41ec21779b08d6c8f8d96`，与 Issue 创建基线相同；读取时间为 2026-08-08。
- Issue #61：`open`，labels 精确为 `approved` + `complexity/complex` + `type/platform`；评论明确授权
  isolated `change/61`、四份合同、实现/测试/推送/PR，并禁止 PR 合并前 live mutation。
- `refs/remotes/origin/change/61`、`refs/heads/change/61` 和绑定 `Closes #61`/`change/61` 的 PR 均不存在；
  当前独立 worktree 从 detached `origin/main` 安全建立唯一 `change/61`。
- canonical `/Users/benque/MyDocs/AISoftPlatform` 为 `main...origin/main [behind 45]` 且只有未跟踪
  `.DS_Store`；本 Change 未在 canonical checkout 编辑或清理该文件。
- 正常 Gitea read 使用用户批准的 host execution path；sandbox DNS 失败后直接切换 host path。
  `orbstack-access-diagnostics` 正常验收调用次数：`0`。

## Candidate verification

以下结果均在 isolated `change/61` worktree、未安装 candidate 的前提下执行；temp Git repo、fake install
root、mock HTTP/identity 与 temp HOME/credential 只证明 candidate，不证明 live host/profile/timer：

- `host-access-broker/v1` strict validate：`PASS`；精确 `9` 个 project、`13` 个 operation、`0` 个 merge
  operation，并与 `gitea-governance/v1` 交叉校验。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest
  codex.runtime.tests.test_host_access -v`：`PASS`，`Ran 18 tests`。覆盖 project/operation allowlist、无任意
  shell/URL/main/force/refspec/merge surface、identity/target mismatch、401/403/404 脱敏非零、cross-project
  credential denial、Keychain Secret 不进入 argv、repo-local binding 二次 no-op、source/target mode/symlink/
  owner/多行 credential 拒绝，以及 profile apply/read-back/automatic restore/rollback/no-op。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/test-host-access-broker.sh`：`PASS`；fake install root 二次
  file manifest byte-identical，且未产生 token/profile/systemd target。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/test-agent-runtime.sh`：`PASS`；mock project profile preflight
  与 Gitea list `404` 均非零 `20/BLOCKED_EXTERNAL`，provider 未被继续调用。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；`Ran 258 tests in 14.538s`，最终输出
  `Codex platform static smoke checks passed.`
- 所有修改 shell 的 `bash -n`：`PASS`；ShellCheck 已安装并执行：`PASS`。
- `python3 -m json.tool codex/config/host-access-broker.json`、strict runtime JSON validate、Secret/cache
  scan、`git diff --check`：`PASS`。

以上 mock `HTTP_4xx`、synthetic Git push surface 与 temp profile transaction 均不标为 live PASS。

## Remote PR / CI

待 push/PR 后回填 final head、mergeable/merged、commit statuses 与 Actions runs。

## Live / external boundary

- host broker live install/upgrade/rollback：`NOT RUN`。
- Mac Keychain、repo credential binding、Git credential mutation与真实 AISoftPlatform canary：`NOT RUN`。
- NewEMaint、HSDB、rsdesign-new、SFMDigitalBoard VM profile/token mutation/rollback：`NOT RUN`。
- `emaintenance`、`sfm` 或其它 timer/service/VM stop/start/restart 与真实 private poll：`NOT RUN`。
- Gitea account/PAT/ACL/visibility/protection/merge、`ci-bot` 恢复或权限扩大：`NOT RUN`。
- 应用、数据库、DockerLab/AppServer、公司内网、生产部署：`NOT RUN`。
- `orbstack-access-diagnostics`：`NOT RUN`；仅保留 emergency fallback 合同。

最终 PR 只能由人手工合并；本会话创建 PR 并读回状态后停止。
