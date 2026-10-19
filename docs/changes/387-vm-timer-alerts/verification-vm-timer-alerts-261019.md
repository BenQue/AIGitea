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

- Commit SHA: `515eb94`（实现提交 `f3a6310`、`022bcb3`、`d4256a3`、`2c0adbf`，Codex 审查修复 `7f5c7c0`、`679fcd2`、`515eb94`）
- 基线：`origin/main` = `7eca227`
- 环境: macOS 本机源码 runtime（`codex/tools/host-access-broker.sh` 在源码树内读仓库 manifest）与已安装 broker 对照；gitea-ci VM `coder` 用户只读
- 本记录负责证明的 acceptance criteria: AC1–AC6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 停用前 `orb -m gitea-ci -u coder systemctl --user list-timers --all` 与 `is-enabled`（2026-10-19T14:54:34Z，14:54:59Z 复读一致） | 基线 | 两个 timer `enabled`、`active (waiting)`，每 15 分钟触发，上次 22:43:38 CST |
| 源码 runtime `orbstack.vm.units.read --project aisoft-platform` | PASS | `timer_count 3`；`agent-poll.timer` 与 `aisoft-agent@emaintenance.timer` 均 `enabled`、service `failed / exit-code / exit_status 20`、`failures_24h 49`、`last_failure_at 2026-10-19T14:43:38Z`；`systemd-tmpfiles-clean.timer` `disabled`、0 次 |
| 24 小时失败分布（journal 按小时） | 观测 | 每小时 2–4 次，01–09 时与 19–22 时无记录（本次 boot 自 10-18 16:18 起，间隙对应 VM 未运行时段），故 49 次而非 96 次 |
| `python3 -m unittest tests.test_host_access` @ `2c0adbf` / `7f5c7c0` | PASS | 213 / 217 tests OK（`VmUnitsReadTests` 9 项，修复后 13 项） |
| 反向证明：`2c0adbf` 的 broker 跑 `7f5c7c0` 的 `VmUnitsReadTests` | FAIL（符合预期） | 12 个失败（截断、异常字段、journal 过滤与异常记录各子用例） |
| `bash codex/tests/test-host-access-broker.sh` | PASS | operation_count 39 |
| readiness，源码 broker | GAP（符合预期） | `LIVE_VM_TIMERS GAP enabled=2 failing=agent-poll.timer:49,aisoft-agent@emaintenance.timer:49` |
| readiness，已安装 broker | BLOCKED（符合预期） | `LIVE_VM_TIMERS BLOCKED operation-not-installed` |
| `bash codex/tests/test-platform-readiness.sh` | PASS | PASS、无 timer、GAP、未安装、不可读五种 |
| 轮询脚本，源码 broker，连续两次（桩通知器） | PASS | 第一次弹两条 timer 通知 `new=2`，第二次 `new=0` |
| 轮询脚本，已安装 broker，连续两次 | PASS | 第一次弹一条 `broker unreadable: orbstack.vm.units.read:REQUEST_DENIED`，第二次 `new=0` |
| `bash codex/tests/test-alert-agent.sh`（bash 5 与 `/bin/bash` 3.2） | PASS | 两者均 `alert agent tests passed` |
| 反向证明：删掉去重判断后跑 `test-alert-agent.sh` | FAIL（符合预期） | rc=1；恢复后 PASS |
| 反向证明：`2c0adbf`、`7f5c7c0` 的轮询脚本各跑下一轮的 `test-alert-agent.sh` | FAIL（符合预期） | rc=5、rc=1 |
| `test-alert-agent.sh` @ `515eb94`，`/bin/bash` 3.2.57 与 `python:3.12-bookworm` bash 5.2.15 + jq 1.6 | PASS | 两者均 `alert agent tests passed` |
| 修复后源码 broker 现场：`orbstack.vm.units.read`、readiness、轮询脚本 | PASS | 两个 timer 仍各 `failures_24h 49`；`LIVE_VM_TIMERS GAP`；首次 `new=2` |
| macOS 全量 `bash codex/tests/smoke.sh` @ `2c0adbf`、`7f5c7c0`、`679fcd2`、`515eb94` | PASS | 四次 rc=0，`Codex platform static smoke checks passed.`；`project-leak (4 baseline files, 11 hits)` 与改动前相同 |
| 推送范围离线闸门：`GitRepository.scope` + `verify_history` | PASS | `git_scope` 19 项与 `git diff --name-only 7eca227 HEAD` 相等，逐 commit 校验通过 |
| `check-change-documents --repo .` | PASS | `change-documents`、`change-pr-url` PASS，gap 0 |
| Codex 只读审查第 1 轮（`codex exec -s read-only`，`2c0adbf`） | FAIL | B1 journal 全用户共用 5000 行截断可漏报；B2 缺字段与异常记录被当成健康；B3 CI 响应结构异常清告警或中止；B4 06 踩坑 34「旧 provider」与 spec 冲突 |
| Codex 复审第 2 轮（`7f5c7c0`） | FAIL | B1、B2、B4 关闭，B3 原例关闭；新阻塞：PR 列表嵌套字段异常在 process substitution 里被吞，清掉已有 CI 告警 |
| Codex 复审第 3 轮（`679fcd2`） | PASS-WITH-NITS | 阻塞关闭，`git_scope` 相等；nit：未知 CI state 应算不可读，已在 `515eb94` 处理 |
| `shellcheck` 新增与改动的 shell | PASS | 无输出 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | 待执行 | 停用前读回已记录；等负责人执行停用命令 |
| AC2 | PASS | 单元测试与源码 runtime 现场读回；只回传状态词、计数与时间；异常输出 fail closed |
| AC3 | PASS | 夹具 PASS、无 timer、GAP、未安装、不可读、结构异常六种；源码与已安装 broker 现场对照 |
| AC4 | PASS | 夹具覆盖 CI 失败、timer 失败、无变化不重复、broker 不可用只报一次，另含结构异常与多 PR 部分失败；`05` §5 写清启用与卸载 |
| AC5 | PASS | `06` 踩坑 34 |
| AC6 | 部分 | 全量 smoke PASS，Codex 交叉审查 PASS-WITH-NITS 且 nit 已处理；合并后两台重装与读回待执行 |

## 遗留风险与未完成项

- AC1 停用由负责人执行命令，实现线程读回并观察 30 分钟。
- AC6 合并后两台重装需负责人执行（Mac 侧 sudo）；重装前已安装入口对新操作返回 `REQUEST_DENIED`，readiness 报 `operation-not-installed`，通知弹一次 broker 不可读。
- 通知的 launchd 启用由负责人在合并后运行 `install-alert-agent.sh`，本记录未在真实 launchd 上安装（测试用桩 `launchctl`）。
- readiness 测试在 Linux 容器里因 worktree 的 `.git` 指向宿主路径而不可运行，bash 5 覆盖由 PR CI 提供。
