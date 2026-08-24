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

# Implementation plan · 判级投影窗口的合并前闸门

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 工具：broker 调用统一捕获 stderr，`REQUEST_DENIED / not allowlisted` 翻译成 `broker-operation-missing`（AC-2） | - | pending |
| T02 | 工具：只读 `--verify` 模式与四选一结论、`remedy` 字段、与 `--apply` 互斥（AC-1、AC-1a、AC-3） | T01 | pending |
| T03 | 测试：verify 四种结论、只读性、broker 翻译、plan/apply 行为不变（AC-5） | T02 | pending |
| T04 | 合同文档：两个 Claude skill 的必经路径、`03` §11 的窗口与历史处置、`06` 踩坑 20 的反向索引（AC-1b、AC-1c、AC-4） | T02 | pending |

T01 先行是因为 T02 的两个读操作要复用同一个 broker 调用助手；先有助手，verify 才不会
再写一遍捕获逻辑。

## Expected touch points

- `codex/tools/apply-classification-labels.sh`（T01、T02）
  - 新增 `run_broker()`：分别捕获 stdout / stderr / rc，供三处调用共用。
  - 新增 `broker_failure_reason()`：stderr 命中 `REQUEST_DENIED` + `not allowlisted`
    时返回 `broker-operation-missing` 与含重装命令的 detail，否则返回调用点自己的原因。
  - 新增 `--verify`；`emit()` 增加第 9 个位置参数 `remedy`（空则该键不出现）。
  - `--apply` 与 `--verify` 同时给出时 `fail` 退出。
- `codex/tests/test-apply-classification-labels.sh`（T03）
  - mock broker 增加 `gitea.issue.labels.read` 分支，按 fixture 返回不同标签集合。
  - 新增 fixture Issue：已投影、未投影、维度取值不符、closed 未投影。
- `skill-for-claude/aisoft-platform/SKILL.md`（T04）——会话标准动作第 4 步与 Common Mistakes。
- `skill-for-claude/issue-session-flow/SKILL.md`（T04）——待合并块、收尾第 2 步、Red Flags。
- `03-Issue-Spec-Plan与单闸门开发流程.md` §11（T04）——「谁投影」小节。
- `06-运维手册与踩坑集.md` 踩坑 20（T04）——一句反向索引。

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-apply-classification-labels.sh`：四个 verify fixture 各断言 `action == "verify"` 与对应 `reason`/`result`；全 `projected` 时 rc=0，任一非 projected 时 rc≠0 |
| AC-1a | 同上：verify 跑完后断言 `broker.log` 中 `gitea.issue.labels.classify` 计数为 0；`--verify --apply` 同时给出时断言 rc≠0 且 stderr 含互斥说明 |
| AC-1b | Review：`skill-for-claude/issue-session-flow/SKILL.md` 待合并块含 `判级:` 行与「不是 projected 不进入待合并」，收尾步骤含 `--verify` |
| AC-1c | Review：`skill-for-claude/aisoft-platform/SKILL.md` 第 4 步含窗口说明、`--verify` 与 `broker-operation-missing` 处置 |
| AC-2 | `bash codex/tests/test-apply-classification-labels.sh`：mock broker 以 exit 20 + stderr `{"code":"REQUEST_DENIED","message":"requested operation is not allowlisted"}` 回应 classify，断言 `reason == "broker-operation-missing"` 且 detail 含 `install-host-access-broker.sh`，rc≠0 |
| AC-3 | 同上：既有全部断言原样保留并通过（closed Issue 仍 `skip/issue-closed` 且不被写入，plan 无写入，`--apply` 只写选中的 Issue） |
| AC-4 | Review：`03` §11 含四个 Issue 的处置结论、依据与读回证据；`git log -p` 确认本 PR 未发起任何标签写入 |
| AC-5 | `bash codex/tests/smoke.sh` |

## 部署与回滚

无部署影响。本仓 `deployment_lifecycle: none`（#163），终态为 `completed`。
回滚方式：revert 本 PR 的单个 merge commit——工具改动是纯增量模式，plan/apply 路径逐字不变，
文档与 skill 回到前一版本；无数据、无外部状态、无服务需要重启。
已安装的 Claude skill 副本随下一次 `skill-for-claude/install.sh` 回到 revert 后的版本。
