---
issue: 35
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/35
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
depends_on: []
status: pr-open
branch: change/35
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/36
created: 2026-08-08
updated: 2026-08-08
---

# Verification

## 只读 baseline

- 时间：2026-08-08；Gitea `1.26.4`。
- sandbox probe：`orbctl=Stopped`、DNS/HTTP/orb exec 失败。
- host probe：`orbctl=Running`，`gitea-ci` running，DNS/HTTP/orb exec 通过。
- 结论：`SANDBOX_PATH_BLOCKED`；OrbStack/Gitea 未停机，后续只读 live probe 使用 host path。
- 9 个显式仓库的 visibility 与 branch protection 已通过 VM-local admin read-only helper 脱敏读回；
  结果记录在 Issue #35 body 和本 Change 的 Summary/Spec。
- 当前 Mac Git credential 对 `admin/aisoft-platform` 为 push/pull，仓库 Admin permission=false；
  branch protection GET 为 `403`。未因此扩权。

## 实现验证

- `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：`PASS`。
  - 214 个 Python unittest 全部通过；
  - architecture、agent runtime、labels/lifecycle、repository settings、legacy collaborator、
    cleanup、retention、private-read helper、skills、host-role、Docker release/image-store、GitHub
    inbound sync 的现有回归全部通过；
  - 新增 service-account bootstrap 与 Gitea service policy shell tests 通过；
  - ShellCheck、`bash -n` 和 strict JSON checks 通过。
- `PYTHONPATH=codex/runtime python3 -m aisoft_gitea_governance.cli --manifest
  codex/config/gitea-governance.json validate`：`PASS`，`repository_count=9`，public allowlist 精确为
  `admin/aisoft-platform`、`admin/myapp`、`admin/smoke-test`。
- `python3 -m unittest codex.runtime.tests.test_gitea_governance -v`：`PASS`，13 个 focused tests
  覆盖 strict manifest、private/public、唯一 agent、manager 非 site-admin、token file mode、
  cross-project Write、protection field preservation、apply/no-op、rollback 和 app.ini 精确编辑。
- `bash codex/tests/test-bootstrap-gitea-service-account.sh`：`PASS`；账号/token 幂等、undeclared
  identity fail closed、credential mode 600、token/password 不进入 argv/stdout。
- `bash codex/tests/test-sync-gitea-service-policy.sh`：`PASS`；drift check、candidate doctor、
  apply/read-back、restart/health mock、backup rollback、invalid candidate 在 restart 前拒绝。
- `git diff --check`、`jq empty codex/config/gitea-governance.json`、manifest exact allowlist assertion、
  repository `__pycache__` absence：`PASS`。

以上均为 platform-local mock/static/synthetic evidence；不等于 live Gitea 账号、ACL、visibility、
service restart、OrbStack VM 或公司内网部署。

## Live Gitea / VM / 公司内网

- PR #36：已创建，`change/35 -> main`；初始 head
  `c8dbe794a93fb95970dceb4a931b920c9795785b` 为 `mergeable=true`、`merged=false`。本次 metadata
  回填会产生新 head，required CI 必须只认最终 SHA。
- 2026-08-08 PR read-back（本 evidence commit 之前）：head
  `f17dba38a0bd1e2afda194a6c2cabbc95d8d1127`，`open`、`mergeable=true`、`merged=false`；commit
  statuses `[]`，`change/35` Actions runs `0`。当前 `main` protection 的
  `enable_status_check=false`，因此 remote CI 为 `NOT CONFIGURED / NOT RUN`，不能把本地 214 tests
  写成 remote CI PASS。
- 同次 VM-local admin read-back：`main` direct push=false、force push=false、
  merge whitelist=true 且 usernames 仅 `admin`；`block_admin_merge_override=false` 是 manifest 在
  人工合并后逐仓库收敛的已知 drift，当前未修改。
- Gitea service accounts/PAT：`NOT RUN`（最终 PR 未人工合并）。
- `DISABLE_REGISTRATION` / default private / Gitea restart：`NOT RUN`。
- 仓库 visibility/collaborator/protection/default branch cleanup：`NOT RUN`。
- project profiles 与 shared `ci-bot` retirement：`NOT RUN`。
- OrbStack VM/应用部署/数据库：`NOT RUN`，且不在本 PR 实施范围。
- 公司内网 Gitea/服务器：`NOT RUN`，未连接。
- PR merge：`NOT RUN`，必须人工执行。

## 回滚证据

工具的 repository rollback/no-op、service config backup/restore 和 invalid-candidate fail-closed 已在
mock/synthetic 环境 `PASS`。真实 pre-snapshot、逐仓库 rollback/no-op 和 service config
backup/restore 只能在最终 PR 人工合并后执行；当前保持 `NOT RUN`。
