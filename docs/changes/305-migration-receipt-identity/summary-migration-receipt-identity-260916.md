---
issue: 305
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/305
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: migration receipt 以 migration identity 为键，却用 receipt 里的 release_id 当门，使任何不带新 migration 的 release 都无法在已部署过的 target 上 migrate 或 activate；修复恢复既有部署合同，但落在 deployment 与 rollback 路径的共享 runtime 上，按平台强制规则判 complex。
risk_flags:
  - deployment
  - rollback
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-migration-receipt-identity-260916.md
  spec: spec-migration-receipt-identity-260916.md
  plan: plan-migration-receipt-identity-260916.md
  verification: verification-migration-receipt-identity-260916.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/305-migration-receipt-identity
pr_url:
created: 2026-09-16
updated: 2026-09-16
---

## 问题/需求总结

`codex/runtime/aisoft_release/runner.py` 的 migration receipt 以 `migration.identity`
（migration 内容哈希）为键写入 state，但两处读取都额外要求 receipt 的 `release_id`
等于当前 release：

- `_run_migration` 查到 `status == "completed"` 后，若 `record["release_id"]` 不等于
  当前 manifest 的 `release_id`，抛 `migration receipt release identity is stale`，
  只有 release_id 相同才返回 `migration-noop`。
- `_require_migration_completed` 在 `activate` 时做同样的比较，抛
  `activation migration receipt release identity is stale`。

后果：一个 target 只要部署过任何一个 release，之后所有**不带新 migration** 的 release
都无法 `migrate`，也无法 `activate`。对已上线项目，这是绝大多数发布。

NewEMaint Issue #124 在 DockerLab 上撞到这一点：release `0c2deaf7` 的三个阶段
`verify-artifact`/`verify-target`/`stage` 全 PASS，`migrate` 报
`DEPLOYMENT_FAILED — migration receipt release identity is stale`；target 上
`006d0c43`（2026-08-09）的 receipt 是 `completed`，两个 release 的 migration identity
相同（`sha256:54b5b303…`）。

## 影响范围

- `codex/runtime/aisoft_release/runner.py`：`_run_migration` 与
  `_require_migration_completed` 两处 `release_id` 比较。
- `codex/runtime/tests/`：`release_test_support.py` 的 `migration_identity()` 按
  release SHA 造不同 identity（SHA_A → `5`×64，SHA_B → `6`×64），
  所以 `test_release_runner.py` 中每个「第二个 release」用例都换了 identity，
  「同 identity、不同 release」这条路径从未被执行过。两处 `stale` 文案在整个测试树里
  零命中，是纯未覆盖分支。
- `codex/tests/check-release-evidence-boundary.py`：`runner.py` 的 sha256 被
  `CURRENT_SOURCE_PINS` 逐字节钉住，改 runner 必须同步推进这一项。
- `docker-release/README.md`：receipt 语义的合同文档，目前只写了 identity 写
  `started`/`completed`，没有写 release_id 的角色。
- `06-运维踩坑与broker.md`：补一条踩坑。

不在范围：NewEMaint 仓任何改动；DockerLab 现场 `state.json` 与已安装 runtime。

## 初步方案与建议

采用 Issue 正文的 **A**：receipt 的键是 migration identity，它表达「这套 migration 已在
这个数据库上跑完」，与哪个 release 带来它无关。identity 命中且 `completed` 时一律判
`migration-noop`，`release_id` 只作审计，不再作门；`_require_migration_completed`
只看 identity 的 `completed`。

**实现上 A 只能取正文括号里的「最近一次 release_id」那一支，不能取
`applied_by_release_ids`**：`codex/runtime/aisoft_release/state.py` 第 163 行用
`set(record) != {"status", "release_id"}` 把 receipt 的键集合钉成精确两项，而
`state.py` 落在 #290/#296 证据闸门的 `SCOPES` 内且不在
`CURRENT_SOURCE_PINS` 的 `{runner, transport, matrix}` 允许集合里——给 receipt 加字段
会撞 `current amendment exceeds its exact file scope`，属于 #65 的授权边界。
保留现有 `release_id` 字段、语义改为「实际执行这套 migration 的那个 release」，
既满足审计需求，又不动 state schema。

`status == started/failed` 的「不确定即禁止自动重跑」语义
（`_ensure_migration_not_uncertain`）不变。

## 风险

- **合同语义变更**：放宽了 `activate` 的前置条件。缓解：只放宽 `completed` 这一支，
  `started`/`failed` 与「无 receipt」仍然拒绝；新增反向用例逐条钉住。
- **证据闸门**：推进 `CURRENT_SOURCE_PINS` 的 runner 哈希是有意的治理动作，
  按该文件自己的注释要求，必须同时有行为测试和真实 E2E 证据。行为测试在本次变更内；
  真实 target 证据由 NewEMaint #124 在 DockerLab 上产出，本次 `verification` 引用它，
  合并前只能如实记为未执行。
- **无数据库风险**：修复方向是「少跑一次 migration」，不会让任何 migration 重复执行，
  也不触发数据库恢复路径。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: migration receipt 以 migration identity 为键，却用 receipt 里的 release_id 当门，使任何不带新 migration 的 release 都无法在已部署过的 target 上 migrate 或 activate；修复恢复既有部署合同，但落在 deployment 与 rollback 路径的共享 runtime 上，按平台强制规则判 complex。
risk_flags:
  - deployment
  - rollback
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 强制 complex：`risk_flags` 含 `deployment`、`rollback`、`shared-core`，三项都在
  `classification.py` 的 `FORCED_COMPLEX_RISKS` 内；AGENTS.md 亦规定
  「CI/制品/部署/回滚」与「共享核心组件」一律按 complex 处理。
- `contract_effect: restore`：`docker-release/README.md` 记载的阶段合同是
  `stage` → `migrate` → `activate`，并写明 migration identity 在运行前写 `started`、
  成功后写 `completed`；release_id 作为门这一条从未进入合同文档，却让文档描述的流程
  在已部署 target 上不可达。修复恢复文档既有语义而非新增能力。
- 本地复现（改动前、pin 同源）：用 patch 让两个 release 声明同一 migration identity，
  A 走完 `stage`/`migrate`/`activate`，B `stage` PASS 后
  `migrate` → `DeploymentError: migration receipt release identity is stale`，
  `activate` → `DeploymentError: activation migration receipt release identity is stale`，
  与 DockerLab 现场一致。
- 覆盖缺口：`rg -n "stale" codex/runtime/tests/ docker-release/` 对 migration 文案零命中。
- `required_docs` 含 `verification`：acceptance criterion 5 的证据是 DockerLab 上
  一次真实 target 执行，diff review 与 required CI 都复现不了，按 `03` §3 判据欠一份验证记录。

### 缺失的 acceptance criteria 或决策

- Issue 正文把 A/B 语义留给负责人在确认点 1 裁决；本文档给出 A 的建议与
  `applied_by_release_ids` 不可行的证据，最终取值以确认点 1 为准。
