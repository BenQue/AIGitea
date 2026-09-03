---
issue: 241
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/241
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
status: approved
branch: change/241-platform-ops-neutral
created: 2026-09-03
updated: 2026-09-03
---

# Spec · gitea-platform-ops 技能去项目名与交付形态运维步骤，守卫扩展到全部 codex/skills

## 目标与原因

把 Codex 兼容 adapter 技能 `codex/skills/gitea-platform-ops/SKILL.md` 收敛到 2026-09-02 定案的平台
定位：平台只管流程管控与环境级指导（Linux 原生 / Linux 容器化 / Windows 三类原则），部署步骤与
细节在项目仓实现；技能与治理文件不含项目名与交付形态实现名。#231 已对七份治理文件完成同样收敛并
固化了 smoke 守卫，但守卫集合只点名了 `codex/skills/` 下两个文件，`gitea-platform-ops` 漏在集合外，
成为终检残留。本 spec 把 Issue #241 正文的 4 条验收标准逐条落成可观察结果；Issue 正文是合同源，本文
不扩张。

## 术语

- **目标技能**：`codex/skills/gitea-platform-ops/SKILL.md`。
- **技能集合**：`codex/skills/*/SKILL.md` 共 7 份（aisoft-matt-workflow、gitea-analyze-change、
  gitea-development-loop、gitea-implement-change、gitea-platform-ops、gitea-spec-plan、
  issue-session-flow）；`codex/vendor/` 不在该目录下，天然不属于技能集合。
- **治理集合（`governance_set`）**：`codex/tests/smoke.sh` 中 #231 定义的数组；本变更后 =
  `skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `skill-for-codex/SKILL.md`、技能集合 7 份、`codex/global-AGENTS.md`、`templates/project/AGENTS.md`，
  共 12 份。
- **项目名 pattern**：`NewEMaint|SFMDigitalBoard|HSDB|WMPDA|SapTable|rsdesign|myapp|smoke-test|LocalWMS`
  （与 #231 AC-1、Issue #241 AC-1 相同）。
- **交付形态 pattern**：`docker-release|PM2|Compose|systemd-native|IIS|sqlite3 .backup|release symlink`
  （#231 AC-2 的五项 + Issue #241 AC-1 的两项）。
- **三项职责**：`gitea-platform-ops` 只负责平台证据、非生产首次部署、事件与回滚规划
  （`skill-for-codex/SKILL.md` §「Skill routing」第 86 行的既有定义）。

## Acceptance criteria

- [ ] **AC-1 目标技能去项目名、去交付形态步骤**：对技能集合 7 份执行
  `grep -n -iE '<项目名 pattern>'` 与 `grep -n -iE 'PM2|sqlite3 .backup|release symlink|docker-release|Compose|systemd-native|IIS'`
  输出均为空。目标技能第 1、11、18 项改写为形态中立原则并逐条指向「the target project's deployment
  documents and scripts」；四条原则齐全：只读证据先行（第 11 项）、停止/回滚优先（第 20 项，原文保留）、
  备份与健康检查（第 18 项）、生产 script-only（第 19 项，原文保留）。逐行对照见下表。
- [ ] **AC-2 守卫扩展**：`smoke.sh` 的 `governance_set` 把两条点名的 `codex/skills/…/SKILL.md` 条目
  替换为 `"$ROOT"/codex/skills/*/SKILL.md`，且在 grep 前对数组逐项 `[[ -f ]]` 断言存在；交付形态守卫
  pattern 改为交付形态 pattern（七项）。反向证明：向一份**新纳入**的技能文件（非目标技能）临时注入
  一个项目名后 `bash codex/tests/smoke.sh` rc=1 并打印 `#231 AC-1` 报错行；恢复后真实树 rc=0。两次
  结果与命令写进 verification。
- [ ] **AC-3 测试与漂移**：`bash codex/tests/smoke.sh` 全绿（rc=0）；`shellcheck -S warning codex/tests/smoke.sh`
  无告警；`bash codex/check-drift.sh` 改动前 CLEAN、改动后未重装 DRIFT（rc=1）并列出
  `gitea-platform-ops/SKILL.md`；重装（`bash codex/install-skills.sh`）由用户独立执行，verification
  记 NOT RUN。
- [ ] **AC-4 技能语义不变**：目标技能 21 个编号项数量与顺序不变；除第 1、2、11、14、18 项与
  description 外其余各项 diff 为空；`smoke.sh` 既有断言 `never begin with anonymous API access`
  （第 5 项）与 `retire-shared-bot`（第 10 项）仍成立；三项职责在改写后各有承载项（见「职责对照」）。

## 逐行对照（改写前 → 改写后）

| 位置 | 改写前（`origin/main` b80af37） | 改写后 | 原因 |
|---|---|---|---|
| 第 3 行 description | `Diagnose or improve the documented Gitea, act_runner, PM2, artifact, deployment, and rollback platform. …` | `Diagnose or improve the documented Gitea, act_runner, artifact, deployment, and rollback platform. …`（其余逐字不变） | 去交付形态实现名 |
| 第 8 行 第 1 项 | `Read the relevant numbered platform documents. For deployment work, read `02-…` and `06-…` first.` | `Read the relevant numbered platform documents. For deployment work, read `02-…` and `06-…` for the platform-level invariants first, then the target project's deployment documents and scripts for every concrete step: the platform describes environment-level principles only, and each project declares and implements its own delivery form.` | 指向目标项目的部署文档与脚本（#232 定案） |
| 第 9 行 第 2 项 | `… Never assume rsDesign or any example repository is the target.` | `… Never assume that any example, template, or previously handled repository is the target.` | 去项目名反例，规则本身不变 |
| 第 24 行 第 11 项 | `Start with read-only evidence: Issue/PR/SHA/run ID, failure step and exit code, logs, runner state, release symlink, PM2 state, migration/backup state, health endpoint, and rollback result.` | `Start with read-only evidence: Issue/PR/SHA/run ID, failure step and exit code, logs, runner state, the currently active release and service state as the target project's deployment documents define them, migration/backup state, health endpoint, and rollback result.` | 只读证据先行原则不变，证据项形态中立 |
| 第 27 行 第 14 项 | `… Documentation-only platform repositories do not need synthetic PM2, artifact, or rollback flows.` | `… Documentation-only platform repositories do not need synthetic service, artifact, or rollback flows.` | 去交付形态实现名 |
| 第 31 行 第 18 项 | `For SQLite, stop the app before migration, back up with `sqlite3 .backup` under WAL, switch the release symlink, use PM2 delete+start, assert online, then health-check.` | `For any migration or release switch, keep this order regardless of delivery form: stop the service before migrating, take a verified backup, switch to the new release, restart, assert the service is online, then health-check against the exact release SHA. The concrete commands come from the target project's deployment documents and scripts, never from this skill.` | 某一形态的运维步骤 → 形态中立顺序（备份与健康检查原则），具体命令指向项目 |

其余 15 个编号项（3–10、12、13、15–17、19–21）逐字不变。

## 职责对照（改写前后三项职责的承载）

| 职责 | 改写前承载项 | 改写后承载项 | 变化 |
|---|---|---|---|
| 平台证据 | 第 2–10、11、12、21 项 | 同上 | 第 11 项证据清单形态中立，其余不变 |
| 非生产首次部署 | 第 14、16、17、18 项 | 同上 | 第 14 项去 PM2 字样；第 18 项从某一形态步骤改为顺序原则并指向项目文档；16、17 不变 |
| 事件与回滚规划 | 第 13、18、19、20 项 | 同上 | 第 18 项如上；13、19、20 不变 |

改写不增删任何职责，也不把任何职责移交给其它技能；`skill-for-codex/SKILL.md` 第 86 行的路由句
不变。

## 接口、数据与兼容性影响

- **技能 front matter `description`**：去掉 `PM2` 一词，触发词其余不变；安装到 `~/.agents/skills/`
  的副本在重装前保持旧文，重装是合并后用户独立执行的动作。
- **`smoke.sh` 守卫**：治理集合从 7 份扩为 12 份；新增的五份（gitea-analyze-change、
  gitea-development-loop、gitea-implement-change、gitea-spec-plan、gitea-platform-ops）在基线上除
  目标技能外对两个 pattern 均为空命中，因此只有目标技能需要改写。交付形态 pattern 追加的两项在基线下
  对整个治理集合只命中目标技能第 24、31 行，不会让其它文件转红。`[[ -f ]]` 断言让 glob 未展开或文件
  改名时守卫 fail closed，而不是被 `if rg` 当作无命中。
- **`smoke.sh` 其它既有断言**保持成立：第 421 行 per-skill 循环仍找到 6 份 `SKILL.md` 与
  `agents/openai.yaml`；`test_company_delivery` 对 `smoke.sh` 不得含字面量 `rg -n -i` 的断言保持
  （守卫写法沿用 `rg -ni`）。
- 不改 `codex/runtime/`、broker 操作表、标签 manifest、`docker-release/`、`codex/vendor/`、
  `agents/openai.yaml`、编号分册、README、根 `AGENTS.md`、两侧 Claude 技能、`skill-for-codex/`。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；本机已安装的 `gitea-platform-ops` 副本用上一版源重跑
  `codex/install-skills.sh` 即恢复（本 Issue 内不执行安装）。
- 本次运行遵循根 `AGENTS.md`，不修改它；被改的治理文件是 Codex 技能源与 smoke 守卫，本 spec 即该授权，
  范围以「术语」中的目标技能与 `codex/tests/smoke.sh` 两处为限。

## 非目标

- 不改 runtime、broker、标签 manifest、`docker-release/`。
- 不改 vendored Matt skills（`codex/vendor/`）。
- 不改其它六份 `codex/skills/*/SKILL.md`（基线 grep 为空）与两侧 Claude 技能。
- 不安装或更新任何全局 skills；不改动任何下游项目仓。

## 未决问题

无。守卫交付形态 pattern 追加 `sqlite3 .backup|release symlink` 两项的解读（与 Issue AC-1 grep 对齐，
基线下不影响其它治理文件）已于 2026-09-03 确认点 1 由人认可，并写入「术语」的交付形态 pattern。
