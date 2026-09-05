---
issue: 228
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/228
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - platform-governance
  - external-contract
  - ci-change
depends_on: []
status: approved
branch: change/228-runner-stall-detection
created: 2026-09-05
updated: 2026-09-05
---

# Spec · #228 runner 停滞检测与 per-job 超时

## 目标与原因

让调度会话**不进 VM** 就能把「runner 正忙」与「runner 领了 job 之后死锁」分开，
并给出一个有实测依据的 per-job 超时取值，使停滞被自动截断而不是无限期占住唯一执行位。

### 取证结论（决定了方案形状）

以下四条都是本次在 gitea-ci 上实测的，其中前两条推翻了 Issue 正文的前提：

1. **act_runner 只在领取时打日志**。每个 task 恰好三行（`task N repo is ...` /
   `Running job with maxParallel=1` / `NewParallelExecutor`），执行期间和完成时一行都没有。
   所以「领了 job 之后零日志」在空闲、正常执行和死锁三种状态下**完全一致**，
   单看日志年龄会误报。实测当场即得一例：最后一条领取日志停在 `11:25:40`，
   读数时刻 `15:25`，静默四小时，而 runner 其实完全空闲。
2. **`runner.timeout` 不是「设得过大」，而是根本没有配置文件**。
   `/opt/act-runner/config.yaml` 不存在，`act_runner.service` 的 `ExecStart` 也没有 `-c`，
   所以 act_runner v1.0.7 走内置默认值：`runner.timeout: 3h`、`runner.capacity: 1`。
3. **runner 是 host executor**（注册标签 `ubuntu-latest:host`），job 以 act_runner 的
   **直接子进程**运行。因此 `ps --ppid <ExecMainPID>` 是一个决定性的探针：
   零子进程即空闲，有子进程即正在执行，最老子进程的已运行秒数即本次执行已耗时。
4. **三个仓的 CI 量级**（`gitea.actions.run.read`，只统计 success run）：

   | 仓库 | 样本数 | 最短 | 中位 | p90 | 最长 |
   |---|---|---|---|---|---|
   | `admin/aisoft-platform` | 17 | 49s | 55s | — | 57s |
   | `admin/LocalWMS` | 26 | 61s | 66s | 127s | 345s |
   | `admin/NewEMaint` | 22 | 236s | 259s | 269s | 296s |

## Acceptance criteria

- [ ] AC-1 broker 新增只读 typed 操作 `orbstack.runner.status`（`host-operator` 路由、
      `mutating: false`、无参数），一次调用回读：systemd 的 `ActiveState`/`SubState`/`ExecMainPID`、
      act_runner 最近一条日志的时间戳与其年龄秒数、最近一次领取的 task 编号与仓库全名、
      act_runner 直接子进程数与最老子进程的已运行秒数。
- [ ] AC-2 该操作不回传任何日志正文。只回传解析出的结构化字段，原始日志留在 VM 上。
- [ ] AC-3 操作表七处同步全部完成，`operation_count` 由 33 变 34，
      `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-4 在**不重装 broker** 的前提下，用候选 manifest 直接调用
      `aisoft_host_access.cli` 验收该操作，回读真实 VM 读数。
- [ ] AC-5 空闲与执行中两种状态各取一次真实读数，证明返回值确实把两者分开。
- [ ] AC-6 `01` §4 记录 act_runner 的超时与并发 as-built 事实（无配置文件、内置默认 3h、
      capacity 1）与建议取值及其实测依据。
- [ ] AC-7 `06` 记录停滞判定规则表（含「零日志不等于死」这条反直觉事实）
      与本次处置顺序：先在 Gitea 侧取消该仓 running 与 queued 的 run，再杀 PPID=1 的孤儿进程。
- [ ] AC-8 「人在 VM 上写 `config.yaml`、给 `ExecStart` 加 `-c`、重启 act_runner」
      写成显式交接项，且 verification 里对应条目如实记为 NOT RUN。

## 接口、数据与兼容性影响

### 为什么叫 `orbstack.runner.status` 而不是 Issue 正文建议的 `gitea.runner.status`

broker 的 `execute()` **按名字前缀分派**：`gitea.` 开头进 `_gitea()`，
用 project-agent 凭据走 Gitea HTTP API。本操作的数据源是 VM 的 systemd journal 与进程表，
经 `orb` 到达，与 `orbstack.vm.status` 同源同凭据。叫 `gitea.` 要么谎报了访问面，
要么必须在 `gitea.` 分支里开一个特例。因此沿用 `orbstack.` 前缀。

### 返回结构

```json
{
  "status": "PASS",
  "project": "<project_id>",
  "operation": "orbstack.runner.status",
  "machine": "gitea-ci",
  "unit": "act_runner.service",
  "service": {"active_state": "active", "sub_state": "running", "main_pid": 533},
  "last_log": {"timestamp": "...", "age_seconds": 14364},
  "last_task": {"id": 1010, "repository": "admin/aisoft-platform", "claimed_at": "..."},
  "execution": {"child_count": 0, "oldest_child_elapsed_seconds": null}
}
```

`last_task` 在日志窗口内没有领取行时为 `null`；`execution.oldest_child_elapsed_seconds`
在 `child_count` 为 0 时为 `null`。

### 为什么不由 broker 给出 verdict

broker 只回事实，不回判断。阈值是随各仓 CI 量级漂移的策略常量，写进 broker 会与
`01` 里的实测表两地分叉。判定规则连同它的依据一起放在 `06`，由调用方按表比对。
`execution.child_count == 0` 本身是事实而不是判断，已经足够承担「空闲 vs 执行中」这一半。

### 兼容性

纯增量。既有 33 个操作的名字、参数、路由和返回结构都不变。未重装 broker 的机器调用
新操作返回 `REQUEST_DENIED`，与既有 fail-closed 行为一致。

## 风险与回滚约束

- 新操作在 VM 上执行三条固定 argv 的只读命令（`systemctl show` / `journalctl` / `ps`），
  不传 shell、不接受调用方参数，无写操作，因此没有需要回滚的状态。
- `ExecMainPID` 取自 systemd 输出后作为 `ps --ppid` 的参数，必须先校验为纯数字且非零，
  否则 fail closed。
- 回滚方式：revert 本 PR 后在两台重装 broker，操作表回到 33 项。

## 非目标

- 不在本次改动 VM 上的任何配置或服务状态；`runner.timeout` 的应用是人工交接项。
- 不新增定时检查或告警通道。
- 不新增取消、重跑或杀进程的 typed 操作——那是人的决定，typed 化会把它变成可自动化的动作。
- 不修复 `gitea.actions.run.read` 对未完成 run 的 `duration_seconds` 计算错误（另立 Issue）。
- 不改动 Gitea 的 `[cron.cleanup_actions]` 配置。

## 未决问题

无。
