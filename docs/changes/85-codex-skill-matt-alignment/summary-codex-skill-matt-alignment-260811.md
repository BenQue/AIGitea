---
issue: 85
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/85
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把复合技能 skill-for-codex 的开发合同对齐到 #57/#60/#75 现行状态（Matt 主路径、readable 命名、24 标签），消除第二套主流程
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-codex-skill-matt-alignment-260811.md
  spec: spec-codex-skill-matt-alignment-260811.md
  plan: plan-codex-skill-matt-alignment-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/85-codex-skill-matt-alignment
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/86
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

`skill-for-codex/SKILL.md` 与 onboarding runbook 仍描述 #57/#60/#75 之前的合同：gitea-* 为主
路由、`change/N` 与 `00-summary.md` 数字命名、八标签无 triage 维度、复制已改名的数字模板。
与 AGENTS.md / global-AGENTS.md 现行合同冲突，即 #60 预警的「两套主流程」。

## 影响范围

`skill-for-codex/SKILL.md`、`skill-for-codex/references/onboarding-runbook.md` 两个文件。
governance manifest gate、legacy ci-bot gate、host-role gate、architecture onboarding、
private-gitea-access 参考等章节语义不变。

## 初步方案与建议

绑定模型改 readable 元组 + `documents` 映射 + `resolve-documents` CLI；标签补 triage 维度
（manifest 共 24）；技能路由改「Matt 主路径（$aisoft-matt-workflow + $triage/$to-spec/
$to-tickets/$implement）+ gitea-* 兼容 adapter + gitea-platform-ops 独立」；runbook 模板清单
实名化并补 Matt 初始化条目；残余数字名全部限定为 pre-#57 legacy 读取兼容。

## 风险

- smoke 对两文件有精确字符串断言，须逐一保留（已列入 AC-5 并验证）。
- 表述若含糊会再次形成双主流程；措辞与 AGENTS.md §初始化与开发编排逐条对应。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把复合技能 skill-for-codex 的开发合同对齐到 #57/#60/#75 现行状态（Matt 主路径、readable 命名、24 标签），消除第二套主流程
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 修改 Agent 行为合同文档，命中「Agent/平台治理变更一律 complex」强制规则。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| AC-1 Matt 主路径 + gitea-* adapter 语义 | PASS | SKILL.md 同段含 `$aisoft-matt-workflow` 与四步路径；adapter 段落明示 compatibility |
| AC-2 数字名仅 legacy 语境 | PASS | `rg '00-summary\|01-spec\|02-plan\|03-verification'` 命中行均含 legacy/pre-#57/兼容 限定（残余 0） |
| AC-3 triage 维度 / 24-label | PASS | 两文件各含 24-label 表述与 `triage/ready-for-agent` ≠ `approved` |
| AC-4 模板清单实名 | PASS | 与 `templates/docs/changes/_template/{summary,spec,plan,verification}.md` 逐一对应 |
| AC-5 smoke 断言串保留 | PASS | ``private-repository `404` ``、`AISOFT_ONBOARDING_MODE=software-repository`、`ensure-gitea-collaborator.sh`、`gitea-governance.json` 各 ≥1 |
| AC-6 `bash codex/tests/smoke.sh` | PASS（叠加 #82 修复验证） | 按 #77 先例临时叠加 PR #83 单行修复后全套通过（325 tests OK + 静态检查），随后还原并确认 worktree 干净 |
| 远端 CI / 人工合并 | NOT RUN | 平台仓库当前无 required CI context；等待人工合并 |
