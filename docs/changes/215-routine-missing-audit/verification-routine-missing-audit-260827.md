---
issue: 215
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/215
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
  - 213
status: verified
branch: change/215-routine-missing-audit
created: 2026-08-27
updated: 2026-08-27
---

# routine missing audit 验证记录

## 基线与范围

- Commit SHA: `05c0fa74889a981bc78cbed802ceb76e6d13d093`（#213/PR #214 merge，fresh `origin/main`）
- 环境: macOS Codex exact linked worktree `issue-215-routine-missing-audit`
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-9
- Merge policy: manual

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| canonical broker `git.fetch.main` + exact SHA/ancestry | PASS | `origin/main=05c0fa74889a981bc78cbed802ceb76e6d13d093` |
| Issue #215 create/classification/lifecycle | PASS | installed canonical broker 创建 Issue；semantic docs 完整后投影并重新读回 `approved + type/platform + complexity/complex`；Issue/label 治理写入不属于 NewEMaint live rollout mutation |
| Mac installed broker compatibility | GAP | installed root broker 仍是已知 13/21 drift；其 read-only audit 返回旧 shape、缺少 routine section 且 top-level `PASS`，不能作为 #213 source 或 live readiness PASS |
| pre-change `host.access.audit` defect replay | PASS (defect reproduced) | 协调约束补充到达前，current-source read-only audit 返回 `RESPONSE_SCHEMA_INVALID: cross-project routine permission response is invalid`；调用仅 GET、target live mutation=0。约束到达后未再用 source runtime 读取 credential 或发 live request |
| missing-account local/mock replay | PASS | account exact 404 建立 `account_state=missing` 后，9 个 cross-project exact 404 依 manifest 顺序投影为 `{repository,state: absent,permission: null}`；routine/top-level 均为 `GAP`，transport methods 全为 GET |
| focused compatibility tests | PASS | 新增/关联 5 tests PASS；正向覆盖 missing+404、missing+exact read、present baseline，负向覆盖 strict 200/auth/server/transport |
| complete host-access tests | PASS | `codex.runtime.tests.test_host_access`：114 tests PASS |
| security Python suites | PASS | host-access + routine-merge + Gitea governance：167 tests PASS |
| broker/bootstrap/rollback/installer shell suites | PASS | `test-host-access-broker.sh`、`test-bootstrap-gitea-service-account.sh`、`test-rollback-gitea-routine-pilot.sh`、`test-install-host-access-broker.sh` 全部 PASS |
| `bash codex/tests/smoke.sh` | PASS | 599 tests PASS；末行 `Codex platform static smoke checks passed.` |
| semantic document audit | PASS | `resolve-documents 215` 返回 exact summary/spec/plan/verification mapping；`check-change-documents` 为 `changes=97 pass=2 gap=0` |
| Controller preflight | PASS | installed broker readback确认 Issue open 与 exact labels；本地 `load_contract` 重算 forced complex/restore、branch、AC-1..AC-9 与四份 required docs；`--verify 215` 返回 `projected`；branch exact、`origin/main` 为 HEAD 祖先、worktree 在验证前 clean |
| live account/PAT/collaborator/protection mutation | NOT RUN | 本任务禁止；NewEMaint live rollout mutation=0 |
| install/routine merge/deploy | NOT RUN | 本任务禁止 |
| push/create PR | NOT RUN | 等待最终 PR 提交确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source/mock) / GAP (installed/live readiness) | account missing + exact cross-project 404 生成 structured absent inventory，routine/top-level `GAP`；Mac installed broker 尚未含该 source contract |
| AC-2 | PASS | ordering 断言 account GET 在第一条 cross-project GET 前；present account + cross-project 404 继续 schema invalid |
| AC-3 | PASS | missing account 下的 non-object、missing/extra field、non-string、unknown permission 继续 `RESPONSE_SCHEMA_INVALID`；present account 既有 matrix 同样通过 |
| AC-4 | PASS | 401/403 保留 `HTTP_401`/`HTTP_403`，5xx 为 `HTTP_ERROR`，transport 为 `TRANSPORT_ERROR`，均未降级 absent |
| AC-5 | PASS | exact read 写入 present/read inventory 且不产生 violation；write/admin/owner 既有测试继续形成 GAP/blocked |
| AC-6 | PASS | 完整 host-access/security/smoke 回归覆盖 target exact write/missing/schema、non-admin identity、scope、required context、human+routine allowlist、push/force denial |
| AC-7 | PASS | enabled audit 输出完整 ordered `cross_project_permissions`；disabled 默认空 list；violation 与 inventory 使用同一 permission evidence |
| AC-8 | PASS | focused 5、host-access 114、security 167、四个 shell suites、full smoke 599、semantic audit 全部通过 |
| AC-9 | PASS (boundary) / NOT RUN (live layers) | audit/source tests mutation=0；无 live account/PAT/collaborator/protection/install/routine merge/deploy；push/create PR 等确认 |

## 遗留风险与未完成项

- live routine layers 仍未 provision；source/mock PASS 只能证明兼容分支与失败边界，live readiness 仍是 `GAP`/`NOT RUN`，不能推定 `PASS`。
- Mac installed broker 为 13/21 drift，不能用它证明 #215 source 行为；本 Change 不 install。需要 fresh live read-only 时只能在另行授权且已验证支持 typed operation 的 installed 路径执行。
- current-source live defect replay 发生在“不再用 source runtime 发 live request”的补充约束到达前；补充约束后没有进一步 source-runtime credential/live access。
- remote PR CI 尚不存在；本记录只证明本地闸门，不能把未来 required CI 写成通过。
