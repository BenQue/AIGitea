---
issue: 91
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/91
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 提供项目常驻指针模板并接入 runbook，使两个 provider 在任意已接入项目的会话第一屏即进入平台流程（审核核心建议第一层）
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-project-pointer-templates-260811.md
  spec: spec-project-pointer-templates-260811.md
  plan: plan-project-pointer-templates-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/91-project-pointer-templates
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/92
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

代理主动使用平台依赖常驻上下文指针；项目级 AGENTS.md/CLAUDE.md 是唯一每会话必然注入的
通道，但平台无模板，9 个治理仓库各自手写，指针覆盖不受控。

## 影响范围

新增 `templates/project/{AGENTS.md,CLAUDE.md}`；runbook §2 项目契约清单改为引用模板并
写明存量仓库逐仓回补程序。不改业务仓库、平台 AGENTS.md、runtime。

## 初步方案与建议

模板四段：平台声明 / 每 Issue 开发路径（Matt 四步）/ 工具分工（Claude=开发/设计、
Codex=维护/部署，默认偏好非硬规则）/ 项目事实占位。交付形态明确「按项目 delivery
profile 决定，平台只统一流程不变量」——不同项目技术方案可不同，流程与指导思想一致。

## 风险

- 模板前两节若被项目随意改写会稀释指针——模板内注释明确「除更新事实外不删改」。
- 回补若批量脚本化会违反逐仓治理——runbook 写明逐仓独立 Issue/小 PR。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 提供项目常驻指针模板并接入 runbook，使两个 provider 在任意已接入项目的会话第一屏即进入平台流程（审核核心建议第一层）
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 新增平台合同表面与接入约定，命中「Agent/平台治理变更一律 complex」。

### 缺失的 acceptance criteria 或决策

- 9 仓实际回补另行逐仓执行（程序已定义）。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| AC-1 模板四段 | PASS | `rg` 四个段标题命中 4 |
| AC-2 CLAUDE.md 单行 | PASS | `wc -l` = 1 |
| AC-3 runbook 接入与回补程序 | PASS | `templates/project` 引用在文；逐仓程序在 §2 |
| AC-4 smoke | PASS（叠加 #82 修复验证） | #77 先例；还原后 worktree 干净 |
| AC-5 未触碰业务仓/平台 AGENTS.md | PASS | diff 仅模板 + runbook + change docs |
| 远端 CI / 人工合并 | PENDING / NOT RUN | PR run 由 #89 workflow 触发（若已合并）；等待人工合并 |
