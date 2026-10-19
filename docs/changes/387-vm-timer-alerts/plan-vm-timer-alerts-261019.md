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
status: approved
branch: change/387-vm-timer-alerts
created: 2026-10-19
updated: 2026-10-19
---

# #387 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | broker 只读 `orbstack.vm.units.read`，单元测试与操作计数，源码 runtime 现场读回 | - | done |
| T02 | readiness `LIVE_VM_TIMERS`，夹具覆盖 PASS、无 timer、GAP、操作未安装、不可读 | T01 | done |
| T03 | Mac 轮询脚本、launchd 模板、安装/卸载脚本与夹具测试，smoke 登记 | T01 | done |
| T04 | `05` 状态行与 §5、`06` 速查与踩坑 34，本目录映射文档 | T02、T03 | done |
| T05 | VM 停用两个 timer（负责人执行命令，实现线程前后读回并观察 30 分钟） | - | pending |
| T06 | 全量 smoke 与 Codex 只读交叉审查，结论记入 verification | T04 | pending |
| T07 | 合并后两台重装 broker，读回新操作与 readiness 本节 PASS；负责人按 `05` §5 启用通知 | T06 | pending |

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/contract.py`、`broker.py`，`codex/config/host-access-broker.json`，`codex/tests/fixtures/manifests/host-access-broker.json`，`codex/runtime/tests/test_host_access.py`，`codex/tests/test-host-access-broker.sh`。不加 runner 方法：调用方是 readiness 与通知脚本，都走 CLI 入口。
- T02：`codex/tools/aisoft-platform-readiness.sh`、`codex/tests/test-platform-readiness.sh`。
- T03：`codex/tools/aisoft-alert-poll.sh`、`codex/tools/install-alert-agent.sh`、`codex/launchd/com.aisoft.platform-alerts.plist.template`、`codex/tests/test-alert-agent.sh`、`codex/tests/smoke.sh`（静态两处与执行区一处）。
- T04：`05-通知与多人协作.md`、`06-运维手册与踩坑集.md`、本目录四份文档。
- T05–T07：只改本目录 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1 | 停用前后 `systemctl --user list-timers --all` 与 `is-enabled` 读回；30 分钟后 `journalctl --user` 按失败 catalog id 无新记录 |
| AC2 | `python3 -m unittest tests.test_host_access`；`test-host-access-broker.sh`；源码 runtime 现场调用 |
| AC3 | `test-platform-readiness.sh`；源码 broker 与已安装 broker 各跑一次 readiness |
| AC4 | `test-alert-agent.sh`（含反向证明）；源码 broker 现场跑两次轮询 |
| AC5 | `git diff` 06 |
| AC6 | `bash codex/tests/smoke.sh`；Codex 只读审查；合并后两台重装与读回 |

## 部署与回滚

无应用部署。平台侧安装影响：合并后两台重装 broker（先 VM 后 Mac），负责人在 Mac 运行 `install-alert-agent.sh` 启用通知。回滚：timer `systemctl --user enable --now`；通知 `install-alert-agent.sh --uninstall`；代码 revert 本 PR 后两台重装。
