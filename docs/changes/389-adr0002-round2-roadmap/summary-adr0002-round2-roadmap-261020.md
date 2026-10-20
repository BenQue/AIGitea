---
issue: 389
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/389
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 ADR 0002 裁定开发流程的路由合同与执行引擎分离并退出 VM 执行引擎，追加第二轮整改路线与平台级 E2E 验收表，属于 Agent 与平台治理决策
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-adr0002-round2-roadmap-261020.md
  spec: spec-adr0002-round2-roadmap-261020.md
  plan: plan-adr0002-round2-roadmap-261020.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/389-adr0002-round2-roadmap
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/390
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

负责人 2026-10-20 对第二轮整改的 D1–D8 全部裁决（D1 = a′：退出 VM 执行引擎，判定开发强度、决定如何开发、确定方案/计划/路线图交给技能）。这些裁决还只在项目库的计划文件里，仓内没有承载它们的 ADR，路线图停在 R8，也没有一张让后续批次共用的端到端退出条件表。本批把裁决落进仓库，作为 R10a/R10b/R10c 与 #370 的开工依据。

## 影响范围

纯文档：新增 `docs/adr/0002-deterministic-development-flow.md` 与 `docs/governance/platform-e2e-acceptance.md`；`docs/governance/remediation-roadmap.md` 追加第二轮表与退出条件；`README.md` 导航表两个入口；`AGENTS.md` 加 ADR 0002 指针（治理文件，单独 commit）。不改代码、manifest、技能、发布包成员与 VM。

## 初步方案与建议

ADR 0002 按 ADR 0001 的体例写六节，四条决定逐条对应 D1 裁决；路由卡字段与推导表写成"合同形状"，具体落点（技能内的 `route-policy.md`）与必用/禁用清单交给 R10b。路线图追加第二轮表，旧表与总规则不动。E2E 表首行用 NewEMaint #279 M1 演练的已核证据。

## 风险

ADR 一旦合并就成为 R10a 删除 Loop 代码的依据；若决定措辞与裁决有出入，后续批次会照错的写。缓解：决定一节逐字引用负责人裁决原话，Codex 只读审查逐条对照。回滚：revert 本 PR，无运行时影响。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 ADR 0002 裁定开发流程的路由合同与执行引擎分离并退出 VM 执行引擎，追加第二轮整改路线与平台级 E2E 验收表，属于 Agent 与平台治理决策
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 新 ADR 改变 Agent 执行路径与平台治理（退出 Development Loop 与 routine merge 的决定），并改 `AGENTS.md` 指针，按 `AGENTS.md`「判级与确认」属 Agent 与平台治理，强制 complex。先例：R0 #364（ADR 0001 与路线图）同判 complex。
- 全部产出是仓内文档，diff review 与 smoke 可完整复现，不声明 verification。

### 缺失的 acceptance criteria 或决策

- 无；D1–D8 已于 2026-10-20 由负责人裁决。
