---
issue: 318
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/318
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/318-provider-skill-parity
created: 2026-10-02
updated: 2026-10-02
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立受控治理步骤应用四份 skill/共享指导提案，记录合同 diff 并停止 | - | done |
| T02 | fresh run 读取指导，加入关键合同与负向变异断言，跑 targeted/full smoke，整理唯一 PR candidate | T01 | done |
| T03 | 人批准提交后 push/唯一 PR/CI；人合并后核对终态、安装 exact main 并 CLEAN 读回 | T02 | awaiting-pr-confirmation |

默认不创建子 Issue。每个 Txx 仅在此 Issue frontier 内执行。

## Expected touch points

- T01：spec 的前四个精确目标文件；不修改 AGENTS.md 或运行时。
- T02：`codex/runtime/tests/test_routine_merge.py` 的 SessionContractTests 与本 Change 证据。
- T03：单一 PR、summary-only `pr_url`、两侧 installer/check-drift、本 worktree 清理。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2/3 | 提案 overlay 的 SessionContractTests，旧 source 5 fail/新 source 6 pass；候选必须在本 worktree 重跑 |
| AC-4 | shared runbook 与 08 合同测试；diff 与 03 权威规则比对 |
| AC-5 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest tests.test_parity tests.test_matt_snapshot tests.test_routine_merge.SessionContractTests -v` 与 `bash codex/tests/smoke.sh`，完整结果分层记录 |
| AC-6 | `check-change-documents`、`apply-classification-labels.sh --verify 318`、exact branch/claim/push receipt、最终 required CI、合并后两端 check-drift |

## 部署与回滚

无部署。Policy manual；PR 提交前确认，合并由人。两端技能从 exact merged source 安装；新项目 acceptance 与 provider 启用独立。source 回滚 revert/PR，installed 回滚到版本化稳定源并核 CLEAN。

## 执行记录

- T01 done：`dc77c93`，独立治理应用并停止。
- T02 done：`b780eab`，fresh read 9 文件；12 合同 tests/27 mutations；targeted 38 PASS；C locale smoke 978 PASS；类外 AST 不变。
- T03 已准备本地证据与 PR body，等待提交确认；required CI、人工 merge、exact-main 技能安装/终态/cleanup 未执行。T03 为交付确认与确定性收尾阶段，不再派产品实现 ticket。
