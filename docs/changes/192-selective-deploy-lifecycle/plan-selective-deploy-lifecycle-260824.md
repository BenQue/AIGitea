---
issue: 192
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/192
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/192-selective-deploy-lifecycle
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · 三档 `deployment_lifecycle`

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 改动前的基线证据：LocalWMS 缺省档上旧工具的判定与那批 Issue 的真实标签（合并后无法重放） | - | done |
| T02 | manifest schema 三档 + 缺省换档，含 Python 侧测试 | T01 | pending |
| T03 | `mark-completed-issues.sh` 三选一分支 + 未知取值 fail closed，含 shell 侧测试 | T02 | pending |
| T04 | 合同文字：`03` §3/§11、`02` §9、`issue-session-flow` skill 源 | T03 | pending |
| T05 | 改动后的同一批命令重跑 + 全量 smoke，写进映射 verification | T03, T04 | pending |

T01 必须最先做：它是唯一在本次改动落地后无法重放的证据（工具本身会被改写）。

## Expected touch points

- T02：`codex/runtime/aisoft_gitea_governance/contract.py`（`DEPLOYMENT_LIFECYCLES`、
  `DEFAULT_DEPLOYMENT_LIFECYCLE`、`RepositoryContract` 注释与判据说明）、
  `codex/runtime/tests/test_deployment_lifecycle.py`。
- T03：`codex/tools/mark-completed-issues.sh`（读取 manifest 之后的终态分支）、
  `codex/tests/test-mark-completed-issues.sh`（新增第三档 fixture 与未知取值用例）。
- T04：`03-Issue-Spec-Plan与单闸门开发流程.md` §3 与 §11、`02-CI与自动部署流水线.md` §9、
  `skill-for-claude/issue-session-flow/SKILL.md` 收尾第 3 步、
  `codex/runtime/tests/test_change_control.py` 与 `codex/runtime/aisoft_loop/classification.py`
  里引用该判定的注释（只在文字与新规则冲突时改）。
- 不改：`codex/config/gitea-governance.json`、broker、CI workflow、`AGENTS.md`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -m unittest tests.test_deployment_lifecycle`（`PYTHONPATH=codex/runtime`） |
| AC-2 | `bash codex/tests/test-mark-completed-issues.sh`（三档各一组断言） |
| AC-3 | 同上，未知取值用例断言非零退出与消息 |
| AC-4 | 同上，`required_docs` 不含 `verification` 的既有断言原样保留并全绿 |
| AC-5 | `git diff --stat origin/main -- codex/config/gitea-governance.json` 无输出 |
| AC-6 | `bash codex/tests/smoke.sh` |
| AC-7 | review：§3 那句与 §11 新表 + 「等待必须有终点」一段的逐句比对 |
| AC-8 | `grep -rn "deployment_lifecycle" 02-*.md skill-for-claude/` 逐处复核 |
| AC-9 | `codex/tools/mark-completed-issues.sh --repo /Users/benque/Projects/LocalWMS 1 7 12 16 34`（计划模式）改动前后各一次 |

## 部署与回滚

无部署影响。回滚为 revert 本 PR；本次不改任何 manifest 数据，无迁移、无状态残留。
映射的 `verification` 文档记录的是跨仓库扫描与 LocalWMS 真实 checkout 上的改动前后对比，
不含部署验收（`## 部署验收` 一节按 `03` §3 整节删除）。
