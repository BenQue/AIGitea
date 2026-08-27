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
| independent review P1 reproduction | FAIL before fix / PASS after fix | 旧实现把 `404 {"message":"repository not found"}` 无条件折叠为 absent；新增 repository-missing、ACL-masked、malformed/unknown 404 negatives 均先稳定红灯，修复后全部以 `HTTP_404` fail closed |
| third review P1 reproduction | FAIL before fix / PASS after fix | `_request_json` 接受 201/202/204/206；set 静默去重 exact/case-fold/cross-page identity；whitespace/非法/超长 login、51-item page、short-page + next/malformed Link 均未在形成 absence 前拒绝。新增矩阵先稳定 14 个 failure，修复后全部 fail closed |
| fourth review P1/P2 reproduction | FAIL before fix / PASS after fix | 旧实现对 `headers.items()`/dict 折叠重复 Link、忽略 `rel=NEXT`、不验证 next canonical URL/query/关系唯一性，并在 JSON parse 前无 body bound。第四轮 7 组 focused tests 在旧 head 稳定出现 7 failures + 4 errors；修复后覆盖 duplicate field-values、case relation、wrong scheme/host/repo/limit/page/extra/duplicate query、multiple next、prev/first/last、2 MiB extra field、Content-Length drift、chunked actual oversize 与 audit 累积预算，全部在 absent 前 fail closed |
| fifth review P1/P2 reproduction | FAIL before fix / PASS after fix | 旧实现不保存跨页 Link 状态、`json.loads` 对 duplicate key last-wins、忽略 Content/Transfer-Encoding、预算在 response 后才 charge，且用 comma/semicolon split 误拒合法 quoted title。第五轮 8 组 focused tests 在旧 head 稳定出现 17 failures + 1 error；修复后覆盖 last=999→2 drift、next↔prev reciprocity、terminal/last、empty `#`、recursive duplicate key、identity/chunked framing、TE+CL、remaining cap pre-reserve、quoted comma/semicolon/escape 与 malformed/control/obs-fold/duplicate params，全部在 transport/parse/absent 前 fail closed |
| sixth review P1/P2 reproduction | FAIL before fix / PASS after fix | 旧实现接受 `NaN|±Infinity` 与 non-finite/超长 float，4301/5000-digit integer、Content-Length、page 泄漏 `ValueError`，deep JSON 泄漏 `RecursionError`，空 `;` path parameter 被接受，异常 header mapping 泄漏原异常。第六轮 5 组 focused tests 在旧 head 稳定出现 6 failures + 7 errors；修复后 `parse_constant`、signed-64 integer/finite float bound、bounded ASCII decimal、`urlsplit` exact raw path 与 header adapter 统一在 absent 前稳定返回 `RESPONSE_SCHEMA_INVALID` |
| seventh review P1/P2 reproduction | FAIL before fix / PASS after fix | 第六轮实现仍把 60,000 层、约 120 KiB 的 JSON 交给正式 decoder，且 65 层/unbalanced/control 输入没有 deterministic pre-scan；malformed IPv6 与 NFKC netloc 从 `urlsplit` 泄漏原生 `ValueError`。第七轮 3 组 focused tests 在旧 head 稳定出现 5 failures + 2 errors；修复后 raw bytes scanner 在 decoder 前执行、总深度固定 64、正确跳过 string/escape/Unicode，malformed authority 的 URL/hostname/userinfo/port 解析异常统一映射为 `RESPONSE_SCHEMA_INVALID`，所有负例 absence=0/mutation=0 |
| missing-account local/mock replay | PASS | account exact 404 建立 `account_state=missing` 后，target + 9 cross-project 均读取 strict 200 collaborator inventory；exact login 缺席才依 manifest 顺序投影 `{repository,state: absent,permission: null}`；routine/top-level 均为 `GAP`，所有 transport methods 为 GET |
| focused compatibility tests | PASS | 第七轮新增 3 tests PASS；前六轮矩阵由完整 host/security suites 一并重放 |
| complete host-access tests | PASS | `codex.runtime.tests.test_host_access`：144 tests PASS |
| security Python suites | PASS | host-access + routine-merge + Gitea governance：197 tests PASS |
| broker/bootstrap/rollback/installer shell suites | PASS | `test-host-access-broker.sh`、`test-bootstrap-gitea-service-account.sh`、`test-rollback-gitea-routine-pilot.sh`、`test-install-host-access-broker.sh` 全部 PASS |
| `bash codex/tests/smoke.sh` | PASS | 629 tests PASS；末行 `Codex platform static smoke checks passed.` |
| semantic document audit | PASS | `resolve-documents 215` 返回 exact summary/spec/plan/verification mapping；`check-change-documents` 为 `changes=97 pass=2 gap=0` |
| Controller preflight | PASS | 第一轮 installed broker readback确认 Issue open/exact labels 且 `--verify 215=projected`；第二至第七轮按 no-network 约束仅用固定 Issue evidence + 本地 `load_contract` 重算 forced complex/restore、branch、AC-1..AC-9 与四份 required docs；branch exact、`origin/main` 为 HEAD 祖先、final worktree clean |
| live account/PAT/collaborator/protection mutation | NOT RUN | 本任务禁止；NewEMaint live rollout mutation=0 |
| install/routine merge/deploy | NOT RUN | 本任务禁止 |
| push/create PR | NOT RUN | 等待最终 PR 提交确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source/mock) / GAP (installed/live readiness) | account missing + target/9 cross-project exact HTTP 200 inventories 完成 strict username/duplicate/case-fold、lossless RFC Link、exact raw path、malformed authority mapping、bounded ASCII page/limit、canonical URL-query、跨页 next/prev/last/terminal state 与 bounded pagination 验证后，routine login 缺席才生成 structured absent evidence；Mac installed broker 尚未含该 source contract |
| AC-2 | PASS | ordering 断言 account GET 在第一条 inventory GET 前；account present 继续使用 permission endpoint，cross-project 404 保持 schema invalid |
| AC-3 | PASS | present account permission schema 不变；missing inventory 要求 exact HTTP 200/list、canonical identifier、trim、unique exact/case-fold identity、strict duplicate/nonstandard/unbounded/depth-bounded JSON、每页 ≤50、bounded terminal pagination |
| AC-4 | PASS | 201/202/204/206 均 `RESPONSE_SCHEMA_INVALID`；repository/ACL/malformed/unknown 404 为 `HTTP_404`；401/403、5xx、transport 保持稳定错误；recursive duplicate-key、NaN/±Infinity、signed-64 integer/finite float、raw depth≤64、unbalanced/control pre-scan、malformed IPv6/NFKC netloc/port、bounded Content-Length/page/limit、abnormal mapping、Content/Transfer-Encoding、TE+CL、128 KiB/page、4 MiB/audit、1000 pages/audit 与 remaining-cap bounded read 均在 request/parse/absent 前 fail closed |
| AC-5 | PASS | exact read 写入 present/read inventory 且不产生 violation；write/admin/owner 既有测试继续形成 GAP/blocked |
| AC-6 | PASS | 完整 host-access/security/smoke 回归覆盖 target exact write/missing/schema、non-admin identity、scope、required context、human+routine allowlist、push/force denial |
| AC-7 | PASS | missing account absent 只来自 exact-200、无 duplicate/case ambiguity、bounded pagination 完整 inventory；present account 仍来自 strict permission evidence；ordered output 与 disabled empty list 不变 |
| AC-8 | PASS | 第七轮 focused 3、host-access 144、security 197、四个 shell suites、full smoke 629、semantic audit 全部通过 |
| AC-9 | PASS (boundary) / NOT RUN (live layers) | audit/source tests mutation=0；无 live account/PAT/collaborator/protection/install/routine merge/deploy；push/create PR 等确认 |

## 遗留风险与未完成项

- live routine layers 仍未 provision；source/mock PASS 只能证明兼容分支与失败边界，live readiness 仍是 `GAP`/`NOT RUN`，不能推定 `PASS`。
- Mac installed broker 为 13/21 drift，不能用它证明 #215 source 行为；本 Change 不 install。需要 fresh live read-only 时只能在另行授权且已验证支持 typed operation 的 installed 路径执行。
- current-source live defect replay 发生在“不再用 source runtime 发 live request”的补充约束到达前；补充约束后没有进一步 source-runtime credential/live access。
- remote PR CI 尚不存在；本记录只证明本地闸门，不能把未来 required CI 写成通过。
- 第二轮复审没有调用 installed/source broker、未发 network/live 请求；repository/ACL/malformed/unknown 404 全部只在 local mock transport 重放。
- 第三轮复审同样未调用 installed/source broker 或 network/live；所有 HTTP status、Link、pagination、identity collision evidence 均为 local mock，sandbox 未执行的 live/remote 层继续 NOT RUN。
- 第四轮复审同样未调用 installed/source broker 或 network/live；lossless headers、pagination URL/query 与 response budget evidence 全部来自 local mock/transport tests，live/remote 层继续 NOT RUN。
- 第五轮复审同样未调用 installed/source broker 或 network/live；pagination state、JSON/framing、remaining budget 与 RFC Link evidence 全部来自 local mock/default-transport tests，live/remote 层继续 NOT RUN。
- 第六轮复审同样未调用 installed/source broker 或 network/live；strict JSON numeric/depth、bounded decimal、exact raw path 与 abnormal mapping evidence 全部来自 local mock/default-transport tests，live/remote 层继续 NOT RUN。
- 第七轮复审同样未调用 installed/source broker 或 network/live；deterministic JSON depth scan 与 malformed Link authority evidence 全部来自 local mock/parser tests，live/remote 层继续 NOT RUN。
