---
issue: 160
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/160
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
branch: change/160-analysis-label-projection
pr_url:
created: 2026-08-23
updated: 2026-08-23
reason: 新增一个 typed broker 写操作与一个治理工具，扩展 Gitea 标签写路径，并给交互会话合同补一步；属平台/Agent 治理变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
override_reason: ''
documents:
  summary: summary-analysis-label-projection-260823.md
  spec: spec-analysis-label-projection-260823.md
  plan: plan-analysis-label-projection-260823.md
---

## 问题/需求总结

`03` §9 的四维标签合同要求每个 Issue 恰好一个 `type/*` 和一个 `complexity/*`。
交互会话（Mac / Claude Code）产出的 Issue 系统性不满足它：判级只写进 summary front matter，
从不投影成 Gitea 标签。

现场证据（2026-08-23 经 broker `gitea.issue.labels.read` 读回）：

| Issue | 标签 |
|---|---|
| #138 | `[]` |
| #146 | `[]` |
| #148 | `[]` |
| #152 | `['completed']` |
| #158 | `['completed']` |

`completed` 是合并后 `mark-completed-issues.sh` 写的；`type/*` 与 `complexity/*` 从头到尾
没有任何组件写过。

根因是**缺路径，不是缺判级**：

- `aisoft_loop.cli apply-analysis`（`cli.py` `_apply_analysis`）是唯一投影 `type/*` 与
  `complexity/*` 的写入点，它调用 `_gitea_from_env()`，只在 Development Loop 内、用 VM 侧
  token 环境运行。交互会话不跑 Loop。
- broker 的 `gitea.issue.labels.set` 只接受 `--lifecycle`，签名上就写不了另外两个维度。
  `contract.py` 对此有明确的原始论证：`type/`/`complexity/` 是 analyzer 输出，
  一个 typed write 会变成绕过产出管线的路径。

这条论证仍然成立，但它排除的是**任意标签写入**，不是**判级产物的投影**。缺的正是后者。

## 影响范围

写路径（新增，不改既有语义）：

1. `codex/runtime/aisoft_host_access/` —— 新增 typed 操作 `gitea.issue.labels.classify`
   （`contract.py` / `broker.py` / `cli.py` / `runner.py`）与 manifest 条目
   （`codex/config/host-access-broker.json`），操作表 29 → 30。
2. `codex/tools/apply-classification-labels.sh` —— 新增 merged-phase 之外的**判级投影执行者**，
   判定取自映射 summary 的 `change_type` 与 `effective_complexity`，默认 dry-run。
3. 测试：`codex/runtime/tests/test_host_access.py`、`codex/tests/test-host-access-broker.sh`
   （`operation_count`）、新增 `codex/tests/test-apply-classification-labels.sh`、
   `codex/tests/smoke.sh` 注册。

合同文档（本变更授权修改，见 spec §5）：

4. `03-Issue-Spec-Plan与单闸门开发流程.md` §11 新增「谁投影 `type/*` 与 `complexity/*`」小节，
   与既有的「谁推进 `completed`」同构。
5. `skill-for-claude/aisoft-platform/SKILL.md` 会话标准动作新增一步——没有调用方的路径
   等于没有路径，这正是 `mark-completed-issues.sh`（#115）在 #158 之前的处境。

**不改动**：`AGENTS.md`、判级判据本身（`classification.py`）、`apply-analysis` 与 Loop、
`mark-completed-issues.sh` / `mark-deployed-issues.sh` 的终态判定、`gitea.issue.labels.set`
的 lifecycle 语义、标签 manifest 内容、CI 与部署脚本。

## 初步方案与建议

分工沿用 `mark-completed-issues.sh` 头部已经写死的架构原则：

> The judgement lives here, never in the broker … The broker performs one
> constrained write and knows nothing about change documents.

- **broker** 只做一次受约束的写：替换 `type/` 与 `complexity/` 两个维度，逐维校验取自
  **已安装的 label manifest**（与 `_lifecycle_labels()` 同一条派生规则：canonical 里带该前缀的名字），
  其余标签按 id 原样带过。两个参数都是必填——typed `arguments` 元组由
  `supplied != set(operation.arguments)` 强制，所以写不出「只有一半」的判级。
- **工具** 承担全部判断：哪些 Issue 是候选、判级值从哪来、closed Issue 怎么处理。
  值来自映射 summary 的 front matter，不接受人工传入标签。

AC-3（历史 Issue 处置）的结论是**不补写已关闭 Issue**，并由工具强制（`issue-closed` 跳过，
不提供 override 开关）。依据三条：

1. `aisoft_loop.cli list-issues` 的请求是 `state=open`（`gitea.py:74`）——检索缺口只存在于
   open Issue 上，closed Issue 补了标签也不进检索结果。
2. 判级事实已经在合并后的 summary 文档里，不可变、可用 `resolve-documents` 检索；
   改 closed Issue 的标签不增加任何信息。
3. 与平台既有姿态一致：retired label 只报告不移除（`_provision_labels`），
   `deployed` → `completed` 降级由人显式做（`_set_issue_lifecycle`）——事后改写已经收尾的记录
   不是自动化该做的事。

`required_docs` 取 `[summary, spec, plan]`，与最接近的先例 #108、#115（同为「broker 操作 +
运维工具」）一致，不含 `verification`：broker 重装是操作前置步骤，不是应用部署。
反例是 #138——它声明了 `verification`，于是 `mark-completed-issues.sh` 跳过它，
而 broker 变更没有对应的部署链路去写 `deployed`，结果它至今一个标签都没有。

## 风险

- **重装前调用会被误读**：新操作在两台重装 broker 之前返回
  `{"code": "REQUEST_DENIED", "message": "requested operation is not allowlisted"}`，
  读起来像身份/权限问题（`06` 踩坑 20）。缓解：spec 把重装列为合并后的显式前置步骤，
  工具的 `--apply` 失败路径原样透出 broker 的 code。
- **同步点遗漏**：新增 typed 操作要同步 6 处，新增 typed 参数另有第 7 处
  （`06` 踩坑 20 的清单）。缓解：plan 逐项列出并由 `smoke.sh` 的 `operation_count` 断言兜住。
- **投影与文档漂移**：summary 被改判级后标签不会自动跟随。缓解：工具幂等且可重跑，
  `before`/`after` 在输出里可见；这与 `mark-completed-issues.sh` 的姿态一致，不引入后台自动写。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增一个 typed broker 写操作与一个治理工具，扩展 Gitea 标签写路径，并给交互会话合同补一步；属平台/Agent 治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「Agent 或平台治理变更一律按 complex 处理」——本变更新增治理写路径并改 Agent 会话合同。
- `contract_effect: add`：`gitea.issue.labels.classify` 与 `apply-classification-labels.sh` 都不存在，
  是新增外部可调用契约，不是恢复既有行为。
- 触及共享核心组件 host-access broker（`contract.py` 的 `EXPECTED_OPERATIONS` 是全项目共享的操作表）。
- 触及 `skill-for-claude/` 下的 Agent 行为契约，须由本 spec 显式授权（`AGENTS.md` 治理文件条款）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文的 AC-1..AC-4 完整且可测；AC-3 要求的「处置结论 + 依据」由本文档
  「初步方案与建议」段给出，并由工具的 `issue-closed` 跳过路径强制。
