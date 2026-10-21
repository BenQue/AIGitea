# 路由表（route policy）

每条 Issue 的开发方式由这张表**查出来**，不由模型自由决定（ADR 0002 D1）。本文件是路由表的唯一来源：
技能、确认点 1 候选、派单任务书与 summary 的 `route:` 块都从这里取值；工具若需要机器读，从本文件生成，
不另维护第二份。复杂度本身仍由 `classification.py` 的规则引擎判定，这张表只把判级结果映射到流程、档位、
方法、验证与审查。

## 查表输入

summary front matter 的 `effective_complexity`、`change_type`、`contract_effect`、`risk_flags`、`confidence`、
`required_docs`；仓库在 governance manifest 里的 `change_control`（缺省 `production`）；仓库角色（平台仓
`admin/aisoft-platform` 或项目仓）。

**高风险 flag**：`security`、`authentication`、`authorization`、`schema-change`、`data-migration`、
`external-contract`、`shared-core`、`ci-integration`、`ci-change`、`artifact`、`deployment`、
`deployment-boundary`、`rollback`、`agent-governance`、`platform-governance`。`change_type` 为 `security` 或
`data` 视同含高风险 flag。`functional-change`、`cross-module`、`cross-service` 强制 complex，但不算高风险。

**安全类**：`security`、`authentication`、`authorization` 任一 flag，或 `change_type: security`。

## 推导表

自上而下取第一行命中。

| 行 | 条件 | process | tier | effort | method | verify | review 平台仓 | review 项目仓 | skills 必用 |
|---|---|---|---|---|---|---|---|---|---|
| R1 | 无 `effective_complexity`、`contract_effect: unclear` 或 `confidence: low` | `awaiting-triage` | `frontier` | `high` | `none` | `none` | `none` | `none` | `triage` |
| R2 | complex 且 `change_control: development` | `complex-development` | `frontier` | `high` | `tdd` | `full` | `human-merge` | `human-merge` | `verification-before-completion` |
| R3 | complex，`production`，含高风险 flag | `complex-production` | `frontier` | `max` | `spec-plan` | `full+reverse-proof` | `cross-provider` | `human-merge` | `to-spec`, `to-tickets`, `executing-plans`, `verification-before-completion` |
| R4 | complex，`production`，无高风险 flag | `complex-production` | `frontier` | `high` | `spec-plan` | `full` | `cross-provider` | `human-merge` | `to-spec`, `to-tickets`, `executing-plans`, `verification-before-completion` |
| R5 | small | `small-direct` | `standard` | `medium` | `implement-only` | `targeted` | `human-merge` | `human-merge` | `verification-before-completion` |

`confirm` 恒为 `2`：合同/启动，与提交最终 PR 前。R1 的 tier/effort 只用于分析，`triage` 之外在 Issue 说不清时加 `grill-me`。

## 细化规则

在推导表结果上按顺序应用，只改所列的格：

| 规则 | 条件 | 改动 |
|---|---|---|
| M1 | R5 且 `change_type: bugfix` | method 改为 `debug-first` |
| V1 | R4 且 `required_docs` 含 `verification` | verify 改为 `full+verification` |
| S1 | R3、平台仓、安全类 | review 改为 `cross-provider+security` |
| P1 | R3、项目仓 | skills 末尾加 `code-review`（Matt 两轴审查，至少 spec 轴） |
| G1 | R3 或 R4，且 `change_type: feature`、`contract_effect: add`，或一个阶段要拆成多个 Issue（大需求） | skills 最前面加 `grill-me` |

## 取值闭集

summary 的 `route:` 块只接受以下取值；`check-change-documents` 校验它们，smoke 钉住本节存在。

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
`small` ↔ `small-direct`，`complex` ↔ `complex-development` 或 `complex-production`，未决 ↔ `awaiting-triage`。

## summary 写法

```yaml
route:
  process: complex-production
  tier: frontier
  effort: high
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full
  review: cross-provider
  confirm: 2
```

同样一段写进判级评论，并在确认点 1 的候选中显示为「路由」行。人可以覆盖任何一格（例如把 small 升到
`frontier`），覆盖必须在 summary 的 `override_reason` 写明哪一格、为什么；覆盖不能把强制 complex 降成 small。

## 必用与禁用

表里的 skills 列只列**必用**项，另有两条全局必用：两个确认点；平台仓 complex 由未参与实现的另一方提供者只读交叉审查。

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
| 按计划执行 | Claude、Cursor：superpowers `executing-plans`；Codex：Matt `implement` |
| 测试驱动、排错 | Claude、Cursor：superpowers `test-driven-development`、`systematic-debugging`；Codex：Matt `tdd`、`diagnosing-bugs` |
| 完成前核验 | Claude、Cursor：superpowers `verification-before-completion`；Codex：`issue-session-flow` 的「验证：真实结果 / NOT RUN」 |
| 代码审查 | 项目仓：superpowers `requesting-code-review` 或 Matt `code-review`；平台仓 complex：另一方只读交叉审查 |
| worktree 与收尾 | 平台技能 `issue-session-flow` |

## 档位到型号

合同只写档位，型号按工具映射在 `08` §7.3；型号会变，路由表不变。派单卡片没有型号字段，人点卡片时按 tier 选。
