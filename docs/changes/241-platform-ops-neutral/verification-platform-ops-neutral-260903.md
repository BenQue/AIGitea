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
status: verified
branch: change/241-platform-ops-neutral
created: 2026-09-03
updated: 2026-09-03
---

# Verification · gitea-platform-ops 技能去项目名与交付形态运维步骤，守卫扩展到全部 codex/skills

## 基线与范围

- Commit SHA: `4ba63a7`（T01 技能改写）、`439274e`（T02 守卫扩展）；`e90ea1b` 为 approved 文档提交；本记录随 T03 提交，SHA 见 PR
- 基线：`origin/main` = `b80af37`（Merge PR #240，#239 param-company-delivery）
- 环境: Mac 本机 checkout（`/Users/benque/MyDocs/AISoftPlatform`，worktree
  `/private/tmp/issue-241-platform-ops-neutral`），本机已安装两侧 skills（基线 CLEAN），真实 `rg` 与
  `shellcheck` 可用
- 本记录负责证明的 acceptance criteria: AC-1～AC-4（spec 同名条目）

## 基线观测（改动前，只能在此刻留下）

| Command / check | Result | Evidence |
|---|---|---|
| Issue AC-1 项目名 grep（`codex/skills/*/SKILL.md` 7 份） | 1 处命中，rc=0 | `gitea-platform-ops/SKILL.md:9`（`Never assume rsDesign or any example repository`） |
| Issue AC-1 交付形态 grep（`PM2\|sqlite3 .backup\|release symlink\|docker-release\|Compose\|systemd-native\|IIS`，同 7 份） | 4 处命中，rc=0 | `gitea-platform-ops/SKILL.md:3`（description `PM2`）、`:24`（`release symlink, PM2 state`）、`:27`（`synthetic PM2`）、`:31`（`sqlite3 .backup`、`release symlink`、`PM2 delete+start`） |
| `rg -ni 'sqlite3 .backup\|release symlink'` 对 #231 七份治理文件 + 7 份技能 | 2 处命中 | 只有 `gitea-platform-ops/SKILL.md:24,31`；其余 12 份为空，追加这两项到守卫不会让其它文件转红 |
| `bash codex/check-drift.sh` | CLEAN，rc=0 | 基线已安装副本与源一致 |
| `bash skill-for-claude/check-drift.sh` | CLEAN，rc=0 | 同上 |
| `bash codex/tests/smoke.sh`（`b80af37` 干净树，241 文档暂挪出树） | PASS，rc=0 | `Ran 660 tests … OK` + `Codex platform static smoke checks passed.` |
| `codex/skills/gitea-platform-ops/agents/openai.yaml` grep 两个 pattern | 空 | 不在改动范围 |
| 半成品文档教训 | GAP → PASS | summary `reason` 含 `*`（`codex/skills/*/SKILL.md`）被 runtime `_parse_scalar` 判为 unsafe YAML scalar 使 `check-change-documents` GAP、smoke rc=1；改为文字描述后 `pass=2 gap=0` |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| Issue AC-1 项目名 grep（`codex/skills/*/SKILL.md` 7 份） | 空，rc=1 | `grep -n -iE 'NewEMaint\|SFMDigitalBoard\|HSDB\|WMPDA\|SapTable\|rsdesign\|myapp\|smoke-test\|LocalWMS' codex/skills/*/SKILL.md` 无输出 |
| Issue AC-1 交付形态 grep（同 7 份） | 空，rc=1 | `grep -n -iE 'PM2\|sqlite3 .backup\|release symlink\|docker-release\|Compose\|systemd-native\|IIS' codex/skills/*/SKILL.md` 无输出 |
| 目标技能逐行对照 review | 与 spec 对照表一致 | `git diff b80af37 -- codex/skills/gitea-platform-ops/SKILL.md`：`6 insertions(+), 6 deletions(-)`，恰为 description 与第 1、2、11、14、18 项；其余 15 项无 diff |
| `grep -c '^[0-9]*\. ' codex/skills/gitea-platform-ops/SKILL.md` | 21 | 编号项数量与顺序不变 |
| `grep -c "target project's deployment documents" …/SKILL.md` | 3 | 第 1、11、18 项各指向一次 |
| `grep -F 'never begin with anonymous API access'` / `grep -F 'retire-shared-bot'` | 各 1 处 | smoke 既有断言仍成立 |
| `bash codex/tests/smoke.sh`（真实树，T01+T02 后） | PASS，rc=0 | `Ran 660 tests … OK` + `Codex platform static smoke checks passed.` |
| 守卫反向证明 1（项目名，新纳入文件） | 报红，rc=1 | `printf '\n参照 NewEMaint 的部署\n' >> codex/skills/gitea-spec-plan/SKILL.md` 后 `bash codex/tests/smoke.sh` 退 1，末两行 `…/gitea-spec-plan/SKILL.md:19:参照 NewEMaint 的部署` + `平台治理文件不得出现具体项目名（#231 AC-1）`；`git checkout --` 恢复后 `grep -c NewEMaint` = 0 |
| 守卫反向证明 2（追加的交付形态项，新纳入文件） | 报红，rc=1 | `printf '\nSwitch the release symlink after backup.\n' >> codex/skills/gitea-implement-change/SKILL.md` 后 smoke 退 1，末两行 `…/gitea-implement-change/SKILL.md:22:Switch the release symlink after backup.` + `平台治理文件不得出现交付形态实现名（#231 AC-2，#241 扩展）`；恢复后 `grep -ci 'release symlink'` = 0 |
| `bash -n codex/tests/smoke.sh`；`shellcheck -S warning codex/tests/smoke.sh` | PASS | 无输出、无告警；`grep -c 'rg -n -i' smoke.sh` = 0（`test_company_delivery` 断言保持） |
| `bash codex/check-drift.sh`（改动后、未重装） | DRIFT，rc=1 | `DRIFT: gitea-platform-ops/SKILL.md` |
| `bash skill-for-claude/check-drift.sh`（改动后） | CLEAN，rc=0 | Claude 侧技能不在本 Issue 范围，预期 CLEAN |
| 重装后 `codex/check-drift.sh` CLEAN | NOT RUN | Issue 非目标：本 Issue 不安装或更新全局 skills；合并后由用户独立执行 `bash codex/install-skills.sh` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | `pass=2 gap=0` | `PASS: change-documents`、`PASS: change-pr-url` |
| `git diff --stat b80af37...HEAD` | 只含 3 个路径 | `codex/skills/gitea-platform-ops/SKILL.md`、`codex/tests/smoke.sh`、`docs/changes/241-platform-ops-neutral/`；`docker-release/`、`codex/vendor/`、`codex/runtime/` 无 diff |
| `codex/tools/apply-classification-labels.sh 241` → `--apply` → `--verify 241` | `projected` | plan `applied:false` → apply `result:updated` → verify `result:projected`，`type/platform` + `complexity/complex` |

命令与输出照实抄；改动前的基线观测见上一节。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 目标技能去项目名、去交付形态步骤 | PASS | 两条 grep 对 7 份技能为空；第 1、11、18 项各指向「target project's deployment documents and scripts」；四条原则由第 11、18、19、20 项承载 |
| AC-2 守卫扩展 | PASS | `governance_set` 含 `"$ROOT"/codex/skills/*/SKILL.md` glob 与 `[[ -f ]]` 循环；交付形态 pattern 七项；反向证明 1、2 均 rc=1 并打印守卫报错行，真实树 rc=0 |
| AC-3 测试与漂移 | PASS | smoke 全绿；shellcheck 无告警；`codex/check-drift.sh` 基线 CLEAN → 改动后 DRIFT 并列出 `gitea-platform-ops/SKILL.md`；重装 NOT RUN |
| AC-4 技能语义不变 | PASS | 21 项不变；diff 恰 6 处；两个既有断言仍命中；spec 职责对照表：平台证据 / 非生产首次部署 / 事件与回滚规划三项职责的承载项集合改写前后相同 |

## 遗留风险与未完成项

- 本机 Codex skills 重装（`bash codex/install-skills.sh`）：NOT RUN——Issue 非目标，合并后由用户独立执行；
  重装后 `codex/check-drift.sh` 应 CLEAN。
- 追加的交付形态守卫项（`sqlite3 .backup|release symlink`）对未来所有 12 份治理文件生效；基线下无其它命中。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
