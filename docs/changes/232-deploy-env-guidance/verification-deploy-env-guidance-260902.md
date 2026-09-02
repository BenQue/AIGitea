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
status: verified
branch: change/232-deploy-env-guidance
created: 2026-09-02
updated: 2026-09-02
---

# Verification · 部署文档收缩为环境级指导

## 基线与范围

- Commit SHA: `b8e9039`（T01 `f989c8e`、T02 `dffbfd6`、T03 `b8e9039`；本记录随 T04 提交，SHA 见 PR）
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
| §4 范围（`## 4` 至 `## 5` 前，183–254 行）`grep -n -iE 'NewEmaint\|rsdesign\|PM2 delete\|--pull never\|target-profile.example'` | 空，rc=1 | 无输出 |
| §4 范围 `grep -n -E 'verify-artifact\|stage\b\|activate\|systemctl'` | 空，rc=1 | 无输出；§4 结构为 `### 4.1 Linux 原生`、`### 4.2 Linux 容器化`、`### 4.3 Windows`、`### 4.4 对所有环境一致的流程不变量`、`### 4.5 项目仓必须自行声明与实现交付方案` |
| `grep -c -iE 'NewEMaint\|rsdesign' skill-for-codex/references/onboarding-runbook.md` | 1（基线 6） | 仅第 3 行「rsdesign-new 只是历史试点证据」；§1.1 两处改为「已声明的项目按各自 manifest 的取值（例如 `gitea`）」「该项目的 adoption Issue」 |
| `grep -n '交付形态参考' AGENTS.md README.md` | 各 1 处 | `AGENTS.md:40`（目录段子列表）、`README.md:171`（`### 交付形态参考（按项目选用，非部署步骤事实源）`） |
| 小节内条目计数 | AGENTS 7 / README 7 | 每行含适用环境与「参考、非部署步骤事实源」 |
| 主线/主表残留 | AGENTS 无；README §5 主表无 | README 第 35 行（§1 待办）与 213 行（§6 权威分工）是正文交叉引用，不在 §5 导航表内 |
| `git diff --stat origin/main...HEAD -- codex/tools codex/tests codex/runtime` | 空 | 检查器与测试逻辑未改 |
| `bash codex/tests/smoke.sh` | PASS，rc=0 | `Ran 651 tests in 34.182s … OK` + `Codex platform static smoke checks passed.`（基线同为 651 tests OK） |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (37 cases)` |
| `bash codex/tests/test-install-claude-skills.sh` | PASS | `claude skill install tests passed` |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | 与基线逐行一致：`GAP: pointer-sections`、`GAP: change-templates`（结构性）、`PASS: change-documents`、`PASS: change-pr-url` |
| `bash skill-for-claude/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: aisoft-platform/references/onboarding-runbook.md`、`DRIFT: aisoft-platform/references/project-align.md`；两份 SKILL.md 此刻 CLEAN（基线时报 DRIFT，说明 #231 的技能副本已在本会话之外被重装；本会话未执行任何安装） |
| `bash codex/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: aisoft-platform/references/project-align.md`、`DRIFT: aisoft-platform/references/onboarding-runbook.md` |
| 重装后 `check-drift.sh` CLEAN | NOT RUN | Issue 非目标：本 Issue 不安装或更新全局 skills；合并后独立执行 |
| `git diff --stat origin/main...HEAD -- docker-release/ architecture/` | 空 | `docker-release/`（#65 冻结）与 `architecture/` 未改动 |
| `git diff origin/main...HEAD -- 02-*.md 12-*.md 13-*.md 14-*.md 15-*.md \| grep -c '^-[^-]'` | 0 | 六份分册只有新增行；`grep -c '> 定位（#232'` 每份 = 1 |
| `git diff origin/main...HEAD -- templates/project/AGENTS.md` | +2 行 | 只新增「部署方案位置」bullet；常驻指针前两节与「工具分工」无 diff |
| `sed -n '33,34p' skill-for-codex/references/project-align.md` | 新措辞 | 第 6 行含「含 `delivery_contract` 如实选取」，第 7 行含「runbook §4（环境级原则，非部署步骤）」与「项目自己的部署文档」 |
| `rg -n '默认主处理者\|primary handler\|维护与部署\|开发与设计\|Codex 为主\|对等补位'` 对本次改动的活文档 | 空，rc=1 | #231 AC-3 守卫在新增文字上无命中（smoke 守卫块同样通过） |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <worktree>` | `pass=2 gap=0` | `PASS: change-documents`、`PASS: change-pr-url` |
| `codex/tools/apply-classification-labels.sh 232` → `--apply` → `--verify 232` | `projected` | plan `applied:false`；apply `result:updated`；verify `result:projected`，`type/platform` + `complexity/complex` |
| `git diff --stat origin/main...HEAD` | 只含平台仓路径 | 6 份分册 + `AGENTS.md` + `README.md` + 2 份 references + `templates/project/AGENTS.md` + `docs/changes/232-deploy-env-guidance/`；无下游仓改动 |

命令与输出照实抄；改动前的基线观测见上一节。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 runbook §4 重写 | PASS | §4 = 三段环境原则（4.1–4.3）+ 不变量清单（4.4）+ 项目自行声明与实现（4.5）；范围内两条 grep 均空 |
| AC-2 runbook 全文去项目名 | PASS | 计数 6 → 1，仅剩第 3 行历史证据说明；§1.1 两处改措辞不改语义（确认点 1 认可） |
| AC-3 导航归类 | PASS | `AGENTS.md` 目录段与 README §5 各一个独立小节、各 7 项、每行含环境与「参考、非部署步骤事实源」；主表/主线无残留 |
| AC-4 检查器与测试不变 | PASS | `codex/tools`、`codex/tests`、`codex/runtime` 无 diff；smoke 651 OK；两份测试 PASS；平台仓 project-check 与基线一致 |
| AC-5 两侧技能安装内容随之变化 | PASS | 两侧 check-drift 如实 DRIFT 且只列两份 references；重装后 CLEAN 记 NOT RUN |
| AC-6 `docker-release/` 不动 | PASS | diff 为空 |
| AC-7 分册定位说明与模板指针 | PASS | 六份分册只新增 `> 定位（#232）` 段；模板只新增「部署方案位置」行；project-align 第 6/7 行新措辞 |

## 遗留风险与未完成项

- 本机 skills 重装（`skill-for-claude/install.sh`、`codex/install-skills.sh`）：NOT RUN——Issue 非目标，
  合并后独立执行；重装后 `check-drift.sh` 应 CLEAN。
- 12/13/14/15 与 02 正文仍含项目名与旧「默认合同」表述，只加了定位说明；正文去留由后续
  「过时文档清理」Issue 处置（Issue 非目标）。
- `smoke.sh` 的 #231 守卫不覆盖 `skill-for-codex/references/`；本 Issue 不新增守卫（非目标），
  references 的去项目化靠本记录的 grep 证据，是否固化守卫留给后续 Issue。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
