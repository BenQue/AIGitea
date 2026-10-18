---
issue: 379
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/379
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 技能源合并为单一来源并改写两侧安装器与漂移检查，新增 Cursor 使用层落点与发布包版本，写入交叉审核固定步骤，属于 Agent 与平台治理及共享核心
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-skills-single-source-261018.md
  spec: spec-skills-single-source-261018.md
  plan: plan-skills-single-source-261018.md
  verification: verification-skills-single-source-261018.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/379-skills-single-source
pr_url:
created: 2026-10-18
updated: 2026-10-18
---

## 问题/需求总结

整改路线 R7（ADR 0001 D5、D6、D8）。平台自定义技能分三处维护：`skill-for-claude/`（两个技能，中文）、`skill-for-codex/`（`aisoft-platform` 与共享 references，英文）、`codex/skills/`（七个技能，英文）。`aisoft-platform` 与 `issue-session-flow` 各有两份内容已分叉的正文。仓库对 Cursor 零支持；本机 Cursor 插件缓存里的 Matt 与 superpowers 不在任何版本核对之内。交叉审核只在 `AGENTS.md` 有一句，没有固定步骤和记录位置。

## 影响范围

新增顶层 `skills/`（唯一技能源与声明）；改写 `codex/install-skills.sh`、`skill-for-claude/install.sh`、两份 `check-drift.sh`、`check-installed-drift.py`、外部技能版本核对脚本与对应测试；`usage/bundle.json` 成员路径、Cursor 薄指针成员与 `--build` 的三种项目级落点，切 1.1.0；`03`、`08`、README、project-align 与 runbook 文档；smoke 的技能路径与守卫。删除 `skill-for-codex/`、`codex/skills/` 与 `skill-for-claude/*/SKILL.md` 中的旧正文。

## 初步方案与建议

见 mapped spec。

## 风险

技能正文合并可能丢失某一侧独有的规则；用逐条对照表与 smoke 现有短语守卫兜底，由 Codex 独立审查。路径迁移面广（smoke 约 40 处、测试与文档），与并行的 R6b 共享 smoke 与泄漏基线，后合并者 rebase。合并后两侧需重装，旧安装目录名不变。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 技能源合并为单一来源并改写两侧安装器与漂移检查，新增 Cursor 使用层落点与发布包版本，写入交叉审核固定步骤，属于 Agent 与平台治理及共享核心
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- AGENTS.md：Agent 与平台治理、共享核心、installer 一律 complex。
- 安装器、漂移检查与发布包都会改变行为，不是恢复既有合同。
- 需要 verification：安装读回与 Cursor 本机核对依赖本机状态，CI 无法重放。

### 缺失的 acceptance criteria 或决策

- 无；默认选择写在 spec，确认点 1 一并确认。
