---
issue: 233
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/233
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on:
  - 231
  - 232
status: pending
branch: change/233-prune-stale-docs
created: 2026-09-02
updated: 2026-09-02
---

# Verification · 清除过时文档与概念

## 基线与范围

- Commit SHA: 待 T05 填写
- 基线：`origin/main` = `0df92177497c1b4b16d9ed0c0bc5780849d7e7fb`（Merge PR #235，#232 deploy-env-guidance）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-233-prune-stale-docs`）；本机两侧 skills 已按 #232 合并后的源重装（基线 CLEAN）
- 本记录负责证明的 acceptance criteria: AC-1～AC-8（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| Issue 验收第 2 条 grep（活文档） | 5 处命中 | `README.md:164`（导航行 Codex-first / Claude parity 条件）、`08…md:147`（§8 Claude Code 接入条件）、`04…md:147`（§10 Codex-first 验证顺序）、`skill-for-codex/SKILL.md:26`（After AISoftPlatform Issue #35）、`skill-for-codex/references/onboarding-runbook.md:97`（Legacy ci-bot collaborator gate） |
| `bash check-md-links.sh <worktree>` | `links=113 broken=3`，rc=1 | 3 条均为 `skill-for-claude/aisoft-platform/SKILL.md -> references/{onboarding-runbook,project-align,private-gitea-access}.md`（install-time 链接，`skill-for-claude/install.sh` 复制后才存在；基线即存在，非本 Issue 引入） |
| `rg -ni '<#231 AC-1 pattern>' skill-for-codex/references/*.md` | 2 处 | `private-gitea-access.md:10`（NewEmaint's `gitea`）、`onboarding-runbook.md:3`（rsdesign-new 历史试点） |
| `bash codex/tests/smoke.sh`（worktree = `origin/main`） | PASS，rc=0 | `Ran 651 tests in 35.248s … OK` + `Codex platform static smoke checks passed.` |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | `GAP: pointer-sections`、`GAP: change-templates`（平台仓结构性 GAP）；`PASS: change-documents`、`PASS: change-pr-url` |
| `bash skill-for-claude/check-drift.sh` | CLEAN，rc=0 | 基线已安装副本与源一致 |
| `bash codex/check-drift.sh` | CLEAN，rc=0 | 同上 |
| `grep -n 'AISOFT_ONBOARDING_MODE=software-repository' codex/tests/smoke.sh` | `465` | 断言对象是 `skill-for-codex/SKILL.md:48` 退役 gate 块 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待 T05 执行 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据见上一节。

## 清单处置结果（AC-1）

待 T05 逐条填写 spec A-01～G-03 的实际处置与改写后行号。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1～AC-8 | NOT RUN | 待 T05 |

## 遗留风险与未完成项

待 T05 填写。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
