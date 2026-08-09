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

# Compose 5.1.4 docker-release/v2 lifecycle implementation plan

## Ticket graph

| Ticket | Delivers | blocked_by | Status |
|---|---|---|---|
| T01 | 安全、确定性、默认零 Docker call 的 v2 lifecycle harness 与 fake/negative/cleanup/evidence tests | [] | complete |
| T02 | 用户单独批准环境中的 Engine 29.7.1 + Compose 5.1.4 + containerd real lifecycle evidence | [T01] | complete |
| T03 | 仅按 T02 PASS evidence 晋级 exact matrix row、完成文档/final gates/单一 PR | [T02] | complete |

## Tasks

### T01 — Build the bounded lifecycle harness

- 先写 fake/static harness red tests：默认 `NOT RUN` 且 Docker call 0；authorization marker、endpoint、
  full SHA、absolute path、digest pin、distinct logical IDs 与 immutable evidence path 缺失时 fail closed。
- 新增 Issue #65 real harness，复用 #27 的 endpoint grammar、daemon ID/data root readback、offline archive
  allowlist与 exact cleanup思想，但固定 v2 lifecycle 和 Compose 5.1.4，不接受 v1/Compose 2。
- 在临时目录生成 run-scoped exact candidate matrix、protected target profile/env、v2 release/model/inventory/
  archive 与 evidence working set；固定 source tree/harness/fixture/candidate matrix SHA；canonical approval
  plan同时绑定architecture lock、Docker/timeout binary、endpoint、baseline inventory与exact resource names。
- 增加 sanitized Docker argv recorder/phase marker；为 artifact/duplicate daemon/wrong store/wrong Compose/
  missing receipt negative paths验证 mutation boundary。
- 增加 disposable PostgreSQL fixture与 migration SQL contract；server、migration、runtime image ID必须各自
  唯一，database/network/volume/resource names绑定 `issue65 + source SHA prefix`。
- 为 success/failure cleanup建立 before/created/after inventory validator；只允许 exact object deletion，
  静态禁止 `docker * prune` 和 unresolved wildcard deletion；exact Compose backend network也必须进入
  approval、created/residual inventory与cleanup。
- 所有remote Docker call设置TERM/KILL wall-clock boundary；后台migration通过 `pid == pgid` handshake和
  process-group terminator防止cleanup与Compose child并发。PASS/failure evidence使用原子no-clobber发布；
  process group未静止时保留execution lock等待人工处置。
- 把 fake/static test与默认 `--not-run` real harness接入 full smoke；不在 T01 访问 daemon或数据库。
- 运行 focused unit/fake、installer、`bash -n`、ShellCheck和 full smoke；提交包含 `#65 T01` 的原子 commit。

### T02 — Execute the separately approved real E2E

- 2026-08-09 first artifact-diagnostic run在`verify-artifact`证明Docker 29 containerd direct OCI manifest
  使用top-level descriptor digest作为inspect identity，而runtime仅接受Config digest；failure cleanup
  恢复两端baseline。用户随后批准本Issue内的最窄runtime/test/README/spec修订，但每个修订后real execute
  仍须重新生成canonical plan并单独批准。
- 在任何 create/start/config/install前，把 exact VM/daemon/resource names、package/binary bytes、ports、
  images、network、volume、commands、cleanup和失败处理列给用户，并取得单独书面批准。
- 对两个不同 task-owned endpoint执行只读 preflight；固定 Engine `29.7.1`、Compose `5.1.4`、containerd
  `2.2.6`、linux/amd64、`DriverStatus` marker、daemon ID/data root和baseline inventory。
- 在任何resource creation前执行独立duplicate-daemon read-only negative；其余wrong Compose、wrong store、
  artifact tamper与missing-receipt negatives统一后置到完整happy lifecycle之后，并证明各自真实mutation
  count为0且inventory不变。missing-receipt使用独立空state root。
- 在producer构建/标记fixture、启动loopback Registry、push/pull digest、生成V2 offline bundle；在
  consumer证明 Registry pull rejected 后用 platform offline stage加载exact bytes。
- 只在consumer启动 disposable PostgreSQL fixture；按顺序执行 verify-artifact、verify-target、stage、
  migrate、activate、status与same-SHA activate no-op，并逐步验证phase isolation、receipts、identity/health。
- 后置negative gate失败时，sanitized failure bundle必须保留已完成的happy lifecycle JSON/state/argv；该run
  仍为FAIL且不能生成PASS evidence，但不得再把真实lifecycle记为`NOT RUN`。
- 成功后先精确cleanup并回读baseline，再生成mode `0444` immutable PASS evidence；失败时cleanup后只记录
  failure，禁止生成PASS evidence或修改production matrix。
- 更新verification中T02结果；提交包含 `#65 T02` 的原子 evidence commit。

### T03 — Promote only the proven compatibility row and deliver

- 只有T02 immutable evidence validator PASS后，修改production matrix revision并增加exact非重叠 row：
  Engine `>=29.7.1,<29.7.2`、Compose `>=5.1.4,<5.1.5`、linux/amd64、containerd，source指向本Issue
  verification；old containerd row和classic rejected row不变。
- 扩展 capability unit/smoke assertions，证明5.1.4 exact supported，5.1.3/5.1.5/其它5.x/classic仍拒绝，
  overlapping/duplicate/evidence drift fail closed。
- 同步 `docker-release` README、相关平台分册、onboarding和Issue #65 verification；真实/fake/external
  证据使用 `PASS`、`BLOCKED`、`NOT RUN` 分开记录。
- 运行focused release、全部Python、installer repeatability、harness fake、`bash -n`、ShellCheck、full
  smoke、JSON、Secret、`git diff --check`；修复后每个新final head重跑全部required gates。
- Agent提交包含 `#65 T03` 的原子commit；Controller fast-forward push唯一`change/65`，创建/更新唯一
  `Closes #65` PR，回读exact remote head、open/unmerged/CI配置并停止等待人工merge。

## Expected touch points

- `codex/tests/integration/`：Issue #65 real lifecycle harness。
- `codex/tests/`：harness fake/static regression与full smoke入口。
- `codex/tests/fixtures/docker-release-v2-lifecycle/`：最小v2/PostgreSQL fixture source与validation inputs。
- `codex/runtime/aisoft_release/transport.py`、`codex/runtime/tests/release_test_support.py`、
  `codex/runtime/tests/test_release_transport.py`：仅限用户2026-08-09批准的direct OCI manifest
  descriptor/Config identity修复与fail-closed回归。
- `docker-release/compatibility/image-stores-v1.json`：仅T02 PASS后由T03修改。
- `codex/runtime/tests/test_release_capability.py`：exact new row正反tests。
- `docker-release/README.md`、`02-CI与自动部署流水线.md`、onboarding runbook：evidence与采用边界。
- `docs/changes/65/`：mapped summary/spec/plan/verification。

除上面精确列出的`transport.py` identity validator修订外，不授权修改其它lifecycle runtime、CLI/schema、
AGENTS、Gitea workflow、业务仓库或环境配置。若实现必须继续改变这些合同，立即返回
`NEEDS_HUMAN_DECISION`。

## Acceptance criteria mapping

| AC | Ticket | Verification |
|---|---|---|
| AC-1 | T01, T02 | source/tree/fixture/hash assertions + real evidence exact values |
| AC-2 | T01, T02 | fake auth/endpoint negative tests + real read-only preflight + daemon ID/data root comparison |
| AC-3 | T01, T02 | public lifecycle driver outputs + state v2 receipt assertions + same-SHA no-op log |
| AC-4 | T01, T02 | Registry/offline archive/identity fake tests + real push/pull/save/load/offline rejection/health |
| AC-5 | T01, T02 | PostgreSQL fixture contract tests + real started/completed/no-op receipt and fixture query |
| AC-6 | T01, T02 | phase-scoped argv/mutation log + state/resource readback |
| AC-7 | T01, T02 | tamper/store/Compose/duplicate/missing-receipt negatives with zero corresponding mutation |
| AC-8 | T01, T02 | cleanup static tests + before/created/after real inventory + immutable evidence validator |
| AC-9 | T03 | exact range unit tests + matrix schema/smoke + source evidence review |
| AC-10 | T01, T03 | focused/full/installer/shell/Secret/diff/final-head gates + PR readback |

## Database migration

平台与业务数据库都不迁移。T02 only使用Issue #65创建的disposable PostgreSQL fixture和非破坏性、
fixture-owned SQL。没有backup/restore；migration failure不自动重跑。没有用户单独批准时整个T02保持
`BLOCKED / NOT RUN`。

## Deployment and rollback

本Change不部署业务应用。平台代码/文档通过人工revert最终PR回滚；matrix exact row与evidence引用必须
一起回滚。Disposable资源通过harness exact identifiers清理；cleanup失败时报告残留并停止，不运行prune、
不删除VM、也不扩大授权。VM创建/删除、daemon配置/restart和PostgreSQL fixture mutation都是独立批准项。
