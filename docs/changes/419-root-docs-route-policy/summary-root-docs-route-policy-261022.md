---
issue: 419
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/419
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 根目录介绍文档未随 R10b 路由表更新，改 AGENTS.md 属于 Agent 与平台治理，按规则强制 complex；只把文档恢复到已合并的路由合同，不新增规则
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-root-docs-route-policy-261022.md
  spec: spec-root-docs-route-policy-261022.md
  plan: plan-root-docs-route-policy-261022.md
  verification: verification-root-docs-route-policy-261022.md
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
depends_on: []
status: pr-open
branch: change/419-root-docs-route-policy
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/421
created: 2026-10-22
updated: 2026-10-22
---

## 问题/需求总结

第二轮治理收口后（`c373f407`，发布包 1.12.0）只读核对仓库根目录介绍文档：README、GLOSSARY、CLAUDE.md 与现行合同一致，
唯独三处没跟上 R10b 的路由表。AGENTS.md「开发编排」把 `$implement #N Txx` 写成唯一的按计划执行入口，没有指向路由表；
README 导航缺路由表一行，08 的导航名与标题不一致，§8 Matt 残余项措辞需按现有证据复核。负责人 2026-10-22 选定范围 A：只修根目录文档。

## 影响范围

`AGENTS.md`、`README.md`，以及本批治理表的两行（`docs/governance/remediation-roadmap.md`、`docs/governance/review-evidence-index.md`）。
不动 `skills/`、`usage/`、`templates/`，发布包版本不变。

## 初步方案与建议

AGENTS.md 一句改为「开发方式以路由表为准」，按路由表写出 Claude/Cursor 与 Codex 的按计划执行入口，保留 smoke 钉住的字面量，压在 5 KB 内。
README §4 给「路由表」加链接，§5 增加路由表一行并把 08 显示名对齐标题，§8 Matt 残余项改成只列尚无证据的部分。

## 风险

AGENTS.md 只剩约 260 B 余量，措辞须精简；smoke 用 `grep -Fq` 钉住 AGENTS.md 多个字面量，改写时必须保留。
范围外的技能、使用合同与项目模板仍写旧句，短期内与根目录不一致，由范围 B 另行处理。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 根目录介绍文档未随 R10b 路由表更新，改 AGENTS.md 属于 Agent 与平台治理，按规则强制 complex；只把文档恢复到已合并的路由合同，不新增规则
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- AGENTS.md「判级与确认」：Agent 与平台治理一律 complex；「治理文件」：只有 complex spec 明确授权才能改 AGENTS.md。
- `agent-governance` 是路由表高风险 flag，命中推导表 R3；平台仓非安全类，不适用 S1。
- 平台仓 complex 的交叉审查结论必须写进映射 verification（`03` §7「交叉审核」），因此声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无；范围已由负责人选定为 A。
