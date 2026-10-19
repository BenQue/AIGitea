---
issue: 387
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/387
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on: []
status: pending
branch: change/387-vm-timer-alerts
created: 2026-10-19
updated: 2026-10-19
---

# #387 验证记录

## 基线与范围

- Commit SHA: 待定（实现提交 `f3a6310`、`022bcb3`、`1b0b6b1` 起）
- 基线：`origin/main` = `7eca227`
- 环境: macOS 本机源码 runtime（`codex/tools/host-access-broker.sh` 在源码树内读仓库 manifest）与已安装 broker 对照；gitea-ci VM `coder` 用户只读
- 本记录负责证明的 acceptance criteria: AC1–AC6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 停用前 `orb -m gitea-ci -u coder systemctl --user list-timers --all` 与 `is-enabled`（2026-10-19T14:54:34Z，14:54:59Z 复读一致） | 基线 | 两个 timer `enabled`、`active (waiting)`，每 15 分钟触发，上次 22:43:38 CST |
| 源码 runtime `orbstack.vm.units.read --project aisoft-platform` | PASS | `timer_count 3`；`agent-poll.timer` 与 `aisoft-agent@emaintenance.timer` 均 `enabled`、service `failed / exit-code / exit_status 20`、`failures_24h 49`、`last_failure_at 2026-10-19T14:43:38Z`；`systemd-tmpfiles-clean.timer` `disabled`、0 次 |
| 24 小时失败分布（journal 按小时） | 观测 | 每小时 2–4 次，01–09 时与 19–22 时无记录（本次 boot 自 10-18 16:18 起，间隙对应 VM 未运行时段），故 49 次而非 96 次 |
| `python3 -m unittest tests.test_host_access` | PASS | 213 tests OK（含新增 `VmUnitsReadTests` 9 项） |
| `bash codex/tests/test-host-access-broker.sh` | PASS | operation_count 39 |
| readiness，源码 broker | GAP（符合预期） | `LIVE_VM_TIMERS GAP enabled=2 failing=agent-poll.timer:49,aisoft-agent@emaintenance.timer:49` |
| readiness，已安装 broker | BLOCKED（符合预期） | `LIVE_VM_TIMERS BLOCKED operation-not-installed` |
| `bash codex/tests/test-platform-readiness.sh` | PASS | PASS、无 timer、GAP、未安装、不可读五种 |
| 轮询脚本，源码 broker，连续两次（桩通知器） | PASS | 第一次弹两条 timer 通知 `new=2`，第二次 `new=0` |
| 轮询脚本，已安装 broker，连续两次 | PASS | 第一次弹一条 `broker unreadable: orbstack.vm.units.read:REQUEST_DENIED`，第二次 `new=0` |
| `bash codex/tests/test-alert-agent.sh`（bash 5 与 `/bin/bash` 3.2） | PASS | 两者均 `alert agent tests passed` |
| 反向证明：删掉去重判断后跑 `test-alert-agent.sh` | FAIL（符合预期） | rc=1；恢复后 PASS |
| `shellcheck` 新增与改动的 shell | PASS | 无输出 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | 待执行 | 停用前读回已记录；等负责人执行停用命令 |
| AC2 | PASS | 单元测试与源码 runtime 现场读回；只回传状态词、计数与时间 |
| AC3 | PASS | 夹具五种情况；源码与已安装 broker 现场对照 |
| AC4 | PASS | 夹具测试覆盖四种情况及反向证明；`05` §5 写清启用与卸载 |
| AC5 | PASS | `06` 踩坑 34 |
| AC6 | 待执行 | 全量 smoke、Codex 审查、合并后两台重装 |

## 遗留风险与未完成项

- AC1 停用由负责人执行命令，实现线程读回并观察 30 分钟。
- AC6 合并后两台重装需负责人执行（Mac 侧 sudo）；重装前已安装入口对新操作返回 `REQUEST_DENIED`。
