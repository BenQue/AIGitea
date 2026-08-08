---
issue: 57
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/57
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 以完整 Matt Pocock skills 替换开发编排层，同时保留 AISoftPlatform 治理、确定性控制与人工合并边界
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-matt-skills-260808.md
  spec: spec-matt-skills-260808.md
  plan: plan-matt-skills-260808.md
  verification: verification-matt-skills-260808.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/57
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

AISoftPlatform 当前的 GSD、Superpowers 和平台自有实现编排存在职责重叠与较高上下文开销。
Matt Pocock skills 更适合作为开发方法与编排层，但不能替代 Issue、合同校验、受保护 `main`、
确定性 CI/部署和人工合并等平台治理。

本 Change 完整保留 Matt 上游 skills，通过薄 adapter 对齐 Gitea triage、spec、plan 和
Development Loop。Agent 可以在 `change/N` 上创建原子 commit，Controller 独占 push、最终 PR、
CI 与状态投影，最终 PR 继续只能由人工合并。

从 Issue #57 起，新 change 文档使用 `<role>-<short-slug>-<YYMMDD>.md`。历史 Issue 和旧固定文件名
保持只读兼容，不批量重命名。

## 影响范围

- change 文档命名、front matter、模板、合同解析和 PR 链接。
- analyzer、Development Loop、Gitea 标签投影及其测试。
- Matt Pocock skills 的固定版本、更新审计和 AISoftPlatform adapter。
- 平台流程与运维文档；不修改业务项目、用户级全局 skills 或部署环境。

## 初步方案与建议

使用完整上游 snapshot 加 manifest，不直接修改 Matt 的 `SKILL.md`。平台只暴露
`reconcile_labels`、`publish_spec`、`publish_plan`、`run_ticket` 等窄接口；新文档由 summary 中的
`documents` 映射解析，禁止无约束 glob。旧 Issue 缺少映射时，仅回退到四个 legacy basename。

## 风险

- 新旧文档合同并存可能导致解析歧义，必须 fail closed 并覆盖兼容测试。
- Agent commit 与 Controller push 的职责变化涉及 Git 边界，必须验证 branch、ancestry、路径、Secret
  和 clean worktree。
- Matt 上游新增 skill、流程、权限或 Git 副作用时不得自动推广，必须升级为 complex 评审。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 以完整 Matt Pocock skills 替换开发编排层，同时保留 AISoftPlatform 治理、确定性控制与人工合并边界
risk_flags:
  - agent-governance
  - platform-governance
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

- 修改 Agent 行为、Controller、Git 提交职责和平台治理合同，命中强制 complex 规则。
- 新命名需要同时变更文档解析、模板、tests、skills 和 PR 链接，属于共享核心合同变化。
- 用户已明确批准 Matt 编排层边界、triage 兼容、spec/plan 对齐、Agent commit 与人工 merge。

### 缺失的 acceptance criteria 或决策

- 无；实现不得扩大到历史 Issue 重命名、业务项目迁移、全局 skill 删除或部署。
