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

# Implementation plan

## 任务分解

1. 保存实时 baseline：Issue/评论/labels、protected `origin/main`、远端 branch/PR 去重、canonical dirty
   状态、Issue #35/#51/#55 合同及现有 agent/profile/host-role/credential helper。只读 Gitea 使用已验证
   host path，不运行 `orbstack-access-diagnostics`。
2. 新增 strict host-access manifest/contract，并与 governance manifest 交叉校验 exact projects、
   identities、Mac checkout、Keychain bindings、OrbStack machine 和四个 VM profiles。
3. 实现 broker/API/Git/credential helper：allowlisted typed operations、HTTP fail-closed/redaction、
   project/manager identity route、repo-local Git binding、change-only push 和无 merge/任意 shell surface。
4. 实现 profile migration transaction：fixed source/target、identity preflight、metadata backup、atomic
   token/profile replace、automatic restore、read-back、latest rollback 和 second-run no-op。
5. 修改 VM profile consumption 与 poll error propagation；installer 复制 runtime/manifest/helper 但不创建
   Secret/profile、不开 timer、不做 live mutation。
6. 增加 Python/shell focused tests并纳入 smoke；覆盖 AC-1–AC-11 的正反向、rollback 与 redaction。
7. 更新 README、运维/private-access/onboarding/platform-ops 说明，把 broker 设为正常路径并把
   `orbstack-access-diagnostics` 标为 emergency-only；明确 onboarding v2 不在本 Issue。
8. 运行 focused tests、full smoke、`bash -n`、ShellCheck、JSON/Secret/diff checks；在
   `03-verification.md` 区分 candidate PASS 与所有 live `NOT RUN`。
9. 提交并以 aisoft-platform-agent 推送唯一 `change/61`，创建包含 `Closes #61` 与本目录链接的 PR；
   更新 Issue 为 `pr-open`，读回 final head、mergeable/merged、statuses 和 Actions runs后停止。
10. 人工合并后另由获准运行从 exact protected-main SHA 执行：broker install/read-back/no-op →
    AISoftPlatform Mac credential canary → 四 profile 逐项 plan/apply/read-back/no-op → `emaintenance`/`sfm`
    及其余 profile private poll → cross-project denial。任何失败只 rollback 当前 project。

## 涉及文件

- `docs/changes/61/{00-summary,01-spec,02-plan,03-verification}.md`
- `codex/config/host-access-broker.json`
- `codex/runtime/aisoft_host_access/**`
- `codex/runtime/tests/test_host_access.py`
- `codex/tools/{host-access-broker,project-profile-migration,git-credential-aisoft-host}.sh`
- `codex/install-host-access-broker.sh`
- `codex/tests/test-host-access-broker.sh`
- `codex/agent/{common,project-poll,provider-poll}.sh`
- `codex/install-vm.sh`
- `codex/tests/{test-agent-runtime,smoke}.sh`
- `templates/agent/project.env.example`
- `README.md`、`06-运维手册与踩坑集.md`
- `skill-for-codex/references/{private-gitea-access,onboarding-runbook}.md`
- `codex/skills/gitea-platform-ops/SKILL.md`

不修改本次运行正在遵循的 root `AGENTS.md`，不修改业务项目仓库。

## 数据库迁移

无。profile/token 迁移只操作受控 mode 600 文件；不直接访问 Gitea PostgreSQL 或业务数据库。

## 测试与验收映射

| Acceptance criterion | Verification |
|---|---|
| AC-1, AC-2, AC-3 | strict manifest unittest；identity/target/cross-project/operation negative matrix |
| AC-4, AC-5 | credential reader/helper + temp Git repo binding tests；argv/output/config Secret scan |
| AC-6, AC-9 | project/provider poll mock 401/403/404/schema/identity mismatch，断言非零 `BLOCKED_EXTERNAL` |
| AC-7, AC-8 | temp HOME/source credential transaction、symlink/mode、injected failure auto-restore、rollback/no-op |
| AC-10 | temporary install root 两次 file manifest byte-identical；无 profile/credential/service/timer |
| AC-11, AC-12 | focused unittest/shell；full smoke；bash/ShellCheck/JSON/Secret/diff checks |

## 部署与回滚

本 PR 不部署。candidate 回滚为 revert。post-merge broker 安装保留 `previous` runtime/manifest/helper，
health 失败回切；Mac repo binding 回滚恢复 pre-config snapshot；profile rollback 只使用该 project 固定
latest backup，恢复 profile/token bytes/uid/gid/mode并再次验证。timer/service/VM restart 不是本 PR 执行项。
