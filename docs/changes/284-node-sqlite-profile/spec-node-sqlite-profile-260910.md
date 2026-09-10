---
issue: 284
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
status: contract-drafting
branch: change/284-node-sqlite-profile
created: 2026-09-10
updated: 2026-09-10
---

# Spec：Node 22 加 SQLite profile 与三处 architecture 合同裁决

## 目标与原因

catalog `2026.09.0` 的 4 个 profile 无一能如实描述「SQLite 加 Next/React/Prisma 加 Node 22、
一个仓库两个环境两种交付形态」的应用。补齐这个 profile 的过程暴露出三条此前没有写下来的
合同语义，其中两条会让 governed transition 路径对本平台的每个项目都不可用。本变更新增
一个 profile，并把三条语义裁决写成可执行的校验规则与 ADR。

四点需求不拆成独立 Issue：下游被阻塞的项目同时命中全部四点，任何一点留到后续 Issue
都不能解除阻塞。

## 裁决（人于 2026-09-10 确认）

- **裁决 A**：`delivery_contract` 保持单值。一个 profile 的 `delivery_contracts` 可以列出多个
  取值，项目按环境各写一份 declaration 与一份 lock。理由：两个环境不只是交付方式不同，OS 与
  CPU 架构也不同，单个 `components` 数组本来就装不下两者，把字段改成数组解决不了这一点，
  还会削弱 ADR-0005 确立的取值互斥性。
- **裁决 B**：`PROJECT_VERSION_DRIFT` 的精确相等比较保持为默认。新增一类 as-built 版本例外，
  复用现有 exception 机制，允许在同一 major 内如实声明与 catalog pin 不同的真实版本。
- **裁决 C**：transition 与 component 的 migration Issue 由「绝对 HTTPS」放宽为「绝对 http 或
  https」。其余检查（host 存在、无凭据、无 query、无 fragment、路径形如 `/.../issues/N`）不变。
  理由：该字段是审计引用，validator 从不解引用它；内网 Gitea 只在 http 端口提供服务，
  https-only 实际只会逼出一个不解析的假 URL。
- **裁决 D**：不新增 `os` category 取值。容器基镜像的 OS 已由 `oci-image` 类目表达，不需要
  第二种建模；另一个候选取值是 interim release，标准支持期已于 2026-07-01 结束，如实入库
  只会在 `COMPONENT_EOL` 上 fail closed。

## Acceptance criteria

- [ ] AC-1：新增 active profile `linux-node-sqlite-v1`，slot 覆盖 os、runtime、package-manager、
      database、framework、frontend、orm、toolchain，不含 Postgres、proxy、container-engine 与
      container-compose slot；`aisoft-architecture validate` 对全部 5 个 profile 通过。
- [ ] AC-2：`linux-node-sqlite-v1` 的 `delivery_contracts` 同时列出 `embedded-sqlite/v1`、
      `pm2-legacy` 与 `docker-release/v1`；两份分别选取其中不同取值的 fixture declaration 都
      `valid: true`，证明按环境拆声明可行。
- [ ] AC-3：project declaration 的 component 支持可选 `as_built: true`。为 true 时必须有唯一
      有效 exception，声明版本必须与 catalog pin 同 major 且不相等；major 为 `0` 时次版本号也
      必须相等；`oci-digest` component 一律拒绝 as-built。
- [ ] AC-4：as-built 声明生成的 lock 在 `resolved_components` 中记录**声明的真实版本**与
      `as_built: true`，而不是 catalog pin；`exception_id` 与 `exception_expires_at` 同时记录。
- [ ] AC-5：未声明 `as_built` 的既有 declaration 行为完全不变，仍在版本不等时报
      `PROJECT_VERSION_DRIFT`。
- [ ] AC-6：`http://` 的绝对 Issue URL 在 component `migration_issue` 与 transition 校验中都被
      接受；相对路径、`#N` 简写、带凭据、带 query 或 fragment 的 URL 在 transition 校验中仍被拒绝。
- [ ] AC-7：新增 ADR 记录四条裁决与其边界；`architecture/README.md` 与 onboarding runbook §9
      同步到新 profile、按环境拆声明、as-built 例外与 http(s) 规则。
- [ ] AC-8：既有 4 个 profile、全部 fixtures 与既有 39 个 architecture 测试不回退；
      `bash codex/tests/smoke.sh` 通过。
- [ ] AC-9：同一份 as-built declaration 连续两次 `lock` 输出 byte-identical。

## 接口、数据与兼容性影响

- **新增（向后兼容）**：`project-architecture-v1.schema.json` 的 component item 增加可选
  `as_built`；`architecture-lock-v1.schema.json` 的 resolved component 增加可选 `as_built`；
  `aisoft_release/contract.py` 的 lock resolved component optional key 集合同步增加 `as_built`，
  否则带 as-built 的 lock 进不了 release 路径。
- **放宽**：`ISSUE_RE` 与 `_is_absolute_issue_url` 接受 http scheme。这是唯一一处放宽，
  对既有声明不产生失效。
- **不变**：catalog 的 component 集合与 revision；`delivery_contract` 单值与 lock 中该字段的
  类型；`aisoft_release` 对 lock `delivery_contract` 的等值断言；既有 4 个 profile 的 `version`；
  `prohibited`、EOL、digest、expiry、checksum 与 lock drift 的 fail-closed 行为。
- **下游边界**：as-built 例外不改变 release 路径的任何门；它只让 lock 如实记录偏差，
  仍受 exception 到期与 `migrate_by` 上限约束。

## 风险与回滚约束

- validator 是所有接入项目共用的共享核心。缓解：as-built 必须逐 component 显式 opt-in，
  默认行为逐字不变，并由既有 fixtures 回归证明。
- as-built 可能被当成长期免检通道。缓解：沿用 180 天上限与 `migrate_by` 上限，且声明版本
  与 pin 相等时直接报错，强制清理过期例外。
- 回滚：本变更只新增文件与可选字段，`git revert` 单个 merge commit 即可完整回退，
  没有数据迁移，没有部署动作。

## 非目标

- 不新增 catalog component，不改 catalog revision。
- 不修改任何应用仓，不生成任何项目的 current lock，不部署。
- 不把内网 Gitea 迁到 443，不改 `delivery_contract` 为数组。
- 不为已 EOL 的 interim OS 提供任何绕过 `COMPONENT_EOL` 的通道。

## 未决问题

无。四条裁决已由人于 2026-09-10 确认。
