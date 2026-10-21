---
issue: 408
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/408
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增三端最小能力集读回、审查证据索引与轮换规则、一步建 PR 子命令，并收敛 approval 记录与 broker 推送闸门的 spec 状态检查，属于新增功能、Agent 与平台治理、共享核心与发布制品
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
  summary: summary-peer-review-evidence-261021.md
  spec: spec-peer-review-evidence-261021.md
  plan: plan-peer-review-evidence-261021.md
  verification: verification-peer-review-evidence-261021.md
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
  - 392
  - 402
status: spec-review
branch: change/408-peer-review-evidence
pr_url:
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

第二轮整改 R15（复审 P1-5、P2-3、P2-7）。「Claude 与 Codex 对等」目前读不回：没有一张三端能力表，也没有一条命令能说清
每端缺什么。交叉审查证据散在各 verification 里，格式不一，R0–R3 没有记录，R5–R6b 缺首轮 head。Cursor 在使用层从没
真实跑过一个 Issue。每批还有确认点 1 改三份文档 `status` 的提交和建 PR 后手工回填 URL 的提交。

## 影响范围

- `08` §7.1 最小能力集表；`codex/tools/check-external-skill-versions.py` 增加每端一行能力结论。
- verification 模板的固定「交叉审查」表；新建 `docs/governance/review-evidence-index.md`；`03` §7 审查方与记录规则。
- approval 只写 summary：spec/plan 模板去掉 `status`，broker 推送闸门 `aisoft_main_integration.py` 不再读 spec 状态。
- 会话工具新增 `aisoft open-pr`（首推、建 PR、回填、提交、再推一步完成）；技能与使用合同改写对应步骤。
- SFM 一个项目侧 small Issue 由 Cursor 会话走完；E2E 表加「工具」列。
- 发布包下一空闲版本（预计 1.9.0）；change 模板 digest 刷新与下游同步清单。

## 初步方案与建议

见 spec。

## 风险

- broker 推送闸门放宽一项检查，属共享核心；合并后要两台重装 broker 才生效，未重装前旧闸门仍要求 spec `approved`，新文档会被拒。
- 模板改动让所有 holder 的 `change-templates` 对照最新版本变红，pin 了发布包的项目不受影响。
- 与并行的 R12 都碰 change 文档合同；版本号可能撞号，后合并者以 merge commit 集成并改发下一版本。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增三端最小能力集读回、审查证据索引与轮换规则、一步建 PR 子命令，并收敛 approval 记录与 broker 推送闸门的 spec 状态检查，属于新增功能、Agent 与平台治理、共享核心与发布制品
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

- 能力读回与 `aisoft open-pr` 是新增功能（`contract_effect: add`）；`03`/`08`、技能与审查规则是 Agent 行为与平台治理。
- broker 推送闸门与会话工具被所有项目共用，是共享核心；模板与工具随发布包分发，是制品。
- 验收含 installed 层三端读回与一次 Cursor 真实会话，不能只靠 diff review 与 required CI 重放，所以欠 `verification`。

### 缺失的 acceptance criteria 或决策

- spec「未决问题」四项在确认点 1 由负责人决定，其中第 1 项（反向审查批次）与原计划 D7 冲突，必须由人定。
