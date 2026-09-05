---
issue: 222
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/222
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增两个 broker typed 操作，其中一个是写路径；broker 是全平台共享核心与治理边界
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - authorization
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-issue-list-state-set-260905.md
  spec: spec-issue-list-state-set-260905.md
  plan: plan-issue-list-state-set-260905.md
  verification: verification-issue-list-state-set-260905.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/222-issue-list-state-set
pr_url:
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

broker 的 `gitea.issue.*` 操作集缺两个能力，Issue 正文给出了 LocalWMS M6 调度会话的实测代价：

- **没有任何操作能改 Issue 开闭状态**。`gitea.issue.update` 只接受 `number/title/body`，
  所以 Issue 只能靠 PR 正文的 `Closes #N` 自动关闭，或由人在 Gitea 界面操作。最严重的一次
  不是多点几下：LocalWMS #188 被误关后，`apply-classification-labels.sh` 的判级投影在
  `state != open` 时拒绝写入，该 Issue 的实现会话拿不到投影、PR 无法进入待合并，卡住直到人重开。
- **没有 `gitea.issue.list`**。只能按号 `gitea.issue.read`，调度会话无法枚举 open Issue，
  因此无法在立案前查重。实测产出两对重复 Issue（LocalWMS #187/#188、#189/#190）。

正文另外要求把一条已实测的 typed 参数语义写进文档：`arguments` 是**精确集合**，少传和多传
同样报 `ARGUMENT_MISMATCH`（实测 `gitea.actions.job.logs.read` 只声明 `["job"]`，
带上 `--sha` 一起发即被拒）。

## 影响范围

| 面 | 文件 | 变化 |
|---|---|---|
| 操作合同 | `codex/runtime/aisoft_host_access/contract.py` | `EXPECTED_OPERATIONS` 增两项，34 到 36 |
| 分发与实现 | `codex/runtime/aisoft_host_access/broker.py` | 两条 dispatch 分支与两个投影 helper |
| 受控调用方 | `codex/runtime/aisoft_host_access/runner.py` | 两个 fixed 方法 |
| 安装期操作表 | `codex/config/host-access-broker.json` | 两条 operations 条目 |
| 单元测试 | `codex/runtime/tests/test_host_access.py` | 新增用例，并把两项加入既有 typed-fields 表 |
| 契约测试 | `codex/tests/test-host-access-broker.sh` | `operation_count` 与 `[.operations[].name] length` 两处计数，加逐操作 arguments 断言 |
| 文档 | `06-运维手册与踩坑集.md` | §1.0 补两条命令与精确集合语义；踩坑表新增一行 |

`cli.py` **不改**：`--number` 与 `--state` 两个 argparse 参数已经存在，`--state` 的
`choices` 已是 `open/closed/all`。因此本次落在踩坑 20 的「六处同步」，不触发第七处
（`test_cli_exposes_only_typed_issue_and_pull_fields` 逐字钉死的 `execute()` kwargs 不变）。

## 初步方案与建议

- `gitea.issue.list`：只读，`project-agent`，`arguments ["state"]`。服务端 `type=issues`
  过滤 PR，客户端再按 `pull_request` 非空二次过滤并**回报被排除的条数**，不静默丢弃。
  分页取全（每页 50，上限 100 页），投影 `number/title/state/labels/created_at/updated_at`，
  **不带 body**。
- `gitea.issue.state.set`：写路径，`project-agent`，`arguments ["number","state"]`，
  `state` 只接受 `open/closed`（`all` 不是 Issue 能处于的状态，在解析凭据前就拒绝）。
- 返回**对象**而不是裸数组：`GovernedHostRunner._call` 硬性要求 broker 返回 dict，
  裸数组会让 runner 方法一调就 `RESPONSE_SCHEMA_INVALID`。

## 风险

- **写路径扩面**：project-agent 从此可以关闭与重开 Issue。这不触碰唯一交付硬闸门
  （PR 由人合并），但确实扩大了受治理身份的可写面，因此判 complex 并带 `authorization`。
- **判级投影窗口可被重新打开**：重开一条 closed Issue 会让 `apply-classification-labels.sh`
  重新可写。这既是 Issue 要的恢复路径（#188），也意味着 #167「closed Issue 永不补写」
  从此不再是物理不可能，而是流程约定。spec 里显式记录这一权衡。
- **验收标准第一条需要重述**：`host.access.audit` 是姿态审计（凭据、token scope、仓库权限、
  分支保护），**不是写入流水账**，仓库里也没有任何 broker 写入日志。见 spec AC-2 的兑现方式。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增两个 broker typed 操作，其中一个是写路径；broker 是全平台共享核心与治理边界
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - authorization
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

- `codex/config/host-access-broker.json` 现有 34 个操作，本次新增两个，`contract_effect: add`。
- `codex/runtime/aisoft_host_access/contract.py:415` 要求操作集合与 `EXPECTED_OPERATIONS`
  **恰好相等**，manifest 与 contract 必须同 commit 变更——这是共享核心而非局部改动。
- 新增的 `gitea.issue.state.set` 是 mutating，扩大 project-agent 的可写面，命中强制 complex
  规则里的 authorization 与 external-contract。
- 声明 `verification` 的判据（`03` §3）：验收证据包含候选 manifest 的实机 broker 调用与
  两台重装后的读回，二者都不能由 diff review 加 required CI 复现。

### 缺失的 acceptance criteria 或决策

- Issue 验收标准第一条写「`host.access.audit` 能看到该写入」。仓库里没有 broker 写入日志，
  `host.access.audit` 报的是凭据/scope/权限/保护姿态。spec 按「写入由受审计的 project-agent
  身份执行，状态变化落在 Gitea Issue 时间线」兑现，需人确认这一重述。
- `gitea.issue.state.set` 是否要加护栏（例如禁止关闭仍有 open PR 的 Issue）。本 spec 的
  取向是**不加**：Issue 正文明确要它能关重复、能重开误关的 Issue，任何护栏都会挡住这两个
  用例本身。需人确认。

## 遗留项（不在本 PR 内，交回人裁决）

> 原第 1 条（两份 `issue-session-flow` skill 的过渡说明）已在确认点 2 经人授权并入本 PR，
> 见 spec 的「治理文件授权」与 AC-9。

1. **`GovernedHostRunner` 有两个方法调不动。** `labels_read()` 与 `issue_labels_read()`
   对应的 broker 操作返回 JSON 数组，而 `runner.py` 的 `_call` 尾部要求返回值是 dict，
   否则抛 `RESPONSE_SCHEMA_INVALID`。这两个方法今天没有调用方，所以一直没暴露。
   本次新增的 `gitea.issue.list` 正是因为知道这条约束才返回对象而不是裸数组。
   **未在本 PR 内修**：改 `_call` 的返回契约会影响全部十几个 runner 方法，
   超出本 Issue 范围。按你「本轮不新开 Issue」的要求，只在此记录并回报。
2. **测试产物 Issue #260** 停在 closed 状态，标题 `test(#222): gitea.issue.state.set
   验收用一次性 Issue`，正文写明是验收产物。不需要任何人处理。
