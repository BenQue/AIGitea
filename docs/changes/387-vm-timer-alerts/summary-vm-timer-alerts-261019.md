---
issue: 387
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/387
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 broker 只读 typed 操作与 readiness 检查、引入 Mac 本地失败通知，并在 VM 上停用两个 agent 定时器，涉及共享核心、平台治理与运维回滚
risk_flags:
  - shared-core
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-vm-timer-alerts-261019.md
  spec: spec-vm-timer-alerts-261019.md
  plan: plan-vm-timer-alerts-261019.md
  verification: verification-vm-timer-alerts-261019.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/387-vm-timer-alerts
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/388
created: 2026-10-19
updated: 2026-10-19
---

## 问题/需求总结

gitea-ci VM 上 `coder` 用户的 `agent-poll.timer` 与 `aisoft-agent@emaintenance.timer` 自 2026-08-12 起每 15 分钟失败一次，两个多月无人知道（复审 P0-3）；平台对自己的 VM 没有任何失败观测，`05` 的失败通知自 7 月备案未实施（复审 P1-6）。本批只做止血，合同与验收见 spec。

## 影响范围

broker 新增只读 `orbstack.vm.units.read`（contract、broker、两份 manifest、单元测试与 shell 测试的操作计数）；`aisoft-platform-readiness.sh` 新增 `LIVE_VM_TIMERS`；新增 Mac 轮询脚本、launchd 模板与安装/卸载脚本及其测试，登记进 smoke；`05` 状态行与 §5、`06` 速查与踩坑 34。VM 上两个 timer 停用（运维动作，不改仓库内单元文件）。使用层发布包成员不变。

## 初步方案与建议

broker 以 VM 运行用户身份读 systemd --user 的 timer 与对应 service，失败次数按 systemd「unit failed」catalog id 从 journal 计数，不读日志正文；readiness 与通知脚本都只经 broker 读取。timer 用 `systemctl --user disable --now` 停用，单元文件保留。

## 风险

新操作需合并后两台重装 broker 才对已安装入口可用，未装时 readiness 报 `operation-not-installed`、通知弹一次 broker 不可读。停用可一条 `enable --now` 恢复。见 spec。

## AI 判级

```yaml
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 broker 只读 typed 操作与 readiness 检查、引入 Mac 本地失败通知，并在 VM 上停用两个 agent 定时器，涉及共享核心、平台治理与运维回滚
risk_flags:
  - shared-core
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 新增 broker typed 操作改变共享核心与 host-access 合同面，属于新增功能与平台治理，强制 complex。
- VM 定时器停用与两台重装后的读回不能由 diff review 与 required CI 复现，因此声明 verification。

### 缺失的 acceptance criteria 或决策

- 无；D1、D2 已由负责人 2026-10-19 确认。
