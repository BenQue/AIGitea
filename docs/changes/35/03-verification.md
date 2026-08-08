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

- 2026-08-08 人工合并读回：PR #36 `merged=true`，head
  `7a4bbb24b8915b91bab76ad525b9185acc096f40`，exact protected-main merge commit
  `69251fd4d07665385eb6d9142038848c2b9392d7`；Issue #35 已关闭。
- 本轮 OrbStack 双路径探针再次确认 sandbox 为 `SANDBOX_PATH_BLOCKED`，host path 上 OrbStack、
  `gitea-ci`、DNS、HTTP 200 和 `orb exec` 均通过。merged source 从 live bare repo 克隆到一次性
  `/tmp/aisoft-issue35-69251fd4`，HEAD/manifest 校验通过。
- service-policy live pre-check 为 `DRIFT`：registration=false、default-private=last；Gitea
  service active、health pass。首次 apply 在安装 candidate/restart 前 fail closed：merged script
  错误地以 root 运行 Gitea doctor，Gitea 1.26.4 拒绝；同 candidate 以 systemd user `git` 运行
  doctor exit 0。live `app.ini` 保持原值，备份目录
  `/var/lib/aisoft/backups/gitea-policy/20260808-issue-35-69251fd4` 只有 mode 600 `app.ini.pre`。
- follow-up Issue #38 负责修复 doctor effective user；其 PR 人工合并前，Issue #35 的 live
  service/account/ACL rollout 暂停，不能标为 deployed。
- PR #39 合并后的 exact main `0396779c3566ba0dbd84da745e6c482fd65a2082` 已通过新一轮
  `verify-merged`；`git`-user doctor 真实通过。随后 restart 的单次即时 healthz 请求在 Gitea ready
  前 connection refused，脚本按设计恢复 pre config。稍后读回为 service active/health pass，且
  live/pre SHA-256 完全相同；service policy 仍为 `DRIFT`，因此 apply 未成功。
- follow-up Issue #41 负责 bounded readiness retry；其 PR 人工合并前继续暂停账号/ACL rollout。
- PR #42 合并后的 exact main `ec5fce7f4e944c961b58b6373fb9023755ab964f` 已真实应用 service
  policy：首次 connection refused 被 bounded retry 吸收，最终 health pass；live config 与
  `app.ini.post` SHA-256 均为 `c8f212b8060f197fc1a84bda77f78c987d750161d55e9f63cb19df677296abd1`，
  两次连续 post-check 均为 `PASS`。
- account bootstrap 前的 installed Gitea 1.26.4 预检发现 bot 不接受显式 must-change-password flag；
  未创建任何账号/PAT。follow-up Issue #43 修复该 CLI 兼容性，合并前继续暂停账号/ACL rollout。
- PR #44 已人工合并到 `main@3b01e29dad23e6d78d83c48014d69ea78a37a83e`；merged source 的
  manifest 与 service policy check 均为 `PASS`。随后第一个 account bootstrap 仍在 mutation 前
  fail closed：调用者 `benque` 无法遍历 root:git 的 `/etc/gitea/app.ini`，旧脚本因此把受保护 config
  误判为不存在；credential root、账号和 PAT 均未创建。实际 Gitea CLI 本就以 `sudo -n -u git`
  执行，follow-up Issue #45 只把 config `test -f/-r` 改为同一 OS user，不扩大 caller 权限。
- PR #48 已人工合并到 `main@d3759c39d66bb60de1d783eac5181a4ee086036f`；exact-main、manifest、
  `verify-merged`、两次 service-policy check、Gitea active/health 均 `PASS`。10 个 declared account
  仍全部为 404，legacy credential 为 mode 600 且 admin token marker 唯一。第一个 manager bootstrap
  随后被 Gitea 1.26.4 拒绝：bot user 不接受 `--random-password`。失败后 manager 仍为 404，managed
  credential root 为 mode 700 且 0 个文件，PAT/ACL/repository mutation 均未发生；Issue #49 独立修复。
- PR #50 已人工合并：head `6d6c173000300750a52bacb7ed016344f47a0d9e`，protected-main merge
  commit `04ab0cce79166ff202318ed48d9b6851b132c511`。新的 exact-main/manifest/merge gate、两次
  service-policy check 与 Gitea health 均 `PASS`。首个 manager bot 与 audit PAT/markers 创建后，PAT
  identity 被 HTTP 403 `You must change your password` 阻止；其余 9 个 agents 尚未开始。用 live CLI
  专用 `must-change-password --unset aisoft-platform-manager` 精确恢复后，manager 读回
  `active=true`、`is_admin=false`，audit PAT identity `PASS`，且没有设置密码。Issue #51 将该恢复纳入
  fail-closed、带 mode 600 marker 的幂等 bootstrap；合并前继续暂停其余账号和仓库 mutation。
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
- Gitea service accounts/PAT：`PARTIAL / BLOCKED`（manager + audit PAT 已恢复并验证；manager mutation
  PAT 与 9 个 project-agent 账号/PAT 等待 Issue #51）。
- `DISABLE_REGISTRATION` / default private / Gitea restart：`PASS`；两次连续 post-check 通过。
- 仓库 visibility/collaborator/protection/default branch cleanup：`NOT RUN`。
- project profiles 与 shared `ci-bot` retirement：`NOT RUN`。
- OrbStack VM/应用部署/数据库：`NOT RUN`，且不在本 PR 实施范围。
- 公司内网 Gitea/服务器：`NOT RUN`，未连接。
- PR #36 merge：`PASS`，由人执行；后续 follow-up PR 继续保持人工 merge gate。

## 回滚证据

工具的 repository rollback/no-op、service config backup/restore 和 invalid-candidate fail-closed 已在
mock/synthetic 环境 `PASS`。真实 service pre/post 已保存于 root-only evidence；manager 账号/audit PAT
已按 marker 管理且验证通过，不回退为必须改密，也不删除。仓库 ACL mutation 尚未开始，因此 ACL
rollback 为 `NOT RUN / NOT NEEDED`。逐仓库 snapshot、apply/no-op 与 rollback 只能在 Issue #51 人工
合并并通过新的 exact-main 预检后执行。
