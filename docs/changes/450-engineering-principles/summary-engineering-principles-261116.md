---
issue: 450
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/450
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 细化共享工程原则，属于 Agent 与平台治理变更；语义落点仅一份 reference，仍按强制 complex 处理。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-engineering-principles-261116.md
  spec: spec-engineering-principles-261116.md
  plan: plan-engineering-principles-261116.md
  verification: verification-engineering-principles-261116.md
route_provider: claude
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: '负责人 2026-11-16 在本票线程裁决执行强度偏离路由 effort max。T01 由会话 f2cce2e4 以 medium 执行，按实保留并经负责人认可。T02 负责人称已把当前会话调为 xhigh 并认为足够、不需要 max，会话元数据 15:24 读回仍为 medium，实际强度未核实。路由卡其余各格不变。'
depends_on: []
status: approved
branch: change/450-engineering-principles
pr_url:
created: 2026-11-16
updated: 2026-11-16
---

## 索引

- Issue：[#450](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/450)。状态、PR 和文档映射以 front matter 为准。
- 需求、授权、精确文案、验收与风险见 spec；Txx 及验证计划见 plan；准备阶段与后续真实执行记录见 verification。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 细化共享工程原则，属于 Agent 与平台治理变更；语义落点仅一份 reference，仍按强制 complex 处理。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: '负责人 2026-11-16 在本票线程裁决执行强度偏离路由 effort max。T01 由会话 f2cce2e4 以 medium 执行，按实保留并经负责人认可。T02 负责人称已把当前会话调为 xhigh 并认为足够、不需要 max，会话元数据 15:24 读回仍为 medium，实际强度未核实。路由卡其余各格不变。'
```

### 判级证据

- 现行 AGENTS.md 与 classification.py 将 Agent / 平台治理列为强制 complex；仓库 change_control 缺省 production。负责人在合同准备完成后指定 Claude Code 接手实施，显式 provider 已同步为 claude，仍命中 R3 / D4。
- verification 承载独立审核、治理停止与 fresh run 的一次性证据以及隔离导出观察；它不代表部署义务。

### 缺失的 acceptance criteria 或决策

- 无；收敛范围已由负责人确认。实现与测试状态在 plan / verification 如实记录。
