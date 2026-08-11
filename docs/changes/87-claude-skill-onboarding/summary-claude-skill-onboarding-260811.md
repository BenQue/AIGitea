---
issue: 87
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/87
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 把 Claude 侧 aisoft-platform 技能纳入版本控制并提供确定性安装/漂移检查，消除双 provider 技能部署脱节（审核 P0）
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-claude-skill-onboarding-260811.md
  spec: spec-claude-skill-onboarding-260811.md
  plan: plan-claude-skill-onboarding-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/87-claude-skill-onboarding
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

Claude 侧技能停在 2026-07-22 且无入库源：其接入手册仍教已被 host-role guard 拒绝的
PM2-on-gitea-ci 流程、16 标签、数字命名。根因是「技能改了没人负责重装、Claude 版无单一
事实源」。

## 影响范围

新增 `skill-for-claude/`（SKILL.md + install.sh + check-drift.sh）、
`codex/tests/test-install-claude-skills.sh`；`codex/tests/smoke.sh` 增两行接入。
references 由安装器从 `skill-for-codex/references/` 单源拷贝，不产生第二份合同文本。

## 初步方案与建议

见 spec。合并后部署（人工或授权会话执行）：
`bash skill-for-claude/install.sh` → `bash skill-for-claude/check-drift.sh` 输出 `CLEAN`；
此后每次合并涉及技能的 PR 都以 `check-drift.sh` 复核两端一致。

## 风险

- Claude 版正文若与 AGENTS.md 漂移会重演双合同——正文逐条对应现行合同并靠 smoke
  串断言保底（后续可加断言）。
- 旧 `~/.claude/skills/aisoft-platform` 会被覆盖——安装前可自行备份；本 PR 不执行安装。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 把 Claude 侧 aisoft-platform 技能纳入版本控制并提供确定性安装/漂移检查，消除双 provider 技能部署脱节（审核 P0）
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

- 新增 Agent 行为合同与安装工具，命中「Agent/平台治理变更一律 complex」。

### 缺失的 acceptance criteria 或决策

- Matt skills 完整装入 Claude harness（与用户手装插件 1.2.3 的版本/命名冲突取舍）为
  显式非目标，留独立决策。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| AC-1 SKILL.md 关键串 | PASS | 触发词含 8 个治理项目名；正文含 readable 元组、$triage 四步、24 标签、broker、单闸门、分工节 |
| AC-2/AC-3 安装器与漂移检查 | PASS | tmp HOME 实测:未装→NOT_INSTALLED(exit 0)、装后→CLEAN、双次幂等 |
| AC-4 测试接入 | PASS | `claude skill install tests passed`；smoke 含新调用 |
| AC-5 smoke | PASS（叠加 #82 修复验证） | 按 #77 先例临时叠加 PR #83 单行修复后全套通过，随后还原、worktree 干净 |
| AC-6 未向真实 ~/.claude 安装 | PASS | 本分支只含仓库文件；实际安装留待合并后执行 |
| 远端 CI / 人工合并 | NOT RUN | 平台仓库当前无 required CI context；等待人工合并 |
