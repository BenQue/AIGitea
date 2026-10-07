---
issue: 355
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/355
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
depends_on: []
status: pending
branch: change/355-claude-skill-pack-align
created: 2026-10-08
updated: 2026-10-08
---

# Verification · Claude 侧外部技能包对齐

## 基线与范围

- Commit SHA: 待实现后填写
- 基线：`origin/main` = `8162fe7`（合同起草时；建 worktree 前经 broker fresh fetch 后以读回为准）
- 环境: Mac 交互会话，Claude Code 2.1.228；本记录不含任何 installed 或 provider-session 验收
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-7

### 改动前基线（2026-10-08，本机只读）

| 观测 | 结果 |
|---|---|
| `codex/vendor/mattpocock/v1.3.1/manifest.json` 的 `commit` | `24fe0ef7737efae15c87225755e9f6f5965e4888` |
| 官方 marketplace 的 `mattpocock-skills` 条目 `sha` | `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` |
| 本机 `installed_plugins.json` 的 Matt 记录 | `mattpocock-skills@claude-plugins-official`，user 与 project 两条，版本 `1.2.3`，`gitCommitSha` `2ab958093e83e0ec752e6c1c5932da465bf23e0c` |
| 上游 pin commit 的 `.claude-plugin/plugin.json` 版本（公开读取） | `1.3.1` |
| `claude plugin list --json` 是否暴露 commit | 否，仅 `id`、`version`、`scope`、`enabled` 与时间戳 |
| `skill-for-claude/` 中 `$` 记法的技能名 | `$triage`、`$to-spec`、`$to-tickets`、`$implement`、`$aisoft-matt-workflow`；末项不在 vendor manifest 技能集合内 |
| 仓库内 `docs/superpowers/`、`.superpowers/` | 均不存在；`.gitignore` 无对应条目 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待填写 |
| AC-2 | NOT RUN | 待填写 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |
| AC-5 | NOT RUN | 待填写 |
| AC-6 | NOT RUN | 待填写 |
| AC-7 | NOT RUN | 待填写 |

## 遗留风险与未完成项

以下属于 #354 的 installed / provider-session 层，本票不执行：

- 注册 `aisoft-platform` marketplace、安装或升级 Claude 侧 Matt 插件：NOT RUN
- 升级后对真实 HOME 读回 `PIN_CLEAN`：NOT RUN
- Claude 与 Codex fresh session 中 `pr` / `implement-spec` / `retro` 的实际发现与行为：NOT RUN
- superpowers 版本更新：NOT RUN（跟随官方 marketplace，本票不自建 pin）
