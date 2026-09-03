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

# Plan · gitea-platform-ops 技能去项目名与交付形态运维步骤，守卫扩展到全部 codex/skills

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 目标技能改写：`codex/skills/gitea-platform-ops/SKILL.md` description 与第 1、2、11、14、18 项按 spec 对照表改写；其余项逐字不变；两条 Issue grep 对技能集合为空 | - | done |
| T02 | 守卫扩展：`codex/tests/smoke.sh` `governance_set` 改为 `codex/skills/*/SKILL.md` glob + `[[ -f ]]` 存在断言，交付形态 pattern 追加两项；`bash codex/tests/smoke.sh` rc=0；反向注入 rc=1 后恢复 | T01 | done |
| T03 | 验证记录：填 verification（基线观测、AC-1～AC-4 命令与输出、反向证明、`check-drift` DRIFT、重装 NOT RUN） | T01, T02 | done |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T02 依赖 T01：守卫扩展后目标技能若未改写，smoke
会对半成品报红。T03 依赖两者定稿后运行。选 vertical slice：纯文本治理收敛，没有需要跨批次保持
红/绿的运行时重构。

## Expected touch points

- **T01**：`codex/skills/gitea-platform-ops/SKILL.md`（仅 spec 对照表列出的 6 处）。
- **T02**：`codex/tests/smoke.sh`（`governance_set` 数组、其后的存在断言、交付形态 `rg -ni` pattern
  与注释；不动其它守卫与断言）。
- **T03**：`docs/changes/241-platform-ops-neutral/verification-platform-ops-neutral-260903.md`。

这是范围提示，不授权扩大 spec：`codex/runtime/`、`codex/vendor/`、`docker-release/`、
`agents/openai.yaml`、其它 `codex/skills/*/SKILL.md`、两侧 Claude 技能都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 目标技能去项目名、去交付形态步骤 | `grep -n -iE '<项目名 pattern>' codex/skills/*/SKILL.md` 为空；`grep -n -iE 'PM2\|sqlite3 .backup\|release symlink\|docker-release\|Compose\|systemd-native\|IIS' codex/skills/*/SKILL.md` 为空；`git diff origin/main -- codex/skills/gitea-platform-ops/SKILL.md` 与 spec 对照表逐行 review；`grep -c "target project's deployment documents and scripts"` ≥ 3 |
| AC-2 守卫扩展 | review `governance_set` 含 `codex/skills/*/SKILL.md` glob 与 `[[ -f ]]` 循环；反向注入：`printf '\n参照 NewEMaint\n' >> codex/skills/gitea-spec-plan/SKILL.md && bash codex/tests/smoke.sh; echo rc=$?` → rc=1；`git checkout -- codex/skills/gitea-spec-plan/SKILL.md && bash codex/tests/smoke.sh; echo rc=$?` → rc=0 |
| AC-3 测试与漂移 | `bash codex/tests/smoke.sh` 退 0；`shellcheck -S warning codex/tests/smoke.sh` 无告警；`bash codex/check-drift.sh` 改动前 CLEAN（基线已记）/ 改动后 DRIFT 退 1 并列出 `gitea-platform-ops/SKILL.md`；重装 NOT RUN |
| AC-4 技能语义不变 | `grep -c '^[0-9]*\. ' codex/skills/gitea-platform-ops/SKILL.md` = 21；`git diff origin/main --stat -- codex/skills/gitea-platform-ops/SKILL.md` 只含 6 处改动行；`grep -F 'never begin with anonymous API access'`、`grep -F 'retire-shared-bot'` 命中；职责对照表 review |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；本机 skills 副本在本 Issue 内不重装，因此无需回滚安装。
映射的 `verification` 文档记录基线观测、AC grep 输出、反向证明、`check-drift.sh` 改动前后对比与
未执行项，不含「部署验收」节。
