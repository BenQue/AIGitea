# ADR 0002 · 确定性开发流程：路由合同与执行引擎分离

## 状态

已采纳（Issue #389，负责人 2026-10-20 裁决）。补充 [ADR 0001](0001-platform-boundary.md)，不撤销它的任何决定；
只把 ADR 0001 D1 表中 K2 的 routine merger 与 K3 的 Controller 标为「按本 ADR 退出」，由 R10a 执行。

## 日期

2026-10-20

## 依据

**要回答的问题**（负责人 2026-10-20 02:50Z）：还要不要启用自动化路径？平台需要一个确定性的开发流程，
定义每个 Issue 怎么开发、怎样区分复杂度，从而决定用什么能力与强度的模型、调哪些技能、用什么方法。

**事实**（项目库 `d1-automation-path-proposal-261020.md`，基线 `main` `77ad607`）：

| 事实 | 证据 |
|---|---|
| 五个仓库 654 条 Issue 中 small 只有 41 条（6%），complex 432 条（66%） | broker `gitea.issue.list --state all` 按标签统计 |
| 无人值守的自治全链（Loop 自动实现 + routine 自动合并）只对 small 开放；Loop 虽也能跑 complex，但 complex 按合同有两个人工确认点、平台仓 complex 一律人合并 | `03` §7、`04` |
| 三个 VM profile 都是 `IMPLEMENT_PROVIDER=none`；VM implement provider 的真实集成与项目级验收从未完成；routine merge 从未发生 | manifest `vm_profile`、`08` §7.2、#385 verification |
| 两个 VM 定时器自 2026-08-12 起每 15 分钟失败，直到 #387 停用 | #387 verification |
| 模型 CLI、技能、凭据、Matt 快照都在 Mac；VM 服务层 `claude`/`codex` 不可达 | `04`、#164、#178 |
| 每条规则在 Controller 路径与会话路径各写一遍（PR URL 回填、判级投影、终态） | `aisoft_loop`、`issue-session-flow` |

**判断**：现在的「自动化路径」把三件事绑在一起。

| 层 | 内容 | 处置 |
|---|---|---|
| 路由合同 | 判级输入 → 走什么流程、什么档位的模型、哪些技能、什么方法、怎么验证、谁审查、几个确认点 | 是产品，升级 |
| 执行引擎 | 谁按路由把 Issue 做到 PR 候选：交互会话、协调者派单的线程、无人值守进程 | 可替换；VM 上的那一种退出 |
| 护栏 | broker typed 操作、受保护 `main`、两个确认点、交叉审查、smoke | 稳固，与引擎无关，不动 |

**裁决**（2026-10-20 03:02Z，负责人原话）：

> 按你的建议。判定开发强度，决定如何开发，确定开发的方案和计划和路线图都交给技能来处理就可以了

03:30–03:41Z 的续裁补充了技能分工与三条原则：Matt 定需求与计划、superpowers 开发；大需求先用 Matt `grill-me`；
superpowers `brainstorming` 只在 how 未收敛时用；**避免过度设计**，路由表只钉必用与禁用，其余技能由模型按情况取舍；
**一套技能一套流程**，Claude、Codex、Cursor 三端一致（superpowers 像 Matt 一样 vendor pin）。
分工细节见项目库 `d1-addendum-skill-division-261020-v3.md`，由 R10b、R10c 落地。

## 决定

### D1 路由合同是产品

每条 Issue 的开发方式由确定性的**路由卡**给出，由技能承载，不由模型自由决定，也不建 daemon。

- 判级输入不变：`change_type`、`contract_effect`、`effective_complexity`、`risk_flags`、`confidence` 与仓库的 `change_control`，
  由现有规则引擎（`classification.py` 的强制 complex 规则）算出。
- 技能拿判级输入查**唯一一张路由表**，得到路由卡，写进 summary front matter 的 `route:` 块与判级评论，
  在确认点 1 的候选中展示。人可以覆盖任何一格，覆盖必须写 `override_reason`。
- 方案与计划由 Matt `to-spec` / `to-tickets` 产出；多 Issue 的路线图由 `issue-session-flow` 的调度会话产出。
- 同一条 Issue 换一个会话、换一个工具，查出来的路线一样。

路由卡字段：

```yaml
route:
  process: small-direct | complex-development | complex-production | awaiting-triage
  tier: standard | frontier | max      # 模型能力档位，不写型号
  effort: medium | high | max          # 推理强度
  skills: [...]                        # 只列必用项；其余由模型自选，verification 写明用了什么
  method: implement-only | debug-first | tdd | spec-plan | prototype-first
  verify: targeted | full | full+verification | full+reverse-proof
  review: human-merge | cross-provider | cross-provider+security
  confirm: 2                           # 固定：合同/启动、提交最终 PR 前
```

推导表的形状（逐格取值、必用与禁用清单由 R10b 定稿）：

| 判级输入 | process | tier / effort | method | verify | review |
|---|---|---|---|---|---|
| small，`contract_effect` 为 restore 或 unchanged，无强制风险 | small-direct | standard / medium | debug-first 或 implement-only | targeted + required CI | human-merge |
| complex，`change_control: development` | complex-development | frontier / high | tdd（合成 T01） | full + required CI | 项目合同决定 |
| complex，`production`，无高风险 flag | complex-production | frontier / high | spec-plan | full（按证据来源加 verification） | 平台仓 cross-provider |
| complex 且含高风险 flag（security、schema/data、external-contract、shared-core、CI/制品/部署/回滚、Agent 或平台治理） | complex-production（强制） | frontier / max | spec-plan | full + reverse-proof + verification | 平台仓 cross-provider 必须；项目仓按项目合同，至少 Matt `code-review` 的 spec 轴 |
| `contract_effect: unclear` 或 `confidence: low` | awaiting-triage | frontier / high（只分析） | — | — | 人裁决 |

约束：

- **单一来源。** 路由表只有一份，放在 `aisoft-platform` 技能的 references 内；若工具需要机器读，从同一文件生成，不维护第二份。
- **只钉两类。** 必用（如大需求的 `grill-me`、complex-production 的 `to-spec` → `to-tickets`、收尾前的完成核验、两个确认点、平台仓 complex 的交叉审查）与禁用或限制（如 `writing-plans` 不替代 Txx 计划、并行子代理不写同一 worktree、外部技能的远端收尾动作不可用、`brainstorming` 不自行定级）。其余技能由模型按 Issue 自选。
- **档位不是型号。** 合同只写档位；型号按工具另列一张映射表，由 R10b 写入 `08` §7（负责人已采纳的初始映射见项目库最终版计划 §2）。型号会变，合同不变。派单卡片由人按 tier 选型号。
- **不加标签维度。** 判级投影仍是现有四维标签，不新增 `route/*`；路由卡只在 front matter 与 Issue 评论里。
- **三端一致。** 路由卡引用的外部技能在 Claude、Codex、Cursor 上是同一 pin 版本（R10c）。

### D2 VM 执行引擎退出

VM 上的 Development Loop（controller、provider adapter、verifier、state）、只服务 Loop 的 `codex/agent` 脚本、
`codex/systemd/` 单元模板、`codex/install-vm.sh` 安装面、routine merge 与 pilot schema、broker 的
`gitea.pull.merge.routine` 与 `vm.profile.*` 操作，全部退出平台 `main`，按 R8 的迁出做法处理（迁出说明列路径与最后所在 commit，
不把树复制进 `archive/`）。VM 上已停用的定时器、旧单元与 LocalWMS 的 routine merger 声明随之清理。

保留并作为路由合同实现的部分：判级规则引擎与 analyzer schema、语义文档 resolver 与合同校验、`change_control`、
会话工具（命名、worktree 归属、文档检查、PR URL 回填、判级投影、终态）以及 K1 凭据托管与 `git.push.change`。

### D3 执行引擎分三个阶段

| 阶段 | 引擎 | 触发条件 | 做什么 |
|---|---|---|---|
| 1（现在） | Mac 交互会话 + 协调者派单的线程（已在用） | 无 | 按卡执行；路由卡的产出、确认点 1 展示与派单任务书字段待 R10b 落地，之前沿用现有判级与派单做法 |
| 2（R11 之后） | 同上 + Mac 上无人值守的只读步骤 | 路由卡落地 | 判级与交叉审查用 `codex exec -s read-only` / `claude -p` 跑，只输出候选，不写远端 |
| 3（条件触发） | Mac 上的 headless implement，只对 small-direct | 见「重开条件」 | 在 worktree 内跑到 `AWAITING_PR_CONFIRMATION`，仍由人确认提交 PR、人合并 |

### D4 合并永远是人

routine 自动合并退出。自动化最多止于「PR 候选」，不越过唯一交付闸门；PR merge 仍不传递部署授权。

## 后果

- **代码与安装面**（R10a）：删除 D2 所列代码、单元与操作，broker 操作 39 → 34，installer 7 → 6；`gitea-token.sh`、
  `gitea-label-manifest.sh`、`change-merge-range.sh`、`aisoft-project-target.sh` 被会话工具依赖，核实后保留；`aisoft_loop/cli.py`
  只留会话工具子命令；manifest 删除 `vm_profile` 段与 routine merger 声明。`AGENTS.md` 中 Development Loop、Controller、
  `IMPLEMENT_PROVIDER=none` 三处由 R10a 以治理文件受控步骤改写。
- **技能**（R10b）：路由表进 `aisoft-platform` 技能，`issue-session-flow` 的确认点 1 候选与派单任务书展示路由卡，
  summary 模板加 `route:` 块，`03` §2 加「路由」小节，`08` §7 加模型档位表；发布包升版。
- **外部技能**（R10c）：superpowers vendor pin，Cursor 与项目级由发布包导出，三端核对同一 commit；改掉 #355「平台不自建 pin」。
  #392 确认点 1 修正：Claude 与 Codex 仍从官方 marketplace 同步、平台不安装，pin 只作核对基准。
- **文档**：`04` 压成「候选状态与迁出说明」，`08` §4、§6 压缩（R10a）；分册全面改现行合同体归 R14。
- **代价**：放弃从未跑通的无人值守自治全链（自动实现 + routine 自动合并）。它只对 small 开放，按事实表候选上限约 6% 的 Issue；需要时按 D3 在 Mac 上重建。
- **不变**：两个确认点、受保护 `main`、broker 唯一写路径、平台仓 complex 的交叉审查、人工合并、独立部署授权。

## 重开条件

无人值守的 implement（阶段 3）只有在下列三条**同时**满足时才可以开 Issue 讨论，且只对 `small-direct` 开放：

1. [平台级 E2E 验收表](../governance/platform-e2e-acceptance.md) 至少有一行是当前发布包版本；
2. 某个项目的 `complexity/small` 占比 ≥ 30%，且月度 small Issue ≥ 10 条；
3. 阶段 2 的只读无人值守步骤已稳定运行一个月。

重开时只在 Mac 上重建（`claude --print` / `codex exec` 的薄封装，形状见 R10a 迁出说明），不回 VM，不恢复 routine 自动合并；
它产出的仍是 PR 候选，提交 PR 与合并由人确认。
