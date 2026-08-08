---
issue: 60
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/60
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将已合并的 Matt 开发编排合同投影到仓库根级与 VM Codex 全局指令，同时保持平台治理和人工合并边界
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-matt-root-rules-260808.md
  spec: spec-matt-root-rules-260808.md
  plan: plan-matt-root-rules-260808.md
  verification: verification-matt-root-rules-260808.md
confidence: high
override_reason: ''
depends_on:
  - 57
status: pr-open
branch: change/60
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/62
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #57 与 PR #59 已把完整 Matt Pocock skills、Gitea adapter、语义文档 resolver 和
`triage → to-spec → to-tickets → implement` 流程合并到 `main`。仓库根级 `AGENTS.md` 与
`codex/global-AGENTS.md` 仍把旧数字 basename 和 `gitea-*` skills 写成主要入口，尚未投影新的
开发编排合同。

本 Change 只更新这两份指令：初始化仓库时以 `$setup-matt-pocock-skills` 配合
`templates/docs/agents/`，每个 Issue 以完整 Matt 流程为主；现有 `gitea-*` skills 继续承担
AISoftPlatform 兼容适配，不再定义第二套开发方法。

## 影响范围

- 仓库根级 Agent 工作原则、change 文档命名与初始化入口。
- VM Codex 全局 skill routing 与每 Issue 开发流程。
- 对指令合同的静态 smoke 检查。
- 不安装用户级 skills，不同步 live 标签，不修改 runtime、业务仓库或部署环境。

## 初步方案与建议

让 `AGENTS.md` 使用语义角色与 `documents` 映射描述 summary/spec/plan，并保留 Issue #57 之前的
legacy basename 只读兼容。让 `codex/global-AGENTS.md` 先调用 `$aisoft-matt-workflow` 完成平台边界
检查，再按场景调用完整 Matt skills；`gitea-*` 仅作为 label、文档、Controller 和运维兼容 adapter。

## 风险

- 根级指令是当前 Agent 的治理来源，合同起草与指令应用必须分开，避免同一运行改变正在使用的规则。
- Matt 与兼容 adapter 的职责若描述不清，可能重新形成两套主流程。
- 只改文字而不更新 smoke 断言会使后续回归无法发现路由漂移。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将已合并的 Matt 开发编排合同投影到仓库根级与 VM Codex 全局指令，同时保持平台治理和人工合并边界
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `origin/main` 为 PR #59 的 merge commit `9f4d5fbf6daea50138f41ec21779b08d6c8f8d96`，并包含
  Issue #57 的完整实现提交。
- 目标直接涉及 `AGENTS.md`、全局 Agent 路由和共享治理合同，命中强制 complex 规则。
- Issue #60 已明确限定为 instruction-only，不安装 skill、不 provision live 标签、不 merge 或 deploy。

### 缺失的 acceptance criteria 或决策

- 无；用户已于 2026-08-08 明确批准本 spec/plan。
