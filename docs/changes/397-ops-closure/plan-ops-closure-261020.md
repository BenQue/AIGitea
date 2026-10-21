---
issue: 397
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/397
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 391
status: approved
branch: change/397-ops-closure
created: 2026-10-20
updated: 2026-10-20
---

# #397 plan：运维闭环第二步（R16）

合同见 spec。每个 ticket 一个或数个本地原子 commit；治理文件（T01）单独提交后停下重读。

| Ticket | 内容 | 覆盖 AC | 确定性检查 |
|---|---|---|---|
| T01 | 治理：`issue-session-flow` 收尾加「重装并读回」、调度会话周清扫；`ci.yml` 加 push-main 触发 | AC2、AC7、AC9 | `test_session_contract`、smoke 技能钉子、`bash -n`；提交后重读 |
| T02 | `check-installed-drift`：`applies_to`、`--host`、macOS 系统链接别名、`installed-drift-baseline.json` 棘轮；夹具测试 | AC1 | `test-installed-drift.py`；Mac 与 VM（`--host vm`）真实读回 |
| T03 | `aisoft-alert-poll.sh` 判级投影闸门与测试 | AC3 | `test-aisoft-alert-poll.sh` 新用例（反向证明） |
| T04 | `aigitea-cleanup-merged.sh`：不自 fetch、remote 推断、`--remote-branches`；本机清理 | AC4 | 清扫测试；`git worktree list`、`git branch` 读回 |
| T05 | `06` §4 PAT 180 天；readiness `PAT_AGE` NOTE 与测试 | AC5 | readiness 测试三种情形 |
| T06 | `templates/project/ci/deploy-notify.sh` 与测试；`05` §1 | AC6 | 模板测试（失败、回滚、前置缺失 exit 0） |
| T07 | routine manifest 字段、policy、K1 routine 种类删除；`aisoft-loop` 死路径（R13 合并后开工） | AC8 | 两个 `validate`、runtime 单测、bootstrap/rotation 测试 |
| T08 | README、路线图、发布包 `--release`、verification；smoke 全绿；Codex 只读审查；判级投影 | AC10、AC11 | smoke、ShellCheck、`usage-bundle.sh --verify`、`--verify 397` |

AC12（合并后两台重装与读回）在收尾第 5 步执行。
