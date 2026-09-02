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
status: contract-drafting
branch: change/232-deploy-env-guidance
created: 2026-09-02
updated: 2026-09-02
---

# Plan · 部署文档收缩为环境级指导

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 共享 references：runbook §4 重写为三类环境原则 + 流程不变量 + 项目自行声明与实现（§4.1 并入）；§9 去「见 §4.1」；§1.1 两处项目名改为中立措辞；`project-align.md` checklist 第 6/7 行事实源措辞 | - | pending |
| T02 | 导航、定位与模板：README §5 新增「交付形态参考」小节并把七项移入；`02`、`12-Linux…`、`12-Windows…`、`13`、`14`、`15` 各加顶部定位 blockquote；`templates/project/AGENTS.md`「项目事实」加「部署方案位置」指针 | - | pending |
| T03 | 根 `AGENTS.md` 目录段：新增「交付形态参考」子列表并把七项移入（独立、只含 `AGENTS.md` 的原子 commit） | - | pending |
| T04 | 验证与记录：Issue 正文 grep、`smoke.sh`、`test-project-check.sh`、`test-install-claude-skills.sh`、两侧 `check-drift.sh`、平台仓 `aisoft-project-check.sh --kind docs`、`docker-release/` diff 为空；填 verification | T01, T02, T03 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T01–T03 互不依赖、各自保持仓库全绿，可由
`$implement #232 Txx` 独立执行与验证；T03 单独成 commit 是根 `AGENTS.md` 治理文件规则的要求，不是
依赖关系。T04 必须等三份文本定稿后运行。选 vertical slice：本变更是纯文本治理收敛，没有需要
跨批次保持红/绿的运行时重构。

## Expected touch points

- **T01**：`skill-for-codex/references/onboarding-runbook.md`（第 3 行保留；§1.1 第 45、67 行附近
  两处措辞；§4 整段 183–276 行替换；§9 第 405–408 行去「见 §4.1」）；
  `skill-for-codex/references/project-align.md`（checklist 第 33、34 行）。
- **T02**：`README.md` §5；`02-CI与自动部署流水线.md`、`12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、
  `12-Windows平台自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、`14-Windows部署与迁移验收清单.md`、
  `15-VMware-Fusion-Windows-ARM原型实施手册.md`（各只在一级标题后插入 blockquote）；
  `templates/project/AGENTS.md`（「项目事实」节一行）。
- **T03**：`AGENTS.md`（`## 目录` 段）。
- **T04**：`docs/changes/232-deploy-env-guidance/verification-deploy-env-guidance-260902.md`。

这是范围提示，不授权扩大 spec：`docker-release/`、`architecture/`、`codex/tools/`、`codex/tests/`、
`codex/runtime/`、`templates/docs/changes/_template/`、`company-delivery/` 都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `S=$(grep -n '^## 4' runbook)`、`E=$(grep -n '^## 5' runbook)`；`sed -n "$S,$((E-1))p" runbook \| grep -n -iE 'NewEmaint\|rsdesign\|PM2 delete\|--pull never\|target-profile.example'` 为空；同范围 `grep -n -E 'verify-artifact\|stage\b\|activate\|systemctl'` 为空；人工 review §4 结构 = 三段原则 + 不变量清单 + 项目自行声明段 |
| AC-2 | `grep -c -iE 'NewEMaint\|rsdesign' runbook` = 1，`grep -n` 只命中第 3 行 |
| AC-3 | `grep -n '交付形态参考' AGENTS.md README.md` 各命中一处小节标题；小节内 7 行各含环境与「非部署步骤事实源」；主表/主线不再含这七项（`grep -n '12-Windows\|docker-release/\|architecture/' README.md AGENTS.md` 只命中小节内） |
| AC-4 | `git diff --stat origin/main...HEAD -- codex/tools codex/tests codex/runtime` 为空；`bash codex/tests/smoke.sh`、`bash codex/tests/test-project-check.sh`、`bash codex/tests/test-install-claude-skills.sh` rc=0；`aisoft-project-check.sh --repo <worktree> --kind docs` = `pass=2 gap=2 skip=4` |
| AC-5 | `bash skill-for-claude/check-drift.sh; echo $?` = 1 且列出 references；`bash codex/check-drift.sh; echo $?` = 1；重装后 CLEAN 记 NOT RUN |
| AC-6 | `git diff --stat origin/main...HEAD -- docker-release/` 为空 |
| AC-7 | `git diff origin/main...HEAD -- 02-*.md 12-*.md 13-*.md 14-*.md 15-*.md \| grep -c '^-[^-]'` = 0（只有新增行）；每份含 `> 定位（#232）`；`git diff origin/main...HEAD -- templates/project/AGENTS.md` 只新增「部署方案位置」行；`grep -n '部署方案位置' templates/project/AGENTS.md` 命中；`project-align.md` 第 6/7 行含新措辞 |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；已安装 references 用上一版源重跑安装脚本即恢复（本 Issue 内不
执行安装）。
