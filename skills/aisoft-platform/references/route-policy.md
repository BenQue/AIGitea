# 路由表（route policy）

每条 Issue 的开发方式由这张表**查出来**，不由模型自由决定（ADR 0002 D1）。本文件是路由表的唯一来源：
技能、确认点 1 候选、派单任务书与 summary 的 `route:` 块都从这里取值；工具若需要机器读，从本文件生成，
不另维护第二份。复杂度本身仍由 `classification.py` 的规则引擎判定，这张表只把判级结果映射到流程、档位、
方法、验证与审查。

## 查表输入

summary front matter 的 `effective_complexity`、`change_type`、`contract_effect`、`risk_flags`、`confidence`、
`required_docs`；仓库的 `change_control`（缺省 `production`；有 `.aisoft/project.json` 时取自它，否则取自 governance manifest）；仓库角色（平台仓
`admin/aisoft-platform` 或项目仓）；显式执行 provider（`codex`、`claude`、`cursor`）。
provider 写入 summary 顶层 `route_provider`，不加入 route 八键或 analyzer 的 AI 判级字段。
不得根据安装目录、技能包可见性或模型名猜 provider。

**高风险 flag**：`security`、`authentication`、`authorization`、`schema-change`、`data-migration`、
`external-contract`、`shared-core`、`ci-integration`、`ci-change`、`artifact`、`deployment`、
`deployment-boundary`、`rollback`、`agent-governance`、`platform-governance`。`change_type` 为 `security` 或
`data` 视同含高风险 flag。`functional-change`、`cross-module`、`cross-service` 强制 complex，但不算高风险。

**安全类**：`security`、`authentication`、`authorization` 任一 flag，或 `change_type: security`。

## 推导表

自上而下取第一行命中。

| 行 | 条件 | process | tier | effort | method | verify | review 平台仓 | review 项目仓 | 必用技能/义务 |
|---|---|---|---|---|---|---|---|---|---|
| R1 | 无 `effective_complexity`、`contract_effect: unclear` 或 `confidence: low` | `awaiting-triage` | `frontier` | `high` | `none` | `none` | `none` | `none` | `triage` |
| R2 | complex 且 `change_control: development` | `complex-development` | `frontier` | `high` | `tdd` | `full` | `human-merge` | `human-merge` | `@completion` |
| R3 | complex，`production`，含高风险 flag | `complex-production` | `frontier` | `max` | `spec-plan` | `full+reverse-proof` | `cross-provider` | `human-merge` | `to-spec`, `to-tickets`, `@plan`, `@completion` |
| R4 | complex，`production`，无高风险 flag | `complex-production` | `frontier` | `high` | `spec-plan` | `full` | `cross-provider` | `human-merge` | `to-spec`, `to-tickets`, `@plan`, `@completion` |
| R5 | small | `small-direct` | `standard` | `medium` | `implement-only` | `targeted` | `human-merge` | `human-merge` | `@completion` |

`confirm` 恒为 `2`：合同/启动，与提交最终 PR 前。R1 的 tier/effort 只用于分析，`triage` 之外在 Issue 说不清时加 `grill-me`。
R2 仍先于 R3：development 即使有高风险 flag 也保持现有命中顺序；R2 不因此新增整套计划执行技能义务。

## Provider 映射

表中 `@plan` 与 `@completion` 是仅供本文件查表的义务引用，必须按显式 provider 展开；
它们不是技能名，绝不能进入最终 `route.skills`。先选 R1–R5，展开本表，再依次应用下面的细化规则。

| provider | @plan | @completion |
|---|---|---|
| codex | `implement` | `issue-session-flow` |
| claude | `executing-plans` | `verification-before-completion` |
| cursor | `executing-plans` | `verification-before-completion` |

这是计划执行与完成核验的唯一 provider 映射。skills 是必用集合；R2/R5 不含 `@plan`，
不据此强制 spec/plan、完整 SP 循环或 Matt 每票双轴。development complex 的合成 T01 按既有 provider 默认执行。
未知/缺失 provider、未展开引用、空/重复/不存在的具体技能或与 provider 矛盾的组合不得静默通过。
R1 不因 provider 合法而获得实施权限。已批准的显式覆盖仍走 override_reason，不把默认当成不可覆盖的品牌选择。

## 细化规则

在推导表结果上按顺序应用，只改所列的格：

| 规则 | 条件 | 改动 |
|---|---|---|
| M1 | R5 且 `change_type: bugfix` | method 改为 `debug-first` |
| V1 | R4 且 `required_docs` 含 `verification` | verify 改为 `full+verification` |
| S1 | R3、平台仓、安全类 | review 改为 `cross-provider+security` |
| P1 | R3、项目仓 | skills 末尾加 `code-review`（Matt 两轴审查，至少 spec 轴） |
| G1 | R3 或 R4，且（`change_type: feature` 或 `contract_effect: add` 或一个阶段要拆成多个 Issue） | skills 最前面加 `grill-me` |

## 取值闭集

summary 的 `route:` 块仍为 process/tier/effort/skills/method/verify/review/confirm 八键；
以下为取值闭集。既有 `check-change-documents` 的形状检查不等于 provider/技能语义校验已实现，
消费者必须从本文件取规则，不能维护另一份技能映射。

| 键 | 取值 |
|---|---|
| process | `small-direct`, `complex-development`, `complex-production`, `awaiting-triage` |
| tier | `standard`, `frontier`, `max` |
| effort | `medium`, `high`, `max` |
| method | `implement-only`, `debug-first`, `tdd`, `spec-plan`, `prototype-first`, `none` |
| verify | `targeted`, `full`, `full+verification`, `full+reverse-proof`, `none` |
| review | `human-merge`, `cross-provider`, `cross-provider+security`, `none` |
| confirm | `2` |

`skills` 写成逗号分隔的一行技能名（不带 `$`、不带包前缀）。`process` 必须与 `effective_complexity` 一致：
`small` ↔ `small-direct`，`complex` ↔ `complex-development` 或 `complex-production`，未决 ↔ `awaiting-triage`；
与 R1 同序：`contract_effect: unclear` 或 `confidence: low` 时不论 `effective_complexity` 写了什么都是 `awaiting-triage`。

## summary 写法

```yaml
route_provider: codex
route:
  process: complex-production
  tier: frontier
  effort: high
  skills: to-spec, to-tickets, implement, issue-session-flow
  method: spec-plan
  verify: full
  review: cross-provider
  confirm: 2
```

同样一段写进判级评论，并在确认点 1 的候选中显示为「路由」行。人可以覆盖任何一格（例如把 small 升到
`frontier`），覆盖必须在 summary 的 `override_reason` 写明哪一格、为什么；覆盖不能把强制 complex 降成 small。

新生成卡必须保存显式 `route_provider`。历史无 route/provider 的文档保持只读兼容，不批改历史；
再次执行时显式指定 provider，重算具体技能并报告差异，不把旧卡默认解释为 Claude。
合同内一致重算直接继续；真正的合同冲突按既有升级规则处理，不新增确认点。
解析回执保留命中规则和本文件字节 SHA256；接口及执行范围见 [execution-adapter](execution-adapter.md)。

## 必用与禁用

推导表经 provider 展开后的 skills 只列**必用**项，另有两条全局必用：两个确认点；平台仓 complex 由未参与实现的另一方提供者只读交叉审查。

**禁用与限制**（所有 process）：

- superpowers `writing-plans` 不替代 Matt `to-tickets` 的 Txx 计划。
- `brainstorming` 不自行定级，只在 how 未收敛时用、只问 how，以 `grill-me` 的结论为输入，结论写进映射 spec 的「方案与决策」节；`grill-me` 与 `brainstorming` 都在确认点 1 之前完成。
- `subagent-driven-development` 只许顺序派发，同一时刻一个写者；`dispatching-parallel-agents` 只做只读调查；并行子代理不写同一 change worktree。
- `finishing-a-development-branch` 的本地 merge、`git push`、建 PR 不可用，停在 `AWAITING_PR_CONFIRMATION`。

## 默认入口（不是硬规则）

其余技能由模型按 Issue 自选，verification 写明用了什么。两个技能包重叠时的默认入口：

| 职责 | 默认入口 |
|---|---|
| 定需求（what） | Matt `grill-me` |
| 定方案（how） | Matt `to-spec` 的方案节；how 未收敛时 superpowers `brainstorming`，技术可行性存疑时 Matt `prototype` |
| 出计划 | Matt `to-tickets` |
| 按计划执行 | 按本文件「Provider 映射」的 `@plan` 选一个入口；执行/审查范围见 execution-adapter |
| 测试驱动、排错 | Claude、Cursor：superpowers `test-driven-development`、`systematic-debugging`；Codex：Matt `tdd`、`diagnosing-bugs` |
| 完成前核验 | 按本文件「Provider 映射」的 `@completion`；报告真实结果 / NOT RUN |
| 代码审查 | 项目仓：superpowers `requesting-code-review` 或 Matt `code-review`；平台仓 complex：另一方只读交叉审查 |
| worktree 与收尾 | 平台技能 `issue-session-flow` |

## 档位到型号

合同只写档位，型号按工具映射在 `08` §7.3；型号会变，路由表不变。派单卡片没有型号字段，人点卡片时按 tier 选。
