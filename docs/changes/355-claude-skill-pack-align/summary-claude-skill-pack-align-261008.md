---
issue: 355
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/355
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增平台自有的 Claude marketplace 条目与插件 pin 检查，并改变 Claude 侧 Agent 行为规则，属于外部契约与 Agent 治理变更，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-claude-skill-pack-align-261008.md
  spec: spec-claude-skill-pack-align-261008.md
  plan: plan-claude-skill-pack-align-261008.md
  verification: verification-claude-skill-pack-align-261008.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/355-claude-skill-pack-align
pr_url:
created: 2026-10-08
updated: 2026-10-08
---

## 问题/需求总结

#352 把 Codex 侧 Matt 快照升到 v1.3.1（`24fe0ef7737efae15c87225755e9f6f5965e4888`）并写明四条
v1.3.1 边界规则，但明确「不修改 Claude-owned plugin」。Claude 侧因此留下三处 source 层缺口：

1. **来源未固定**：Claude 的 Matt 插件来自官方 marketplace，平台对它钉哪个 commit 没有发言权，
   也没有任何检查能回答「已装插件是不是平台期望的那个 commit」。
2. **边界规则缺席**：`pr` / `implement-spec` / `retro` / GLOSSARY-CONTEXT 四条规则只写在
   `codex/skills/aisoft-matt-workflow/SKILL.md`；`skill-for-claude/aisoft-platform/SKILL.md` 还引用了
   `$aisoft-matt-workflow`，而 Claude 侧 `skills.manifest` 根本不装这个技能。
3. **superpowers 无映射**：平台现行文档没有一处说明 superpowers 的默认落点与收尾菜单如何服从
   平台合同。

本票只补 source 层。实际插件升级与两 provider fresh-session 验收属于 #354。

**范围追加（2026-10-08）**：合同确认后，用户追加第 4 项——外部技能包升级后的人工适配检查清单，
并在本会话再次确认并入本票（Issue 正文已同步范围第 4 项与 AC-8）。它不改变判级：仍是 source 层的
文档与技能文本，不新增定时任务、自动检查工具或安装动作。

## 影响范围

- 新增：仓库根 `.claude-plugin/marketplace.json`；`skill-for-claude/check-plugin-pin.sh` 与
  `check-plugin-pin.py`；`codex/tests/test-claude-plugin-pin.sh`。
- 修改：`skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `.gitignore`、`codex/tests/smoke.sh`、`README.md`、`08-双工具共存与实施.md`；范围追加后另含
  `skill-for-codex/SKILL.md`（仅一段指向清单的入口）。
- 不动：`AGENTS.md`、`codex/skills/**`、`codex/vendor/**`、`codex/install-skills.sh`、
  `skill-for-claude/skills.manifest`、`skill-for-claude/install.sh`、`skill-for-claude/check-drift.sh`、
  `codex/tools/check-installed-drift.*`、Controller、broker、main protection、required CI。

## 初步方案与建议

见映射的 spec。三个需要在合同里定死的选择：

- marketplace 放在仓库根：只有这个位置同时支持按目录与按 git URL 注册。
- 四条规则与 superpowers 映射内联进 `aisoft-platform` 技能，不新装 adapter 技能。
- 插件 pin 检查是独立工具，不并入现有 `check-drift.sh`，也不进入八安装面检查。

## 风险

- 已装插件的 commit 只记录在 Claude Code 的内部文件 `installed_plugins.json` 里，格式没有公开
  承诺。检查对不认识的 schema 一律 fail closed，不判 CLEAN。
- 检查落地后，本机在 #354 执行前会如实读出非 CLEAN；这是期望行为，不是回归。
- `AGENTS.md` 的目录描述不会提到新增的两个入口；导航由 README 与 08 承担。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增平台自有的 Claude marketplace 条目与插件 pin 检查，并改变 Claude 侧 Agent 行为规则，属于外部契约与 Agent 治理变更，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type=platform` 与 `contract_effect=add` 各自独立强制 complex
  （`codex/runtime/aisoft_loop/classification.py` 的 `FORCED_COMPLEX_TYPES` 与 `contract_effect` 规则）。
- marketplace 条目是 Claude Code 读取的外部契约（`external-contract`）；Claude 侧技能文本是安装为
  Agent 行为的治理文件，位于 `smoke.sh` 的 `governance_set`（`agent-governance`、`platform-governance`）。
- 仓库 `aisoft-platform` 的 `routine_auto_merge_enabled=false`，且平台治理变更固定 manual。
- 声明 `verification`：`claude plugin validate` 的本机结果、改动前本机已装插件的基线读回，
  required CI 都无法重放（`03` §3「何时声明 `verification`」第二行）。
- 2026-10-08 本会话只读复核 Issue 正文的盘点：vendor manifest `commit` 为
  `24fe0ef7737efae15c87225755e9f6f5965e4888`；官方 marketplace 的 Matt 条目 `sha` 为
  `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`；本机已装记录为
  `mattpocock-skills@claude-plugins-official` 1.2.3，`gitCommitSha`
  `2ab958093e83e0ec752e6c1c5932da465bf23e0c`；上游该 pin 的 `plugin.json` 版本为 `1.3.1`；
  `skill-for-claude/` 下以 `$` 记法出现的技能名共 5 个，其中仅 `$aisoft-matt-workflow` 不在 vendor
  manifest 的技能集合内。

### 缺失的 acceptance criteria 或决策

- 无。Issue 留给 spec 的「二选一」已在 spec 的「设计决定」中定案。
