# 03 · Issue / Spec / Plan 与单闸门开发流程

> v3 当前文档契约（2026-07-14）。Issue 是所有工作的主键；小变更允许从明确的 Issue 直接进入 Development Loop，复杂变更必须先完成 spec/plan。最终 PR 合并是唯一交付硬闸门。

## 1. 绑定模型

```text
Issue #N
  ↔ change/N
  ↔ docs/changes/N/{00-summary,01-spec,02-plan,03-verification}.md
  ↔ final PR（Closes #N）
  ↔ commit / CI / deployment SHA
```

- 所有变更必须有 Issue 和 `00-summary.md`。
- 小变更可以不写 spec/plan，但 Issue 必须有可验证的 acceptance criteria。
- 复杂变更必须有 `01-spec.md` 和 `02-plan.md`。
- 部署、迁移和高风险运维变更必须有 `03-verification.md`。
- 新 Issue 从分析开始使用单一 `change/N` 分支；旧 `spec/N` 仅作迁移兼容。
- 文档与代码进入同一个最终 PR，不再强制独立 docs-only spec PR。

## 2. AI 判级与路由

AI 先判断变更对产品合同的作用，再结合 Issue 显式要求和强制风险规则判定有效复杂度：

```text
restore / unchanged  → small 候选
add / change         → complex
unclear              → awaiting-triage，等待人澄清

强制复杂风险规则
  > Issue 明确要求 complexity/complex
  > Issue 要求 complexity/small 且通过 AI 校验
  > AI 根据 Issue 与仓库证据自动判级
```

small 候选包括恢复既有明确行为的 Bug 修复、纯文档修正、只补充或修正测试，以及不改变外部行为的局部重构或维护。候选还必须目标清楚、范围局部、可简单 revert，且不触发任何强制复杂规则。

出现以下任一项即强制 complex：

- 新增任何产品功能，或改变既有功能、业务规则、用户交互和其他外部可观察行为。
- 存在多个合理方案或未收敛的业务/技术决策。
- 涉及 schema、历史数据迁移、兼容窗口、API 或数据格式。
- 涉及认证、权限、安全、外部系统契约或共享核心组件。
- 跨模块、跨服务或影响核心业务流程。
- 修改 CI、制品、部署、健康检查、备份或回滚。
- 修改 `AGENTS.md`、Agent 行为、自动化 controller 或平台治理规则。
- 失败后不能简单 revert，或数据/运行风险较高。

Issue 作者可以显式选择复杂度，但 `complexity/small` 不能绕过强制复杂规则，`complexity/complex` 不能由 AI 自动降级。标签与实际内容冲突时，AI 依据仓库证据更正并留下理由。信息不足、内容冲突或风险边界无法确定时，Issue 保持 `awaiting-triage` 且不添加 complexity 标签。

## 3. 文档合同

```text
docs/changes/N/
├── 00-summary.md       # 必须
├── 01-spec.md          # complex 必须
├── 02-plan.md          # complex 必须
└── 03-verification.md  # deploy/migration 必须，其他推荐
```

所有 change 文档的共同 front matter 至少包含：`issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`status`、`branch`、`pr_url`、`created`、`updated`；complex 的 spec/plan/verification 固定使用 `effective_complexity: complex`。`00-summary.md` 另外完整保存 analyzer schema 的 `reason`、`required_docs` 和 `override_reason`。无法安全判级时，summary 的 `assessed_complexity` 为 `needs-human-decision`，并从 front matter 与 `## AI 判级` YAML 同时省略整个 `effective_complexity` key，不保留空值或 placeholder；其他 complex 文档尚不得创建。

`01-spec.md` 必须定义目标、可测验收标准、接口/数据/兼容影响和非目标。`02-plan.md` 必须把每条验收标准映射到有序任务、文件和验证命令。Loop 不得自行修改已经确认的 acceptance criteria 或扩大范围。

## 4. 三维标签合同

每个 Issue 的标签分为三个正交维度：

| 维度 | 标签 | 语义 |
|---|---|---|
| 类型 | `type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform` | 变更是什么；每个 Issue 最多一个主要类型 |
| 复杂度 | `complexity/small`、`complexity/complex` | AI 判定需要哪条流程；互斥，无法判定时都不写 |
| 流程状态 | `needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`deployed` | Issue 当前阶段 |

类型的默认关系是：`type/bugfix`、`type/docs`、`type/test`、不改变外部行为的 `type/refactor` 是 small 候选；`type/feature` 和改变平台行为或治理合同的 `type/platform` 强制 complex；`type/maintenance` 由 AI 按实际合同影响判定。

`awaiting-triage` 只表示 AI 无法安全判级、内容冲突或合同不完整，阻止自动路由。`approved` 是合同完整后的运行控制信号，不是 spec 审批闸门，也不授权合并或部署。受控 wrapper 可以在合同完整时自动写入 `approved`，但 controller 启动前必须重新验证合同，不能只信任标签。

## 5. 小变更路径

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved（合同完整）
  → Development Loop
  → final PR + CI
  → 人工合并
  → 确定性部署
```

## 6. 复杂变更路径

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/complex + spec-drafting
  → 人与 AI 完成 01-spec.md + 02-plan.md
  → spec-review（可选，不是硬闸门）
  → approved（合同完整）
  → Development Loop
  → final PR + CI
  → 人工合并
  → 确定性部署
```

统一路由合同：

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved, or complexity/complex + spec-drafting
  → unresolved input: awaiting-triage with no complexity label
```

## 7. 最终 PR

PR 必须：

- 使用 `Closes #N`。
- 链接 `docs/changes/N/` 中本变更要求的文档。
- 说明验收标准与测试证据。
- 说明迁移、部署和回滚影响（若适用）。
- 通过受保护 `main` 要求的 `CI / test (pull_request)`。

PR 合并是唯一交付硬闸门。Analyzer、Loop、provider wrapper 和 CI 都不得合并 PR。

## 8. 升级给人的条件

Loop 只有在合同冲突、必须扩范围、破坏性迁移、安全/权限决策、缺凭据或外部服务、同一根因连续失败三次、验证不可靠或达到预算上限时才停止并请求人决定。普通编译、测试、构建和范围内 review 失败由 Loop 自主处理。

## 9. 当前实施状态

- AI 自动分析和七个流程状态标签保留。
- 七个 `type/*` 与两个 `complexity/*` 已于 2026-07-15 在当前本地 Gitea provision 并读回；第二次同步为 `created=0 existing=16`，Issue #8 当时读回 `type/platform`、`complexity/complex`、`spec-drafting`。外部状态可能漂移，使用前仍须重新 GET。
- 当前 v2 wrapper 尚未消费新分类字段，标签的 runtime routing 未启用。
- 现有 one-shot 自动实现仍停用。
- Development Loop、单分支 analyzer 和 CI feedback adapter 尚未实现。
- 在 Codex 真实 Issue 验证通过前，不启用 Claude Code Loop。
## 依赖 Issue

`00-summary.md` 可用可选字段 `depends_on` 声明 Issue 编号列表；缺省或 `[]`
表示没有依赖。依赖只影响 PR 就绪门，不改变分支、CI 或人工合并规则：
当前 PR 的 CI 通过后，全部依赖 Issue 必须同时为 closed 且带有 `deployed`
生命周期标签，Loop 才能进入 `READY_FOR_REVIEW`。否则保存
`awaiting_dependencies`，后续轮询只重查 CI 与依赖，不再次调用 provider、
不创建第二个 PR，也不自动合并。
