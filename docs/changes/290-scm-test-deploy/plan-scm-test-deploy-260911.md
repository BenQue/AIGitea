---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: approved
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
---

# 计划

| Ticket | blocked_by | 内容 | 验收 |
|---|---|---|---|
| T01 | [] | 独立合同与说明调整，提交后停止 | AC-5 |
| T02 | [T01] | 下一轮重读合同，实现scm-ci/test条件及矩阵/生命周期测试 | AC-1–4 |
| T03 | [T02] | 回归、diff审查、唯一manual PR确认 | AC-1–5 |

T01不实施runtime；T02无需重复询问本次已明确的行为选择。不得在T01改AGENTS。

预期验证：PYTHONPATH=codex/runtime:. python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release*.py'；矩阵须有production零副作用反例。semantic docs check、git diff --check。无shell修改则不增加shell专项。
source可Git revert；部署/数据库回滚不由该source变更执行。现场始终NOT RUN直到独立回执。
