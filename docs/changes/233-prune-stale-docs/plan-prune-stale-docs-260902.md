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
status: approved
branch: change/233-prune-stale-docs
created: 2026-09-02
updated: 2026-09-03
---

# Plan · 清除过时文档与概念

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | provider 等价与 Codex-first（spec A 组）：`08` 改名并同步 README/`09`/`archive/11` 链接；`08` §1/§4/§7/§8/§10 改写（§4 历史条目暂存到 T03 的 archive 文件）；`04` §3/§10 | - | done |
| T02 | 退役身份与已兑现条件句（spec B 组）：`skill-for-codex/SKILL.md`、`onboarding-runbook.md`、`private-gitea-access.md`、`gitea-platform-ops/SKILL.md`、`04` §11、`06` 四处；删除 `smoke.sh:465–466` 陈旧断言（B-14） | - | done |
| T03 | 状态历史与判定（spec C/D/F 组）：新建 `archive/平台状态历史-20260902.md` 并收录 README §1 与 `08` §4 迁出条目；README header/§1 改写与 §5 导航行（A-13）；`archive/README.md` 索引；`09` header 与 §0.2 落地对照；02/12–15 定位尾句 | T01 | done |
| T04 | 根 `AGENTS.md` 目录段（spec E 组，独立、只含 `AGENTS.md` 的原子 commit） | - | done |
| T05 | `smoke.sh` references 项目名守卫（G-01）+ 反向证明；验证与记录：AC-2 grep、链接脚本、smoke、project-check、test-install-claude-skills、两侧 check-drift、非目标 diff；填 verification | T01, T02, T03, T04 | done |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T01、T02、T04 互不依赖、各自保持仓库全绿
（T02 内含删除 `smoke.sh:465–466`，否则删除退役 gate 块后 smoke 会红）。T03 依赖 T01 只因 archive
文件要收录 `08` §4 迁出的原文。T04 单独成 commit 是根 `AGENTS.md` 治理文件规则的要求。T05 的守卫扩展
依赖 T02 清掉 references 的两处项目名命中。选 vertical slice：本变更是纯文本治理收敛加一条静态守卫，
没有需要跨批次保持红/绿的运行时重构。

## Expected touch points

- **T01**：`08-Codex双工具共存与实施.md` → `08-双工具共存与实施.md`（`git mv`；`:3`、`:14–15`、`:48–84`、
  `:119`、`:131`、`:145`、`:147–155` 删、`:165`、`:167`、`:168`）；`04-Agent编排与定时任务.md`（`:37–38`、`:147`、`:156`）；
  `09…md:510`；`archive/11-Codex-Loop运行时实施计划.md:5`（链接目标）；`README.md:164`（A-13，链接目标必须随
  改名同步，否则 T01 自身留下悬空链接）。
- **T02**：`skill-for-codex/SKILL.md`（`:26`、`:44–70`、`:79`）；`skill-for-codex/references/onboarding-runbook.md`
  （`:3`、`:19`、`:43`、`:45`、`:97–126`、`:258`）；`skill-for-codex/references/private-gitea-access.md:10`；
  `codex/skills/gitea-platform-ops/SKILL.md`（`:21`、`:23`）；`04…md:160`；`06…md`（`:70`、`:196`、`:232`、`:399`）；
  `codex/tests/smoke.sh:465–466`。
- **T03**：`archive/平台状态历史-20260902.md`（新建）；`archive/README.md`（表格加一行）；`README.md`
  （`:3`、`:11`、`:14–32` 按 C 组、§1 末尾加 C-14）；`09…md`（`:3–6`、§0 末尾）；`02…md:3`、`12-Linux…md:3`、
  `12-Windows…md:3`、`13…md:3`、`14…md:3`、`15…md:3`（各只改 blockquote 尾句）。
- **T04**：`AGENTS.md`（`:38`、`:57`）。
- **T05**：`codex/tests/smoke.sh`（#231 守卫块之后新增 references 项目名守卫）；
  `docs/changes/233-prune-stale-docs/verification-prune-stale-docs-260902.md`。

这是范围提示，不授权扩大 spec：`docker-release/`、`architecture/`、`codex/runtime/`、`codex/tools/`、
`codex/config/`、`templates/`、`company-delivery/`、`07`、`01`、`03`、`05` 都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | verification「清单处置结果」表逐条填写 A-01～G-03 的实际处置与改写后行号；`grep -c '待定'` = 0 |
| AC-2 | Issue 正文 grep（spec AC-2 原文命令）无输出，rc=1 |
| AC-3 | `bash check-md-links.sh <worktree>`（脚本正文写入 verification）：`BROKEN` 集合 = 基线 3 条 install-time 链接；`grep -rn '08-Codex双工具共存与实施.md' --include='*.md' .` 无 `](` 形式命中 |
| AC-4 | `bash codex/tests/smoke.sh` rc=0；`bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` = `pass=2 gap=2 skip=4`；`bash codex/tests/test-install-claude-skills.sh` rc=0 |
| AC-5 | `git diff --stat origin/main...HEAD -- 03-*.md` 为空；`git diff origin/main...HEAD -- AGENTS.md` 只含目录段两行；`git diff origin/main...HEAD -- README.md` 不触及 §3/§4；`git diff origin/main...HEAD -- skill-for-codex/SKILL.md` 不触及 `:86–99`；`git diff origin/main...HEAD -- skill-for-codex/references/onboarding-runbook.md` 不触及 `:36–41`、`:51–68`、`:260–262`；`git diff origin/main...HEAD -- 04-*.md` 不触及 §9；`git diff origin/main...HEAD -- 09-*.md` 不触及 §16；review spec「语义对照」列 |
| AC-6 | 单独执行新增守卫块：临时追加 `参照 NewEMaint` 到 runbook → 报红退出；恢复后 `grep -c NewEMaint` = 0；`grep -n 'AISOFT_ONBOARDING_MODE=software-repository' codex/tests/smoke.sh` 无输出 |
| AC-7 | `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/runtime codex/tools codex/config templates company-delivery` 为空；`git diff --stat origin/main...HEAD -- archive/` 只含三项 |
| AC-8 | `bash skill-for-claude/check-drift.sh; echo $?` = 1；`bash codex/check-drift.sh; echo $?` = 1；重装后 CLEAN 记 NOT RUN |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；已安装 skills/references 用上一版源重跑安装脚本即恢复（本 Issue
内不执行安装）。
