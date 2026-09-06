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
status: contract-drafting
branch: change/264-sync-main-docs
created: 2026-09-06
updated: 2026-09-06
---

# Plan · 主文档与 AGENTS.md 目录同步到 09-05 合并批次现状

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 根 `AGENTS.md` 目录节（spec A-01～A-05），独立、只含 `AGENTS.md` 的原子 commit | - | pending |
| T02 | `README.md`（spec B-01～B-08）：版本头、§1 日期与四条新状态条目、§5 06 一行、技能安装小节 | - | pending |
| T03 | `04` §4 `analysis_provider` 定义（D-01）+ `08` §3 引用与 §5 初始化段 Claude 侧入口（C-01、C-02） | - | pending |
| T04 | onboarding-runbook §2 `templates/project/ci/`（E-01）+ `skill-for-claude/install.sh` 重装 + `check-drift.sh` 回 `CLEAN` | - | pending |
| T05 | 验证与记录：AC-1～AC-6 逐条命令、smoke、check-change-documents，填 verification | T01, T02, T03, T04 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T01～T04 互不依赖、各自保持仓库全绿。T01 单独成 commit
是根 `AGENTS.md` 治理文件规则的要求（#233 T04 同处置）。选 vertical slice：本变更是纯文档同步，没有需要
跨批次保持红/绿的运行时重构。

## Expected touch points

- **T01**：`AGENTS.md`（`:42` 后插 1 行、`:49`、`:54`、`:55` 后插 1 行、`:56`）。
- **T02**：`README.md`（`:3`、`:11`、`:19` 后插 4 行、`:153`、`:160` 后插「技能安装与漂移核对」小节）。
- **T03**：`04-Agent编排与定时任务.md`（`:84` 后插段落）；`08-双工具共存与实施.md`（`:41` 后插 1 条、`:80`）。
- **T04**：`skill-for-codex/references/onboarding-runbook.md`（`:113` 后插 1 条）；本机 `~/.claude/skills/aisoft-platform/references/`
  由 install.sh 更新（不在仓库内）。
- **T05**：`docs/changes/264-sync-main-docs/verification-sync-main-docs-260906.md`。

这是范围提示，不授权扩大 spec：`03`、`06`、`09`、`codex/skills/`、`codex/runtime/`、`codex/tools/`、`codex/config/`、
`templates/`、`docker-release/`、`architecture/`、`company-delivery/` 都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `ls -d */` 逐项 `grep -F "<dir>/" AGENTS.md`；`grep -c 'install-source-guard.sh' AGENTS.md` ≥ 1，installer 行 8 个路径逐个 grep；`grep -F 'issue-session-flow' AGENTS.md`；`git diff -U0 origin/main...HEAD -- AGENTS.md` 的 hunk 头全部落在 `@@ -35..57`；`git log --format=%s origin/main..HEAD -- AGENTS.md` 恰好 1 条且该 commit `--stat` 只含 `AGENTS.md` |
| AC-2 | `sed -n '3p;11p' README.md` 含 `2026-09-06`；`for n in 222 223 225 228 243 250 252 254; do awk '/^## 1\./,/^## 2\./' README.md \| grep -c "#$n"; done` 每项 ≥ 1；`grep -F '27 条' README.md`；`grep -oE '^\| [0-9]+ \|' 06-*.md \| sort -n \| tail -1` = 27 |
| AC-3 | `grep -c 'skill-for-claude/install.sh' README.md 08-*.md`；`grep -c 'check-drift.sh' README.md 08-*.md`；`grep -n 'codex/install-skills.sh' README.md 08-*.md` 与上两条同段 |
| AC-4 | `awk '/^## 2\./,/^## 3\./' skill-for-codex/references/onboarding-runbook.md \| grep -F 'templates/project/ci/'`；`awk '/^## 4\./,/^## 5\./' 04-*.md \| grep -cE 'analysis_provider\|`codex`\|`claude`\|`none`'`；`grep -n 'analysis_provider' 08-*.md` 只含「见 `04` §4」形式的引用 |
| AC-5 | `bash codex/tests/smoke.sh` rc=0；`bash skill-for-claude/check-drift.sh`（改前 DRIFT）→ `bash skill-for-claude/install.sh` → `bash skill-for-claude/check-drift.sh` 输出 `CLEAN`；`cd codex/runtime && python3 -m aisoft_loop.cli check-change-documents --repo <worktree>` 全部 PASS |
| AC-6 | `git diff --stat origin/main...HEAD -- codex/skills/ 03-*.md 06-*.md 09-*.md codex/runtime codex/tools codex/config templates docker-release architecture company-delivery` 为空；`git diff origin/main...HEAD -- 'docs/changes/*/summary-*.md' 'docs/changes/*/00-summary.md'` 只含本 Issue 目录 |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；Claude 侧已安装 references 用上一版源重跑 `skill-for-claude/install.sh`
即恢复（Codex 侧本 Issue 不重装）。
