---
issue: 395
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/395
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
depends_on:
  - 389
  - 391
  - 392
status: pending
branch: change/395-route-card
created: 2026-10-20
updated: 2026-10-21
---

# R10b 路由卡验证记录

## 基线与范围

- 基线：`origin/main` = `08be6f4`（2026-10-21 broker `git.fetch.main` PASS）；实现中 R13（#396）合并，`origin/main` 前进到 `43db3d0`，按平台做法撤回未发布的 1.5.0 记录后用 merge commit `c3aa107` 集成，改发 1.6.0。
- 环境：macOS 本机（bash 3.2.57，Python 3）；Codex CLI 0.161.0（`codex exec -s read-only`）。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-9。

## 按 Txx 执行（superpowers `executing-plans`，内联、同一时刻一个写者）

| Ticket | commit | 证据 |
|---|---|---|
| 合同 | `5bf9679`、`7e1ce7b` | 确认点 1：负责人 2026-10-21 01:09Z 回「确认」，标签 `approved` |
| T01 治理步骤 | `b0576ff` | 技能、`03`、`08` 单独 commit 后停止，重读 AGENTS.md 与已提交的路由表再动 runtime |
| T02 解析与模板 | `84ba40b` | 见下表 T02 行 |
| T03 查表测试与守卫 | `8e8cf46` | 见下表 T03 行 |
| T04 发布包与路线图 | `5bd6a3c`、`c735ef9`、`c3aa107`、`2495264` | 1.5.0 → 撤回 → 集成 R13 → 1.6.0 |
| 审查修复 | `b082796` | Codex 第 1 轮 |

本票用到的技能：Matt 风格的映射 spec/plan（本会话直接写）；superpowers `executing-plans`、`test-driven-development`、`verification-before-completion`；平台 `issue-session-flow`。没有用 `brainstorming`（how 在确认点 1 前已收敛）。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T02 先看着测试红：`python3 -m unittest tests.test_contract`（新增路由测试，`contract.py` 未改） | FAILED (failures=11, errors=1)，全部 `unsupported front matter syntax at line 16` | 红因正是解析器不认 `route:` 缩进键 |
| T02 实现后同一命令 | Ran 30 tests, OK | |
| T02 全量 runtime：`python3 -m unittest discover -s tests -t .` | Ran 713 tests, OK | |
| `change-template-sync.sh --refresh-digest` 后 `--verify-digest` | digest pinned | 下游 stale=4 是预期：模板前进，pin 发布包的项目不受影响 |
| `check-change-documents --repo .` | changes=181 gap=0 | 本票 summary 带 `route:` |
| 反向证明（本票 summary `effort: max` → `low`） | GAP：`route.effort='low' is outside high, max, medium` | 恢复后 gap=0 |
| T03 `python3 -m unittest tests.test_route_policy` | Ran 5 tests, OK | 五类 classifier case 逐格一致 |
| 反向证明：路由表 R4 effort `high` → `max` | FAILED (failures=3) | 恢复后 OK |
| 反向证明：闭集 tier 加 `ultra` | FAILED (failures=1) | 恢复后 OK |
| smoke 路由守卫在副本上：删 R5 行 / tier 闭集加值 / 技能去掉指针 | 三者都 RED | 第一次删行未变红：bash 3.2 下失败的 `[[ ]]` 不触发 `set -e`，守卫改为 grep 管道后变红 |
| `bash -n codex/tests/smoke.sh`、`shellcheck codex/tests/smoke.sh` | 通过 | SC2016（字面 Markdown 反引号）两处用 directive 标注 |
| Codex 独立查表（只读，只给 `## AI 判级` 段与路由表） | R3，未触发细化规则，路由卡与 summary 逐格一致 | `codex exec -s read-only`，输出 `LOOKUP-DONE` |
| broker scope 闸门离线复现（源码 `GitRepository.scope` + `verify_history`，head `b082796`） | SCOPE_AND_HISTORY_PASS | 第 1 轮里 #392 路径曾触发 `SCOPE_DENIED`，已从本地历史移除 |
| `usage-bundle.sh --release 1.6.0` 后 `--verify` | `VERIFIED 1.6.0` | |
| 全量 smoke（集成后 head） | 见「全量 smoke」 | |
| `apply-classification-labels.sh --apply 395` 后 `--verify 395` | `projected`（platform / complex） | 2026-10-21 读回 |

## 全量 smoke

- head `531039a`（集成 R13 并发 1.6.0 之后、本记录补齐之前）：`bash codex/tests/smoke.sh` exit 0，`Codex platform static smoke checks passed.`；runtime 单测 Ran 724 tests OK。
- 之后只改了 `docs/changes/395-route-card/` 下的 plan 与本文件；最终 head 的 smoke 见确认点 2 候选。

## #392 Cursor 一行的更正（AC-9）

#392 verification 的 Cursor fresh 会话一行写的是 NOT RUN（CLI 未登录）。合并后补测：2026-10-20 14:48Z，负责人 `cursor-agent login` 后，在 main `149e469` 的 `--build` 产物落地的临时检出里跑 `cursor-agent -p --mode ask --trust`，rc=0，PASS。CSV 功能需求加载项目级 `.cursor/skills/brainstorming/SKILL.md`，「接入 AISoft 平台开 Issue 走判级」加载 `.claude/skills/aisoft-platform/SKILL.md`；superpowers 15 个技能全部来自项目级 `.cursor/skills`。出处：项目库 `governance-remediation-handoff-392-20261020T145354-53b6.md`。

原计划直接改 #392 的文件；Codex 第 1 轮发现 broker 的 Git scope 闸门不允许一个 Issue 改另一个 Issue 的 `docs/changes/` 目录（`SCOPE_DENIED`），且逐提交检查不接受 add→revert，所以把该改动从本地未推送的历史里移除，更正改记在这里。

## Codex 交叉审查

第 1 轮（head `cc698b7`，只读）：`CHANGES_REQUESTED`。

| # | 发现 | 处置 |
|---|---|---|
| blocker | #392 路径越过 Issue 目录，broker 会 `SCOPE_DENIED` | 从历史移除，更正记在本文件；spec `git_scope` 与 AC-9 同步修改 |
| should-fix | `confidence: low` 但仍写 `effective_complexity: small` 时，查表落 R1 而校验要求 `small-direct` | `validate_route` 先判 R1；新增 `test_route_process_follows_the_unresolved_row_first`（先红后绿）；路由表闭集说明同步一句 |
| should-fix | verification 未填 | 本文件 |
| nit | G1 的「拆成多个 Issue」条件测试未覆盖 | `lookup` 加 `splits_into_issues`，补三个断言 |

第 2 轮（head `531039a`，只读）：`CHANGES_REQUESTED`，无代码问题。blocker 复现已消除（`GitRepository.scope` 17 个路径，11 个提交均未触及 `docs/changes/392-*`），R1 修复经 72 格矩阵验证，merge 完整保留 R13 改动，1.6.0 只追加。两条文档问题：本文件缺全量 smoke 与判级投影记录（已补上节）；plan T04 仍列 #392 路径（已改为本票 verification）。

Codex 认可实现者的三项裁决（拆表保值、提前建 verification、grep 管道代替 `[[ ]]`），并核对旧解析在 692 份文档与 60 组 `documents` 边界输入上的结果与报错文本不变。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `test_route_policy.py` 五类 case；表编辑反向证明 |
| AC-2 | PASS | `test_contract.py` 路由用例；全量 `check-change-documents` gap=0；本票 summary 反向证明 |
| AC-3 | PASS | 模板 `route:` 块；`--verify-digest` |
| AC-4 | PASS | 两个技能的 diff；Codex 审查逐条核对 |
| AC-5 | PASS | `03` §2.2、`08` §5 三行与 §7.3 |
| AC-6 | PASS | smoke 守卫与副本反向证明 |
| AC-7 | PASS | 本票 summary `route:` 通过检查；Txx commit 见上；Codex 独立查表一致 |
| AC-8 | PASS | smoke exit 0；`--verify` 1.6.0；`bash -n` 与 ShellCheck；判级投影 `projected`；Codex 第 2 轮仅文档问题，见下 |
| AC-9 | PASS（按修改后的 AC-9） | 上节；路线图 R10b 行 |

## 遗留风险与未完成项

- 真实 small Issue 的确认点 1 路由行：NOT RUN，由 R11 的项目采用 Issue（D4，判 small）承接。
- `type/feature` 大需求链（grill → to-spec →（如触发）brainstorming → to-tickets → executing）：NOT RUN，由合并后第一条 `type/feature` Issue 承接。
- Codex 侧 superpowers 仍是 `PIN_NOT_INSTALLED`（R10c 已知事实），Codex 走路由表「默认入口」的 Matt 列；本票 Codex 侧只验了独立查表。
- 合并后技能要重装（`bash codex/install-skills.sh "$HOME"`、`bash skill-for-claude/install.sh "$HOME"`）并读回 drift；broker 未改，不需要两台重装。
- 记忆规则「派单卡片用 Opus 5 high」由路由卡的 tier 取代，合并后更新项目记忆。
