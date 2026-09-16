---
issue: 305
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/305
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - deployment
  - rollback
  - shared-core
depends_on: []
status: approved
branch: change/305-migration-receipt-identity
created: 2026-09-16
updated: 2026-09-16
---

# Spec：migration receipt 以 migration identity 为唯一判据

## 目标与原因

让「已在这个数据库上跑完这套 migration」成为 migration receipt 的唯一含义，恢复
`docker-release/README.md` 已经记载的 `stage` → `migrate` → `activate` 阶段合同：
一个不带新 migration 的 release，必须能在已部署过其它 release 的 target 上
`migrate` 成 no-op 并 `activate`。

当前 `runner.py` 在 identity 命中之后又拿 receipt 里的 `release_id` 与当前 manifest
比较，使这条路径对任何已部署 target 恒定失败。负责人在确认点 1 选定语义 **A**。

## Acceptance criteria

- [ ] AC-1：release A 完成 `migrate` 后，与 A 声明**相同** migration identity、
      `release_id` 不同的 release B，`migrate` 返回 `migration-noop`，
      不新增 migration 容器事件，receipt 的 `status` 仍为 `completed`，
      `release_id` 仍为**实际执行**这套 migration 的 A，随后 `activate` 成功。
- [ ] AC-2：identity 相同但 receipt 为 `started` 或 `failed` 时，`migrate` 与
      `activate` 仍按现有语义拒绝，且不产生任何 Docker mutation。
- [ ] AC-3：identity 相同、receipt 缺失时，`activate` 仍要求一份 `completed` receipt
      并拒绝；`migrate` 正常执行 migration 并写 `completed`。
- [ ] AC-4：既有 `codex/runtime/tests/test_release_runner.py` 全部用例保持通过；
      `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-5：`docker-release/README.md` 写明 receipt 以 migration identity 为键、
      `release_id` 仅作审计；`06-运维踩坑与broker.md` 补一条踩坑。
- [ ] AC-6：`codex/tests/check-release-evidence-boundary.py` 的
      `CURRENT_SOURCE_PINS[runner.py]` 推进到修改后的真实 sha256，
      `CURRENT_SOURCE_PINS` 的键集合仍是 `{runner, transport, matrix}` 的子集。

AC-1 到 AC-4 对应 Issue 正文验收标准 1–3，AC-5 对应正文第 4 条，AC-6 是实现本次修复
在证据闸门下的必要条件。正文第 5 条（DockerLab 真实 target 证据）由 NewEMaint #124
产出与记录，不在本 Issue 验收内，本次 `verification` 只引用它并如实标注未执行。

## 接口、数据与兼容性影响

- **state schema 不变**：migration receipt 的键集合仍是精确的
  `{"status", "release_id"}`，`state.py` 一个字节都不动。既有 v1/v2 state 无需迁移，
  已部署 target 上的 receipt 直接可用。
- **`release_id` 语义收窄为审计**：它记录实际执行这套 migration 的那个 release，
  不再参与任何判据。`migration-noop` 路径不写 state。
- **放宽的只有一支**：`completed` + identity 命中。`started`/`failed`/缺失的行为
  逐字不变，`_ensure_migration_not_uncertain` 不动。
- **向后兼容**：修复前能成功的每一条路径，修复后仍成功且结果相同；修复只把原本抛
  `DeploymentError` 的两个分支变成成功。没有反向的行为收紧。

## 风险与回滚约束

- 放宽 `activate` 前置条件的风险边界：`activate` 仍要求 exact staging receipt、
  要求 identity 对应的 receipt 存在且为 `completed`。AC-2/AC-3 是这条边界的反向证明。
- 不触发数据库写：修复方向是「少跑一次 migration」，不会让任何 migration 重复执行，
  也不进入 `database_restore` 路径。
- 回滚方式：本次改动是纯 runtime 源码与文档，`git revert` 该 PR 的 merge commit 即可
  完全回到修复前行为；无 state 迁移、无制品、无部署动作需要撤销。
- 证据闸门：推进 `CURRENT_SOURCE_PINS` 的 runner 哈希是该文件自身设计的推进路径
  （runner 已在允许集合内），不扩大 `CURRENT_SOURCE_PINS` 的键集合，
  不触碰 `SCOPES`、`CONTENT_EXEMPT` 或 baseline 常量。

## 非目标

- 不改 `codex/runtime/aisoft_release/state.py`，不给 receipt 增加字段。
- 不改 `_ensure_migration_not_uncertain` 的 `started`/`failed` 语义。
- 不改 NewEMaint 仓任何内容。
- 不改 DockerLab 现场 `state.json`、已安装 runtime 或任何部署状态。
- 不处理 DockerLab 已安装 runtime 与 pin 的 3 文件差异（#124 已记录，是否重装另议）。

## 未决问题

无。A/B 语义已在确认点 1 由负责人选定为 A，且 `applied_by_release_ids` 的不可行性
已由 `state.py` 的精确键集合与证据闸门的文件范围证明。
