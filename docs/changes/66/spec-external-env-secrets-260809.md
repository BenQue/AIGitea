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

# External environment reference security spec

## 目标与原因

恢复 `docker-release/v2` 的 coherent contract：normalized Compose model 可以保存外部环境变量引用，
包括敏感命名的 environment key，但绝不保存 Secret value。producer artifact verification 必须继续
独立于 target、Docker、Compose binary 与 Secret；consumer readiness 必须继续比较 producer/target
normalized model 的精确相等性。

## Acceptance criteria

- [x] **AC-1 Scoped positive rule**：仅在
  `services.<service>.environment.<key>` 中允许敏感命名 key，且 value 必须精确匹配 `${NAME}` 或
  `${NAME:?required}`；`JWT_SECRET=${JWT_SECRET:?required}` 与
  `DATABASE_URL=${DATABASE_URL:?required}` 通过 `verify-artifact`。
- [x] **AC-2 Embedded value rejection**：literal Secret、literal database/connection URL、literal
  token/password、null sensitive value，以及 `${NAME:-literal}` / `${NAME:+literal}` 等嵌入
  default/alternate value 的表达式继续 fail closed。
- [x] **AC-3 Unknown sensitive fields**：Compose model 中除上述精确 environment value 位置外的
  sensitive-named field，即使其 value 看似外部引用，也继续 fail closed。
- [x] **AC-4 Existing boundaries**：release manifest、architecture lock、offline inventory、target
  profile 和 state 的 sensitive-field validation 语义不变，并保留相关 regression coverage。
- [x] **AC-5 Artifact-only isolation**：合法敏感 environment 外部引用通过真实 CLI/runner
  `verify-artifact`；结果仍含 `target_facts=NOT_READ`、`docker_calls=0`，fake Docker event count 为 0，
  target profile/env file 可以不存在。
- [x] **AC-6 Target equality**：`verify-target` 继续分别验证 producer/target model，并要求完整 model
  equality；任一 environment key/value drift 在任何 target mutation 前拒绝。
- [x] **AC-7 Compatibility**：`docker-release/v1` legacy commands、v2 schema/state、phase permission、
  offline identity 与 compatibility matrix 不变；不以本 Change 声称 Compose 5.1.4 real E2E support。
- [x] **AC-8 Verification**：contract、Compose security、CLI/runner 和 phase regression tests、完整
  release suite、installer/fake harness、Python/shell/static checks、完整平台 smoke 与
  `git diff --check` 通过；未运行的真实环境项如实记录。
- [ ] **AC-9 Delivery gate**：所有内容进入单一 `change/66` 与唯一 `Closes #66` PR；回读 exact final
  head 和 live required status。只有实际 required CI 通过才能写 PASS，最终 merge 只由用户操作。

## 接口、数据与兼容性影响

- `docker-release/v2` normalized Compose model 的允许语法收敛为纯引用 `${NAME}` 或明确的缺失错误
  `${NAME:?required}`。不接受在 release bytes 内提供 default/alternate literal 的 Compose substitution。
- manifest/schema/state version 不变；不新增字段、不改 checksum、canonical JSON 或 target profile。
- `verify-artifact` 与 `verify-target` CLI 参数、成功结果和错误码不变；非法值继续返回
  `INVALID_CONTRACT`。
- producer/target model equality 使用现有完整 Mapping equality，不增加省略、重命名或 normalize
  fallback。

## 风险与回滚约束

- 扫描必须以结构化路径 tuple 判断，不能用字符串前缀、substring 或任意 environment 名称放行。
- 通用 `SENSITIVE_KEY` pattern 与 manifest/lock/inventory/profile/state 调用点不得弱化。
- 若回归出现，回滚方式为人工 revert 最终 PR；artifact 不原地重写，consumer 重新 pin 人工 merge 后的
  exact platform SHA/bytes。
- 本 Change 没有数据库 migration、部署或环境回滚动作。

## 非目标

- 不修改 NewEmaint、其 `change/59`、`JWT_SECRET` 接口或任何 downstream bytes。
- 不执行 Issue #65 的 Docker/Compose/containerd E2E，不改 compatibility matrix。
- 不操作 DockerLab、公司服务器、target profile、Secret、database/migration、Nginx、image
  transport/load、deployment、health/browser/rollback、workflow dispatch、VM/Docker restart 或 prune。
- 不修改 Gitea 权限、protected main、required CI 或执行 PR merge。

## 未决问题

无。允许语法、路径、正反例、zero-call、equality、兼容和交付边界均已明确。
