---
issue: 438
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
status: pending
branch: change/438-skill-frontmatter-yaml
created: 2026-11-03
updated: 2026-11-03
---

# 验证记录：技能 frontmatter 严格 YAML

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `7bd38270`
- 环境: Mac（Ruby Psych 后端，无 PyYAML）；OrbStack VM `gitea-ci`（PyYAML 6.0.3 后端，系统包 `python3-yaml`）
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前用 Ruby Psych 解析 8 个技能 frontmatter | 1 FAIL / 7 OK | `skills/aisoft-platform/SKILL.md: mapping values are not allowed in this context at line 3 column 262`；其余 7 个 OK |

命令与输出照实抄。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待填写 |
| AC-2 | NOT RUN | 待填写 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |
| AC-5 | NOT RUN | 待填写 |
| AC-6 | NOT RUN | 待填写 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex | 待填写 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 待填写。
