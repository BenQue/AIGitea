---
issue: 65
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/65
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - migration
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 22
  - 27
  - 58
status: approved
branch: change/65
pr_url:
created: 2026-08-08
updated: 2026-08-09
---

# Compose 5.1.4 docker-release/v2 lifecycle verification

## Baseline

| Check | Status | Evidence |
|---|---|---|
| Fresh Gitea main | PASS | `origin/main@97445947fff79a4c2db6fa764feb21660e281556`; current task worktree started byte-equal and clean |
| Issue #65 | PASS | open, `content_version=1`, 0 comments, 0 labels; complete complex/platform acceptance contract |
| Duplicate branch/PR | PASS | baseline had no `origin/change/65`; repository `open_pr_counter=0` |
| Protected main | PASS / PARTIAL AUTH | live public branch API: `protected=true`, status checks disabled and contexts `[]`; authenticated protection detail unavailable without live broker |
| Required remote CI | NOT CONFIGURED / NOT RUN | main combined status `pending` with `total_count=0`, `statuses=[]`; repository contains no `.gitea/workflows/*` |
| Canonical checkout preservation | PASS | canonical `main@d20811b...` and user `.DS_Store` remained untouched; task uses Codex worktree |
| Compatibility matrix | PASS | revision `2026.08.2`; Compose `>=2.27,<3` containerd supported, classic rejected; SHA-256 `52bf05c6a72187c99c1fba009d63d00e3d81368cc0b61066e9f6ac33b8eb19ff` |
| Source bytes | PASS | source `97445947...`; root tree `cecc2c66...`; `docker-release/` tree `cf6bf356...`; release runtime tree `b5a9c0d5...` |
| Existing real harness | GAP CONFIRMED | Issue #27 harness uses `docker-release/v1` and Compose v2, no PostgreSQL fixture; cannot satisfy #65 |
| Baseline focused release | PASS | 77 tests on clean main |
| Baseline full smoke | PASS | 275 tests + static checks on clean main; real harness default `NOT RUN` path only |
| Mapped contract | PASS | semantic resolver returned the exact four Compose lifecycle basenames; contract/document regressions 21 tests PASS |
| Live label projection | BLOCKED_EXTERNAL | exact `aisoft-platform-agent` Keychain item is missing; legacy `ci-bot` was rejected as the wrong identity. User delegation explicitly approves the interactive contract, but live labels/comments remain unchanged |

## T01 Local harness and deterministic checks

| Check | Status | Evidence |
|---|---|---|
| Contract resolver/front matter | PASS | semantic resolver返回#65四个exact basename；contract/document regressions 21 tests PASS |
| Harness default zero-call | PASS | 无参数仅输出Issue #65 `NOT RUN`；fake Docker日志不存在 |
| Fake authorization/endpoint/identity negatives | PASS | 表驱动实际执行exact marker/host/ID/SHA/digest/port/evidence-path拒绝并逐例证明Docker call 0；same daemon、plan SHA drift与Compose 5.1.5也fail closed |
| Driver/wrapper/fixture checks | PASS | Python `-I -S`隔离、wrapper argv byte/order保真、wrong Compose injection、DockerAdapter seam、`pid == pgid` handshake、`bash -n`/`sh -n`均PASS |
| Approval, timeout and evidence contract | PASS (STATIC/FAKE) | canonical plan绑定candidate matrix/architecture/Docker+timeout binary/baseline/exact backend network；direct/lifecycle timeout、process-group终止、no-clobber evidence与retained-lock failure路径通过ShellCheck/fake/static门；真实行为仍属T02 `NOT RUN` |
| Phase isolation and cleanup contract | PASS (STATIC) | harness固定public phase顺序、phase-scoped argv、started/completed/no-op状态捕获、negative boundary、before/created/after含RepoDigest inventory与exact cleanup validator；真实行为仍属T02 `NOT RUN` |
| Focused release / installer | PASS | `bash codex/tests/test-docker-release-install.sh`与Issue #65 fake harness通过 |
| ShellCheck / full smoke | PASS | 新增四个shell source ShellCheck 0 findings；`bash codex/tests/smoke.sh`通过，real harness只走默认`NOT RUN` |

## T02 Separately authorized real E2E

| Area | Status | Reason / evidence |
|---|---|---|
| Task-owned producer/consumer VM or daemon | BLOCKED / NOT RUN | exact environment mutation尚未列出并取得用户单独批准 |
| Engine 29.7.1 / Compose 5.1.4 / containerd 2.2.6 preflight | BLOCKED / NOT RUN | 无获准endpoint |
| Registry + offline V2 lifecycle | BLOCKED / NOT RUN | 无获准real Docker mutation |
| Disposable PostgreSQL migration receipt | BLOCKED / NOT RUN | 无获准fixture mutation |
| Negative real fail-closed | BLOCKED / NOT RUN | 无获准endpoint |
| Success/failure exact cleanup | BLOCKED / NOT RUN | 无获准created resources |
| Immutable PASS evidence | NOT RUN | 只有上述全部PASS后才能生成 |

## T03 Compatibility promotion and final delivery

| Check | Status | Evidence |
|---|---|---|
| Production matrix exact Compose 5.1.4 row | NOT RUN | T02 PASS前matrix必须保持zero diff |
| Exact range positive/negative tests | NOT RUN | pending T03 |
| Final required local gates | NOT RUN | pending final head |
| Single Closes #65 PR | NOT RUN | pending Controller handoff |
| Human merge | NOT RUN | forbidden for Agent/Controller |
| Business deployment | NOT RUN / OUT OF SCOPE | NewEmaint/DockerLab/AppServer/production explicitly excluded |

## Acceptance criteria result

| AC | Status | Notes |
|---|---|---|
| AC-1 | PARTIAL | fresh source/trees/matrix/harness/fixture identity contract已固定；real version readback pending T02 |
| AC-2 | BLOCKED / NOT RUN | no approved disposable endpoints |
| AC-3 | BLOCKED / NOT RUN | real lifecycle pending |
| AC-4 | BLOCKED / NOT RUN | real Registry/offline path pending |
| AC-5 | BLOCKED / NOT RUN | disposable PostgreSQL fixture pending separate approval |
| AC-6 | PARTIAL | phase argv/static boundary PASS；real phase logs pending T02 |
| AC-7 | PARTIAL | fake duplicate daemon/wrong Compose与static negative paths PASS；real negatives pending T02 |
| AC-8 | PARTIAL | exact cleanup/evidence validator已实现并通过静态门；真实before/after inventory pending T02 |
| AC-9 | NOT RUN | forbidden before complete real evidence |
| AC-10 | PARTIAL | clean-main baseline gates PASS; implementation/final-head gates and PR pending |

## Rollback and remaining gates

- 当前没有Docker、PostgreSQL、matrix、Gitea权限、PR、merge或deployment mutation需要回滚；T01只新增本地
  harness/fixture/docs并修改full smoke入口。
- 实现代码/文档只通过人工revert最终PR回滚。
- T02 environment mutation与删除/cleanup必须使用用户另行批准的exact清单；未获批时继续保持
  `BLOCKED / NOT RUN`，不得用fake/static结果替代。
