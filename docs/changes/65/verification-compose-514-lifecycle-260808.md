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
| Approval, timeout and evidence contract | PASS | canonical plan绑定candidate matrix/architecture/Docker+timeout binary/baseline/exact backend network；真实run与failure paths均验证process-group、no-clobber evidence、execution lock与exact cleanup |
| Phase isolation and cleanup contract | PASS | immutable evidence固定public happy lifecycle先于real negative gates、phase-scoped argv/mutation counts、state receipts、before/created/after含RepoDigest inventory与exact cleanup validator |
| Focused release / installer | PASS | `bash codex/tests/test-docker-release-install.sh`与Issue #65 fake harness通过 |
| ShellCheck / full smoke | PASS | 收敛后`bash -n`、四个shell source ShellCheck、fake harness与`git diff --check`均PASS；focused transport 19 tests、`bash codex/tests/smoke.sh` 277 tests/static smoke PASS；real harness只走默认`NOT RUN` |

## T02 Separately authorized real E2E

| Area | Status | Reason / evidence |
|---|---|---|
| Task-owned producer/consumer VM or daemon | PASS | 用户分阶段批准的`aisoft-65-producer`与重建后的`aisoft-65-consumer`均为Issue-owned disposable OrbStack VM；未重启/切换其它VM或daemon |
| Engine 29.7.1 / Compose 5.1.4 / containerd 2.2.6 preflight | PASS | 两端均为linux/amd64 containerd store；daemon ID与DockerRootDir分别为`494f46cb…`/`/var/lib/docker`和`e810cc9d…`/`/var/lib/docker-aisoft-65-consumer` |
| Final approved plan | PASS | final execute绑定`approval_plan_sha256=f9d36a7a1602ac684f97e22959daca3b24a3915fa7058f29253b37309ad1027e`；duplicate-daemon evidence SHA-256 `3ce8cccf…`；preflight mutations 0 |
| Registry producer path | PASS | 256 MiB loopback Registry完成两个fixture push、digest inspect/pull、release-scoped tags与`docker image save`；consumer Registry pull按要求拒绝，随后offline stage exact bytes |
| Normalized target paths | FAILED THEN FIXED / FINAL PASS | 绑定plan `c2821428…`的run在real `verify-artifact` PASS后，`verify-target`以Docker call 0拒绝`TMPDIR`尾随斜杠形成的非规范化`release_root`；failure bundle `issue-65-compose-5.1.4-97445947fff7.json.failure.63949.json`、cleanup `PASS`、两端before==after。Final plan已证明physical normalized workdir通过完整lifecycle |
| PostgreSQL 18 fixture volume | FAILED THEN FIXED / FINAL PASS | 绑定plan `bce65393…`已真实通过`verify-artifact`、`verify-target`与consumer offline `stage`，随后fixture health为`unhealthy`；failure bundle `issue-65-compose-5.1.4-97445947fff7.json.failure.98378.json`、cleanup `PASS`、两端before==after。只读image Config证明digest为PostgreSQL 18.4、`PGDATA=/var/lib/postgresql/18/docker`、`VOLUME=/var/lib/postgresql`；final plan以`/var/lib/postgresql`完成healthy migration lifecycle |
| Happy lifecycle before negatives | PASS | 绑定plan `88f39a3d…`先证明完整happy lifecycle；后置missing-receipt独立state root mode错误由failure bundle `issue-65-compose-5.1.4-97445947fff7.json.failure.21402.json`记录。Final plan显式`chmod 0700`后，happy lifecycle与全部后置negative共同进入immutable PASS evidence |
| Direct OCI manifest identity | PASS | descriptor digest或同一manifest content-verified Config digest通过；任意其它digest fail closed；real `verify-artifact` Docker calls=0 |
| Disposable PostgreSQL migration receipt | PASS | PostgreSQL 18.4 disposable fixture健康；首次migration `started → completed`、第二次`migration-noop`，marker count=`1`；restore `NOT RUN` |
| Negative real fail-closed | PASS | duplicate daemon、artifact tamper、wrong Compose、wrong store、missing staging receipt均按要求拒绝，mutation count 0且各自inventory不变 |
| Failure and success exact cleanup | PASS | 所有诊断run及final run均producer/consumer before==after；execution lock已删除；无prune |
| Immutable PASS evidence | PASS | `issue-65-compose-5.1.4-97445947fff7.json` mode `0444`，SHA-256 `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89`，internal validator PASS |

## T03 Compatibility promotion and final delivery

| Check | Status | Evidence |
|---|---|---|
| Production matrix exact Compose 5.1.4 row | PASS | revision `2026.08.3`只新增Engine `>=29.7.1,<29.7.2`、Compose `>=5.1.4,<5.1.5`、linux/amd64/containerd supported row；旧rows不变 |
| Exact range positive/negative tests | PASS | public `require_supported`证明5.1.4 exact支持；5.1.3/5.1.5/5.2.0、Engine邻界、classic拒绝；duplicate/overlap fail closed |
| Final required local gates | PASS | `bash codex/tests/smoke.sh`通过280 tests与static smoke；focused release、installer、fake harness、`bash -n`、ShellCheck、JSON、Secret与`git diff --check`均PASS |
| Single Closes #65 PR | NOT RUN | pending Controller handoff |
| Human merge | NOT RUN | forbidden for Agent/Controller |
| Business deployment | NOT RUN / OUT OF SCOPE | NewEmaint/DockerLab/AppServer/production explicitly excluded |

## Acceptance criteria result

| AC | Status | Notes |
|---|---|---|
| AC-1 | PASS | fresh source/tree、plan-bound runtime/fixture hashes、real Engine/Compose/containerd/daemon与immutable evidence均固定 |
| AC-2 | PASS | 两个获批task-owned disposable VM/daemon identity与不同data root已真实验证 |
| AC-3 | PASS | complete public lifecycle与state v2 receipts固定在immutable evidence |
| AC-4 | PASS | Registry/offline V2、direct OCI identity、consumer pull rejection、exact image identity与health PASS |
| AC-5 | PASS | disposable PostgreSQL migration started/completed/no-op与marker count 1 PASS；restore NOT RUN |
| AC-6 | PASS | real phase argv/mutation counts与state/resource readback满足隔离合同 |
| AC-7 | PASS | 全部real negatives按预期拒绝、mutation 0、inventory不变 |
| AC-8 | PASS | success/failure exact cleanup、before==after与immutable PASS/failure evidence已验证 |
| AC-9 | PASS | 仅按real evidence增加exact非重叠Compose 5.1.4 row；其它5.x/classic继续不支持 |
| AC-10 | PARTIAL | implementation/final-head required local gates PASS；唯一`Closes #65` PR与remote readback pending |

## Rollback and remaining gates

- 获批的task-owned producer/consumer VM仍运行并只保留digest-pinned Registry/PostgreSQL prerequisite
  images；final T02的Registry/PostgreSQL/Compose containers、fixture images/tags/digests、network、volume与
  临时文件均由exact cleanup删除，两端inventory恢复approved baseline。
- Production matrix已按immutable evidence增加唯一exact row；Gitea权限、merge与deployment未修改。
- 实现代码/文档只通过人工revert最终PR回滚。
- 2026-08-09用户确认收敛方向：Issue目标是验证计划部署的exact Docker/Compose组合并窄范围晋级，避免
  harness负例先于主lifecycle造成反复审批。最终获批plan已完成真实happy-path-first lifecycle、negative
  gates、exact cleanup与immutable PASS evidence；未执行任何业务部署。
- T02已按用户逐次批准的exact plan完成；后续不得把该证据外推为Compose其它5.x、classic或业务部署。
