---
issue: 425
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/425
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/425-review-principles
created: 2026-10-22
updated: 2026-10-23
reason: 补充跨提供者共享工程原则中的审查思想，命中 Agent 和平台治理强制 complex；不改变具体流程。
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-review-principles-261022.md
  spec: spec-review-principles-261022.md
  plan: plan-review-principles-261022.md
  verification: verification-review-principles-261022.md
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider
  confirm: 2
override_reason: ''
status: pr-open
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/426
---

# Summary：共享工程原则的审查思想

## 问题与授权

负责人希望从 Anthropic 的代码审查文章获取启发，写入纲领性文件，并要求 Claude Code 评价审议。负责人随后明确：只补充审查思想，具体流程仍应结合平台与项目情况。
2026-10-22 已就收紧后的文案完成 Codex / Claude Code 讨论，Claude Code 最终 `VERDICT: ACCEPT`。负责人进一步明确：“同意，按这版文案写入《共享工程原则》，只补充审查思想，不修改现有具体流程，按平台现有治理要求推进。”本次确认覆盖本 Issue 精确文案实施、必要的发布登记与既有治理验证，不重复询问启动。负责人随后明确指定 Claude Code 评议使用 Fable 5、high；本 Issue 后续审议调用按此执行，作为调用参数记录，不修改共享路由或全局配置。2026-10-23 负责人明确“确认提交 #425 的唯一最终 PR，按现有治理要求推进，CI 全绿后停在待人工合并”，确认点 2 已通过；授权本分支普通推送、唯一最终 PR 及合同内 CI 修复，合并、安装、项目采用与部署仍不在授权内。

## 影响范围

唯一思想正文为现有 `skills/aisoft-platform/references/engineering-principles.md`；追加五条审查思想与 Anthropic 来源，保留原有引言及四部分。
沿用现有技能入口和三端分发路径；成员内容变化只追加 usage bundle minor 候选 1.15.0。其余修改仅为本 Issue 四份语义文档、冻结 patch 与本 Issue 审议索引行；精确路径见 mapped spec 的 `git_scope`。
不修改具体流程、根 Agent 文件、runtime、tests、CI 或安装器，不产生安装或项目采用事件。

## 当前状态

合同与启动已批准，T01/T02 已完成。完整 smoke 与三端隔离导出实跑于正文/包提交 `6550228fc2c239f860bcd923638687f43648ee10`，之后仅规范提案格式与归档证据，正文及 bundle 未变。R1/R2 的导航摘要分歧与处置保留为历史；按负责人指定，以 Fable 5 / high 对当前候选 `cfc13a64cefe1b82864a1fb75729f8d362c65ebf` 重新作 R3 独立审议，Standards 与 Spec 均 PASS，F1–F3 处置获独立认可、无新增发现。当前审议依据为 R3，详见 verification。负责人已确认提交唯一最终 PR，本分支进入 PR 发布与 CI 验收；唯一 PR 地址以 front matter 的 `pr_url` 为准，required `CI / verify (pull_request)` 按该 PR 最新 exact head 另行读回，全绿后停在 `READY_FOR_REVIEW` 等待人工合并。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 补充跨提供者共享工程原则中的审查思想，命中 Agent 和平台治理强制 complex；不改变具体流程。
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

任意已注册项目都可参考这些原则，符合平台共享能力边界。虽然只有文档，Agent 和平台治理触发 complex；平台默认 production，采用 R3 路由及既有两个确认点。

### 缺失的 acceptance criteria 或决策

无。文案与范围已批准；2026-10-23 确认点 2 已通过，CI 全绿后等待人工合并。
