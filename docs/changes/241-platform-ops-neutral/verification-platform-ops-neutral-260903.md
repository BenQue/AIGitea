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
status: pending
branch: change/241-platform-ops-neutral
created: 2026-09-03
updated: 2026-09-03
---

# Verification · gitea-platform-ops 技能去项目名与交付形态运维步骤，守卫扩展到全部 codex/skills

## 基线与范围

- Commit SHA: 待填写
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
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄；改动前的基线观测见上一节。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |
| AC-2 | 待填写 | 待填写 |
| AC-3 | 待填写 | 待填写 |
| AC-4 | 待填写 | 待填写 |

## 遗留风险与未完成项

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
