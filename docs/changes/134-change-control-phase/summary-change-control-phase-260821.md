---
issue: 134
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/134
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/134-change-control-phase
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/135
created: 2026-08-21
updated: 2026-08-21
reason: 修改判级运行时的 required_docs 决策与 governance manifest schema，触及平台治理与共享核心
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-change-control-phase-260821.md
  spec: spec-change-control-phase-260821.md
  plan: plan-change-control-phase-260821.md
  verification: verification-change-control-phase-260821.md
---

## 问题/需求总结

强制 complex 类别要求 summary + spec + plan + verification 四份映射文档。这对已上生产的应用合理，但对**尚未首次生产部署、正在主动开发**的项目构成主要重复成本，且落在收益最低的地方：spec 与 plan 的内容在 Mac 交互开发中已即时产生并执行，再誊写一遍是重复劳动。

LocalWMS 路线图 M1 的七个纵切面全部涉及 schema/迁移，逐个强制 complex 即 28 份文档；而该项目尚未部署过任何环境。

## 影响范围

- governance manifest schema：repository 条目新增可选 `change_control`
- `codex/runtime/aisoft_gitea_governance/contract.py`：解析、校验、`RepositoryContract` 字段
- `codex/runtime/aisoft_loop/`：`classification.route()`、`analysis.analyze_route()`、`contract.load_contract()`、`controller.Controller`、`cli`，并新增 `change_control.py` 解析器
- `03-Issue-Spec-Plan与单闸门开发流程.md`

**不改变任何既有项目的行为**：未声明该字段的仓库默认 `production`。

## AI 判级

```yaml
change_type: platform
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: [platform-governance, shared-core]
required_docs: [summary, spec, plan, verification]
override_reason: ''
```

平台治理叠加判级共享核心，强制 complex。本仓库自身为 `production` 阶段，故本变更仍写满四份。

## 结论

按交付阶段分级 `required_docs`，缺省更严。闸门、判级分类、部署治理均不变。
