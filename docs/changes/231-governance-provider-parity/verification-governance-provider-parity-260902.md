---
issue: 231
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/231
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on: []
status: verified
branch: change/231-governance-provider-parity
created: 2026-09-02
updated: 2026-09-02
---

# Verification · 平台治理去项目化、去部署细节，Claude/Codex 等价

## 基线与范围

- Commit SHA: `56af183`（T01–T04 实现头，`eb06dc3` 为 approved 文档提交；本记录与 smoke 守卫随 T05 一并提交，SHA 见 PR）
- 基线：`origin/main` = `ff39b30`（Merge PR #230，#229 project-label-write-path）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-231-governance-provider-parity`），本机已安装两侧 skills（基线 CLEAN）
- 本记录负责证明的 acceptance criteria: AC-1～AC-7（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| AC-1 grep（7 份范围文件） | 7 处命中 | `skill-for-claude/aisoft-platform/SKILL.md:3,22,83,84`（项目名列表、NewEMaint 参照、rsdesign-new、NewEMaint DockerLab）、`codex/global-AGENTS.md:13`（rsDesign）、`skill-for-codex/SKILL.md:24`（rsDesign）、`templates/project/AGENTS.md:52`（参照 NewEMaint） |
| AC-2 grep（7 份范围文件） | 4 处命中 | `skill-for-claude/aisoft-platform/SKILL.md:3,10,22`（docker-release 触发词、docker-release/ 子合同、docker-release/v2 + PM2）、`templates/project/AGENTS.md:52`（docker-release/v2、PM2、Windows/IIS） |
| AC-3 grep（活文档） | 5 处命中 | `templates/project/AGENTS.md:41,42`（开发与设计 / 维护与部署）、`skill-for-claude/aisoft-platform/SKILL.md:63,64`（默认主处理者 / 对等补位）、`skill-for-codex/SKILL.md:103`（primary handler） |
| `bash skill-for-claude/check-drift.sh` | CLEAN | 基线已安装副本与源一致 |
| `bash codex/check-drift.sh` | CLEAN | 同上 |
| `bash codex/tools/aisoft-project-check.sh --repo /Users/benque/MyDocs/AISoftPlatform --kind docs` | `result: pass=2 gap=2 skip=4` | `GAP: pointer-sections`、`GAP: change-templates`（平台仓结构性 GAP）；`PASS: change-documents`、`PASS: change-pr-url` |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| AC-1 grep（7 份范围文件） | 空，rc=1 | `grep -rn -iE 'NewEMaint\|SFMDigitalBoard\|HSDB\|WMPDA\|SapTable\|rsdesign\|myapp\|smoke-test\|LocalWMS' <7 files>` 无输出 |
| AC-2 grep（7 份范围文件） | 空，rc=1 | `grep -rn -iE 'docker-release\|PM2\|Compose\|systemd-native\|IIS' <7 files>` 无输出 |
| AC-3 grep（活文档，排除 archive/、docs/changes/、codex/vendor/、.git/、smoke.sh 守卫本身） | 空，rc=1 | `grep -rn -E '默认主处理者\|primary handler\|维护与部署\|开发与设计\|Codex 为主\|对等补位' …` 无输出 |
| 「工具分工」段 Claude 技能 vs 模板 | IDENTICAL | `diff <(awk … skill-for-claude/aisoft-platform/SKILL.md) <(awk … templates/project/AGENTS.md)` 无差异 |
| `grep -n -iE '1\.26\|merge-only\|custody\|allowlist' templates/project/AGENTS.md` | 空，rc=1 | 常驻指针两节不含平台内部实现 |
| 会话标准动作 4–7 步各一行 | PASS | `grep -n -E '^[4-7]\. '` 命中第 39–42 行，无缩进续行；各行含 `06` 踩坑 20/21、`03` §3、`06` §1.0 |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (37 cases)`；其中对齐 fixture 断言 `PASS: pointer-sections` 与 `result: pass=8 gap=0 skip=0` |
| `bash codex/tests/test-install-claude-skills.sh` | PASS | `claude skill install tests passed`（`aisoft-platform` 仍交叉引用 `issue-session-flow`） |
| `bash codex/tests/smoke.sh`（含新增三条守卫） | PASS，rc=0 | `Ran 651 tests … OK` + `Codex platform static smoke checks passed.`；首跑红一次：`test_company_delivery` 断言 smoke.sh 不得含字面量 `rg -n -i`，守卫改为仓库既有写法 `rg -ni` 后绿 |
| 守卫反向证明 | 报红 | 向 `templates/project/AGENTS.md` 临时追加 `参照 NewEMaint 的 docker-release/v2；Codex 为主`，单独执行守卫块 → 打印命中行 + `平台治理文件不得出现具体项目名（#231 AC-1）` 并退出；随后恢复文件（`grep -c NewEMaint` = 0） |
| `shellcheck -S warning codex/tests/smoke.sh codex/tests/test-project-check.sh` | PASS | 本机 shellcheck 可用，无告警 |
| `bash skill-for-claude/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: aisoft-platform/SKILL.md`、`DRIFT: issue-session-flow/SKILL.md` |
| `bash codex/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: aisoft-platform/SKILL.md` |
| 重装后 `check-drift.sh` CLEAN | NOT RUN | Issue 非目标：本 Issue 不安装或更新全局 skills；合并后独立执行 |
| `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` | `result: pass=2 gap=2 skip=4` | 与基线逐行一致：`GAP: pointer-sections`、`GAP: change-templates`（结构性）、`PASS: change-documents`、`PASS: change-pr-url` |
| `git diff --stat origin/main...HEAD` | 只含平台仓路径 | 7 份治理文件 + 2 份测试 + `docs/changes/231-governance-provider-parity/`；无下游仓改动 |
| `codex/tools/apply-classification-labels.sh --verify 231` | `projected` | `type/platform` + `complexity/complex`；broker `gitea.issue.labels.read` 读回同两枚标签 |

命令与输出照实抄；改动前的基线观测见上一节。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 去项目化 | PASS | 范围 grep 为空；两份 `aisoft-platform` description 只含通用触发词；`smoke.sh` 守卫固化 |
| AC-2 去部署细节 | PASS | 范围 grep 为空；「部署边界」只留流程不变量并指向项目 profile/AGENTS.md；`smoke.sh` 守卫固化 |
| AC-3 provider 等价 | PASS | 活文档 grep 为空；Claude 技能与模板「工具分工」段 IDENTICAL；Codex 技能与 global-AGENTS 为同义英文；`smoke.sh` 守卫固化 |
| AC-4 Claude 侧简化取向 | PASS | 两份 Claude 技能各含「approved 之后默认自主推进」「只在这些情况暂停」，八类暂停条件齐全、措辞与 Codex 侧不同；会话标准动作 4–7 步各一行并指向 `06`/`03` 编号 |
| AC-5 项目模板瘦身 | PASS（按确认点 1 认可的解读） | 模板不含 1.26/merge-only/custody/allowlist；占位符为环境类别；`test-project-check.sh` 对齐 fixture `PASS: pointer-sections`；平台仓自身结果与基线一致 |
| AC-6 测试与漂移 | PASS | smoke 全绿；两侧 check-drift 如实 DRIFT；重装后 CLEAN 记 NOT RUN |
| AC-7 下游不动 | PASS | diff 只含平台仓路径；下游 `pointer-sections` 转 GAP 属预期，各项目按 project-align 自行跟进 |

## 遗留风险与未完成项

- 本机 skills 重装（`skill-for-claude/install.sh`、`codex/install-skills.sh`）：NOT RUN——Issue 非目标，
  合并后独立执行；重装后 `check-drift.sh` 应 CLEAN。
- 下游已接入项目的 `pointer-sections` 转 GAP：预期，不在本 Issue 内修复。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
