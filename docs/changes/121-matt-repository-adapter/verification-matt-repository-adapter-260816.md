---
issue: 121
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/121
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
  - cross-module
depends_on: []
status: verified-local
branch: change/121-matt-repository-adapter
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Verification：AISoftPlatform Matt repository adapter

## 环境与版本

- Source baseline：`origin/main` = `2a09bb6f26fccaaf41397f68e78a1bffc80f7702`。
- Worktree：`/private/tmp/issue-121-matt-repository-adapter`。
- Branch：`change/121-matt-repository-adapter`。
- Final commit / PR / CI：待验证后填写。
- Artifact / deployment：不适用；本 Change 只交付 source contract。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| Analyzer schema + slug validation | PASS | `validate-analysis` 与 `render-analysis` 生成 mapped summary；slug 为 `matt-repository-adapter` |
| TDD red | PASS | exact selector：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access.HostAccessContractTests.test_exact_projects_profiles_and_no_merge_surface codex.runtime.tests.test_host_access.VmProfilePathPrependContractTests.test_aisoft_platform_profile_is_analyzer_only codex.runtime.tests.test_host_access.MattRepositoryAdapterTests`；exit 1，3 failures + 3 errors，分别证明 `vm_profile: null`、三份 `docs/agents` 缺失与 CLAUDE block 缺失 |
| TDD green | PASS | 以同一 exact selector 重跑；exit 0，`Ran 4 tests ... OK` |
| template byte comparison | PASS | 三次 `cmp -s templates/docs/agents/<name> docs/agents/<name>` 均 exit 0 |
| complete host-access unittest | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access`：77 tests OK |
| complete runtime unittest | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'`：360 tests OK |
| `bash codex/tests/smoke.sh` | PASS | final run exit 0；`Codex platform static smoke checks passed`；包含 360 tests OK |
| `bash -n` / ShellCheck | PASS | 修改的 `smoke.sh`、`test-host-access-broker.sh` 均通过；broker shell test 单独通过 |
| baseline diff / Secret scan | PASS | `git diff --check origin/main`；13-file allowlist；controller 同规则高风险 key pattern 零命中 |
| code review | PASS | 两名只读 reviewer：无 P0/P1/P2 剩余；2 个审计性 finding 与 1 个 stale-count P3 均已修复 |
| required remote CI | NOT CONFIGURED | protected-main read-back 为 `enable_status_check=false`、contexts 空 |

## Acceptance criteria 结果

- AC-1：`PASS`，三份配置与 canonical templates byte-identical。
- AC-2：`PASS`，CLAUDE 保留 `@AGENTS.md` 且唯一 Agent skills block/三链接均由 unittest + smoke 固定。
- AC-3：`PASS`，manifest 字段与 Analyzer-only 边界精确匹配。
- AC-4：`PASS`，loader、完整 `profile-spec` 投影及五项目 approved set 由 77 项 host-access suite 覆盖。
- AC-5：`PASS`，13-file allowlist 不含 `AGENTS.md`、vendor/global installed skills、live/service/deploy 文件；Secret scan 零命中。
- AC-6：`PASS`，360 runtime tests、完整 smoke、bash/ShellCheck、baseline diff 均通过。
- AC-7：`PENDING`，等待原子提交、broker push、唯一 PR 与远端 read-back。

## Live / external checks

- Installed broker bytes refresh：`NOT RUN`（不在本 PR 授权内）。
- typed `vm.profile.plan/apply/read-back` on new source：`NOT RUN`（合并前 installed manifest 仍无此 profile）。
- Analyzer canary：`NOT RUN`（依赖上两项）。
- timer/service enable/start/restart：`NOT RUN`，并明确禁止。
- Secret/PAT/key create/read/rotation：`NOT RUN`，并明确禁止。
- 公司内网、公司 VM、Runner/Registry、test/production deployment：`NOT RUN`。
- #120 Matt flow：`BLOCKED_EXTERNAL`，等待 #121 人工合并及 profile live read-back。

## 重复部署

- 第一次：`NOT RUN`；本 Change 无部署。
- 第二次：`NOT RUN`；本 Change 无部署。

## 故意失败与回滚

- 失败场景：实现前上述 exact focused selector 返回 exit 1（3 failures + 3 errors），实现后同一 selector
  返回 exit 0（4 tests OK）；red-before-green seam 可重放，`PASS`。
- live profile rollback：`NOT RUN`；本 Change 未 apply live profile。
- 数据恢复验证：不适用，无数据库或业务数据变更。

## 遗留风险与未完成项

- source PR 合并不等于 installed profile 生效；合并后仍需独立授权的 install/plan/apply/read-back/canary。
- #121 的 type/complexity/triage live 标签 projector 因本 Change 正在引导该能力而不可达；未绕过 broker。
