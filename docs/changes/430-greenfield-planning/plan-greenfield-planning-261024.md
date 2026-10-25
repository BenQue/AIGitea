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
updated: 2026-10-25
---

# Plan：全新项目需求发现与滚动阶段规划

## 全局约束与接口

负责人于 2026-10-25 确认本修订计划及 spec：固定修订、同步 Issue 并读回，设为 approved 后启动 T01；T01 治理文件提交后停止，由 fresh run 在同一合同授权内继续。确认点 2 前不 push、不建 PR。Claude 合同评估已完成并吸收进本版；实施授权来自负责人的本次确认。

- 唯一 Issue #430，exact branch `change/430-greenfield-planning`，唯一 worktree writer；最大允许范围为 spec git_scope 的 13 个文件。
- 当前 provider 为 Codex；执行前以现行 `route-policy` 解析具体技能。若负责人改由 Claude 实施，显式更新 provider 并记录重算差异，不能带着 Codex 路由直接执行 SP。
- 新方法只新增通用 reference 与薄指针；Issue、Txx、两确认点、人合并、部署边界及 production/development 现行规则不变。
- 任何 Gitea/Git 远端写入经 typed broker；没有最终 PR 确认之前不 push、不建 PR。
- 不安装、调用或接入 Spec Kit/GSD/gstack，不修改真实项目、用户技能目录、外部 vendor、runtime 或 CI 脚本。
- 公开原文、内部约定和本票设计推断分别说明。已有代码项目转现行导入/对齐；项目资料不写进平台仓。
- 阶段 ID 只是文档引用；不新增 machine schema、resolver role、lifecycle 或批准状态。
- 每票「验证」字段里的每个反引号片段都是必跑命令，证据按计划原样记录命令字符串，实际取值（RELEASE_BASE、NEXT_MINOR、RELEASE_DATE、ISOLATED_BUNDLE，以及 T03 经 broker fresh-fetch 后的 main SHA 即 FRESH_MAIN）写在 evidence 文本里。逐票进展只写 Ticket graph 的 Status、verification 的 aisoft-execution 证据，或本文末尾成对标记的执行证据区；改动本计划其它内容属于语义合同变更，按既有机制处理。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 通用方法、最小模板、现有入口衔接与使用包版本；独立治理提交后 STOP | - | done |
| T02 | fresh run 场景核验、隔离分发与现有回归证据 | T01 | done |
| T03 | 实际实现的独立评议、finding 收口及最终 PR 候选 | T02 | done |

Txx 是唯一任务身份。后续 provider 使用执行视图时只从本 canonical plan 派生，不维护另一份 Task 清单。

## T01：通用方法与入口受控更新

- **交付/范围**：实现 spec §2–6 的 canonical reference 和内嵌模板；按 spec §6.2–6.3 给 aisoft-platform 与 issue-session-flow 两个技能、getting-started、USER-GUIDE、CONTRACT 加指针与必要衔接，03 回链可选。先在 usage/bundle.json 的 members 登记新 reference（mode 为 skill），再追加向后兼容 minor release。只更新本票合同的实际决定与进展。
- **blocked_by**：无；负责人已明确确认完整合同，启动前仍须完成 Issue 合同同步，并核对远端与 summary.status 均为 approved。
- **AC**：AC-3、AC-5、AC-7、AC-11。
- **接口/约束**：复用现有路线图表形；新增规划字段用正文或模板，不扩工具 schema。所有重复规则回链 canonical reference，路由细节回链 route-policy，通用原则回链 engineering-principles。新 reference 只写阶段规划专属做法，「外部技能包边界」只加一句指针。避开 spec §6 列出的 smoke 守卫。在 `prepare-ticket 430 T01` 之前经 broker fresh-fetch main，完成必要整合与版本重算，记录固定 RELEASE_BASE 与最新发布版本；之后 RELEASE_BASE 固定，T02 沿用同值。准备时基线 08aac8d5 上最新已发布版本是 1.16.0（#427），对应下一 minor 为 1.17.0，实施前重算。若实施 provider 改变，解析命令显式换成实际 provider。
- **验证**：
  - `git diff --check`
  - `bash codex/tools/aisoft check-change-documents --porcelain`
  - `bash codex/tools/aisoft resolve-route 430 --provider codex`
  - `bash codex/tools/usage-bundle.sh --release "$NEXT_MINOR" --today "$RELEASE_DATE" --compatibility minor --notes '新增全新项目需求发现与滚动阶段规划方法及入口'`
  - `bash codex/tools/usage-bundle.sh --verify --baseline-ref "$RELEASE_BASE"`
  - `AISOFT_USAGE_BASELINE_REF="$RELEASE_BASE" LC_ALL=C bash codex/tests/smoke.sh`
- **Expected**：仅允许文件发生必要变化；文档与路由合法；新 release 追加且历史不变，新 reference 已是成员；完整 smoke 在治理 commit 之前通过；模板不要求一次补齐全项目设计；没有安装、下游采用或新的外部包依赖。这些仅证明 source/local 一致。
- **停止条件**：需要范围外文件、运行时支持、新状态/权限/审批、外部包安装或真实项目写入时按现有机制升级。治理内容通过上述本地检查后独立 commit，**立即 STOP**；不在同一 run 继续按刚改的治理规则执行 T02。后续 fresh run 在原合同授权内继续，不另加普通批准点。

## T02：fresh run 与场景、隔离分发验证

- **交付/范围**：fresh run 重读本票已批准版本、现行 AGENTS/相关技能、T01 commit 和完整 diff；核对唯一 writer、branch、BASE 与依赖完成证据。fresh run 重读后先写 T01 的 Status 与 aisoft-execution 完成记录（T01 的 AC-11 只证明 commit 前检查、独立 commit 与 STOP 这一切片），再准备 T02。按下表执行人工 source/local 场景核验，构建一次隔离使用包并核对实际分发字节，运行现有完整 smoke。结果只写本票 verification/summary；不新写测试框架。
- **blocked_by**：T01。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5、AC-6、AC-7、AC-8、AC-9、AC-10、AC-11（T02 证明场景部分与 fresh run 重读切片）。
- **接口/约束**：新会话按既有 ownership 交接核对，不能抢占 worktree。场景是匿名最小资料或本地静态推演，不是实际业务项目 pilot；明确其证据级别（source）。若需修订治理文案，只在 spec scope 内另一个受控治理提交后 STOP/fresh run；不靠放松检查消除失败。若改动了任一发布包成员，按 spec §6.4 删除本批未合并 release 条目并以同一版本号重发。ISOLATED_BUNDLE 使用新建空临时目录，不能指向真实项目或用户 skills 目录。`--build` 把落点写在 `$ISOLATED_BUNDLE/project/` 下：逐字比对源 reference 与 `project/.agents/skills/aisoft-platform/references/greenfield-planning.md`、`project/.claude/skills/aisoft-platform/references/greenfield-planning.md`、`project/.cursor/skills/aisoft-platform/references/greenfield-planning.md`，并核对相邻薄指针实际可解析。受改的两个技能按既有 manifest 目标导出。S5 的子 Issue 只在新建的临时 Git 仓夹具里建 change 目录并运行两条命令，不在本 worktree 内创建；development 变体为静态推演。源码内链接按项目分发后的相对路径检查，不把维护分册当作项目一定具有的文件。

| 场景 | 输入与操作 | 应观察结果 / 反例 |
|---|---|---|
| S1 想法未接入 | 非维护者 Codex 用户，没有项目仓，只有一句业务想法 | 只产出本地笔记并转接 getting-started 的登记与采用；不配置 .scratch tracker，不运行 to-spec/to-tickets/triage/wayfinder；记录当时实际可用的工具与技能 |
| S2 小型单阶段 | 一个目标、一个 Issue 足以实现 | 三种资料可合并；该 Issue 兼作规划 Issue，规划文件在其 git_scope 内；无强制调度会话或额外批准 |
| S3 多领域多阶段 | 当前身份与核心数据、下一业务流程、远期分析 | 当前有边界与退出证据；下一只有轮廓；远期不虚构任务和交付日期；访谈在远期分支停下并写成假设行 |
| S4 已有材料或代码 | 分别给旧需求文档与已有实现 | 前者复用并补缺口；后者转现行对齐/增量 Issue，不重做项目初始化 |
| S5 路由差异 | production/development、small/complex、Codex/Claude/Cursor；多 Issue 阶段中 maintenance 加 change 的 production complex 子 Issue | 新方法只引用现行路由；development 仍可 AC+合成 T01，provider 只选一个执行入口；该子 Issue 的 resolve-route 与 check-change-documents 均 PASS，路由卡与 resolve-route 输出一致（人按 route-policy 覆盖时 override_reason 写明 skills） |
| S6 当前合同变化 | 新发现影响一个已 approved Issue 的 AC | 调整经 broker 评论记到该 Issue、不改其正文，由其会话停下受影响部分并按现有合同变更处理；独立 Issue 可继续；无静默改合同 |
| S7 远期假设失效 | 远期集成取消，对当前无影响 | 更新理由、依赖和后续方向；不自动阻塞独立当前阶段 |
| S8 跨会话恢复 | 去掉聊天历史，只给项目 AGENTS.md | 从「项目规则」找到入口，恢复当前/下一范围、关键未知和证据；不存在第二任务图 |
| S9 其它规划包可见 | 本机可见会自建项目或阶段状态的规划包 | 不被当作本方法的工具；Matt 基线仍可工作；记录能力缺口，不自动安装或接管编排 |
| S10 完成证据冲突 | Issue 已合并但阶段集成或业务观察缺失 | 记录结果未证实/缺口；不将合并、CI、部署或 UAT 混为一谈 |
| S11 并行 Issue 与规划资料 | 两张并行实现 Issue 都发现路线图需要调整 | 两者都不改规划资料，只在各自 Issue 记录；调度会话起草，由一张规划 Issue 写入并列进其 git_scope |

- **验证**：
  - `git diff --check`
  - `bash codex/tools/aisoft check-change-documents --porcelain`
  - `bash codex/tools/aisoft resolve-route 430 --provider codex`
  - `bash codex/tools/usage-bundle.sh --verify --baseline-ref "$RELEASE_BASE"`
  - `bash codex/tools/usage-bundle.sh --build "$ISOLATED_BUNDLE"`
  - `AISOFT_USAGE_BASELINE_REF="$RELEASE_BASE" LC_ALL=C bash codex/tests/smoke.sh`
- **Expected**：S1–S11 的预期和反例都有可复核的观察位置；隔离导出字节正确；文档/路由/历史/完整 smoke 通过。静态推演不声称真实 provider 会话已执行或真实项目已采用。
- **停止条件**：失败按原因记录，未运行写 NOT RUN；若所需修复超出文件/行为范围、环境阻塞或重复失败，按现有升级规则处理。没有本票 shell 改动；若未来发现必须改 shell，需先解决 scope 冲突，再履行 bash -n/ShellCheck 等既有义务。

## T03：独立评议与最终候选

- **交付/范围**：在本地候选提交后固定实际 BASE/HEAD，检查未提交/未跟踪遗漏。由未参与实现的另一提供者只读审查实际全量 diff、文档引用与验证证据；在 verification 按 03 §7 的「交叉审查」节与固定表头记录发现与处理，在 review-evidence-index 只加本票适用条目（若 #429 先合并，从 main 重建该表后只补本票一行）。整理最终候选摘要。
- **blocked_by**：T02。
- **AC**：AC-12；复核全部 AC。
- **接口/约束**：前置 Claude 合同评估不等于本任务。若 Codex 实施，独立方为 Claude；若 Claude 实施，独立方为 Codex。评议不得改别人的 worktree。实际模型/档位、来源范围、时间与回执如实记录，不以模型名称代替审查证据。候选前经 broker fresh-fetch main 并记录 FRESH_MAIN；若 main 已前进，按 03「main 整合与发布」现行规则与升级条件处理，不在本计划另定做法。治理修复仍按受控步骤和 fresh run 规则执行；发布包成员有改动时另跑完整 smoke。
- **验证**：
  - `git status --short`
  - `git diff --check`
  - `bash codex/tools/aisoft check-change-documents --porcelain`
  - `bash codex/tools/aisoft classify --verify 430`
  - `bash codex/tools/usage-bundle.sh --verify --baseline-ref "$FRESH_MAIN"`
- **Expected**：实际差异覆盖 spec scope，所有 AC 有证据或明确未达成，审查无未解决的阻塞 finding，判级读回为 projected，候选 exact HEAD 与工作树一致；平台内相关跟踪行只反映真实合并后交付范围，不声称部署/安装。候选停在 `AWAITING_PR_CONFIRMATION`。
- **停止条件**：未得到确认点 2 不 push、不创建最终 PR；最终 PR 由人合并。证据不足或 review 阻塞不能写 READY_FOR_REVIEW。若负责人只委托本轮合同准备，则完全不启动本任务。

## 文件分配与范围

| 任务 | 允许触点 |
|---|---|
| 本轮准备 | 仅本票 summary/spec/plan/verification 四份文件；同一 Issue 自包含正文和现行判级/生命周期投影 |
| T01 | spec git_scope 中新 reference、aisoft-platform 与 issue-session-flow 两个技能、getting-started、usage/USER-GUIDE、usage/CONTRACT、03（可选回链）、usage/bundle 及本票四份文档 |
| T02 | 本票 summary/verification 的结果；范围内治理修复须重新受控提交并 STOP |
| T03 | 本票 verification/summary、必要合同澄清与 review-evidence-index；真实 finding 修复按已有范围和治理停止规则 |

不需要修改 README、04、08、route-policy、aisoft-matt-workflow、AGENTS、change 模板、skills.manifest、安装脚本或 runtime。无数据库迁移。无对外业务 API 变化。源码和发布包的恢复方式见 spec §8。

## 验收映射

| AC | 任务 | 主要证据 |
|---|---|---|
| AC-1 | T02 | S1、S2、S3、S4；入口和转接指针 |
| AC-2 | T02 | S3；三种深度模板、访谈收口及反例 |
| AC-3 | T01/T02 | T01 文本与 scope diff；S2、S8、S11 |
| AC-4 | T02 | S3、S7；全局边界、决定落点与假设记录 |
| AC-5 | T01/T02 | T01 resolve-route 读回；S5 |
| AC-6 | T02 | S6、S7、S10；变化与结果证据 |
| AC-7 | T01/T02 | T01 scope diff 与技能边界文本；S9 |
| AC-8 | T02 | S8；只从 AGENTS.md 出发的恢复推演 |
| AC-9 | T02 | release 验证、隔离 build、三工具字节与链接核对 |
| AC-10 | T02 | 场景记录、文档检查、完整 smoke、反向范围核验 |
| AC-11 | T01/T02 | T01：commit 前本地检查（含完整 smoke）、治理 commit 与 STOP；T02：开头的 fresh run 重读证据 |
| AC-12 | T03 | 最终独立评议与 finding 闭环 |

## 执行证据

<!-- execution-evidence:start -->
2026-10-25：T01 治理 commit 后 STOP 并经 fresh run 核验完成；T02 场景、三端隔离导出、完整 smoke 与两轴审查完成。T03 治理修复 a6d0a733407815c98fda765cd36045a0ee14a782 后再次 STOP，本轮 fresh run 恢复原始起点，五项检查、两轴及 Claude Opus 5.5/high 的 R2 复审均 PASS，F1/F2 fixed、residual/new=0；T03 完成记录已补齐。仅证据回填后的最终完整 HEAD 回执归同一 Issue，完成最终核对后进入 AWAITING_PR_CONFIRMATION。原批准持续有效，确认点 2 前不 push、不建 PR。
<!-- execution-evidence:end -->
