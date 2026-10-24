---
issue: 430
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/430
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/430-greenfield-planning
created: 2026-10-24
updated: 2026-10-24
---

# Plan：全新项目需求发现与滚动阶段规划

## 全局约束与接口

本计划是确认点 1 候选。当前只准备文档、判级与完整 Issue，以下 T01–T03 均未获准执行。负责人将自行提交 Claude 内部评估；评估不是实施授权。

- 唯一 Issue #430，exact branch `change/430-greenfield-planning`，唯一 worktree writer；精确范围为 spec 的 15 个文件。
- 当前 provider 为 Codex；执行前以现行 `route-policy` 解析具体技能。若负责人改由 Claude 实施，显式更新 provider 并记录重算差异，不能带着 Codex 路由直接执行 SP。
- 新方法只新增通用 reference 与薄指针；Issue、Txx、两确认点、人合并、部署边界及 production/development 现行规则不变。
- 任何 Gitea/Git 远端写入经 typed broker；没有最终 PR 确认之前不 push、不建 PR。
- 不安装、调用或接入 Spec Kit/GSD/gstack，不修改真实项目、用户技能目录、外部 vendor、runtime 或 CI 脚本。
- 公开原文、内部约定和本票设计推断分别说明。已有代码项目转现行导入/对齐；项目资料不写进平台仓。
- 阶段 ID 只是文档引用；不新增 machine schema、resolver role、lifecycle 或批准状态。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 通用方法、最小模板、现有入口衔接与使用包版本；独立治理提交后 STOP | - | pending |
| T02 | fresh run 场景核验、隔离分发与现有回归证据 | T01 | pending |
| T03 | 实际实现的独立评议、finding 收口及最终 PR 候选 | T02 | pending |

Txx 是唯一任务身份。后续 provider 使用执行视图时只从本 canonical plan 派生，不维护另一份 Task 清单。

## T01：通用方法与入口受控更新

- **交付/范围**：实现 spec §2–6 的 canonical reference 和内嵌模板；给三个已有技能、getting-started、usage 两份文档、03/04 添加指针与必要衔接。新增 reference 为 usage bundle 成员，并追加向后兼容 minor release。只更新本票合同的实际决定与进展。
- **blocked_by**：无。前置条件是负责人对完整合同的明确 `approved`；当前尚不满足。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5、AC-6、AC-7、AC-8、AC-9、AC-11。
- **接口/约束**：复用现有路线图表形；新增规划字段用正文或模板，不扩工具 schema。业务规划文件位置由项目唯一入口说明。所有重复规则回链 canonical reference；路由细节回链 route-policy。共享治理文案一次受控提交，既有包原文与 pin 不动。
- **验证**：逐条核对 spec 的入口、三种深度、权限和文档归属；运行文档/路由/使用包检查，检查 diff 无越界。实施时 fresh-fetch main，记录固定 `RELEASE_BASE` 与最新发布版本；若 #429 等已发布新版本，先按现行分支整合规则处理，再取下一 minor。

```bash
git diff --check
bash codex/tools/aisoft check-change-documents --porcelain
bash codex/tools/aisoft resolve-route 430 --provider codex
bash codex/tools/usage-bundle.sh --release "$NEXT_MINOR" --today "$RELEASE_DATE" --compatibility minor --notes '新增全新项目需求发现与滚动阶段规划方法及入口'
bash codex/tools/usage-bundle.sh --verify --baseline-ref "$RELEASE_BASE"
```

`NEXT_MINOR`、`RELEASE_DATE`、`RELEASE_BASE` 必须由该次真实基线确定并记录，不照抄准备时的 1.16.0。若实施 provider 改变，上述解析命令显式换成实际 provider。

- **Expected**：仅允许文件发生必要变化；文档与路由合法；新 release 追加且历史不变；模板不要求一次补齐全项目设计；没有安装、下游采用或新的外部包依赖。这些仅证明 source/local 一致。
- **停止条件**：需要范围外文件、运行时支持、新状态/权限/审批、外部包安装或真实项目写入时按现有机制升级。治理内容通过必要本地检查后独立 commit，**立即 STOP**；不在同一 run 继续按刚改的治理规则执行 T02。后续 fresh run 在原合同授权内继续，不另加普通批准点。

## T02：fresh run 与场景、隔离分发验证

- **交付/范围**：fresh run 重读本票已批准版本、现行 AGENTS/相关技能、T01 commit 和完整 diff；核对唯一 writer、branch、BASE 与依赖完成证据。按下表执行人工 source/local 场景核验，构建一次隔离使用包并核对实际分发字节，运行现有完整 smoke。结果只写本票 verification/summary；不新写测试框架。
- **blocked_by**：T01。
- **AC**：AC-1 至 AC-10，及 AC-11 的 fresh run 证据。
- **接口/约束**：新会话按既有 ownership 交接核对，不能抢占 worktree。场景是匿名最小资料或本地静态推演，不是实际业务项目 pilot；明确其证据级别。若需修订治理文案，只在 spec scope 内另一个受控治理提交后 STOP/fresh run；不靠放松检查消除失败。

| 场景 | 输入与操作 | 应观察结果 / 反例 |
|---|---|---|
| S1 想法未接入 | 无仓库登记、只有一句业务想法 | 产生可迁移草案和 onboarding 转接；不声称已注册、可直接实施 |
| S2 小型单阶段 | 一个目标、一个 Issue 足以实现 | 三种资料可合并；无强制里程碑、调度会话或额外批准 |
| S3 多领域多阶段 | 当前身份与核心数据、下一业务流程、远期分析 | 当前有边界与退出证据；下一只有轮廓；远期不虚构任务和交付日期 |
| S4 已有材料或代码 | 分别给旧需求文档与已有实现 | 前者复用并补缺口；后者转现行对齐/增量 Issue，不重做项目初始化 |
| S5 路由差异 | production/development、small/complex、Codex/Claude/Cursor | 新方法只引用现行路由；development 仍可 AC+合成 T01，provider 只选一个执行入口 |
| S6 当前合同变化 | 新发现影响一个已 approved Issue 的 AC | 停受影响部分并按现有合同变更处理；独立 Issue 可继续；无静默改合同 |
| S7 远期假设失效 | 远期集成取消，对当前无影响 | 更新理由、依赖和后续方向；不自动阻塞独立当前阶段 |
| S8 跨会话恢复 | 去掉聊天历史，只提供项目入口与 Issue 链接 | 可恢复当前/下一范围、关键未知和证据；不存在第二任务图 |
| S9 技能不可用 | 项目未允许或未安装候选技能包 | Matt 基线仍可工作；记录能力缺口，不自动安装或接管编排 |
| S10 完成证据冲突 | Issue 已合并但阶段集成或业务观察缺失 | 记录结果未证实/缺口；不将合并、CI、部署或 UAT 混为一谈 |

**验证命令**（每次变量取该 run 固定的真实值）：

```bash
git diff --check
bash codex/tools/aisoft check-change-documents --porcelain
bash codex/tools/aisoft resolve-route 430 --provider codex
bash codex/tools/usage-bundle.sh --verify --baseline-ref "$RELEASE_BASE"
bash codex/tools/usage-bundle.sh --build "$ISOLATED_BUNDLE"
AISOFT_USAGE_BASELINE_REF="$RELEASE_BASE" LC_ALL=C bash codex/tests/smoke.sh
```

`ISOLATED_BUNDLE` 使用新建空临时目录，不能指向真实项目或用户 skills 目录。逐字比对源 reference 与导出 `.agents/skills/aisoft-platform/references/greenfield-planning.md`、`.claude/skills/aisoft-platform/references/greenfield-planning.md`、`.cursor/skills/aisoft-platform/references/greenfield-planning.md`；核对相邻薄指针实际可解析。三个修改技能按既有 manifest 目标导出：`aisoft-matt-workflow` 仍只到 Codex，不能要求它出现在 Claude/Cursor。既有源码内链接按项目分发后的相对路径检查，不把维护分册当作项目一定具有的文件。

- **Expected**：S1–S10 的预期和反例都有可复核的观察位置；隔离导出字节正确；文档/路由/历史/完整 smoke 通过。静态推演不声称真实 provider 会话已执行或真实项目已采用。
- **停止条件**：失败按原因记录，未运行写 NOT RUN；若所需修复超出文件/行为范围、环境阻塞或重复失败，按现有升级规则处理。没有本票 shell 改动；若未来发现必须改 shell，需先解决 scope 冲突，再履行 bash -n/ShellCheck 等既有义务。

## T03：独立评议与最终候选

- **交付/范围**：在本地候选提交后固定实际 BASE/HEAD，检查未提交/未跟踪遗漏。由未参与实现的另一提供者只读审查实际全量 diff、文档引用与验证证据；在 verification 记录发现与处理，在 review-evidence-index 只加本票适用条目。整理最终候选摘要。
- **blocked_by**：T02。
- **AC**：AC-10、AC-11；复核全部 AC。
- **接口/约束**：前置 Claude 合同评估不等于本任务。若 Codex 实施，独立方为 Claude；若 Claude 实施，独立方为 Codex。评议不得改别人的 worktree。实际模型/档位、来源范围、时间与回执如实记录，不以模型名称代替审查证据。治理修复仍按受控步骤和 fresh run 规则执行。
- **验证**：fresh `git status`、`git diff --check`、文档检查、scope diff、必要受影响检查；读取实际 reviewer 报告与 finding 闭环。无代码运行变化时不无理由反复全量 smoke；新增修改、失败或未消除问题才触发相应重测。
- **Expected**：实际差异覆盖 spec scope，所有 AC 有证据或明确未达成，审查无未解决的阻塞 finding，候选 exact HEAD 与工作树一致；平台内相关跟踪行只反映真实合并后交付范围，不声称部署/安装。候选停在 `AWAITING_PR_CONFIRMATION`。
- **停止条件**：未得到确认点 2 不 push、不创建最终 PR；最终 PR 由人合并。证据不足或 review 阻塞不能写 READY_FOR_REVIEW。若负责人只委托本轮合同准备，则完全不启动本任务。

## 文件分配与范围

| 任务 | 允许触点 |
|---|---|
| 本轮准备 | 仅本票 summary/spec/plan/verification 四份文件；同一 Issue 自包含正文和现行判级/生命周期投影 |
| T01 | spec.git_scope 中新 reference、三个技能、getting-started、usage/USER-GUIDE、usage/CONTRACT、03/04、usage/bundle 及本票四份文档 |
| T02 | 本票 summary/verification 的结果；范围内治理修复须重新受控提交并 STOP |
| T03 | 本票 verification/summary、必要合同澄清与 review-evidence-index；真实 finding 修复按已有范围和治理停止规则 |

不需要修改 README、08、route-policy、AGENTS、change 模板、skills.manifest、安装脚本或 runtime。无数据库迁移。无对外业务 API 变化。源码和发布包的恢复方式见 spec §8。

## 验收映射

| AC | 任务 | 主要证据 |
|---|---|---|
| AC-1 | T01/T02 | S1、S2、S4；入口和转接指针 |
| AC-2 | T01/T02 | S3；三种深度模板及反例 |
| AC-3 | T01/T02 | S2、S8；唯一入口、Issue/Txx 原始合同链接 |
| AC-4 | T01/T02 | S3、S7；全局边界与假设记录 |
| AC-5 | T01/T02 | S5；现行 route-policy 解析与文案对照 |
| AC-6 | T01/T02 | S6、S7、S10；变化与结果证据 |
| AC-7 | T01/T02 | S9；scope diff 和技能选择说明 |
| AC-8 | T01/T02 | S8；不含聊天历史的恢复推演 |
| AC-9 | T01/T02 | release 验证、隔离 build、三工具字节与链接核对 |
| AC-10 | T02/T03 | 场景记录、文档检查、完整 smoke、反向范围核验 |
| AC-11 | T01/T02/T03 | 治理 commit/STOP/fresh run 记录、最终独立评议 |

## 执行证据

当前 T01–T03 全部 pending；本轮检查只针对合同候选本身，见 verification。未开始的任务不得记录为完成。
