---
issue: 167
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/167
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: approved
branch: change/167-classification-window-gate
created: 2026-08-24
updated: 2026-08-24
---

# Spec · 判级投影窗口的合并前闸门

## 目标与原因

判级投影的窗口在合并时静默关闭。目标是让「投影尚未完成」在窗口关闭**之前**被一条确定性
命令报出来，并把这条命令放在会话必经的路径上，使它不依赖执行者记得去查。

不改变的是 #160 的姿态：已关闭 Issue 不补写判级标签，不提供 override。要修的是提醒，
不是补写能力。

## Acceptance criteria

- [ ] **AC-1** `codex/tools/apply-classification-labels.sh --verify <selector>` 读回 Issue 的
      当前标签，与映射 summary 的 `change_type` / `effective_complexity` 比对，并给出四选一的
      确定性结论：`projected`、`projection-missing`、`projection-mismatch`、
      `projection-window-closed`。只有全部为 `projected` 时退出码为 0。
- [ ] **AC-1a** `--verify` 是只读的：只调用既有的非 mutating 操作 `gitea.issue.read` 与
      `gitea.issue.labels.read`，在任何情形下都不调用 `gitea.issue.labels.classify`。
      `--verify` 与 `--apply` 互斥，同时给出即报错退出。
- [ ] **AC-1b** `skill-for-claude/issue-session-flow/SKILL.md` 的待合并块新增 `判级:` 一行，
      要求填入 `--verify` 的真实读回结果，并明确写出「不是 `projected` 就不进入待合并，
      合并会永久关闭窗口」。收尾步骤要求对本 Issue 跑一次 `--verify`，
      把 `projection-window-closed` 显式报出来并按 `03` §11 记录。
- [ ] **AC-1c** `skill-for-claude/aisoft-platform/SKILL.md` 的会话标准动作第 4 步写明
      窗口在合并时关闭、`--verify` 是唯一能区分「已投影」与「从没投影过」的检查，
      并把 `broker-operation-missing` 的处置写进同一步。
- [ ] **AC-2** broker 因操作表陈旧而拒绝时（stderr 含 `REQUEST_DENIED` 与 `not allowlisted`），
      工具报 `broker-operation-missing`，`detail` 直接说明操作表是安装期固定的、需要在
      Mac 与 gitea-ci 两台重装，并给出 `sudo bash codex/install-host-access-broker.sh`
      与 `06` 踩坑 20 的指引。该翻译对工具发出的每一个 broker 调用一致生效。
- [ ] **AC-3** 不新增 typed broker 操作，不新增 override 开关，
      `--apply` 对 closed Issue 的行为逐字不变（仍是 `skip / issue-closed`，不写入）。
      plan 与 apply 两种模式的既有输出字段与退出语义不变。
- [ ] **AC-4** `03` §11 写明对 #163、#138、#146、#148 的处置结论与依据，
      并附读回证据；不对任何已关闭 Issue 发起写入。
- [ ] **AC-5** `bash codex/tests/smoke.sh` 全绿；
      `codex/tests/test-apply-classification-labels.sh` 覆盖 AC-1、AC-1a、AC-2、AC-3。

## 接口、数据与兼容性影响

### 命令行

新增互斥模式开关 `--verify`。既有调用形态（无开关 = 计划、`--apply` = 写入、
`--repo` / `--range` / `--project` / 位置参数）逐字不变。

### JSON 输出

verify 模式复用既有 emit 结构，`action` 取 `verify`，并新增一个可选字段：

| 字段 | 语义 |
|---|---|
| `remedy` | 有可执行补救时给出那一条命令；**没有补救时该键不出现** |

`remedy` 的缺席本身就是机器可读的结论：窗口已关闭时无事可做。

verify 的逐 Issue 结论：

| 结论 | 触发条件 | 计入失败 | `remedy` |
|---|---|---|---|
| `projected` | 两个维度的标签都存在且与 summary 一致 | 否 | 无 |
| `projection-missing` | Issue 仍 open，一个或两个维度没有标签 | 是 | `--apply N` |
| `projection-mismatch` | Issue 仍 open，某维度有标签但取值与 summary 不同 | 是 | `--apply N` |
| `projection-window-closed` | Issue 已 closed 且未投影 | 是 | 无 |
| `documents-unresolved` / `classification-missing` / `classification-incomplete` | 读不出判级 | 是 | 无 |
| `broker-operation-missing` / `state-unreadable` / `labels-unreadable` | 读不出 Issue 现状 | 是 | 视情形 |

closed 且已投影 = `projected`，不是失败：窗口关闭对一个已经做完的 Issue 没有意义。

### 与 plan 模式的差异（刻意）

plan 模式里 `documents-unresolved` 一类是非失败 skip，verify 模式里计为失败。
两种模式回答的问题不同：plan 问「我会写什么」，缺文档只是没得写；verify 问
「它现在是不是已经投影了」，读不出证据不等于是。plan/apply 的退出语义不受影响。

## 风险与回滚约束

- **闸门误报会让人学会忽略它。** 四种结论全部由读回证据决定，不含推测；
  证据不足一律计为失败并说明读不到什么，不输出「大概没问题」。
- **修复不得依赖它要修的前提。** verify 用的两个操作在新增 `gitea.issue.labels.classify`
  之前就已存在，因此 broker 即使是旧表，闸门照常工作：先报「没投影」，
  `--apply` 再报「需要重装」。
- **skill 改动的生效边界。** 源在 `skill-for-claude/`，已安装副本要跑 `install.sh` 才更新；
  `check-drift.sh` 已能报告漂移，本次不改该机制。
- **回滚**：单 PR revert 即可。工具改动是纯增量模式，plan/apply 路径不变；
  文档与 skill 回到前一版本，无数据、无外部状态、无部署影响。

## 非目标

- 不改 `gitea.issue.labels.classify` 的写入语义，不改 `mark-completed-issues.sh` 的终态判定（#163 交付物）。
- 不补写任何已关闭 Issue 的标签，不提供 override 开关，不新增 typed broker 操作。
- 不引入自动合并、自动重装或后台自动写标签。
- 不改 `skill-for-claude/install.sh` 与 `check-drift.sh` 的机制，不在本变更内重装本机 skill 或 broker。
- 不给 `#168`（verification 模板与作者指引）做任何铺垫或改动。

## 未决问题

- 无。
