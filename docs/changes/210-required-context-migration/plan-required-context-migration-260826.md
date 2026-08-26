---
issue: 210
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/210
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/210-required-context-migration
created: 2026-08-26
updated: 2026-08-26
---

# Evidence-approved required-context migration 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | strict manifest evidence schema 与普通 drift 负向合同测试 | - | pending |
| T02 | migration plan/apply 的 snapshot-first、完整 read-back 与失败关闭 | T01 | pending |
| T03 | exact snapshot rollback、CLI 边界、运维说明与全量验证 | T02 | pending |

## Expected touch points

- T01：`codex/config/gitea-governance.json`、`contract.py`、
  `codex/runtime/tests/test_gitea_governance.py`。
- T02：`reconcile.py`、`cli.py`、governance runtime tests。
- T03：必要时 `codex/tools/gitea-governance.sh` / `codex/tests/smoke.sh`、
  `06-运维手册与踩坑集.md` 与本 Issue verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2 | manifest parser 单测：strict keys、exact repo/context、full SHA、PR event/success 正反例 |
| AC-3, AC-4 | planner 单测：空起点唯一放行；任意 context/其它字段 drift 继续 blocker |
| AC-5, AC-6 | apply 单测：snapshot-before-PATCH 顺序、snapshot/PATCH/read-back 失败与全字段比较 |
| AC-7 | rollback 单测：exact snapshot 恢复/read-back 与 repo/branch/schema mismatch 拒绝 |
| AC-8 | `python3 -m unittest codex.runtime.tests.test_gitea_governance`、`python3 -m compileall codex/runtime/aisoft_gitea_governance`、`bash codex/tests/smoke.sh`、修改 shell 的 `bash -n`/ShellCheck |
| AC-9 | `git diff origin/main...HEAD`、broker read-back 与 verification 的 `NOT RUN` 清单 |

## 部署与回滚

本 Change 不部署、不执行 live protection apply。source 回滚为整体 revert 唯一 PR。未来独立
授权的 live migration 必须保留 apply 前 exact snapshot；任何失败或撤销使用同 repository 的
rollback 入口恢复 snapshot，再完整读回 protection。
