---
issue: 225
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/225
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
depends_on: []
status: approved
branch: change/225-actions-read-projection
created: 2026-09-05
updated: 2026-09-05
---

# Spec：actions 只读投影的两个假值

## 目标与原因

让 `gitea.actions.*` 这一组只读操作不再把「拿不到」伪装成「拿到了」。两处：
长日志的开头段现在结构性不可读，未开始的 run 的时长现在是一个荒谬但合法的整数。

两者同因：**投影层把上游的占位值当成了事实往外发**。日志那一处发的是「只有尾部的日志」
而没有任何手段取回头部；时长那一处发的是「零值时间参与减法的结果」。

## Acceptance criteria

- [ ] AC-1 `gitea.actions.job.logs.read` 在日志超过窗口时同时返回**开头段与结尾段**，
      中间一行标注省略字节数以及两端各自的实际字节数。
- [ ] AC-2 截断后的 `returned_bytes` **不超过** `LOG_MAX_BYTES`（65536）。
      标注行计入预算，不叠加在预算之上——旧实现返回 65577 是因为标注加在 64 KiB 之外。
- [ ] AC-3 未截断的日志逐字不变：`truncated: false`，`returned_bytes == original_bytes`，
      `log` 与上游脱敏后完全相同。
- [ ] AC-4 `gitea.actions.run.read` 对 `started_at` 或 `completed_at` 为零值时间
      （unix epoch、`0001-01-01`）的 run/job/step，把**该时间戳字段本身**投影为 `null`，
      并因此把 `duration_seconds` 投影为 `null`；不再返回 epoch 秒数。
- [ ] AC-5 已完成 run/job/step 的 `started_at`、`completed_at`、`duration_seconds` 取值不变。
- [ ] AC-6 单测覆盖 running（`completed_at` 零值）、cancelled-before-start（`started_at` 零值）、
      completed 三态，并覆盖头尾截断、预算上界与短日志原样返回。
- [ ] AC-7 窗口大小、方向与标注格式写进 `06-运维手册与踩坑集.md` 的 broker 段。
- [ ] AC-8 用一次真实的超过 64 KiB 的 job 日志验证：排在 `steps` 最前面的步骤，其 stdout 可读。
- [ ] AC-9 不改任何 typed 操作的 `arguments`，`codex/config/host-access-broker.json`
      的操作数保持 36，`bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

**`arguments` 不动。** typed `arguments` 是精确集合，给已有操作增删参数会让所有既有调用方
当场 `ARGUMENT_MISMATCH`（`06` 踩坑 26）。因此不取 Issue 正文的方案 2（`--step`/`--grep`）
与方案 3（`--offset`），本次只改返回投影。操作数不变，smoke 的三处枚举点不需要同步。

**日志窗口的头尾配比定为 1:3**，即头段拿走可用预算的四分之一（约 16 KiB），
尾段拿走其余四分之三（约 48 KiB）。理由是两端回答的不是同一类问题，所需篇幅也不同：

- **尾段回答「为什么失败」**，篇幅不可预测——一次 npm 报错、一段 stack trace、
  一张测试失败摘要都可以很长。它是既有实现唯一保留的部分，缩得太狠等于用一个新的
  失效换掉一个旧的。保留四分之三意味着此前能读到的失败摘要绝大多数仍然完整。
- **头段回答「跑的是哪棵树、在什么环境上」**，篇幅高度可预测且很短——runner banner、
  `actions/checkout` 的输出、检出 SHA、依赖安装的开头，量级是几 KB。
  16 KiB 对这一类证据是大幅过量，而这正是把 #225 那一整类失效一次性消灭所需要的全部。

配比写成常数 `LOG_HEAD_DIVISOR = 4` 而不是两个独立的字节数，是为了让
「头 + 尾 = 一个窗口」这条不变式由算术保证，改窗口时不会漏改一边。

**标注行计入预算。** 旧实现先切 64 KiB 再前缀标注，于是实际返回 65577 字节。
新实现先按标注可能达到的最大长度预留，再分配两段，因此 `returned_bytes` 恒 ≤ 65536。
预留量用整份日志的长度当三个占位数字的替身求得——省略字节数与任一端都不可能比整份日志长，
所以用更大的数渲染出的标注只会比真实的长，预留因此是上界而不是估计。

**零值时间戳投影为 `null` 是可见的返回值变化。** 既有调用方今天读到的
`started_at: "1970-01-01T08:00:00+08:00"` 是假值，改成 `null` 与 `_optional_text`
早已确立的「拿不到就给 null」一致，不新增也不删除字段。

## 风险与回滚约束

- broker 是共享核心：本次只改两个只读操作的返回投影，不触碰凭据、写路径、操作表与身份路由。
- source 合并不改变 installed broker 的字节。Mac 与 gitea-ci VM 各自重装前，
  实机行为不变。重装是人工交接项。
- 回滚即 revert 本 PR：单文件行为改动 + 单测 + 文档，无迁移、无状态、无部署产物。

## 非目标

- 不加 `--step` / `--grep` / `--offset` 参数。
- 不改窗口总量 `LOG_MAX_BYTES = 65536`。
- 不新增 typed 操作，不改 `arguments`，不动 operation_count。
- 不替 LocalWMS 撤掉 #193 的 tee + 末尾重印绕法。那是项目仓的决定，且在两台重装之前仍是它唯一可用的手段。
- 不执行两台重装。

## 未决问题

- 无。
