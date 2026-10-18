---
issue: 375
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/375
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增只读版本核对工具并调整两侧平台技能对外部技能包的约束，属于 Agent 与平台治理
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-skills-update-261018.md
  spec: spec-skills-update-261018.md
  plan: plan-skills-update-261018.md
  verification: verification-skills-update-261018.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/375-skills-update
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/376
created: 2026-10-18
updated: 2026-10-18
---

## 问题/需求总结

整改路线 R5。superpowers 已升到 7.0.0，Claude 侧插件在适配核对之前就随官方 marketplace 自动更新了；Codex 侧实际生效版本没人核实过；R1/R3/R4 改了技能源，本机已装的两侧平台技能已漂移；CLI 升级后 `08` §7 的 provider 验收矩阵没有重跑。本票补做 superpowers 适配核对、按结论调整两侧平台技能、新增只读版本核对脚本，并记录本机矩阵与重装结果。

## 影响范围

`08` §5（superpowers 映射表与 6.4.2 → 7.0.0 适配示例）、两侧平台技能 `aisoft-platform` 的外部技能包段落、新增 `codex/tools/check-external-skill-versions.sh` 与其 Python 实现、适配记录 `codex/config/external-skill-adaptation.json`、新测试与 smoke 登记、整改路线 R4/R5 两行。

## 初步方案与建议

见 mapped spec。要点：适配核对四项中三项无影响，第 2 项（brainstorming 先定级、可在聊天内批准小改动或直接做快速任务）需要在两侧平台技能写明它不替代平台判级与 `approved`；版本核对脚本只读本机文件和两个 CLI 的 `--version`，与适配记录比较，落后时报 `REVIEW_NEEDED`。

## 风险

技能源改动会让本机已装技能继续漂移，合并后须由负责人重装两侧技能并用 `check-installed-drift.sh` 读回；脚本读的是 Claude Code 与 Codex 的本机文件格式，格式变化时只会报 `UNKNOWN`，不会误报通过。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增只读版本核对工具并调整两侧平台技能对外部技能包的约束，属于 Agent 与平台治理
risk_flags:
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

- 新增工具（新增功能）并修改两侧平台技能的行为约束（Agent 与平台治理），按 `AGENTS.md` 判级规则强制 complex。
- 适配核对的依据是本机已装插件文件与 Codex 模型可见技能列表，provider 矩阵与重装读回也只在本机成立，required CI 无法复现，所以声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。Codex 侧是否启用或升级 superpowers 属于负责人的本机配置，本票只报告事实（见 spec 非目标）。
