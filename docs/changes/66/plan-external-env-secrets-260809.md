---
issue: 66
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/66
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - external-contract
  - shared-core
  - artifact
  - deployment
depends_on: []
status: implementing
branch: change/66
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

# External environment reference implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | Issue #66 contract、fresh baseline 与 red regression coverage | - | completed |
| T02 | 路径精确、value 严格的 Compose sensitive-field validation | T01 | completed |
| T03 | CLI/runner/phase/equality regression 与 adopter documentation | T02 | completed |
| T04 | 完整平台验证、verification、原子 commit 与唯一 PR handoff | T03 | in_progress |

## Tasks

### T01 — Contract and red tests

- 固定 fresh `main`、Issue/PR/CI 与 live bytes；复现当前 `INVALID_CONTRACT`。
- 创建映射的 summary/spec/plan/verification，记录 complex/security/shared-core 边界。
- 为合法敏感 env reference、literal/default/unknown field、zero-call 与 equality 添加失败优先测试。

### T02 — Compose-aware sensitive validation

- 提供共享的 strict environment-reference grammar 与 Compose path-aware sensitive scanner。
- producer loader 与 Compose validator 使用同一规则；仅精确 environment value 位置可例外。
- 保持通用 scanner 及 manifest、lock、inventory、profile/state 调用点不变。

### T03 — Runtime and documentation regression

- 真实调用 `verify-artifact` CLI/runner 验证成功 payload 与 zero-call/target-not-read。
- 验证 `verify-target` 完整 model equality 和 mutation=0 的 drift failure。
- 更新 `docker-release/README.md`，说明允许语法、default literal 禁令与 sensitive key 仅限 environment。

### T04 — Verification and delivery

- 运行 focused、full release、compile、installer、fake harness、shell syntax/ShellCheck、完整 smoke 和
  diff/Secret checks。
- 更新 verification 的 exact commands/counts；Issue #65 real E2E 与全部环境动作保留 NOT RUN。
- 创建范围内原子 commit，推送唯一 `change/66`，创建唯一 `Closes #66` PR；回读 final head/status 并
  停在人工 merge gate。

## Expected touch points

- `codex/runtime/aisoft_release/{contract,compose,security}.py`
- `codex/runtime/tests/{release_test_support,test_release_contract,test_release_cli,test_release_phases}.py`
- `docker-release/README.md`
- `docs/changes/66/`

以上是范围提示；不授权修改 schema/state/compatibility matrix、其它 Issue 文档、应用仓库或环境。

## 数据库迁移

无。测试只生成临时 JSON release fixture，不连接数据库、不读取 env file、不调用 Docker。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | contract/Compose/CLI positive tests，覆盖 `JWT_SECRET` 与 `DATABASE_URL` |
| AC-2 | literal Secret/URL/token/password/null/default/alternate negative table tests |
| AC-3 | producer loader 与 target validator unknown sensitive-field tests |
| AC-4 | manifest/lock/inventory/profile/state regression + existing full release suite |
| AC-5 | real CLI main + runner phase test；`target_facts=NOT_READ`、`docker_calls=0`、events `[]` |
| AC-6 | `verify-target` sensitive environment equality pass/drift fail，mutations `[]` |
| AC-7 | v1 regression、schema/state tests、matrix zero diff review |
| AC-8 | focused/full/smoke/installer/fake/syntax/ShellCheck/diff commands |
| AC-9 | live branch/PR/final-head/status readback；manual merge gate review |

## 部署与回滚

无部署。代码通过人工 revert 最终 PR 回滚；任何 downstream 恢复只在本 PR 人工 merge 后重新 pin
exact merged SHA/bytes。本 Change 不运行 Docker、migration、health、rollback 或 production action。
