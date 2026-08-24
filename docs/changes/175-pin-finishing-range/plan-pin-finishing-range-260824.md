---
issue: 175
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/175
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
status: approved
branch: change/175-pin-finishing-range
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · 175-pin-finishing-range

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `codex/agent/change-merge-range.sh`：把 range 解析成「commit → Issue」的带 sha 归属结果，并产出 `selector` 行与 `pinned`；单测覆盖 | - | pending |
| T02 | `mark-completed-issues.sh` 改用该 library；计划新增 `selector` 行与逐行 `commit`；空范围自有错误 | T01 | pending |
| T03 | `apply-classification-labels.sh` 同改，plan/verify 两种模式都覆盖；窗口姿态与取值来源不动 | T01 | pending |
| T04 | `mark-deployed-issues.sh` 不改的理由写进头部注释，并用测试钉住它没有 `--range` 面 | - | pending |
| T05 | 改写 `issue-session-flow` 收尾第 2、3 步与 `03` §11；跑 `skill-for-claude/install.sh` | T02, T03 | pending |

每个 ticket 都是可独立验收的 vertical slice：T01 有自己的单测，T02/T03 各自的工具测试
在改完后立即全绿，T04 是一条断言，T05 是文档与 skill 的同步改写。

## Expected touch points

- T01：`codex/agent/change-merge-range.sh`（新增）、`codex/tests/test-change-merge-range.sh`（新增）、`codex/tests/smoke.sh`（登记新文件与新测试）
- T02：`codex/tools/mark-completed-issues.sh`、`codex/tests/test-mark-completed-issues.sh`
- T03：`codex/tools/apply-classification-labels.sh`、`codex/tests/test-apply-classification-labels.sh`
- T04：`codex/tools/mark-deployed-issues.sh`（仅注释）、`codex/tests/test-mark-deployed-issues.sh`
- T05：`skill-for-claude/issue-session-flow/SKILL.md`、`03-Issue-Spec-Plan与单闸门开发流程.md`

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `codex/tests/test-change-merge-range.sh` 断言 `pinned` 等于本次解析出的编号集合；`test-mark-completed-issues.sh` / `test-apply-classification-labels.sh` 断言把 `pinned` 的编号传给 `--apply` 得到与计划一致的写入；`03` §11 与 SKILL.md 收尾第 2、3 步的 diff review |
| AC-2 | `test-change-merge-range.sh` 断言 `selector` 行含 `range` 字面量与每条 commit 的 `commit`/`subject`/`issues`；两个工具测试断言逐 Issue 行带 `commit` 且等于产出它的 sha |
| AC-3 | 既有断言原样保留并全绿：`test-mark-completed-issues.sh` 的 #163 合取用例、`test-apply-classification-labels.sh` 的 `issue-closed` / `projection-window-closed` / 取值来源用例；新增断言「`--apply` 的 broker 参数面未新增任何键」 |
| AC-4 | `test-mark-deployed-issues.sh` 新增断言：`mark-deployed-issues.sh` 对 `--range` 报未知选项 / 不解析它；`03` §11 与工具头部注释的 diff review |
| AC-5 | `bash codex/tests/smoke.sh`；其中 `test-change-merge-range.sh` 含「两次运行之间 `git commit --allow-empty` 一次，同一个 `--range 'HEAD~1..HEAD'` 命中不同 Issue，而同一个 `pinned` 编号命中同一个 Issue」的确定性用例 |

## 部署与回滚

无部署影响：本仓 `deployment_lifecycle: none`，本次不改 broker、不改 CI、不改安装脚本
（`codex/agent/` 下的新 library 由既有的 same-directory-first / `../agent/` 解析找到，
两个消费工具都从仓库 checkout 运行，`install-vm.sh` 不安装它们）。

回滚：`git revert` 单个 merge。已安装的 Claude skill 副本回滚后需重跑
`skill-for-claude/install.sh` 使其与仓库源一致。
