---
issue: 412
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/412
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把第二轮路线图与 E2E 验收表回写到 Gitea 已合并的事实，并在 03 与 AGENTS.md 新增治理表回写规则，属于 Agent 与平台治理流程变更
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-governance-table-writeback-261021.md
  spec: spec-governance-table-writeback-261021.md
  plan: plan-governance-table-writeback-261021.md
  verification: verification-governance-table-writeback-261021.md
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
status: approved
branch: change/412-governance-table-writeback
pr_url:
created: 2026-10-21
updated: 2026-10-21
---

## 问题/需求总结

第二轮终审 §5 第 1 项。路线图第二轮 11 行里 10 行仍写「进行中」或「未开工」，Gitea 上全部已合并；E2E 验收表缺
NewEMaint #313 的 test 数据库恢复演练，三行采用记录停在「合并后在 main 上读回」。「状态列靠下一批顺手改」两轮都失灵，
本批把表格回写到事实，并把回写定为每批自己 PR 里的固定步骤。合同见映射 spec。

## 影响范围

- `docs/governance/remediation-roadmap.md`：第二轮各行状态、推荐顺序下的现状说明、「用法」一行。
- `docs/governance/platform-e2e-acceptance.md`：验收记录加 NewEMaint #313 行，采用记录换成 main 上的读回，「用法」一行。
- `03-Issue-Spec-Plan与单闸门开发流程.md` §7 新增「治理表回写（平台仓）」小节与来历行；`AGENTS.md` 一行指针。
- `codex/tests/smoke.sh` 加一个 `require_heading` 钉住新小节（不加 `grep -Fq`，棘轮基线不变）。
- 不改技能、runtime、broker、模板与 `usage/`，不发使用层新版本，合并后无需重装。

## 初步方案与建议

回写规则选「同 PR 预写」：平台批次在本批 PR 里把自己的路线图行写成合并后状态（`已完成（#N，发布包 X）`），E2E 行同理；
行与代码同一次 merge 进入 `main`，PR 不合并时行也不会出现。收尾时读回 `origin/main` 上这一行。不选「收尾小提交」，因为
受保护 `main` 不允许直推，收尾小提交要再开一个 Issue 和 PR。规则写在 `03`（维护层合同）与 `AGENTS.md`（两端会话都自动加载），
不写进 `issue-session-flow` 技能：技能是发布包成员，改它要发新版本并与并行批次抢 1.11.0，而这条规则只约束平台仓。

## 风险

- 并行批次也改路线图表格，rebase 时表格冲突块不能整块取一侧，要从 `origin/main` 重建。
- 规则只写在文档里，仍靠会话遵守；收尾读回是唯一的确定性核对。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把第二轮路线图与 E2E 验收表回写到 Gitea 已合并的事实，并在 03 与 AGENTS.md 新增治理表回写规则，属于 Agent 与平台治理流程变更
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

- 修改 `AGENTS.md` 与 `03` 的流程合同：AGENTS.md「判级与确认」把 Agent 与平台治理列为强制 complex，且只有 complex spec 能授权改 `AGENTS.md`。
- 表格回写本身是恢复文档与事实一致，单独看是 small；与规则同批后整体按 complex。
- 验收证据来自 Gitea PR 读回与各项目 `main` 上的 `aisoft bundle status`，不能由 diff review 与 required CI 重放，因此声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。
