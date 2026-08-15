---
issue: 115
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/115
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 变更新增 broker Issue 级 label typed 操作（扩展对外操作面）、新增 completed 终态推进能力与其判定依据（生命周期治理合同），并触及 gitea.py 标签投影、contract.py 生命周期集合与 mark-deployed-issues.sh 等共享消费者，属治理合同新增且跨模块，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-issue-labels-completed-260815.md
  spec: spec-issue-labels-completed-260815.md
  plan: plan-issue-labels-completed-260815.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/115-issue-labels-completed
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/119
created: 2026-08-15
updated: 2026-08-15
---

## 问题/需求总结

八个生命周期标签中的 `completed`（「最终 PR 已合并且该变更无需部署，交付已完成」）**没有任何
写入者**，而它恰好是平台自身最常见变更形态（文档、平台工具、治理）的唯一正确终态。

### 现状核对（2026-08-15，本仓 HEAD `314153e`）

| 事实 | 证据 |
|---|---|
| controller 最远推进到 `pr-open` | `codex/runtime/aisoft_loop/controller.py:361` |
| **controller 结构上不可能写 `completed`** | `_set_lifecycle` 的七处调用全在 Loop 内；Loop 在创建 PR 后即结束，合并是之后发生的外部事件，controller 不在场 |
| `mark-deployed-issues.sh` 只写 `deployed` | `codex/tools/mark-deployed-issues.sh:77`——`completed` 只作为待剥离的 lifecycle 之一出现 |
| `apply-analysis` 写 route 派生生命周期 | 对已合并 Issue 使用会把状态**倒退**回 `spec-drafting`/`approved` |
| broker 无 Issue 级 label 操作 | 24 个 allowlisted 操作中，`gitea.labels.read`/`provision` 是**仓库级标签定义**（#108 交付），无 `/issues/{index}/labels` 面 |

第二行是 Issue 正文没有区分的关键：`completed` 不可达**不是遗漏了一行代码，而是没有任何组件
处在能观察到「合并」的位置上**。因此「谁负责推进终态」不是三选一的偏好问题——controller 可
按证据直接排除。

### #108 合并后新增的两个约束

1. **Issue 上可能合法挂着项目扩展标签**。#108 引入 `project_extensions.allowed_prefixes`
   （`area/`、`priority/`），NewEMaint 实测 37 个 Issue 引用。一个「取值限定在 canonical 内」
   的天真 set 实现会把它们连带擦掉。所幸 `gitea.py:_reconcile_labels`（`:133-150`）已实现正确
   投影：只替换被指定维度，其余一律保留——**本 Issue 应复用它，不新写第二套投影**。
2. **canonical 已是 27 项而非 24 项**，且 `type/*` 为 10 个。任何新的取值约束必须从
   `codex/config/gitea-labels.json` 派生，不得再复制枚举。

### 顺带暴露的第五份 manifest 副本

`mark-deployed-issues.sh:77` 硬编码了八个 lifecycle 名。#108 已把 runtime 侧的 type 集合副本
收敛为从 `CHANGE_TYPES` 派生并加 parity 断言，但这个 shell 工具漏网——而它正是改 lifecycle 的
工具。本 Issue 触及同一处，应一并收敛。

## 影响范围

仅平台仓库。

- `codex/runtime/aisoft_host_access/{contract,broker,runner}.py` 与
  `codex/config/host-access-broker.json`：新增 Issue 级 label typed 操作。
- `codex/runtime/aisoft_loop/gitea.py`：复用/暴露既有标签投影，使终态推进不擦除项目扩展标签。
- 终态推进的执行者（独立工具，见下）：新增或扩展 `codex/tools/` 下的确定性命令。
- `codex/tools/mark-deployed-issues.sh`：lifecycle 集合改为从 manifest 派生，与新工具共用。
- `codex/tests/`：`test-host-access-broker.sh`（含 `operation_count`）、
  `codex/runtime/tests/test_host_access.py`、`test_gitea.py`、`smoke.sh`。
- 文档：`03-Issue-Spec-Plan与单闸门开发流程.md` 的终态推进责任、
  `skill-for-codex/references/onboarding-runbook.md` §8「合并后收尾」。

不修改：`AGENTS.md` 的判级与单闸门合同、CI workflow、部署链路、任何项目仓库的实际标签，
以及 `completed`/`deployed` 两个终态的既有语义与互斥关系。

## 初步方案与建议

1. **两个 typed 操作**：`gitea.issue.labels.read`（只读）与 `gitea.issue.labels.set`
   （mutation）。命名沿用 #108 确立的区分——有 `issue.` 段是 Issue 级挂载，无则是仓库级定义。
   取值合法性从 manifest 派生，fail closed；不提供删除任意标签的能力。
2. **终态推进由独立工具执行**，与 `mark-deployed-issues.sh` 对称：合并后由人或运维会话运行，
   而非 controller（不在场）、也非合并后 CI 步骤（改 required CI 是治理变更，且需给 runner
   发放 Issue 写凭据，扩大凭据面）。
3. **`completed` 判定依据取自映射 summary 的 `required_docs` 是否含 `verification`**，
   而非人工输入——与既有判级合同一致，可审计、可重放。
4. **幂等**：已处于 `completed` 的 Issue 重复执行为 no-op；已 `deployed` 的 Issue 不得被降级
   为 `completed`（两终态互斥且 `deployed` 更强）。
5. **lifecycle 集合单一事实源**：新工具与 `mark-deployed-issues.sh` 共用从 manifest 派生的
   集合，参照 #108 的 `gitea-label-manifest.sh` 共享库模式。

## 风险

- **误伤既有标签**：Issue 级 set 若不复用 `_reconcile_labels` 的投影语义，会擦掉 `type/*`、
  `triage/*` 或项目扩展标签。缓解：复用而非重写，并为「set lifecycle 时保留其它维度」加测试。
- **终态误判**：把需要部署的变更标为 `completed`，会让它永远不进入部署视图。缓解：判定依据
  取自 summary 的 `required_docs`，并对已 `deployed` 的 Issue fail closed。
- **broker 操作面扩大**：新增 mutation 操作。缓解：无自由参数（仅 Issue number 与受约束的
  lifecycle 取值）、无删除路径、沿用 #108 的 fail-closed 与分页上限模式。
- **安装期固定配置**：broker manifest 改动后，Mac 与 gitea-ci VM **两台都要重装**才生效，
  否则新操作返回 `REQUEST_DENIED`（形似权限问题）。这是 #108 实测踩到的坑，须写进 verification
  或 PR 交接说明。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 变更新增 broker Issue 级 label typed 操作（扩展对外操作面）、新增 completed 终态推进能力与其判定依据（生命周期治理合同），并触及 gitea.py 标签投影、contract.py 生命周期集合与 mark-deployed-issues.sh 等共享消费者，属治理合同新增且跨模块，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 强制 complex 命中「外部契约」：新增 typed 操作即扩展 broker 对外操作面。
- 强制 complex 命中「Agent/治理」：`completed` 终态的推进者与判定依据是生命周期治理合同的
  组成部分，当前合同对此为空白。
- 强制 complex 命中「共享核心」：`gitea.py` 的标签投影被 controller 与 apply-analysis 共同
  消费；lifecycle 集合被 controller、`mark-deployed-issues.sh` 与新工具共同消费。
- 强制 complex 命中「跨模块」：host-access broker、aisoft_loop runtime 与 `codex/tools/`
  三处同批次变更。
- `contract_effect: add`（非 `change`）的依据：既有 typed 操作与既有终态语义都不改变，本次是
  在其上新增操作与新增可达路径。
- 无部署影响，故 `required_docs` 不含 `verification`：不产出制品、不触及 AppServer/production，
  `ops/` 与 `docker-release/` 不在影响范围内。

### 缺失的 acceptance criteria 或决策

- 已澄清（不再未决）：「合并后谁负责推进终态」——controller 结构上不在场，可直接排除；
  合并后 CI 步骤需扩大 runner 凭据面并改 required context（本身即治理变更）。故取独立工具，
  与 `mark-deployed-issues.sh` 对称。spec 将据此写死，不再作为未决问题。
- 待 spec 确认：`completed` 推进的**触发时机与执行者身份**（人工运维会话 vs 定时巡检）、
  以及是否同时提供批量补齐历史 Issue 的能力（NewEMaint #65/#67、平台 #107 与 #108 均已合并
  且无部署影响，目前无终态）。
- 待 spec 确认：Issue 级 set 的取值约束粒度——仅限 lifecycle 维度，还是开放全部受管维度。
  前者攻击面更小，后者能覆盖「合并后补 `type/*`」等场景。
