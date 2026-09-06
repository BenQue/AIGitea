---
issue: 264
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/264
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: verified
branch: change/264-sync-main-docs
created: 2026-09-06
updated: 2026-09-06
---

# Verification · 主文档与 AGENTS.md 目录同步到 09-05 合并批次现状

## 基线与范围

- Commit SHA: `477f2f2`（T04 之后、本文件之前的 head；本文件与 PR 回填不改正文）
- 基线：`origin/main` = `54602a3d`（PR #263 merge，broker `git.fetch.main` 后取得）
- 环境: Mac，worktree `/private/tmp/issue-264-sync-main-docs`；本机 `~/.claude/skills/`
- 本记录负责证明的 acceptance criteria: spec AC-1～AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git diff -U0 origin/main...HEAD -- AGENTS.md \| grep '^@@'` | PASS | `@@ -42,0 +43`、`@@ -49 +50`、`@@ -54 +55`、`@@ -56 +57,3`，全部落在目录节 35–57 行内 |
| `git log --format=%h origin/main..HEAD -- AGENTS.md` + `git show --stat` | PASS | 恰好 1 条 `758ad22`，`1 file changed, 6 insertions(+), 3 deletions(-)`，只含 `AGENTS.md` |
| `for d in $(ls -d */); do grep -qF "\`$d" AGENTS.md; done` | PASS | 10 个目录（architecture/ archive/ codex/ company-delivery/ docker-release/ docs/ skill-for-claude/ skill-for-codex/ sync/ templates/）全部命中 |
| 8 个 installer 路径 + `codex/lib/install-source-guard.sh` 逐个 `grep -F AGENTS.md` | PASS | 9 个字符串全部命中，`issue-session-flow` 命中 |
| `sed -n '3p;11p' README.md` | PASS | 两行均含 `2026-09-06` |
| `awk '/^## 1\./,/^## 2\./' README.md \| grep -c "#N"`（N ∈ 222 223 225 228 243 250 252 254） | PASS | 1 1 1 1 1 1 2 1 |
| `grep -c '27 条' README.md` | PASS | 1 |
| `awk 'NR>=445' 06-*.md \| grep -oE '^\| [0-9]+ \|' \| tr -d '\| ' \| sort -n \| tail -1` | PASS | 27（§2 踩坑表从 `:445` 起；不加 `NR>=445` 会被 `:432` 退出码表的 `64` 干扰，plan 里的原命令需按此收窄） |
| `grep -c 'skill-for-claude/install.sh' README.md 08-*.md`；`grep -c 'check-drift.sh' README.md 08-*.md` | PASS | README 2/3，08 1/1；`codex/install-skills.sh` 分别在 README `:174`（同一表格）与 08 `:81`（同一句） |
| `awk '/^## 2\./,/^## 3\./' onboarding-runbook.md \| grep -c 'templates/project/ci/'` | PASS | 1 |
| `awk '/^## 4\./,/^## 5\./' 04-*.md \| grep -cE 'analysis_provider\|\`codex\`\|\`claude\`\|\`none\`'` | PASS | 6；`grep -n analysis_provider 08-*.md` 只有 `:47` 一条「定义与含义见 04 §4」的引用 |
| `bash skill-for-claude/check-drift.sh`（T04 改后、重装前） | PASS（观测） | `DRIFT: aisoft-platform/references/onboarding-runbook.md`，rc=1 |
| `bash skill-for-claude/install.sh` | PASS | `Claude skills installed from .../skills.manifest: aisoft-platform issue-session-flow` … `Pruned 0 stale entries; each declared skill tree is exact.` |
| `bash skill-for-claude/check-drift.sh`（重装后） | PASS | `CLEAN`，rc=0（改动前基线同为 `CLEAN`） |
| `cd codex/runtime && python3 -m aisoft_loop.cli check-change-documents --repo /private/tmp/issue-264-sync-main-docs` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `result: changes=121 pass=2 gap=0` |
| `git diff --stat origin/main...HEAD -- codex/skills/ 03-*.md 06-*.md 09-*.md codex/runtime codex/tools codex/config templates docker-release architecture company-delivery` | PASS | 空（0 行） |
| `sed -n 526p 09-*.md \| grep -c '14 条'`；`git diff --stat origin/main...HEAD` | PASS | 1；8 files changed（AGENTS.md、README.md、04、08、runbook、本 Issue 三份文档），无其它 summary |
| README 钉住短语（`两台公司`、`本地 OrbStack`、`` exact `docker-release/v2` bytes ``、`Architecture declaration/lock`）`grep -F` | PASS | 4 个全部仍在 |
| `bash codex/tests/smoke.sh` | PASS | `Codex platform static smoke checks passed.` rc=0（含 runtime unittest `OK`、claude skill install tests、host-role 与 installer source-guard 测试；worktree 位于 origin/main 顶端，staleness 闸门未触发） |
| `codex/tools/apply-classification-labels.sh --verify 264` | PASS | `"result":"projected","change_type":"docs","complexity":"complex"`（`--apply` 于确认点 1 后执行，`result: updated`） |

命令与输出照实抄。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 目录节 10 目录一一对应、8 installer + source guard、`issue-session-flow`；hunk 全在 35–57，独立 commit `758ad22` |
| AC-2 | PASS | `:3`/`:11` 均 2026-09-06；八个 `#N` 各 ≥ 1；`27 条` 且 06 §2 表最大编号 = 27 |
| AC-3 | PASS | README §5「技能安装与漂移核对」表与 08 `:81` 同句并列列出两侧 install 与 check-drift |
| AC-4 | PASS | runbook §2 含 `templates/project/ci/`；04 §4 三取值表；08 只引用 |
| AC-5 | PASS | smoke 见上表；check-drift DRIFT→CLEAN；check-change-documents 121 PASS |
| AC-6 | PASS | 非目标路径 diff 为空；`09:526` 与其它 summary 未动 |

## 遗留风险与未完成项

- Codex 侧 `~/.agents/skills/aisoft-platform/references/onboarding-runbook.md` 本 Issue 不重装（Issue 验收第 6 条：由人在
  Codex 会话另行自查），合并后 `bash codex/check-drift.sh` 预期报该文件 DRIFT，重跑 `codex/install-skills.sh` 即回 CLEAN。
- 本机 `~/.claude/skills/` 已装入本分支的 references；若 PR 被拒或 rebase 后内容变化，需从合并后的 `main` 重跑
  `skill-for-claude/install.sh`。
- README §1 新条目写明 typed 操作「进入 source 不等于生效，仍需两台重装」；本 Issue 不做任何 live/安装动作。
