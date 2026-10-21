---
issue: 395
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/395
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把路由合同落成技能内唯一一张路由表并让 summary 携带路由卡，改动平台技能、change 模板、front matter 合同校验与发布包，属于 Agent 与平台治理及共享核心
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
  summary: summary-route-card-261020.md
  spec: spec-route-card-261020.md
  plan: plan-route-card-261020.md
  verification: verification-route-card-261020.md
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
override_reason: ''
depends_on:
  - 389
  - 391
  - 392
status: approved
branch: change/395-route-card
pr_url:
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

ADR 0002 D1 把路由合同定为产品：每条 Issue 的开发方式由确定性的路由卡给出，由技能承载。R9 只定了字段和推导表的形状，逐格取值、必用与禁用清单、summary 怎么携带、确认点 1 与派单怎么展示都还没有落地；现在每个会话靠记忆规则（例如「派单卡片用 Opus 5 high」）各自决定档位与技能。

## 影响范围

- 新增 `skills/aisoft-platform/references/route-policy.md`（唯一路由表），`aisoft-platform` 与 `issue-session-flow` 两个技能加路由节与候选/派单字段。
- `templates/docs/changes/_template/summary.md` 加 `route:` 块；`codex/runtime/aisoft_loop/contract.py` 的 front matter 解析接受 `route` 映射并校验取值闭集（`check-change-documents` 由此覆盖）。
- `03` §2、`08` §5 与 §7、路线图 R10b 行；smoke 结构守卫；发布包 1.6.0（1.5.0 已被 R13 占用）。
- #392 verification 的 Cursor 一行更正记在本票 verification（broker 不允许改别的 Issue 目录）。

## 初步方案与建议

见 spec。

## 风险

- front matter 解析是共享核心：改错会让全部 change 的文档检查变红。用全量 `check-change-documents` 与既有测试兜底。
- broker 用列 0 锚定的正则读 summary 与 `^  spec: `，`route` 子键避开 `spec` 即不受影响，不改 broker、不需要两台重装。
- 模板改动要同步刷新 `change-template-sync.json` 的 digest。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把路由合同落成技能内唯一一张路由表并让 summary 携带路由卡，改动平台技能、change 模板、front matter 合同校验与发布包，属于 Agent 与平台治理及共享核心
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

- 改 `skills/` 与 `03`/`08` 是 Agent 行为与平台治理（AGENTS.md「判级与确认」）。
- 改 `contract.py` 的 front matter 解析是共享核心；模板与技能是发布包成员。
- 验收含 Codex 侧查表与 fresh 会话读回，不能只由 diff review 与 required CI 复现，所以欠 `verification`。

### 缺失的 acceptance criteria 或决策

- 无；spec 的两项实现选择在确认点 1 一并确认。
