---
issue: 402
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/402
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 随发布包新增项目内 aisoft 工具入口与采用批处理，改写平台技能、使用合同、项目模板、发布包合同与项目检查器，属于新增功能、Agent 与平台治理、共享核心与发布制品
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-usage-tool-entry-261021.md
  spec: spec-usage-tool-entry-261021.md
  plan: plan-usage-tool-entry-261021.md
  verification: verification-usage-tool-entry-261021.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: grill-me, to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
confidence: high
override_reason: ''
depends_on:
  - 391
  - 392
  - 395
status: approved
branch: change/402-usage-tool-entry
pr_url:
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

项目会话离开平台检出就做不了文档检查、判级投影与收尾：技能正文要求运行平台仓里的 `aisoft_loop.cli` 与
`codex/tools/*.sh`，发布包只锁文本不锁工具。HSDB、LocalWMS、SFM 三个项目还没有 pin 发布包（R11，裁决 D4）。

## 影响范围

- 新增 `codex/tools/aisoft` 与发布包工具包成员（项目内 `.aisoft/bin/aisoft` + `.aisoft/lib/`）。
- `usage-bundle.py`：`tool-provenance`、`--adopt`、发布说明与兼容级别；`aisoft-project-check.sh`：manifest 回退、
  `tool-provenance` 与 `agents-budget`。
- 技能正文、`usage/CONTRACT.md`、`templates/project/AGENTS.md`；E2E 表与路线图；发布包下一空闲版本。
- HSDB、LocalWMS、SFM 各一个采用 Issue 与 PR（项目仓）。

## 初步方案与建议

见 spec。

## 风险

- 工具包约 40 个文件进入每个项目仓，靠 `tool-provenance` 锁字节，升级只经 `--adopt`。
- 项目检查器的结果计数被测试钉死，新增两行要同步测试。
- 版本号可能与并行批次撞号，后合并者以 merge commit 集成并改发下一版本，项目 PR 随之重跑 `--adopt`。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 随发布包新增项目内 aisoft 工具入口与采用批处理，改写平台技能、使用合同、项目模板、发布包合同与项目检查器，属于新增功能、Agent 与平台治理、共享核心与发布制品
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 新增会话工具与 `--adopt` 是功能新增（`contract_effect: add`）；技能与使用合同是 Agent 行为与平台治理。
- 发布包合同与项目检查器被所有项目共用，是共享核心；工具包随发布包分发，是制品。
- 验收含无平台检出环境的真实会话动作与三个项目的采用读回，不能只由 diff review 与 required CI 重放，所以欠 `verification`。

### 缺失的 acceptance criteria 或决策

- 无；spec「未决问题」的四项实现选择在确认点 1 一并确认。
