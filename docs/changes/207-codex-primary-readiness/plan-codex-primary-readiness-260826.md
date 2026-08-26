---
issue: 207
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/207
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - ci
  - shared-core
depends_on: []
status: approved
branch: change/207-codex-primary-readiness
created: 2026-08-26
updated: 2026-08-26
---

# Codex 主处理就绪实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | development complex 的 Controller 可执行路径与 production 对照测试 | - | pending |
| T02 | 双工具合同统一、Codex 会话入口与三层只读 readiness 检查 | T01 | pending |
| T03 | 唯一 PR、真实 CI context 读回与 evidence-gated manifest 更新 | T02 | pending |

## Expected touch points

- T01：`codex/runtime/aisoft_loop/contract.py`、`controller.py`、
  `codex/runtime/tests/test_contract.py`、`test_controller.py`。
- T02：规格授权的 Codex/Claude skills、03/04/08 主文档、`codex/check-drift.sh`、
  `codex/tools/aisoft-platform-readiness.sh`、对应 shell tests 与 `smoke.sh`。
- T03：`codex/config/gitea-governance.json`、本 Issue verification/summary；先开 PR 并读回
  CI，证据不足时不得修改 manifest。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -m unittest codex.runtime.tests.test_contract codex.runtime.tests.test_controller` |
| AC-2 | 同上，并审阅 production 默认值及既有 ticket graph 用例 |
| AC-3 | `rg` 旧数字/旧规则审计 + `bash codex/tests/smoke.sh` |
| AC-4 | 审阅 `codex/skills/issue-session-flow/SKILL.md` 与升级条件 |
| AC-5 | `bash codex/tests/test-codex-drift.sh` 与 `bash codex/tests/test-platform-readiness.sh` |
| AC-6 | broker `gitea.actions.run.read --sha <PR_HEAD_SHA>` 真实读回 |
| AC-7 | `bash codex/tests/smoke.sh`、`bash -n`、可用时 `shellcheck` |
| AC-8 | `git diff origin/main...HEAD` + live/installed 操作清单核对 |

## 部署与回滚

无部署。最终 PR 可整体 revert。skills/runtime 安装、live branch protection apply 与部署
均不在本计划执行，verification 必须明确记录为 `NOT RUN`。
