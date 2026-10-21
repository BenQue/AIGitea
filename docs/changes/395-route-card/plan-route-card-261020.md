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
status: approved
branch: change/395-route-card
created: 2026-10-20
updated: 2026-10-20
---

# R10b 路由卡实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理步骤：`route-policy.md`、两个技能的路由节与候选/派单字段、`03` §2 路由小节、`08` §5 四行与 §7 档位表；单独 commit 后停止，fresh 重读 | - | pending |
| T02 | front matter 接受并校验 `route:`；summary 模板带 `route:` 并刷新模板 digest；全量 `check-change-documents` 仍 gap=0 | T01 | pending |
| T03 | `test_route_policy.py` 五类 case 查表；smoke 路由表结构守卫与反向证明 | T01, T02 | pending |
| T04 | 发布包 1.6.0（1.5.0 已被 R13 占用）；#392 Cursor 行更正；路线图 R10b 行；本票 verification；Codex 独立查表与只读交叉审查 | T03 | pending |

按 superpowers `executing-plans` 依 Txx 顺序内联执行，同一时刻一个写者；每张 ticket 至少一个原子 commit，主题含 `#395 Txx`。

## Expected touch points

- T01：`skills/aisoft-platform/references/route-policy.md`、`skills/aisoft-platform/SKILL.md`、`skills/issue-session-flow/SKILL.md`、`03-Issue-Spec-Plan与单闸门开发流程.md`、`08-双工具共存与实施.md`
- T02：`codex/runtime/aisoft_loop/contract.py`、`codex/runtime/tests/test_contract.py`、`templates/docs/changes/_template/summary.md`、`codex/config/change-template-sync.json`
- T03：`codex/runtime/tests/test_route_policy.py`、`codex/tests/smoke.sh`
- T04：`usage/bundle.json`、`docs/changes/392-superpowers-vendor-pin/verification-superpowers-vendor-pin-261020.md`、`docs/governance/remediation-roadmap.md`、`docs/changes/395-route-card/*`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `PYTHONPATH=codex/runtime python3 -m unittest codex/runtime/tests/test_route_policy.py`；人工对照 spec「路由表」节 |
| AC-2 | `PYTHONPATH=codex/runtime python3 -m unittest codex/runtime/tests/test_contract.py`；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` gap=0 |
| AC-3 | `bash codex/tools/change-template-sync.sh --verify-digest` |
| AC-4 | review：两个技能的 diff；`bash skill-for-claude/check-drift.sh`、`bash codex/check-drift.sh` 重装后 CLEAN |
| AC-5 | review：`03`、`08` 的 diff |
| AC-6 | `bash codex/tests/smoke.sh`；反向证明：临时删表行/写闭集外取值后 smoke 红，恢复后绿 |
| AC-7 | `check-change-documents` 读本 Issue；verification 记 Txx commit；`codex exec -s read-only` 独立查表输出 |
| AC-8 | `bash codex/tests/smoke.sh`；`bash codex/tools/usage-bundle.sh --verify`；`bash -n codex/tests/smoke.sh`；`shellcheck codex/tests/smoke.sh`；`codex/tools/apply-classification-labels.sh --verify 395` |
| AC-9 | review：两处 diff |

## 部署与回滚

无部署影响。合并后负责人或会话重装技能（`bash codex/install-skills.sh "$HOME"`、`bash skill-for-claude/install.sh "$HOME"`）并读回 drift；broker 未改，不需要两台重装。回滚 = revert 整个 PR。
