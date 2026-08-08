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

# Implementation plan

## 任务分解

1. 保存 2026-08-08 只读 baseline：Gitea 1.26.4、9 个 exact repositories、visibility、
   `main` protection/merge allowlist、当前 Write credential 的 Admin API `403`、service config 与
   sandbox/host OrbStack 探针。所有输出脱敏。
2. 新增 strict `gitea-governance/v1` manifest 和 semantic validator，固定 public allowlist、
   private internal apps、manager/human/shared bot、唯一 project agents、PAT scopes、server policy、
   `main`/branch cleanup 规则和公司内网继承策略。
3. 实现单账号 bootstrap：只接受 manifest identity 与预先创建的安全 output path；调用当前
   Gitea admin CLI 创建 bot user/最小 PAT，credential file 缺失或身份漂移时 fail closed；以 mocks
   验证 Secret 不进入 argv/stdout。
4. 实现 governance `validate/check/apply/rollback`：默认只读；一次 apply/rollback 只允许一个
   exact repo；保存 normalized pre/post snapshots；校准 manager/project-agent/visibility/branch cleanup/
   protection 并逐项读回；shared bot retirement 为独立后置 flag。
5. 实现 Gitea service policy `--check/--apply/--rollback`：只处理
   `DISABLE_REGISTRATION`、`DEFAULT_PRIVATE`、`FORCE_PRIVATE`，保存原始 config、保持 owner/mode，
   `gitea doctor check --all` 或等价配置检查通过后才 restart，并验证 HTTP/API。
6. 更新基础设施、运维、onboarding、内网迁移和 skill references；说明 OrbStack host control、
   Gitea identity 与 project deploy OS identity 互不替代，旧 `ci-bot` 仅作为迁移兼容。
7. 运行 focused tests、full smoke、bash syntax、ShellCheck（若可用）、JSON/secret/diff checks；写
   `03-verification.md`，将未执行的 live Gitea/service/VM/company 动作标为 `NOT RUN`。
8. push `change/35` 并创建单一最终 PR `Closes #35`。人工 merge 前停止所有 live apply。
9. 人工合并后读回 exact protected-main SHA，再按顺序执行：server policy → manager bootstrap 与
   每仓库 Admin → project agent 逐仓库 bootstrap/profile/Write → visibility → protection/branch cleanup
   → project real smoke → shared bot 逐仓库退出。每一步 read-back 后才进入下一仓库。
10. 在本地全部验收后，公司内网另开 migration Change：先做目标 inventory/mapping 和账号重建，
    再复用同一逻辑 policy；不复制本地 token/Secret，不连接 GitHub。

## 涉及文件

- `docs/changes/35/{00-summary,01-spec,02-plan,03-verification}.md`
- `codex/config/gitea-governance.json`
- `codex/runtime/aisoft_gitea_governance/**`
- `codex/tools/{gitea-governance,bootstrap-gitea-service-account,sync-gitea-service-policy}.sh`
- `codex/runtime/tests/test_gitea_governance.py`
- `codex/tests/test-{bootstrap-gitea-service-account,sync-gitea-service-policy}.sh`
- `codex/tests/smoke.sh`
- `README.md`
- `01-基础设施-VM-Gitea-Runner.md`
- `06-运维手册与踩坑集.md`
- `07-内网与生产平移路线.md`
- `skill-for-codex/references/{private-gitea-access,onboarding-runbook}.md`
- 必要的 `codex/skills/gitea-platform-ops/SKILL.md` 同步说明。

## 数据库迁移

无。账号和 PAT 通过 Gitea 支持的 CLI/API 管理，不直接读写 Gitea PostgreSQL。业务数据库、
Runner DB 和应用数据不在范围内。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2, AC-3, AC-9, AC-10 | `gitea-governance validate`；manifest JSON/semantic tests；文档 review |
| AC-4 | `bash codex/tests/test-bootstrap-gitea-service-account.sh`；argv/stdout/credential mode negative tests |
| AC-5, AC-6, AC-7 | governance mock API unittest；live post-merge `check/apply/check` 与 pre/post snapshot review |
| AC-8 | `bash codex/tests/test-sync-gitea-service-policy.sh`；post-merge config backup/restart/HTTP/API read-back |
| AC-11 | focused unittest/shell tests；`bash codex/tests/smoke.sh`；`bash -n`；ShellCheck；`jq empty`；`git diff --check` |
| AC-12 | Gitea PR/CI review；人工 merge；merge SHA 与 `03-verification.md` live evidence review |

## 部署与回滚

本 PR 本身不部署。合并后本地 Gitea policy reconciliation 属于受控平台部署，必须写入
`03-verification.md`：每个仓库至少执行 pre-check、apply、post-check 和第二次 no-op；service
policy 需要两次幂等执行并故意注入一次 invalid temp config，证明 restart 前 fail closed。

回滚按单仓库 pre-snapshot 恢复 visibility/collaborators/protection；service policy 恢复原始
`app.ini` bytes、owner、mode 并重启验证。任何 project agent/profile 失败时保留或回加该仓库
`ci-bot` Write，不能影响其它仓库。公司内网实施有自己的 backup/restore 和变更窗口，不由
本地验证自动授权。
