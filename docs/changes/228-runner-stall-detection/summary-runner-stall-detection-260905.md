---
issue: 228
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/228
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 broker typed 只读操作属于共享核心与平台治理合同扩面，同时改动 CI 可靠性文档与运维处置顺序，触发强制 complex 规则
risk_flags:
  - shared-core
  - platform-governance
  - external-contract
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-runner-stall-detection-260905.md
  spec: spec-runner-stall-detection-260905.md
  plan: plan-runner-stall-detection-260905.md
  verification: verification-runner-stall-detection-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/228-runner-stall-detection
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/259
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

2026-08-29 事故里全平台 CI 停摆约 5 小时，而六个可用观测信号（`systemctl is-active`、
`systemctl status`、Gitea Actions 页面、`gitea.actions.run.read`、`gitea.commit.status.read`、
`orbstack.vm.status`）**没有一个能区分「runner 正忙」与「runner 领了 job 之后死锁」**。
LocalWMS 调度会话据此判断「正忙，等即可」而没有升级，直到实现会话进入 VM 看进程树才发现真相。

Issue #228 要求补两样东西：一个能让调度会话不进 VM 就区分忙与死的只读手段；一个 per-job
超时，使停滞被自动截断而不是无限期占住唯一执行位。

## 影响范围

- `codex/runtime/aisoft_host_access/`：新增一个 host-operator 路由的只读 typed 操作。
- `codex/config/host-access-broker.json`、`codex/tests/test-host-access-broker.sh`、
  `codex/runtime/tests/test_host_access.py`：操作表同步与计数。
- `01-基础设施-VM-Gitea-Runner.md` §4：act_runner 的超时与并发 as-built 事实与建议取值。
- `06-运维手册与踩坑集.md`：新增停滞判定手册段与一条踩坑（处置顺序）。
- 不改动任何业务仓、CI workflow、部署脚本或凭据。

## 初步方案与建议

1. 新增 `orbstack.runner.status`（host-operator，只读，无参数），一次性回读 act_runner 的
   systemd 状态、最近一条日志时间戳、最近一次领取的 task 与仓库，以及 act_runner 的
   直接子进程数与最老子进程的已运行秒数。
2. `runner.timeout` 的取值由三个仓的 CI 实测量级推出，写进 `01`；**VM 上的配置与重启是人工交接项**。
3. `06` 记录本次处置顺序（先在 Gitea 侧取消该仓 running 与 queued 的 run，再杀 PPID=1 的孤儿进程）
   与停滞判定规则表。

## 风险

- 取证阶段推翻了 Issue 正文的一个前提：act_runner **执行期间和完成时都不打日志**，
  每个 task 只有三行领取日志。所以「领了 job 之后零日志」不是死锁独有的信号，
  空闲与正常执行同样零日志。只按日志年龄判定会当场误报——本次实测即是一例。
  规避：判定规则以子进程存在性与已运行秒数为主，日志时间戳只作旁证。
- 新增 typed 操作要两台重装才生效，重装是人工交接项；未重装时调用返回 `REQUEST_DENIED`
  而不是权限问题（`06` 踩坑 20）。
- `runner.timeout` 的实际生效与超时后 Gitea 侧显示为失败，**本次无法验证**，
  必须由人在 VM 上配置并重启后单独验收。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 broker typed 只读操作属于共享核心与平台治理合同扩面，同时改动 CI 可靠性文档与运维处置顺序，触发强制 complex 规则
risk_flags:
  - shared-core
  - platform-governance
  - external-contract
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- broker 操作表是共享核心：`contract.py` 的 `EXPECTED_OPERATIONS` 有 33 项，
  被全部项目会话与全部治理工具消费，新增一项改变外部可调用面。
- AGENTS.md 明确「共享核心组件、CI/制品/部署/回滚，以及 Agent 或平台治理变更一律按 complex 处理」。
- 验收证据含只能在真实 VM 上一次性观测到的读数（journalctl、进程树、systemd 状态），
  required CI 无法复现，按 `03` §3 判据必须声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文给出五条验收标准；其中「超时触发时 Gitea 侧显示为失败」需要人先在 VM 上
  应用配置，本次以显式交接项与 NOT RUN 记录，不写成通过。
