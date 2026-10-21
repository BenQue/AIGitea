---
issue: 403
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/403
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 分册改现行合同体并改写 smoke 闸门与 readiness 工具，属平台治理与 CI 变更
risk_flags:
  - platform-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-docs-current-contract-261021.md
  spec: spec-docs-current-contract-261021.md
  plan: plan-docs-current-contract-261021.md
  verification: verification-docs-current-contract-261021.md
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
  - 391
  - 395
  - 396
status: pr-open
branch: change/403-docs-current-contract
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/404
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

第二轮整改 R14：01–08 与 README 仍是变更日志体，规则与 Issue 叙事、过时状态、手写日期版本混排；smoke 与单测逐字钉正文。本票把分册改成「现行合同 + 来历」体例，README 状态改由 `aisoft-platform-readiness.sh --render-readme` 生成，smoke 正文钉子改钉小节标题并设 `grep -Fq` 棘轮，收紧 R13 遗留的文档站点值基线。合同见映射 spec。

## 影响范围

01–08、README、GLOSSARY、12/13 与 `architecture/README.md` 的站点值、`codex/tests/smoke.sh` 与新棘轮基线、`aisoft-platform-readiness.sh` 及其测试、`test_architecture_governance.py`、泄漏基线、路线图。技能、模板与 `usage/` 不变。

## 初步方案与建议

见 spec「范围」与 plan 的 Ticket graph。

## 风险

删段落时误删现行规则；由 Codex 对照改写前原文逐节核对。与并行批次在 smoke 计数、`06`、`01` 上冲突时以 merge commit 集成 main 并从 `origin/main` 重建冲突块。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 分册改现行合同体并改写 smoke 闸门与 readiness 工具，属平台治理与 CI 变更
risk_flags:
  - platform-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改 `codex/tests/smoke.sh`（平台 required CI）与平台治理分册，按 AGENTS.md「CI/制品/部署/回滚、Agent 与平台治理一律 complex」。
- 验收含反向证明与 Codex 只读审查，证据不能全部由 diff review 与 required CI 重放，因此声明 `verification`。
- 路由：R3（complex、production、含高风险 flag `platform-governance`、`ci-change`）。

### 缺失的 acceptance criteria 或决策

- 无；三处实现选择已在确认点 1 由负责人确认（2026-10-21）。
