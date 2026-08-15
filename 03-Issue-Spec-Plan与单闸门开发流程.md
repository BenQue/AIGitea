# 03 · Issue / Spec / Plan 与单闸门开发流程

> v3 当前文档契约（更新 2026-08-11）。Issue 是所有工作的主键；小变更允许从明确的 Issue 直接进入 Development Loop，复杂变更必须先完成 spec/plan。最终 PR 合并是唯一交付硬闸门。Issue #75 已把 readable branch/directory 合同合并进 protected `main`；既有固定数字路径只作证据驱动的 legacy 兼容。

## 1. 绑定模型

```text
Issue #N
  ↔ change/N-short-description
  ↔ docs/changes/N-short-description/<role>-<short-description>-<YYMMDD>.md
  ↔ final PR（Closes #N）
  ↔ commit / CI / deployment SHA
```

- 所有变更必须有 Issue 和映射的 `summary` 文档。
- 小变更可以不写 spec/plan，但 Issue 必须有可验证的 acceptance criteria。
- 复杂变更必须有映射的 `spec` 和 `plan` 文档。
- 部署、迁移和高风险运维变更必须有映射的 `verification` 文档。
- 新 Issue 从分析开始使用单一 `change/N-short-description` 分支；已有 `change/N` 与更早的 `spec/N` 只按历史证据兼容，不作为新 writer 的可选格式。
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
docs/changes/N-short-description/
├── summary-<slug>-YYMMDD.md       # 必须
├── spec-<slug>-YYMMDD.md          # complex 必须
├── plan-<slug>-YYMMDD.md          # complex 必须
└── verification-<slug>-YYMMDD.md  # deploy/migration 必须，其他推荐
```

文件名固定为 `<role>-<short-description>-<YYMMDD>.md`：slug 使用 2–4 段 lowercase ASCII `kebab-case`、至少包含一个字母、硬上限 32 字符，完整 basename 不超过 64 字符；分支、目录、worktree、文档和 front matter 必须使用同一 `(N, slug)`。slug 创建后不可修改；纠错应开新 Issue。日期等于各文件首次创建日期，普通更新只修改 `updated`，不重命名。

新 worktree basename 固定为 `issue-N-short-description`。`main`、`master`、`head`、`merge`、`pull`、`pr`、`refs`、`change`、`changes`、`docs`、`worktree`、`tmp`、`temp`、`legacy` 是保留 slug，`tmp-`、`temp-`、`legacy-` 前缀同样禁止。同一 Issue 同时出现 legacy/readable 名称或多个 slug 时必须以 `CHANGE_NAME_CONFLICT` 停止。

所有 change 文档的共同 front matter 至少包含：`issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`status`、`branch`、`pr_url`、`created`、`updated`；complex 的 spec/plan/verification 固定使用 `effective_complexity: complex`。summary 另外完整保存 analyzer schema 的 `reason`、语义 `required_docs`、`documents` 角色到真实 basename 的映射和 `override_reason`。无法安全判级时，summary 的 `assessed_complexity` 为 `needs-human-decision`，并从 front matter 与 `## AI 判级` YAML 同时省略整个 `effective_complexity` key，不保留空值或 placeholder；其他 complex 文档尚不得创建。

新合同只使用 `summary`、`spec`、`plan`、`verification` 角色；Controller 严格读取 `documents` 映射并校验角色、slug、日期、目录边界和唯一性，不使用无约束 glob。没有映射的历史 summary 仅回退到 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md`，新 writer 不再生成这些名称，也不批量重命名历史文件。

映射的 spec 必须定义目标、可测验收标准、接口/数据/兼容影响和非目标。映射的 plan 必须把每条验收标准映射到 `Txx` 垂直切片、`blocked_by`、预期 touch points 和验证命令。Loop 不得自行修改已经确认的 acceptance criteria 或扩大范围。

## 4. 平台三维标签与 Matt triage

每个 Issue 的标签分为三个正交维度：

| 维度 | 标签 | 语义 |
|---|---|---|
| 类型 | `type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`、`type/security`、`type/reliability`、`type/data` | 变更是什么；每个 Issue 最多一个主要类型 |
| 复杂度 | `complexity/small`、`complexity/complex` | AI 判定需要哪条流程；互斥，无法判定时都不写 |
| 流程状态 | `needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`completed`、`deployed` | Issue 当前阶段 |

类型的默认关系是：`type/bugfix`、`type/docs`、`type/test`、不改变外部行为的 `type/refactor` 是 small 候选；`type/feature` 和改变平台行为或治理合同的 `type/platform` 强制 complex；`type/maintenance` 由 AI 按实际合同影响判定。

Issue #108 增加的三个类型按同一套既有强制规则判定，不新增判级规则：

| 类型 | 判定证据 | 复杂度默认 |
|---|---|---|
| `type/security` | 安全缺陷、凭据处理、认证/授权或权限边界变更。证据是变更触及 token/credential 存储与传递、权限模型、broker/CI 的信任边界，或修复可被利用的缺陷 | 强制 complex（AGENTS.md「认证/权限/安全」） |
| `type/data` | 数据模型、schema 或数据迁移变更。证据是变更改动表/字段/索引定义、迁移脚本，或既有数据的读写语义 | 强制 complex（AGENTS.md「schema/数据迁移」） |
| `type/reliability` | 可用性、韧性或故障恢复变更。证据是变更针对超时/重试/降级/健康检查/回滚路径，或修复只在故障态下暴露的行为 | 按 `contract_effect` 判定：恢复既有行为（`restore`/`unchanged`）是 small 候选，`add`/`change` 走 complex |

`type/security` 与 `type/data` 的强制不依赖 analyzer 是否填了对应 `risk_flags`：risk flag 是可能被遗漏的分析输出，类型标签是 Issue 上不可省略的事实，两条路径都强制才没有缝隙。`type/reliability` 刻意不强制——可用性修复常常正是「恢复既有产品行为」，一律 complex 会把真实的 small 修复挡在流程外，判定权交给 `contract_effect`。

`awaiting-triage` 只表示 AI 无法安全判级、内容冲突或合同不完整，阻止自动路由。`approved` 是合同完整后的运行控制信号，不是 spec 审批闸门，也不授权合并或部署。受控 wrapper 可以在合同完整时自动写入 `approved`，但 controller 启动前必须重新验证合同，不能只信任标签。

Matt triage 另有两个正交维度：category 使用 `triage/bug` 或 `triage/enhancement`，state 使用 `triage/needs-triage`、`triage/needs-info`、`triage/ready-for-agent`、`triage/ready-for-human`、`triage/wontfix`。每个已 triage Issue 恰好一个 category 和一个 state。`triage/ready-for-agent` 只允许 Agent 处理下一阶段，永远不替代 `approved`；`triage/wontfix` 关闭 Issue，但不得写入 `completed` 或 `deployed`。所有标签 mutation 通过同一个 projector，更新一个维度时保留其他维度和非受管标签。

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
  → 人与 AI 完成映射的 spec + plan
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

- body 恰有一行 `Closes #N`，不能额外关闭其他 Issue。
- head 精确为 `change/N-short-description`，并链接 `docs/changes/N-short-description/` 中同 slug 的 summary 与要求文档。
- 说明验收标准与测试证据。
- 说明迁移、部署和回滚影响（若适用）。
- 通过受保护 `main` 要求的 `CI / test (pull_request)`。

PR 合并是唯一交付硬闸门。Analyzer、Loop、provider wrapper 和 CI 都不得合并 PR。

## 8. 升级给人的条件

Loop 只有在合同冲突、必须扩范围、破坏性迁移、安全/权限决策、缺凭据或外部服务、同一根因连续失败三次、验证不可靠或达到预算上限时才停止并请求人决定。普通编译、测试、构建和范围内 review 失败由 Loop 自主处理。

## 9. 当前实施状态

- Issue #57/#60 已把文档 resolver、writer、Matt triage projector、frontier ticket、Agent commit 后置校验、固定 upstream snapshot 与根级路由合并进 source；Issue #75 又统一了 readable branch/directory/worktree/PR 绑定。
- platform canonical taxonomy 为 20 个（Issue #108 把 `type/*` 扩为 10 个），Matt 另加 7 个 namespaced `triage/*`，source manifest 共 27 个；准确集合以 `codex/config/gitea-labels.json` 的 `canonical` 为准。外部状态可能漂移，部署到每个仓库前必须用 broker `gitea.labels.provision` 同步并读回。
- 旧 Issue 与历史文档不重命名；新 writer 只产生语义 basename，并从 Issue #75 起要求目录、branch、worktree 与同一 slug 一致。
- Provider 默认仍为 `IMPLEMENT_PROVIDER=none`；每个项目必须在独立 profile 完成真实验收后才能启用。
- `READY_FOR_REVIEW` 仍停止在人工 merge gate；本次治理变更不部署。
## 10. 依赖 Issue

映射的 summary 可用可选字段 `depends_on` 声明 Issue 编号列表；缺省或 `[]`
表示没有依赖。依赖只影响 PR 就绪门，不改变分支、CI 或人工合并规则：
当前 PR 的 CI 通过后，全部依赖 Issue 必须同时为 closed 且带有 `completed` 或
`deployed` 生命周期终态，Loop 才能进入 `READY_FOR_REVIEW`。否则保存
`awaiting_dependencies`，后续轮询只重查 CI 与依赖，不再次调用 provider、
不创建第二个 PR，也不自动合并。

## 11. 合批关闭与交付终态

合批 PR 可在 merge message body 中逐行列出多个 `Closes #N`。部署成功后的确定性
工具必须处理全部编号并去重，不能只从 subject 猜一个 Issue。更新标签时必须保留
type、complexity 和非生命周期标签。最终 PR 已合并且明确无需部署时使用
`completed`；需要部署的变更只有在确定性部署与验证成功后使用 `deployed`。两者互斥，
都不授权合并；Gitea `Closed` 本身也不证明部署成功。

### 谁推进 `completed`

`deployed` 由应用部署链路在健康检查成功后回写（02 §9）。`completed` 没有对应的
自动触发点：controller 的 lifecycle 写入全在 Development Loop 内，而 Loop 在创建
最终 PR 时就结束了，没有任何组件处在能观察到「合并」的位置上。因此 `completed`
由人在合并后显式运行 `codex/tools/mark-completed-issues.sh` 推进（#115）：

```bash
codex/tools/mark-completed-issues.sh --range 'origin/main~5..origin/main'
```

默认只输出逐 Issue 的判定计划、不做任何写入；确认计划无误后加 `--apply` 才经
broker `gitea.issue.labels.set` 写入。是否该用 `completed` 的判定取自该 Issue 映射
summary 的 `required_docs` 是否含 `verification`——含则说明该变更要部署，终态应是
`deployed`，工具会跳过并给出理由，不接受人工传入的终态判断。已经是 `deployed` 的
Issue 不会被降级为 `completed`：那是对「它到底发生了什么」的判断，必须由人显式做。
