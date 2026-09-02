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
status: pending
branch: change/231-governance-provider-parity
created: 2026-09-02
updated: 2026-09-02
---

# Verification · 平台治理去项目化、去部署细节，Claude/Codex 等价

## 基线与范围

- Commit SHA: 待实现后填写
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
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |
| AC-2 | 待填写 | 待填写 |
| AC-3 | 待填写 | 待填写 |
| AC-4 | 待填写 | 待填写 |
| AC-5 | 待填写 | 待填写 |
| AC-6 | 待填写 | 待填写 |
| AC-7 | 待填写 | 待填写 |

## 遗留风险与未完成项

- 本机 skills 重装（`skill-for-claude/install.sh`、`codex/install-skills.sh`）：NOT RUN——Issue 非目标，
  合并后独立执行；重装后 `check-drift.sh` 应 CLEAN。
- 下游已接入项目的 `pointer-sections` 转 GAP：预期，不在本 Issue 内修复。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
