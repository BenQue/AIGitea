---
issue: 134
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/134
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/134-change-control-phase
pr_url: ''
created: 2026-08-21
updated: 2026-08-21
---

# Spec · 按交付阶段分级 required_docs（#134）

## 1. manifest schema

repository 条目新增**可选**键 `change_control`，取值 `development` 或 `production`。

- 未声明则为 `production`（缺省取更严的一档）；
- 非法取值抛 `ContractError`，**不静默回落**；
- 可选键的放行不得退化为「任意键都接受」：`_exact_keys` 增加显式 `optional` 参数，未知键仍然拒绝。

## 2. 判级运行时

`Classification.route(*, change_control="production")`：

| 阶段 | 强制 complex 的 required_docs |
|---|---|
| `production` | `summary` + `spec` + `plan`（+ `verification`） |
| `development` | `summary`（+ `verification`） |

**`verification` 的取舍两阶段完全相同**，仍由 analyzer 输出决定。原因：`required_docs` 含 `verification` 同时承载着「该变更要部署，终态是 `deployed` 而非 `completed`」这一既有语义（见 `codex/tools/mark-completed-issues.sh`）。若在 `development` 下无条件附加 verification，会把不部署的变更误判为要部署。

`small` 路由完全不受阶段影响。

## 3. 验收标准的来源

`production` 的 complex 从 spec 的验收章节取 acceptance criteria。`development` 没有 spec，改由 **Issue 正文**提供，与 small 同源。

**门槛本身不放宽**：缺可测验收仍然 fail closed。这是刻意的——verification 文档要证明的正是这些标准，没有标准则 verification 无从成立。

## 4. 解析链路

新增 `codex/runtime/aisoft_loop/change_control.py`。Loop 只掌握 `GITEA_REPO`，按仓库名查 governance manifest（`AISOFT_GOVERNANCE_MANIFEST`，缺省 `/usr/local/share/aisoft/gitea-governance.json`）。

**manifest 是唯一事实来源**，不经 project env 复制，避免漂移。以下每条不确定路径都回落 `production`：manifest 不存在、格式损坏、`repositories` 结构异常、仓库未登记、取值非法。

阶段经 `cli` 传给 `analyze_route` 与 `Controller`，再传给 `load_contract`；各层签名默认值均为 `production`，未接线的调用方行为不变。

## 5. 明确不变

- 受保护 `main`、禁止直接与强制 push、必需 status check；
- **人工合并仍是唯一交付硬闸门**；不新增 broker merge 操作，`merge_operation_count == 0` 断言不动；
- 判级分类（`type/*`、`complexity/*`、强制 complex 的类别集合）不变；
- 生命周期标签不变：`development` 的 complex 仍进 `spec-drafting`。该状态实质含义是「等人工复核后置 `approved`」，改动它会改变人工审批流，超出本变更范围；
- 部署治理（docker-release/v2、host-role gate）不变。

## 可测验收标准

| 编号 | 标准 |
|---|---|
| AC-1 | `validate` 接受合法 `change_control`，并对非法取值 fail closed |
| AC-2 | 未声明该字段的既有 10 个仓库解析结果全部为 `production` |
| AC-3 | 判级对 `development` 输出 `summary`（+ 条件性 verification），对 `production` 输出四项 |
| AC-4 | `load_contract` 对 `development` 的 complex 不因缺 spec/plan 拒绝，对 `production` 仍拒绝 |
| AC-5 | `development` 缺可测验收仍然拒绝；`verification` 的条件性两阶段一致 |
| AC-6 | `smoke.sh` 退出 0，`merge_operation_count == 0` 等既有断言未被放松 |

## 未决问题

无。

## 回滚

`git revert` 本 PR 的合并提交。所有新增参数均有 `production` 默认值，回滚后行为立即恢复；若届时已有 manifest 条目声明了 `change_control`，会因未知键被 `_exact_keys` 拒绝——属预期的 fail-closed，一并移除该字段即可。
