---
issue: 320
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/320
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/320-push-head-anchor
created: 2026-10-02
updated: 2026-10-02
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立受控步骤应用六份治理文案，记录 exact diff/head 与治理完成收据，然后停止该运行 | - | done |
| T02 | fresh run 重读新指导与合同，完成四场景与负向验证、既有测试、审查与唯一最终 PR 候选 | T01 | done-awaiting-pr-confirmation |

不创建子 Issue；一次合同确认同时确认此颗粒度与依赖。T01 结束后不得在同一运行直接接 T02；重新进入本会话的 fresh run 读取后继续。

## Expected touch points

- T01：spec 精确授权的六份治理文案；本 Change 文档和受控步骤收据。
- T02：本 Change 验证证据；既有测试源只读。授权 PR 后 mapped summary-only 回填与 scope 内 CI 修复继续，但不能引入 runtime 修改。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/2/3 | six-file diff review；四场景桌面推演；负向矩阵（旧锚/漏比对/他人改写/范围扩张/branch 与 session 不符） |
| AC-4 | verification 各层真实状态与收据，不将 synthetic/pass 写成 live |
| AC-5 | T01 receipt + 停止；T02 fresh read 与 scope guard（runtime/AGENTS 字节不变） |
| 合同与 tuple | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 320 --repo .`、`check-change-documents --repo .`、`git diff --check` |
| 既有语义/兼容 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest tests.test_routine_merge.SessionContractTests tests.test_parity tests.test_matt_snapshot -v` |
| 全量闸门 | `LC_ALL=C bash codex/tests/smoke.sh`；保持该基线已采用的 C locale，不修改 fixture/test 合同 |
| 最终 PR candidate | `bash codex/tools/apply-classification-labels.sh --repo . --project aisoft-platform --verify 320` 必须 type/complexity 均 projected；请求 exact Issue/branch/manual 提交确认 |

## 部署与回滚

无部署，无全局安装；manual，由人合并。提交前确认后才 push/唯一 PR/required CI。合并后证明 exact merge 在 origin/main，terminal dry-run/apply、文档检查、精确 worktree/branch 清理与归档。若任一步未完成，不声称真实解决。治理源回滚使用 revert/PR。

## T01 执行记录

六份已批准治理文案已独立应用，diff 与批准提案一致、scope/文档检查 PASS。仅提交本 Issue 的治理源与合同证据；停止本轮，T02 不在本轮执行。收据：`evidence/t01-governance-apply.json`。

## T02 执行记录

Fresh run 重读 PASS；17合成场景 PASS，恢复旧锚时合法回填/CI修复两例错误停止；38 targeted tests PASS；Standards/Spec 各0发现。完整 smoke 首次 sandbox localhost bind 被拒，受控 host 同命令 exit=0/978 runtime tests，static smoke PASS。runtime/tests/AGENTS字节保持基线，六治理源保持批准提案。候选文档提交后仅做 metadata/文档/范围和fresh head检查，测试结果绑定未变的治理源哈希；最后请求绑定 exact Issue/branch/manual 的唯一最终 PR 提交确认。
