---
issue: 222
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/222
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - authorization
  - platform-governance
depends_on: []
status: approved
branch: change/222-issue-list-state-set
created: 2026-09-05
updated: 2026-09-05
---

# Spec · #222 broker 的 gitea.issue.list 与 gitea.issue.state.set

## 目标与原因

给 broker 补两个 typed 操作，消除 Issue 正文实测到的两处流程缺口：调度会话立案前无法查重，
以及没有任何操作能改 Issue 的开闭状态（一次误关会经由
`apply-classification-labels.sh` 的 `projection-window-closed` 放大成实现会话的阻塞）。

两个操作都不触碰唯一交付硬闸门：PR 仍只由人合并（routine-auto 走它自己的独立路径），
终态标签仍由 `mark-completed-issues.sh` 按 `required_docs` 判定，判级投影仍由
`apply-classification-labels.sh` 管。

## Acceptance criteria

- [ ] **AC-1**：`gitea.issue.list` 是只读操作，`identity_route` 为 `project-agent`，
      `arguments` 恰为 `["state"]`，`--state` 接受 `open`、`closed`、`all`。
- [ ] **AC-2**：`gitea.issue.state.set` 是 mutating 操作，`identity_route` 为 `project-agent`，
      `arguments` 恰为 `["number","state"]`，可关闭与重开 Issue。该写入由
      `host.access.audit` 持续核对的同一个 project-agent 身份执行，`host.access.audit`
      读回该身份的 `repository_permission` 与 token scope 均与 manifest 一致。
- [ ] **AC-3**：`gitea.issue.state.set` 的 `--state` 只接受 `open` 与 `closed`；
      `all` 在解析凭据、发出任何请求之前被拒。
- [ ] **AC-4**：`gitea.issue.list` 分页取全，不是只读第一页；返回每条 Issue 的
      `number`、`title`、`state`、`labels`、`created_at`、`updated_at`，**不含 body**。
- [ ] **AC-5**：`gitea.issue.list` 的结果不含 pull request 条目，且被排除的条数在返回值里
      显式可读，不是静默丢弃。
- [ ] **AC-6**：两个操作都进 `codex/config/host-access-broker.json`；
      `operation_count` 由 34 变 36，`codex/tests/test-host-access-broker.sh` 的两处计数同步更新，
      `bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-7**：`06` 写明 typed `arguments` 是精确集合——少传与多传同样报
      `ARGUMENT_MISMATCH`——并给出实测例子；踩坑表新增对应一行。
- [ ] **AC-8**：不重装也能验收：用候选 manifest 直接调
      `python3 -m aisoft_host_access.cli ... broker --operation gitea.issue.list --state open`
      取到真实结果。两台重装为人工交接项，在 verification 中显式标注未执行。

## 接口、数据与兼容性影响

### `gitea.issue.list`（只读）

```
--operation gitea.issue.list --state {open,closed,all}
```

请求 `GET /repos/{owner}/{repo}/issues?state=<state>&type=issues&limit=50&page=<n>`，
逐页取到不足一页为止，上限 100 页（与 `_issue_comments` 同一约定；超出即
`RESPONSE_SCHEMA_INVALID`，不静默截断）。

返回**对象**：

```json
{
  "state": "open",
  "count": 15,
  "pull_requests_excluded": 0,
  "issues": [
    {"number": 222, "title": "...", "state": "open",
     "labels": ["needs-analysis"], "created_at": "...", "updated_at": "..."}
  ]
}
```

三条设计决定，各自有理由：

1. **返回对象而不是裸数组**。`GovernedHostRunner._call` 要求 broker 输出是 dict
   （`runner.py` 尾部 `if not isinstance(value, dict)` 直接抛 `RESPONSE_SCHEMA_INVALID`），
   裸数组会让新增的 runner 方法一调就失败。
2. **不带 body**。这个操作的用途是查重与枚举，不是读内容；`aisoft-platform` 当前 200 条以上
   Issue，带 body 会让一次列举的输出膨胀几个数量级，而正文本身用 `gitea.issue.read` 按号取。
3. **`pull_requests_excluded` 显式回报**。Gitea 的 `/issues` 端点默认同时返回 Issue 与 PR。
   服务端 `type=issues` 已经过滤，客户端按 `pull_request` 非空再滤一次是第二道网；
   计数回报使「服务端过滤失效」这件事可见，而不是把 PR 悄悄吞掉。

`labels` 投影为**名字数组**，与 `_issue_comments` 的投影取向一致：原始 label 对象带
id、color、url 与仓库路径，逐字透传会让一个受治理的只读面随 Gitea 的响应形状一起变。

### `gitea.issue.state.set`（写）

```
--operation gitea.issue.state.set --number <n> --state {open,closed}
```

`PATCH /repos/{owner}/{repo}/issues/{number}`，body `{"state": "<state>"}`。
返回与 list 同形的单条投影，另加 `changed`：

```json
{"number": 190, "title": "...", "state": "closed", "labels": ["needs-analysis"],
 "created_at": "...", "updated_at": "...", "changed": true}
```

`changed` 不是冗余字段：Gitea 在开闭变更上**不更新 `updated_at`**（实测四次调用读回同一个
时间戳），所以调用方没有别的办法分辨「真的改了」与「本来就是这个状态」。

- **`all` 被拒**：`--state` 的 argparse `choices` 为三值，因为它服务于
  `gitea.pulls.read`；`all` 不是一条 Issue 能处于的状态。校验在解析凭据之前完成，
  错误码用 `ARGUMENT_INVALID`——与紧邻的 `gitea.pulls.read` 对 `--state` 的校验同码，
  语义也对：参数集合是对的，值超出范围。
- **幂等**：目标状态与当前状态相同时，读回当前投影并返回 `changed: false`，不发 PATCH。
  重试因此不产生多余写入。

### 与既有治理面的关系

- **不改交付闸门**：PR 合并仍只由人（或 routine-auto 的独立 merger 在最终 head 全硬门后）完成。
- **判级投影窗口**：重开一条 closed Issue 会让 `apply-classification-labels.sh` 重新可写。
  这正是 Issue 要的恢复路径（LocalWMS #188 被误关后卡死），代价是 #167 的
  「closed Issue 永不补写」从物理不可能降级为流程约定。**本 spec 接受这个代价**：
  两者是同一个开关的两面，保留误关就无法恢复，加护栏就挡住 Issue 要的用例本身。
- **无写入流水账**：仓库里没有任何 broker 写入日志，`host.access.audit` 报的是
  凭据、token scope、仓库权限与分支保护的**姿态**。AC-2 因此按「写入由受审计身份执行」
  兑现，状态变化的逐次证据在 Gitea 的 Issue 时间线上，可由 `gitea.issue.read` 读回。

## 风险与回滚约束

| 风险 | 处置 |
|---|---|
| project-agent 可写面扩大到 Issue 开闭状态 | 判 complex；操作不接受除 number/state 外任何参数；唯一交付闸门不变 |
| 误关正在推进的 Issue | 由 `gitea.issue.state.set --state open` 直接恢复——这正是本 Issue 要解决的问题 |
| 大仓 `--state all` 一次拉全量 | 每页 50、上限 100 页；超出 fail-closed 而非静默截断 |
| 新操作未重装即调用 | 返回 `REQUEST_DENIED`，按踩坑 20 处置：两台重装，不往权限方向查 |

**回滚**：`git revert` 本次 commit 后两台重装 broker，操作表回到 34 项。已经被本操作
关闭或重开的 Issue 不会自动回滚，需人工在 Gitea 上改回——但那与今天没有该操作时的
人工路径完全一样，不构成不可逆状态。

## 非目标

- 不新增任何 CLI 参数（`--number` 与 `--state` 已存在）。
- 不做按 label、里程碑、作者或关键字的服务端筛选；查重按 title 在调用方本地做。
- 不新增 broker 写入日志或审计流水账——那是独立议题，不在本 Issue 范围内。
- 不给已有操作增删参数（`arguments` 是精确集合，加参数是破坏性变更，#243 已踩过）。
- 不改 `AGENTS.md`、controller、CI 或部署脚本。
