---
issue: 115
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/115
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/115-issue-labels-completed
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/119
created: 2026-08-15
updated: 2026-08-15
---

# Spec：`completed` 终态可达，Issue 级标签写入成为 typed 能力

## 目标与原因

让「已合并且无需部署」的变更能够到达它唯一正确的终态，并把 Issue 级标签写入纳入 broker
typed 操作面。

根因不是「忘了写一行推进代码」，而是**没有任何组件处在能观察到「合并」的位置上**：
controller 的 `_set_lifecycle` 七处调用全在 Loop 内，Loop 在创建 PR 时结束；`mark-deployed`
只覆盖部署路径；`apply-analysis` 会让已合并 Issue 状态倒退。因此本 Issue 交付的是一个
**合并后阶段的执行者**，而不是修补既有组件。

### 与 #108 的边界（已定）

#108 交付的是**仓库级标签定义**（`/repos/{o}/{r}/labels`），本 Issue 交付**Issue 级标签挂载**
（`/repos/{o}/{r}/issues/{index}/labels`）。命名区分沿用 #108 确立的规则：**有 `issue.` 段的是
挂载，无的是定义。**

#108 的两项成果是本 Issue 的前提：canonical manifest 已是 `schema_version: 2` 的单一事实源；
`project_extensions.allowed_prefixes` 使 Issue 上可能合法挂着 `area/*`、`priority/*`。

## Acceptance criteria

- [ ] **AC-1**：新增 typed 操作 `gitea.issue.labels.read`（project-agent、只读、参数 `number`）
      与 `gitea.issue.labels.set`（project-agent、mutation、参数 `number` + `lifecycle`）。
      `lifecycle` 取值从安装期 label manifest 的八个生命周期标签派生；越界取值 fail closed，
      不静默忽略。
- [ ] **AC-2**：`set` **只改 lifecycle 一个维度**。同一 Issue 上的 `type/*`、`complexity/*`、
      `triage/*` 与项目扩展标签（`area/*`、`priority/*`）在操作前后逐一不变。测试以同时挂
      四类标签的 Issue fixture 证明。
- [ ] **AC-3**：目标 lifecycle 标签在仓库中不存在时 fail closed，并在错误信息中指向
      `gitea.labels.provision`（#108），而不是创建标签——定义与挂载是两个操作面。
- [ ] **AC-4**：已带 `deployed` 的 Issue 请求 `completed` 被拒绝。两个终态互斥且 `deployed`
      更强，降级必须是显式的人工决定，不能由本工具静默完成。
- [ ] **AC-5**：幂等——目标 lifecycle 已是该 Issue 当前唯一 lifecycle 时返回 `result: "no-op"`
      且不发出 `PUT`；连续执行两次，第二次输出与第一次一致。
- [ ] **AC-6**：`completed` 的判定依据取自该 Issue 映射 summary 的 `required_docs` 是否含
      `verification`，不接受人工传入的复杂度或终态判断。判定发生在工具层，**不在 broker 内**。
- [ ] **AC-7**：八个 lifecycle 名从 manifest 派生并由新工具与
      `mark-deployed-issues.sh` 共用；仓库内不再有第二处硬编码的 lifecycle 列表。
- [ ] **AC-8**：本 PR 内**任何 Issue 的真实标签零变更**。推进工具默认 dry-run，真实写入需要
      显式 `--apply`。
- [ ] **AC-9**：`bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

### broker typed 操作（新增两项，22 → 24 → 26）

```python
"gitea.issue.labels.read": ("project-agent", False, ("number",)),
"gitea.issue.labels.set":  ("project-agent", True,  ("number", "lifecycle")),
```

CLI 新增 `--lifecycle`。取值**不在 argparse 里写死 choices**——那会成为第六份 manifest 副本；
在 broker 内对照已加载的 label manifest 校验，越界返回 `ARGUMENT_MISMATCH`。

`set` 的算法（复用 `aisoft_loop/gitea.py:_reconcile_labels` 已验证的投影语义，不新写一套）：

1. 读 Issue 当前标签与仓库标签定义（取 id）。
2. `final = {当前标签中所有非 lifecycle 的 id} ∪ {目标 lifecycle 的 id}`。
3. 目标已是当前唯一 lifecycle → 不发 `PUT`，返回 `no-op`。
4. 当前含 `deployed` 且目标为 `completed` → `REQUEST_DENIED`。
5. `PUT /issues/{number}/labels`，返回 `{issue, before, after, result, status}`。

**没有删除任意标签的能力**，也不能清空 lifecycle：`set` 的语义是「替换 lifecycle 维度」，
不是「设置任意标签集合」。

### 终态推进工具（新增）

`codex/tools/mark-completed-issues.sh`，与 `mark-deployed-issues.sh` 对称：

- 输入合并范围或显式 Issue 号，解析 `change/N-slug` 与 `Closes #N`。
- 对每个候选 Issue：`aisoft_loop.cli resolve-documents N` → 读 summary front matter 的
  `required_docs` → 含 `verification` 则**跳过并说明理由**（该变更需要部署，终态应是 `deployed`）。
- 默认 dry-run，输出机器可读计划；`--apply` 才经 broker `gitea.issue.labels.set` 写入。
- 判定逻辑全在此工具，broker 只做受约束的写——**broker 不读 change 文档、不做业务判定**，
  这条边界与既有 typed 操作一致。

### lifecycle 单一事实源

`codex/agent/gitea-label-manifest.sh`（#108 建立）新增 `aisoft_label_manifest_lifecycle`，
与既有 `_canonical` / `_prefixes` / `_retired` 三个 reader 并列。
`mark-deployed-issues.sh:77` 的硬编码数组改为调用它。

### 向后兼容性

- 不改变任何标签语义，不改 `completed` / `deployed` 的定义与互斥关系。
- 不改 controller、`apply-analysis` 与 Loop 的任何既有行为——它们本来就不在合并后阶段。
- 既有 22 个 typed 操作的签名与身份路由不变。

## 风险与回滚约束

| 风险 | 缓解 |
|---|---|
| `set` 擦掉 type/triage/项目扩展标签 | 复用既有投影语义 + AC-2 的四类标签 fixture |
| 需要部署的变更被误标 `completed` | 判定取自 `required_docs`；AC-4 对已 `deployed` fail closed |
| broker mutation 面扩大 | 仅两个参数、仅 lifecycle 维度、无删除、无自由文本 |
| **manifest 改动后未重装 broker** | #108 实测坑：新操作返回 `REQUEST_DENIED`，形似权限问题。Mac 与 gitea-ci VM 两台都要跑 `install-host-access-broker.sh`，写入 PR 交接说明 |
| 第六份 lifecycle 副本悄悄出现 | AC-7 + 一条禁止硬编码 lifecycle 列表的 smoke 断言 |

回滚：单 PR revert。无数据迁移、无制品、无部署；因 AC-8 保证零真实标签变更，回滚无残留状态。

## 非目标

- **不开放 `type/*`、`complexity/*`、`triage/*` 的写入**（2026-08-15 决策）。`complexity/*` 是
  AI 判级输出、`triage/*` 是 Matt 编排输出，二者都有既定产出链路；开放手工写入等于提供绕过
  它们的路径。将来若确有需要，另开 Issue 扩展。
- **不执行任何真实 Issue 的终态补齐**（2026-08-15 决策，沿用 #108 先例）。NewEMaint #65/#67、
  平台 #107/#108 的补齐是合并后另行授权的动作。
- 不新增标签删除能力（与 #108 一致，刻意排除）。
- 不改 CI workflow、required context 或部署链路；不给 runner 发放 Issue 写凭据。
- 不实现定时巡检或自动触发——执行时机由人决定。

## 未决问题

> 进入 `approved` 前必须清空所有会改变实现方向的未决问题。

无。起草过程中的三个分叉均已定：

1. **谁推进终态** —— 独立工具。controller 结构上不在场（Loop 在建 PR 时结束）；合并后 CI
   步骤需扩大 runner 凭据面并改 required context，本身即治理变更。按证据判定，非人工偏好。
2. **`set` 的取值粒度** —— 仅 lifecycle 维度（2026-08-15 用户决策）。
3. **是否顺带补齐历史 Issue** —— 否，只交付能力（2026-08-15 用户决策）。
