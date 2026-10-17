---
issue: 366
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/366
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 重写AGENTS.md并从技能与治理文档移出单票合同，属于Agent和平台治理变更
risk_flags:
  - agent-governance
  - cross-module
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-agents-contract-slim-261017.md
  spec: spec-agents-contract-slim-261017.md
  plan: plan-agents-contract-slim-261017.md
confidence: high
override_reason: ''
depends_on:
  - 364
status: pr-open
branch: change/366-agents-contract-slim
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/367
created: 2026-10-17
updated: 2026-10-17
---

## 问题/需求总结

整改路线 R1。`AGENTS.md` 13,036 字节，已关闭的 #327 的单票合同复制在 13 个治理与文档文件里，违反 ADR 0001 D9。本票把 `AGENTS.md` 重写为不超过 5 KB 的维护层规则，移出单票合同，加入 ADR D4 准入问题，并修复 macOS 上 #360 canonical 测试的既有失败。

## 影响范围

`AGENTS.md`、五份技能、`docs/agents/` 与模板、`03`/`04`/`06`/`08`/`README.md`、一份 reference、三个 runtime 测试文件、`smoke.sh` 注释、整改路线。不改 runtime 产品代码、broker、CI、installer、manifest。

## 初步方案与建议

见 mapped spec 的迁移对照表与 ticket。

## 风险

技能源变化后，本机已安装的技能会和源码漂移，需要负责人在 R5 重装。删段落可能误删仍有效的规则，由迁移对照表逐条核对。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 重写AGENTS.md并从技能与治理文档移出单票合同，属于Agent和平台治理变更
risk_flags:
  - agent-governance
  - cross-module
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- AGENTS.md：Agent 或平台治理变更一律 complex；跨技能、文档与测试多模块。
- 证据可由 diff review 与 required CI 复现，不声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。
