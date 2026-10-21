---
issue: 402
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/402
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 391
  - 392
  - 395
status: spec-review
branch: change/402-usage-tool-entry
created: 2026-10-21
updated: 2026-10-21
---

# R11 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理步骤：五份技能正文改写为 `aisoft <子命令>` 与维护层小节、`usage/CONTRACT.md`「会话工具」节、`templates/project/AGENTS.md`「项目事实」固定结构；单独 commit 后停止，fresh 重读 | - | pending |
| T02 | `codex/tools/aisoft` 入口与子命令；`aisoft-project-check.sh` 的 manifest 回退 | T01 | pending |
| T03 | 发布包合同：工具包成员与 `tool-provenance`、`releases[].notes/compatibility`、落后区间判定、`--build` 生成 `provenance.json` 与历史副本 | T02 | pending |
| T04 | `--adopt`；`aisoft-project-check.sh` 的 `tool-provenance` 与 `agents-budget` 行及测试计数 | T03 | pending |
| T05 | 测试与守卫：`test-aisoft-entry.sh`（闭包与反向证明）、`test-usage-bundle.sh` 增补、smoke 登记与技能 rg 守卫 | T04 | pending |
| T06 | 发布下一空闲版本；`03`/`06` 指向说明；全量 smoke；Codex 只读交叉审查 | T05 | pending |
| T07 | 三个项目：各开 Issue、`--adopt`、AC-1 无平台检出会话动作；负责人确认后推送并开 PR；E2E 表「采用记录」与路线图 | T06 | pending |

按 superpowers `executing-plans` 依 Txx 顺序内联执行，同一时刻一个写者；每张 ticket 至少一个原子 commit，主题含 `#402 Txx`。

## Expected touch points

- T01：`skills/aisoft-platform/SKILL.md`、`skills/aisoft-platform/references/{onboarding-runbook,project-align,private-gitea-access}.md`、`skills/issue-session-flow/SKILL.md`、`usage/CONTRACT.md`、`templates/project/AGENTS.md`
- T02：`codex/tools/aisoft`、`codex/tools/aisoft-project-check.sh`
- T03–T04：`codex/tools/usage-bundle.py`、`codex/tools/usage-bundle.sh`、`usage/bundle.json`、`codex/tools/aisoft-project-check.sh`、`codex/tests/test-aisoft-project-check.sh`
- T05：`codex/tests/test-aisoft-entry.sh`、`codex/tests/test-usage-bundle.sh`、`codex/tests/smoke.sh`
- T06：`usage/bundle.json`、`03-Issue-Spec-Plan与单闸门开发流程.md`、`06-运维手册与踩坑集.md`
- T07：`docs/governance/platform-e2e-acceptance.md`、`docs/governance/remediation-roadmap.md`、本目录 verification；三个项目仓各自的 change 目录与采用文件

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 采用项目的 small Issue 在 `sandbox-exec`（拒读平台检出）+ 临时 HOME 下跑 `.aisoft/bin/aisoft` 四步，记录输出 |
| AC-2 | `rg` 导出目录 `.claude/skills`；smoke 守卫与反向证明 |
| AC-3 | 三个项目 `usage-bundle.sh --project-status` 读回；E2E 表链接 |
| AC-4 | `bash codex/tests/test-aisoft-entry.sh`（含删模块反向证明） |
| AC-5、AC-6 | `bash codex/tests/test-usage-bundle.sh` 新增用例；`--verify --baseline-ref origin/main` |
| AC-7 | `bash codex/tests/test-aisoft-project-check.sh` 新增用例；`wc -c` 模板节 |
| AC-8 | `bash codex/tests/smoke.sh`、`usage-bundle.sh --verify`、`check-change-documents`、`codex-review-402.md` |

## 回滚

整 PR revert；三个项目 PR 各自 revert。
