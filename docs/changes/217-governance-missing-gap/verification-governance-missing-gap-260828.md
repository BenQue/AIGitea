---
issue: 217
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/217
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 215
status: verified
branch: change/217-governance-missing-gap
created: 2026-08-28
updated: 2026-08-28
---

# governance missing collaborator GAP 验证记录

## 基线与范围

- Baseline SHA: `78a36de53a063e338cf257dada29ec432637cfee`（#215/PR #216 merge）
- Tested source head: `3d5ae37`（首轮独立复审 P2 有界修复；后续 docs-only commit 不改变 source bytes）
- 基线：fresh canonical broker fetch 后 `origin/main=78a36de53a063e338cf257dada29ec432637cfee`
- 环境: macOS Codex managed linked worktree；source/local fake transport；live evidence 只引用委派源任务已完成的 read-only preflight
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8
- Merge policy: manual

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 完整合同读取 | PASS | `aisoft-platform`、`issue-session-flow`、private-access、AGENTS/README/03/04/06/08/09、#213/#215 docs、governance runtime/manifests/tests 已读 |
| canonical broker `git.fetch.main` | PASS | sandbox 首次 `TRANSPORT_ERROR`；同一 typed operation 在 host context 重试 PASS；HEAD/main/origin/main exact `78a36de...` |
| post-#215 installed live preflight | PASS (defect observed) | source task mutation=0；host.access.audit 返回 expected structured GAP；installed governance check 仍报 `collaborator permission response is invalid`，无可信 plan |
| local exact-404 defect replay | PASS (defect reproduced) | account removed；collaborator inventory保留 exact identity；permission GET=HTTP 404；pre-change `_check` 在 account GET 前抛 `ApiError`，mutating calls=0 |
| lifecycle readback | PASS | 用户确认合同后，canonical broker 精确投影并读回 `approved + type/platform + complexity/complex`；该 Issue governance 写入不属于 NewEMaint live mutation |
| pre-fix focused TDD | FAIL before fix / PASS after fix | 4 个 focused cases 中 exact missing+404 正向 case 在旧实现稳定抛 `ApiError`；其余 strict negatives 保持通过；修复后 4/4 PASS |
| 首轮独立复审 P2 | FAIL before fix / PASS after fix | 旧实现把 missing project agent 加入全局 evidence，并把同一 evidence 传入 cross-project audit；5 个 focused cases 中 project-agent stale inventory+404 与 cross-project same routine identity 404 两项稳定错误通过。收窄后 configured routine target 正向继续 PASS，project/shared/unknown/cross-project 404 全部 fail closed，5/5 PASS、methods全为GET |
| governance targeted | PASS | `test_gitea_governance` 47 tests PASS；含 target configured routine missing 404、project/shared/unknown/cross-project 404 negatives、account-before-permission、strict 200 schema、401/403/500/transport、present 404 与 apply zero-mutation negatives |
| security Python suites | PASS | governance + host-access + routine-merge：205 tests PASS |
| broker/bootstrap/rollback/installer shell suites | PASS | `test-host-access-broker.sh`、`test-bootstrap-gitea-service-account.sh`、`test-rollback-gitea-routine-pilot.sh`、`test-install-host-access-broker.sh` 全部 PASS |
| `bash codex/tests/smoke.sh` | PASS | 637 tests PASS；末行 `Codex platform static smoke checks passed.` |
| semantic document audit | PASS | `resolve-documents 217` 返回 exact 四角色 mapping；`check-change-documents` 为 `changes=98 pass=2 gap=0`；`git diff --check` PASS |
| Controller preflight | PASS | installed broker readback确认 Issue open/exact labels；classification `--verify 217` 返回 `projected`；本地 `load_contract` 重算 platform/complex/restore、branch、AC-1..AC-8、depends_on #215 与四份 required docs；canonical manual PR title/body 成功渲染；`origin/main` 为 HEAD 祖先 |
| live account/PAT/credential/collaborator/protection | NOT RUN | 本任务禁止；mutation=0 |
| install/#74/routine merge/manual merge/deploy | NOT RUN | 本任务禁止 |
| push/create PR | NOT RUN | 等待最终 PR 提交确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source/mock) / GAP (installed) | 同次 `_check` 只把每个 repository exact missing 的 configured routine merger 形成 target-scoped evidence；其 target permission 404 投影 `missing`，NewEMaint 精确生成 `set-routine-merger-write`；installed bytes 未更新 |
| AC-2 | PASS | project/routine account 三态既有矩阵不变；account GET 早于 target permission；project missing stale inventory 404、routine present-non-admin/site-admin 404 均抛 `ApiError` |
| AC-3 | PASS | account missing 时，HTTP 200 的 null/root/missing/extra/non-string/unknown permission 全部继续 `ContractError` |
| AC-4 | PASS | configured routine missing 对应 target permission 401/403/500/transport(0) 全部保持原 `ApiError`；project/shared/unknown/cross-project same-name 404 均 fail closed；apply 默认 evidence 为空，404 继续 fail closed |
| AC-5 | PASS | full governance/security/smoke 重放覆盖 exact Write、manager/project/routine身份、required contexts、human+routine merge allowlist、direct/force denial、cross-project read安全与 write/admin/owner blocker |
| AC-6 | PASS | 新正向/负向 check call inventory 全为 GET；apply 404 在 evidence 文件与任何 PUT/PATCH/POST/DELETE 前失败；live mode、pre-snapshot 与 mutation caller code path未放宽 |
| AC-7 | PASS | CLI JSON keys/planned action names不变；仅内部 target-scoped keyword-only `missing_routine_merge_agent`，默认 fail-closed，cross-project audit无兼容参数；无 manifest、broker、credential 或 host.access.audit 改动 |
| AC-8 | PASS (source/local) / NOT RUN (remote/live) | governance 47、security 205、四个 shell suites、full smoke 637、semantic/Controller preflight 全部 PASS；push/PR/CI/install/live/merge/deploy 均未运行 |

## 遗留风险与未完成项

- installed/live governance 仍是 blocker；source 修复未 push、合并或安装，不能把 source/local PASS 推定为 installed/live PASS。
- remote PR/required CI 尚不存在；本记录只证明本地闸门，不能把未来 CI 写成通过。
- 第二轮独立复审尚未执行；本轮只证明 P2 本地修复与全闸门重放，等待协调者安排复审。
- Codex 宿主 worktree 外层 basename 为 `ca13/AISoftPlatform`，不是 contract 推荐的
  `issue-217-governance-missing-gap`；branch/docs/front matter exact，本次 Controller preflight 如实保留该宿主例外。
