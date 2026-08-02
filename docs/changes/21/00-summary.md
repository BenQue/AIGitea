---
issue: 21
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/21
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立 gitea-ci 的 SCM+CI/CD 主机角色硬边界并迁移或清理现存业务运行时，同时退役本地 prod-sim 测试 VM
risk_flags:
  - security
  - shared-core
  - ci-change
  - deployment
  - migration
  - destructive-operation
  - rollback
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/21
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

## 问题/需求总结

`gitea-ci` 当前同时承载 Gitea/Runner/缓存/通知等平台组件，以及
`rsdesign-new`、遗留 MyApp Notes 和失控的 `sfm-board` smoke 进程。目标角色已经明确为
SCM 加经过 allowlist 批准的 CI/CD 组件，不再允许业务 Web/API、业务数据库或长驻测试
进程。另一个本地 OrbStack `prod-sim` VM 仅用于早期测试，用户已明确授权退役删除。

## 影响范围

- 新增 machine-readable host-role/capability 合同和 fail-closed guard。
- 纠正 README、基础设施、CI/部署、运维和内网平移文档中的同机测试假设。
- 编排 `rsdesign-new` 迁移、SFM smoke 清理、MyApp Notes 退役、制品保留、Redis/Nginx
  收口；应用仓库修改仍须在各自仓库走 Issue/PR。
- 精确删除 OrbStack machine `prod-sim`，并保留可重建而非虚假的原地回滚证据。

## 初步方案与建议

先交付不依赖机器名称猜测的 host profile、capability allowlist 和 guard；任何业务 runtime
启动或部署在 `scm-ci` 角色上必须在 mutation 前失败。现存应用按“一项一证据、一项一停止
点”迁移或清理，保留 Gitea、Runner、Verdaccio、Mailpit、离线工具链和仍有引用的制品。

`prod-sim` 删除作为独立不可逆 Gate：同时核对 name 与 ID，确认无唯一数据或依赖，记录
最小重建基线，再只对精确目标执行删除；禁止 `--all`，不得把授权扩展到其它 VM。

## 风险

- 误判服务身份可能删除 CI/CD 依赖或业务数据，所有 live 操作必须先做进程、cgroup、端口、
  Nginx、数据库、timer、workflow 与文件引用交叉核对。
- 应用迁移和数据库/目录删除具有不同回滚边界，不能用一个批量清理命令处理。
- OrbStack 删除会永久丢失 VM 内文件；若发现唯一数据或身份不一致必须 `BLOCKED`。
- host-role guard 若只依赖可伪造环境变量会失效，目标 profile 必须与本机身份绑定并限制权限。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立 gitea-ci 的 SCM+CI/CD 主机角色硬边界并迁移或清理现存业务运行时，同时退役本地 prod-sim 测试 VM
risk_flags:
  - security
  - shared-core
  - ci-change
  - deployment
  - migration
  - destructive-operation
  - rollback
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改平台主机职责、共享部署 guard、CI 行为和跨项目部署边界。
- 涉及真实服务停止、数据库/目录清理、应用迁移和永久 VM 删除。
- 回滚方式从应用回切、数据恢复到“只能重建 VM”不等，必须逐项验证。

### 缺失的 acceptance criteria 或决策

- 无。用户已授权删除精确 `prod-sim` VM；其它 live 删除仍受本 spec 的逐项 Gate 约束。
