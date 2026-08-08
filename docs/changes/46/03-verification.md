---
issue: 46
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/46
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
  - compatibility
  - artifact
  - platform-governance
depends_on:
  - 27
status: pr-open
branch: change/46
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/47
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## Baseline

- exact baseline：`origin/main@3b01e29dad23e6d78d83c48014d69ea78a37a83e`；Issue #45 worktree 对
  `docker-release/compatibility/image-stores-v1.json` 与 `codex/tests/smoke.sh` 均为 zero diff。
- committed matrix：containerd row 为 `supported`，evidence 精确绑定
  `issue-27-containerd-a75181cd7209`；classic row 为 `rejected + evidence:null`。
- 旧 smoke jq assertion 要求 `all(.rows[]; rejected + null)`，对上述 matrix exit 1。full smoke 的
  216 个 Python tests 全部 `OK`，总脚本随后因该静态断言退出 1；不能写为 full smoke PASS。
- image-store assertion 修复后，full smoke 继续在 exact `retire-shared-bot` skill grep 退出 1；skill
  已包含相同的逐仓库 retirement 和完整 project-agent evidence gate，但没有 purpose-built command
  name。后续全部静态检查单独执行为 `PASS`，确认没有第三个既有门禁失败。

## Candidate verification

- 新 jq assertion exact row/status/evidence check：`PASS`；containerd exact real-E2E evidence 与 classic
  rejected/null evidence 分开验证，row IDs 只能是两个 committed values。
- `gitea-platform-ops` exact retirement command + 原 evidence gate check：`PASS`；补充
  `gitea-governance.sh retire-shared-bot` 后仍完整要求 private read、Issue/comment/label、feature push、
  PR、main-push-denied 与 main-merge-denied。
- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`；216 个 Python unittest、全部 shell/
  installer/mock/integration harness 与 static checks 通过，末行
  `Codex platform static smoke checks passed.`，exit 0。
- `bash -n codex/tests/smoke.sh`、ShellCheck、`git diff --check`：`PASS`。
- compatibility matrix/runtime/VM/Docker/制品/部署/company intranet mutation：`NOT RUN`。
- PR #47 initial head `74607184f2e2729e17809941f5a1feec87daf939`：`open`、
  `mergeable=true`、`merged=false`；metadata 回填将产生 final head，必须重新读回。
- PR merge：`NOT RUN`，必须人工执行。
