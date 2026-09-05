---
issue: 225
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/225
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: broker 是共享核心组件，本次改的是两个 governed read 的返回投影，所有调用方都读它
risk_flags:
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-actions-read-projection-260905.md
  spec: spec-actions-read-projection-260905.md
  plan: plan-actions-read-projection-260905.md
  verification: verification-actions-read-projection-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/225-actions-read-projection
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/262
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`gitea.actions.*` 这一组只读操作有两个投影缺陷，都会让读者拿到一个**看起来合法、实际不是事实**的值。

**一、日志截头不截尾。** `gitea.actions.job.logs.read` 在超过 64 KiB 时只保留尾部，
前缀一行 `[truncated: N leading bytes omitted]`。尾部偏置本身有道理——失败步骤的报错打印在最后——
但它把「排在前面的步骤的输出」变成了结构性不可读。而 CI 里排在前面的恰恰是检出信息、
环境校验、依赖安装这类出了问题最需要看的步骤。LocalWMS Issue #193 的 run 835 是一次真实失效：
`Check out merge preview` 打印的「本次检出的是哪棵树」落在被丢弃的 119843 字节里，
逐步骤时间线能证明该步退 0，但**跑的是哪棵树取不回来**。

**二、`duration_seconds` 在某些 run 上返回 unix epoch。** 实测 `admin/LocalWMS`
run 1016 返回 `1788522654`、run 1007 返回 `1788503541`。

## 影响范围

- `codex/runtime/aisoft_host_access/broker.py`：`_actions_job_logs` 的截断分支、
  `_duration_seconds`，以及 run/job/step 三处时间戳投影点。
- `codex/runtime/tests/test_host_access.py`：截断与 duration 的单测。
- `06-运维手册与踩坑集.md`：broker 段的日志窗口说明，踩坑表新增一行。
- **不动** `codex/config/host-access-broker.json`：不新增操作、不改 `arguments`，
  operation_count 保持 36。

## 初步方案与建议

**日志**取 Issue 正文的方案 1 + 4：在同一个 64 KiB 预算内同时保留头尾两段，
中间用一行标注省略字节数与两端各自的实际字节数；窗口大小、方向与标注格式写进 06。
不改调用签名——typed `arguments` 是精确集合，给已有操作加参数是破坏性变更（踩坑 26）。

**duration** 的归因需要更正 Issue 评论的说法。评论写的是「没有 `completed_at` 的 run」，
实测读数不是这样：

| run | status | conclusion | started_at | completed_at | duration_seconds |
|---|---|---|---|---|---|
| 1016 | completed | cancelled | `1970-01-01T08:00:00+08:00` | `2026-09-04T19:50:54+08:00` | 1788522654 |
| 1007 | completed | cancelled | `1970-01-01T08:00:00+08:00` | `2026-09-04T14:32:21+08:00` | 1788503541 |

缺的是 **`started_at`**：这两条是**排队时被取消、runner 从未领取**的 run，
Gitea 把 Go 的零值时间按服务器时区渲染成 `1970-01-01T08:00:00+08:00` 发了出来。
减法本身没错，错的是其中一个操作数不是时间。

推论有两条，都改变了修法：

- **running run 早就返回 `null`**，因为零值落在 `completed_at` 上会撞进既有的 `end < start` 守卫。
  真正漏网的是「从未开始」这一态，不是「尚未结束」。
- 只把 `duration_seconds` 置 null 不够：`started_at` 字段本身仍然会把
  `1970-01-01T08:00:00+08:00` 当事实报出去，读者可以照样自己减一遍得到同样的荒谬值。
  修在**时间戳投影层**——零值时间戳一律投影为 `null`——才是消灭这个值，而不是把它挪个地方。

## 风险

- broker 是共享核心，改的是返回投影，所有读 CI 证据的会话都受影响。缓解：只放宽可读性
  与只把假值改成 `null`，不改 `arguments`、不改操作表、不改任何写路径。
- 生效需要两台重装（踩坑 20）。本次交付到 source 合并为止，重装是人工交接项，写进 verification。
- `started_at` 从「1970 字符串」变成 `null` 是返回值形状的可见变化。既有调用方读到的
  本来就是假值，改成 `null` 是把 `_optional_text` 已有的「拿不到就给 null」约定补齐，
  不新增字段、不删字段。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: broker 是共享核心组件，本次改的是两个 governed read 的返回投影，所有调用方都读它
risk_flags:
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md` 把「共享核心组件」列为强制 complex，`broker.py` 是全平台唯一治理访问路径。
- `contract_effect: change`：`gitea.actions.job.logs.read` 的 `log` 正文构成与
  `gitea.actions.run.read` 的时间戳/时长取值都会变，属于既有 governed read 的外部行为变更，
  不是恢复既有合同。
- 声明 `verification`：验收要求「用一次真实的长 job 日志验证靠前步骤 stdout 可读」，
  这份证据来自实机 Gitea 的真实 job，diff review 与 required CI 都重放不了；
  两台重装同样只能靠一次真实观测记录（判据见 `03` §3，与复杂度无关）。

### 缺失的 acceptance criteria 或决策

- 无。头尾配比由本次按既有 64 KiB 总量裁定并在 spec 说明理由，Issue 正文已授权
  「头 N KB + 尾 N KB」的形状而把 N 留给平台裁。
