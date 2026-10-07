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
status: approved
branch: change/355-claude-skill-pack-align
created: 2026-10-08
updated: 2026-10-08
---

# Implementation plan · Claude 侧外部技能包对齐

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | marketplace 条目、pin 检查工具、fixture 测试与 smoke 登记 | - | pending |
| T02 | Claude 侧技能的 Matt 四条规则与 superpowers 映射、`.gitignore`、三组 smoke 守卫 | - | pending |
| T03 | README 与 08 的导航说明、verification 记录、全量闸门 | T01, T02 | pending |

T01 与 T02 互不依赖，但同由本会话在同一 worktree 顺序实现，不并行写入。

## Expected touch points

- **T01**：`.claude-plugin/marketplace.json`（新）、`skill-for-claude/check-plugin-pin.sh`（新）、
  `skill-for-claude/check-plugin-pin.py`（新）、`codex/tests/test-claude-plugin-pin.sh`（新）、
  `codex/tests/smoke.sh`（`bash -n` 清单、ShellCheck 清单、`--source-only` 执行、测试执行区）。
- **T02**：`skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `.gitignore`、`codex/tests/smoke.sh`（可解析性、两侧对照、落点三组守卫）。
- **T03**：`README.md`（技能安装与漂移核对）、`08-双工具共存与实施.md`（§5）、
  `docs/changes/355-claude-skill-pack-align/verification-claude-skill-pack-align-261008.md`。

每个 ticket 改文档或 smoke 前先 `rg` `codex/runtime/tests` 与 `codex/tests` 里钉住的短语和计数。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash skill-for-claude/check-plugin-pin.sh --source-only`；`bash codex/tests/test-claude-plugin-pin.sh` 的 source 不一致用例；本机 `claude plugin validate .`（local 层，记入 verification） |
| AC-2 | `bash codex/tests/test-claude-plugin-pin.sh` 的一致、两种不一致、缺失、schema 不可识别与凭据样式不外泄用例 |
| AC-3 | smoke 的可解析性守卫及其反向证明；`bash codex/tests/test-install-claude-skills.sh` |
| AC-4 | smoke 的落点守卫；`git diff --stat origin/main -- codex/vendor` 为空 |
| AC-5 | smoke 的两侧对照守卫及其反向证明；verification 的逐条对照表 |
| AC-6 | `bash codex/tests/smoke.sh`；`bash -n` 与 `shellcheck` 新增及改动的 shell；`resolve-documents 355`；`check-change-documents`；`git diff origin/main` 审查无删除测试或 skip |
| AC-7 | verification 的分层表与 `NOT RUN` 清单审查 |

反向证明一律在临时副本上做：删除被钉的短语或改动 pin 后确认守卫变红，不改动工作树内的受管文件。

## 部署与回滚

无部署影响。回滚为 revert 本 Issue 的线性 commit。声明 `verification` 是因为 `claude plugin validate`
与改动前的本机插件基线读回无法由 required CI 重放，不表示本票要部署。
