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

# Verification · #228

## 基线与范围

- Commit SHA: `d1ae0cc61c6f5cc09b10d408e9ec23fcabb073b1`（PR 259 head）
- 基线：`origin/main` = `00f7d539...`（PR 253 / #250 合并后重新 rebase；rebase 后 smoke 重跑仍 exit 0）
- 环境：Mac 本机 checkout ＋ gitea-ci OrbStack VM（只读）
- 本记录负责证明的 acceptance criteria: AC-1 ~ AC-8

## 改动前的基线观测（合并后无法重放）

这一节的读数只在改动前才取得到，全部来自 2026-09-05 的 gitea-ci。

| 观测 | 命令 | 读数 |
|---|---|---|
| act_runner 版本与标签 | `act_runner --version`；`/opt/act-runner/.runner` | `gitea-runner version v1.0.7`；`labels: ["ubuntu-latest:host"]` |
| 有没有配置文件 | `sudo ls -la /opt/act-runner/` | **无 `config.yaml`**；目录里只有 `.runner`、`promote-to-prod.sh`、缓存目录 |
| ExecStart 有没有 `-c` | `systemctl cat act_runner` | `ExecStart=/usr/local/bin/act_runner daemon`，**无 `-c`** |
| 因此生效的默认值 | `act_runner generate-config` | `runner.timeout: 3h`、`runner.capacity: 1`、`runner.shutdown_timeout: 0s` |
| Gitea 侧第二道超时 | `sudo sed -n '46,53p' /etc/gitea/app.ini` | `[actions]` 只有 `ENABLED = true`；**无 `[cron.cleanup_actions]` 段** |
| Gitea 版本 | `gitea --version` | `1.26.4` |

### 日志形状（推翻了 Issue 正文的前提）

`journalctl -u act_runner -n 40 --output=short-iso --no-pager` 显示：每个 task 恰好三行
（`task N repo is ...` / `Running job with maxParallel=1` / `NewParallelExecutor`），
**执行期间和完成时一行都没有**。task 1005–1010 的领取行彼此间隔约 1 分钟，
而 task 999 与 1000 之间静默 67 分钟——那是空闲，不是停滞。

同一时刻的直接反例：最后一条领取日志是 `2026-09-05T11:25:40+08:00`，读数时刻 `15:25`，
静默 4 小时，而 `ps -o pid,ppid,etime,stat,comm --sort=start_time` 显示 act_runner（PID 533）
**零子进程**，runner 完全空闲。**按「零日志超过 N 分钟」判定会在这里当场误报。**

### 三仓 CI 实测量级（broker `gitea.actions.run.read`，只统计 success run）

| 仓库 | 样本 | 最短 | 中位 | p90 | 最长 |
|---|---|---|---|---|---|
| `admin/aisoft-platform` | 17 | 49s | 55s | — | 57s |
| `admin/LocalWMS` | 26 | 61s | 66s | 127s | 345s |
| `admin/NewEMaint` | 22 | 236s | 259s | 269s | 296s |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONPATH=... python3 -m unittest tests.test_host_access.ActRunnerStatusTests -v` | PASS | `Ran 10 tests ... OK` |
| `PYTHONPATH=... python3 -m unittest tests.test_host_access -q` | PASS | `Ran 168 tests ... OK` |
| `bash codex/tests/smoke.sh`（T01 后） | PASS | `Ran 681 tests ... OK` / `Codex platform static smoke checks passed.` / exit 0 |
| `bash codex/tests/smoke.sh`（T03 后，全量） | PASS | `Ran 681 tests in 41.696s` / `OK` / `Codex platform static smoke checks passed.` / `EXIT=0` |
| `bash codex/tests/smoke.sh`（全部改动就位后，最终一次） | PASS | `Ran 681 tests in 35.912s` / `OK` / `Codex platform static smoke checks passed.` / `SMOKE3_EXIT=0` |
| `apply-classification-labels.sh --verify 228` | PASS | `"project":"aisoft-platform","repository":"aisoft-platform","result":"projected","change_type":"platform","complexity":"complex"` |
| `aisoft-loop check-change-documents` | PASS | `PASS: change-documents` / `PASS: change-pr-url` / `changes=112 pass=2 gap=0` |
| PR 259 上的 required CI | PASS | run 1056（`pull_request`），head `d1ae0cc61c6f5cc09b10d408e9ec23fcabb073b1`，`completed / success / 55s` |
| 安装的 broker 调用新操作 | 预期失败（已复现） | `{"code": "REQUEST_DENIED", "message": "requested operation is not allowlisted", "status": "BLOCKED_EXTERNAL"}`——这正是 `06` 踩坑 20 的形态，证明交接项 1 尚未执行 |
| 候选 manifest 直接调用（空闲态） | PASS | 见下方读数 A |
| 候选 manifest 直接调用（执行中） | PASS | 见下方读数 B |
| VM 上应用 `runner.timeout: 20m` 并重启 | **NOT RUN** | 人工交接项，见下方交接清单 |
| 超时触发后 Gitea 侧 run 显示为失败 | **NOT RUN** | 依赖上一项先由人完成 |

### 读数 A：runner 空闲（真实 VM，未重装 broker）

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
    --access-manifest codex/config/host-access-broker.json \
    --governance-manifest codex/config/gitea-governance.json \
    --label-manifest codex/config/gitea-labels.json \
    broker --project aisoft-platform --operation orbstack.runner.status
{
    "execution": {"child_count": 0, "oldest_child_elapsed_seconds": null},
    "last_log": {"age_seconds": 15723, "timestamp": "2026-09-05T03:25:40Z"},
    "last_task": {"age_seconds": 15723, "claimed_at": "2026-09-05T03:25:40Z",
                  "id": 1010, "repository": "admin/aisoft-platform"},
    "machine": "gitea-ci",
    "observed_at": 1788594463,
    "operation": "orbstack.runner.status",
    "project": "aisoft-platform",
    "service": {"active_state": "active", "main_pid": 533, "sub_state": "running"},
    "status": "PASS",
    "unit": "act_runner.service"
}
```

这一条读数本身就是本 Issue 的论点：`last_log.age_seconds` 是 15723 秒（4 小时 22 分），
按日志年龄判定会报「停滞」；`execution.child_count == 0` 同时证明它其实**完全空闲**。

### 读数 B：runner 执行中（真实 VM）

同一条命令，在 `admin/aisoft-platform` 的 task 1011 执行期间取得：

```json
{
    "execution": {"child_count": 1, "oldest_child_elapsed_seconds": 0},
    "last_log": {"age_seconds": 3, "timestamp": "2026-09-05T07:50:51Z"},
    "last_task": {"age_seconds": 3, "claimed_at": "2026-09-05T07:50:51Z",
                  "id": 1011, "repository": "admin/aisoft-platform"},
    "machine": "gitea-ci",
    "observed_at": 1788594654,
    "service": {"active_state": "active", "main_pid": 533, "sub_state": "running"},
    "status": "PASS",
    "unit": "act_runner.service"
}
```

同一个 run 内连取六次，`oldest_child_elapsed_seconds` 随真实时间递增，
证明它量的是真实执行时长而不是一个常数：

```
observed_at  execution                                                  task
1788594669   {'child_count': 1, 'oldest_child_elapsed_seconds': 15}     1011
1788594669   {'child_count': 1, 'oldest_child_elapsed_seconds': 15}     1011
1788594669   {'child_count': 1, 'oldest_child_elapsed_seconds': 15}     1011
1788594670   {'child_count': 1, 'oldest_child_elapsed_seconds': 15}     1011
1788594670   {'child_count': 1, 'oldest_child_elapsed_seconds': 16}     1011
1788594670   {'child_count': 1, 'oldest_child_elapsed_seconds': 16}     1011
```

### A 与 B 的对照就是本 Issue 要的那一维

| | 读数 A（空闲） | 读数 B（执行中） |
|---|---|---|
| `service.active_state` | `active` | `active` |
| `service.sub_state` | `running` | `running` |
| `execution.child_count` | **0** | **1** |
| `execution.oldest_child_elapsed_seconds` | `null` | 0 → 16（递增） |

systemd 侧两次完全一致——那正是原来六个信号的处境。分开它们的是 `execution` 这一对字段。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 新增只读 typed 操作并回读六类事实 | PASS | 读数 A/B 含 `service` 三项、`last_log`、`last_task`、`execution` 两项；`test_operation_is_read_only_host_operator_and_argument_free` 钉住路由、非 mutating 与空参数集 |
| AC-2 不回传日志正文 | PASS | `test_no_journal_text_crosses_the_boundary` 断言序列化结果不含 `NewParallelExecutor` / `level=info` / `msg=` / `localhost:3000`；读数 A/B 中也没有 |
| AC-3 七处同步与 smoke 全绿 | PASS | `operation_count` 33→34；`bash codex/tests/smoke.sh` 两次 exit 0，`Ran 681 tests ... OK`。第三处 `runner.py` 经核对无需改动（见下） |
| AC-4 免重装、候选 manifest 验收 | PASS | 读数 A/B 都由 `python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json ...` 取得，安装的 broker 未重装 |
| AC-5 空闲与执行中两组读数 | PASS | 读数 A 与读数 B 的对照表 |
| AC-6 `01` §4.1 as-built 与建议取值 | PASS | `01-基础设施-VM-Gitea-Runner.md` §4.1，含实测表与 20m 推导 |
| AC-7 `06` 判定规则与处置顺序 | PASS | `06` §1.0.1 判定表、§1.0.2 处置顺序、踩坑 23 |
| AC-8 交接项与 NOT RUN 如实记录 | PASS | 本文「人工交接清单」三项全部标 NOT RUN，执行结果表对应两行同样标 NOT RUN |

### 关于「七处同步」的第三处

`06` 踩坑 20 列的第三处是 `runner.py`。`GovernedHostRunner` 只覆盖 Issue/change/PR
生命周期，既有的 `orbstack.vm.status` 与四个 `vm.profile.*` 都不在其中；本操作同属
host-operator 路由，同样不进。这是**核对后确认无需改动**，不是漏改。

## 人工交接清单（本次未执行）

以下三项都需要 VM 上的 root 权限或会中断正在执行的 job，**本次全部 NOT RUN**：

1. **两台重装 broker**。合并后在 Mac 与 gitea-ci VM 各执行一次
   `sudo bash codex/install-host-access-broker.sh`，再用
   `--operation host.access.audit` 与 `--operation orbstack.runner.status` 确认。
   未重装时新操作返回 `REQUEST_DENIED`——那是安装期操作表陈旧，不是权限问题（`06` 踩坑 20）。
2. **应用 `runner.timeout: 20m`**。步骤见 `01` §4.1。必须先确认
   `execution.child_count == 0`（重启会杀掉正在执行的 job）。
3. **验证超时确实生效**。构造一个会挂住的 job，确认 20 分钟后 Gitea 侧该 run 变为
   **失败**而不是永远排队，且失败原因可读。这一条是 Issue #228 的第二条验收标准，
   在第 2 项完成前无法验证。

## 遗留风险与未完成项

- `runner.timeout` 是否能中断一个在 FIFO `open()` 上阻塞的 job，本次未验证。
  2026-08-29 那次阻塞了 4h19m，**超过了当时生效的 3h 默认值**，所以「默认超时没能截断它」
  是既有事实。缩短取值不必然改变这一点；上面交接清单第 3 项就是为验证它而列的。
  在它被验证之前，`orbstack.runner.status` 的停滞判定是本平台唯一可依赖的检测手段。
- Gitea 侧 `[cron.cleanup_actions]` 的内置默认值本次**未在本机回读**，只确认了「无显式配置」。
- **与 PR 257（#201）在 `06` 上的冲突已实际发生并已解决**：两条变更都往踩坑表尾部加了一行、
  都编号为 **23**——正是踩坑 22 描述的形态。PR 257 先合并占住 23，本分支 rebase 时 git 如实
  报了 `CONFLICT (content)`，本次把自己的一条改成 **24**。`01` 两侧改的是不同小节
  （本次 §4.1、#201 §5），自动合并无冲突。
  值得记下的是：这一次冲突**被检测到了**，因为两侧行文不同；踩坑 22 那次没有被检测到，
  是因为两侧文本恰好相同。可检测与否取决于文本是否巧合相同，不取决于语义是否冲突。
- broker 的 `gitea.actions.run.read` 对没有 `completed_at` 的 run（cancelled / running）
  把 `duration_seconds` 算成了一个 unix epoch（实测 `admin/LocalWMS` run 1016 返回
  `1788522654`）。这是本次取证顺带发现的独立缺陷，**不在本 Issue 范围内**，另立 Issue。
