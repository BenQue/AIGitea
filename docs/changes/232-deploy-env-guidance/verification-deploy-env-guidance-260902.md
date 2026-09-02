---
issue: 232
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/232
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on:
  - 231
status: pending
branch: change/232-deploy-env-guidance
created: 2026-09-02
updated: 2026-09-02
---

# Verification · 部署文档收缩为环境级指导

## 基线与范围

- Commit SHA: 待 T04 填写
- 基线：`origin/main` = `aefb135`（Merge PR #234，#231 governance-provider-parity）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-232-deploy-env-guidance`）；本机两侧 skills 已安装但自 #231 起未重装
- 本记录负责证明的 acceptance criteria: AC-1～AC-7（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| `grep -c -iE 'NewEMaint\|rsdesign' skill-for-codex/references/onboarding-runbook.md` | 6 | 第 3 行（历史试点证据说明）、45（`git_remote_name` 示例）、67（#73 adoption 顺序）、186（§4 `rsdesign-new` PM2）、208、209（§4 NewEmaint 示例 profile） |
| §4 范围（183–276 行）`grep -n -iE 'NewEmaint\|rsdesign\|PM2 delete\|--pull never\|target-profile.example'` | 5 处命中 | §4 相对行 4、9、26、27、52 |
| `bash skill-for-claude/check-drift.sh` | DRIFT，rc=1 | `DRIFT: aisoft-platform/SKILL.md`、`DRIFT: issue-session-flow/SKILL.md`（#231 合并后未重装，与本 Issue 无关） |
| `bash codex/check-drift.sh` | DRIFT，rc=1 | `DRIFT: aisoft-platform/SKILL.md`（同上） |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | `GAP: pointer-sections`、`GAP: change-templates`（平台仓结构性 GAP）；`PASS: change-documents`、`PASS: change-pr-url` |
| `bash codex/tests/smoke.sh`（基线，worktree = `origin/main`） | PASS，rc=0 | `OK` + `Codex platform static smoke checks passed.` |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据见上一节。

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

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
