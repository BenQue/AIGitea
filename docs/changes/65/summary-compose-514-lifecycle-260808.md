---
issue: 65
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/65
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 Compose 5.1.4 增加 task-owned Engine 29 containerd 的真实 docker-release/v2 lifecycle evidence，并只按证据窄范围调整共享 compatibility matrix
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
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-compose-514-lifecycle-260808.md
  spec: spec-compose-514-lifecycle-260808.md
  plan: plan-compose-514-lifecycle-260808.md
  verification: verification-compose-514-lifecycle-260808.md
confidence: high
override_reason: ''
depends_on:
  - 22
  - 27
  - 58
status: pr-open
branch: change/65
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/71
created: 2026-08-08
updated: 2026-08-09
---

## 问题/需求总结

AISoftPlatform `main@97445947fff79a4c2db6fa764feb21660e281556` 已合并 Issue #58 的
`docker-release/v2` 分阶段 lifecycle。Issue #65开始时Compose 5.1.4真实consumer E2E保持
`BLOCKED / NOT RUN`，compatibility matrix revision `2026.08.2`仅覆盖Compose `>=2.27.0,<3.0.0`。
现已在两个task-owned disposable daemon完成Engine 29.7.1、Compose 5.1.4、linux/amd64、containerd
完整lifecycle/negative/cleanup evidence，并仅把matrix晋级为revision `2026.08.3`的exact非重叠row。

Issue #65 要求使用两套不同 daemon ID/data root 的 task-owned disposable producer/consumer，
对 merged `docker-release/v2` 依次验证 artifact、target、stage、migration、activation、status 与
same-SHA no-op。Registry/offline identity、disposable PostgreSQL receipt、negative fail-closed 和
exact cleanup 都是同一 acceptance evidence 的必需部分；fake/static tests 不能替代真实 E2E。

## 影响范围

- 新增 #65 专用 real lifecycle harness、它的 fake/static regression 和 deterministic fixture/evidence
  合同。
- 在用户单独批准后，仅操作精确命名的 disposable producer/consumer daemon/VM 与 disposable
  PostgreSQL fixture。
- 只有 real E2E 全部通过后，才以 exact Engine `29.7.1`、Compose `5.1.4`、linux/amd64、containerd
  证据调整共享 image-store compatibility matrix。
- 同步 `docker-release` README、平台文档、Issue #65 verification 与 full smoke 入口。
- 不修改 NewEmaint、DockerLab、AppServer、production、公司服务器、Gitea 权限或 live service。

## 初步方案与建议

复用 Issue #27 的双 daemon identity、offline archive allowlist 与 cleanup inventory 设计，但不复用其
`docker-release/v1`/Compose 2 结论。新增 harness 通过现有公开 `ReleaseRuntime`/`DockerAdapter`
seam 执行 v2 分阶段 lifecycle；测试运行使用 run-scoped candidate matrix，生产 matrix 在 evidence
完成前保持不变，从而打破“未支持版本无法执行 lifecycle、未执行 lifecycle 又不能晋级”的循环。

Harness 默认只输出 `NOT RUN`，只有同时给出 Issue #65 exact authorization marker、两个不同 endpoint、
完整 source SHA、digest-pinned/preloaded fixture、临时路径与 evidence 输出路径时才允许 preflight 或
execute。每个 phase 记录固定 argv，并验证上一 phase receipt、下一 phase mutation 不会提前发生。
成功和失败路径都只精确删除本 Issue 创建的 container、image/tag、network、volume、build 和临时文件，
绝不运行 prune。

## 风险

- 真实 Docker 与 PostgreSQL mutation 可能残留资源；必须在每次 mutation 前固定 inventory，在失败 trap
  和成功尾声逐项删除并回读差异。
- Compose 5.1.4 的 normalized model、`--pull never --no-build` 或 container identity 语义可能与
  Compose 2 不同；任何差异都必须先判断为独立合同缺陷或真实不兼容，不能放宽 validator。
- Migration 结果在中断后可能不确定；started/failed receipt 不得自动重跑，也不得执行 restore。
- candidate matrix 只属于 run-scoped test input；真实 evidence 完成前不得复制到 production matrix，
  失败时 matrix 必须保持 zero diff。
- Gitea 没有 configured required status context；最终 head 仍必须跑 repository required local gates，
  不能把 `statuses=[]` 写成 remote CI PASS。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 Compose 5.1.4 增加 task-owned Engine 29 containerd 的真实 docker-release/v2 lifecycle evidence，并只按证据窄范围调整共享 compatibility matrix
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
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```
