---
issue: 184
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/184
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: []
depends_on: []
status: contract-drafting
branch: change/184-project-target-fail-closed
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan：目标仓库由 checkout 判定

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 共享解析库 `codex/agent/aisoft-project-target.sh`：从 checkout remote 反查 `project_id`/`repository`，合并显式 `--project`，四种结局（推断成功 / 显式覆盖 / 不一致 / 不可确定）各自有确定输出 | - | pending |
| T02 | `apply-classification-labels.sh` 接入 T01：移除默认值、输出带 `project`/`repository`、plan 与 `--verify` 两个模式同受保护 | T01 | pending |
| T03 | `mark-completed-issues.sh` 接入 T01：移除默认值、输出带 `project`/`repository`、保留 #163 与 #172 既有行为 | T01 | pending |
| T04 | 基线观测与改动前后对比写进映射的 verification（真实 LocalWMS checkout 上的假通过/假失败，以及修复后的结果） | T02 | pending |

每个 ticket 结束时 `bash codex/tests/smoke.sh` 必须全绿；T02/T03 各自的专项测试也必须全绿。

## Expected touch points

- **T01**：新增 `codex/agent/aisoft-project-target.sh`。放在 `codex/agent/` 而不是
  `codex/lib/`：它被 `codex/tools/*` 以「同目录优先，其次 `../agent/`」的方式 source，与 #175 的
  `change-merge-range.sh` 消费者相同；`codex/lib/`（#171）装的是 installer 从 `$ROOT` source 的库，
  不随工具进入扁平安装目录。
- **T02**：`codex/tools/apply-classification-labels.sh`、`codex/tests/test-apply-classification-labels.sh`。
  测试侧需要：mock broker 变为 project-aware（按 `--project` 分别返回 state/labels）；
  fixture 仓加一个指向 fixture Gitea 的 remote；新增 fixture access/governance manifest；
  新增假通过形状的 Issue 601。
- **T03**：`codex/tools/mark-completed-issues.sh`、`codex/tests/test-mark-completed-issues.sh`。
  测试侧需要：既有 `run()` 显式传 `--project`（fixture 仓保持无 remote，以便覆盖「不可确定」
  一路），末尾另加带 remote 的推断用例。
- **T02/T03 共同**：`codex/tests/smoke.sh` 的 `bash -n` 列表补入新库文件（ShellCheck 已按
  `codex/agent/*.sh` 通配覆盖）。
- **文档**：`03-Issue-Spec-Plan与单闸门开发流程.md` 中描述这两个工具的段落补上新合同；
  `06-运维手册与踩坑集.md` 增加一条踩坑（默认值静默读错仓库的症状与识别方式）。
- **不触碰**：`codex/tools/host-access-broker.sh`、`codex/runtime/**`、`codex/config/**`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-apply-classification-labels.sh`：断言 broker.log 中 `--project` 全部等于推断出的 fixture 项目，且 `grep -c -- '--project aisoft-platform'` 为 0 |
| AC-2 | 同上：Issue 601 的 `--verify` 非零退出且 `reason == "projection-missing"`；同时断言若目标误为 decoy 项目则其标签恰好构成 `projected`（fixture 数据自证形状） |
| AC-3 | 两个工具的测试各一条：`--project <另一个项目>` 配可推断的 checkout → 非零退出、stdout 为空、broker.log 行数为 0 |
| AC-4 | 两个工具的测试各一条：无 remote 的 checkout 且不传 `--project` → 非零退出、broker.log 行数为 0、stderr 含 `--project` |
| AC-5 | 两个工具的测试：`jq -e '.project == ... and .repository == ...'` 覆盖 plan / `--apply` / `--verify` 三类输出行 |
| AC-6 | 两个工具的测试：无 remote 的 checkout + 显式 `--project` → 退 0 且结论正确（`mark-completed` 的既有全部用例即此形态） |
| AC-7 | `bash codex/tests/smoke.sh`；两个专项测试文件的既有断言逐条保留不改语义 |
| AC-8 | `grep -rn -- '--project)' codex/tools/` 输出写进 summary「影响范围」；`03` 段落 diff review |
| AC-1/AC-2 真实系统 | 映射的 verification：改动前后在 `/Users/benque/Projects/LocalWMS` 上跑同一条 `--verify 1 11 57`，记录退出码与输出 |

## 部署与回滚

无部署影响。回滚为 `git revert` 单个 commit；两个工具从 checkout 运行，不存在已安装副本需要同步。
