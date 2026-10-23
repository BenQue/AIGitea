---
issue: 427
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/427
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
  - cross-module
depends_on: []
branch: change/427-workflow-route-review
created: 2026-10-23
updated: 2026-10-23
git_scope:
  - docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md
  - docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md
  - docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md
  - docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md
  - skills/aisoft-platform/references/route-policy.md
  - skills/aisoft-platform/references/execution-adapter.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/issue-session-flow/SKILL.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 08-双工具共存与实施.md
  - templates/docs/agents/issue-tracker.md
  - docs/agents/issue-tracker.md
  - templates/docs/changes/_template/summary.md
  - templates/docs/changes/_template/plan.md
  - docs/changes/_template/summary.md
  - docs/changes/_template/plan.md
  - codex/config/change-template-sync.json
  - codex/config/external-skill-adaptation.json
  - codex/runtime/aisoft_loop/route_policy.py
  - codex/runtime/aisoft_loop/ticket_execution.py
  - codex/runtime/aisoft_loop/review_candidate.py
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/aisoft_loop/documents.py
  - codex/runtime/aisoft_loop/cli.py
  - codex/tools/aisoft
  - codex/runtime/tests/test_route_policy.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/test_documents.py
  - codex/runtime/tests/test_ticket_execution.py
  - codex/runtime/tests/test_review_candidate.py
  - codex/runtime/tests/test_session_contract.py
  - codex/tests/smoke.sh
  - codex/tests/test-usage-bundle.sh
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
---

# Spec：修复路由与候选审查范围

## 目标与原因

实现用户认可方案的第一阶段：F1/F6 优先，F2/F3/F5 仅做与两者直接相关的适配。不全面替换 Superpowers，不重写分类/调度引擎。
当前风险来自平台固定源码的可达路径，尚无证据证明历史 Issue 已漏审。验收必须区分规则改正、机械检查、真实调用与现场采用。

基线是 `dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`。Matt v1.3.1 / SP v7.0.0 保持不变。
需求、默认分工与非目标已经由用户明确，不再调用采访补问已有答案；本文件与计划一并提交原确认点 1。

## 方案与决策

### D1：F1 同一来源、显式 provider、具体技能

route-policy 保留为唯一规则源。增加同文件内的 provider 映射，平台薄解析器读取规则/映射，最终 route.skills 仍为具体技能名，不输出能力占位符。不能让测试与生产分别维护技能硬编码表。

route 保留现有八个键及闭集；新增 summary 顶层 `route_provider`，值限 `codex|claude|cursor`。新生成卡必须显式输入 provider 并保存它；解析回执记录命中规则和 policy 摘要。缺失/未知 provider 不得静默当 Claude/SP。旧无 provider 的文档继续只读解析，不批改历史；再次执行时显式选 provider、重新解析并报告差异，不凭旧卡猜默认。它不引入第三个人工确认：合同内一致重算直接继续，真实范围/合同变化按既有升级规则处理。

Codex 的计划执行/完成核验映射 Matt implement / 平台 issue-session-flow；Claude/Cursor 映射 SP executing-plans / verification-before-completion。R2、R5 同样映射核验，不能漏校验或强制全套 SP。未决 R1 只允许分析，不能借合法 provider 进入实现。
保留 M1/V1/S1/P1/G1 的现有语义；尤其项目 R3 的 code-review 义务不因默认执行入口消失。本票不改变 R2 在高风险 development 情形的现有优先级，不偷换风险政策。

本票准备阶段使用现 schema 的具体技能卡，在 summary.override_reason 显式写明与旧 R3 字面列表的差异；T02 后再按批准的 provider 字段格式补齐本票，不静默回写历史 Issue。

### D2：F2 Txx 是合同，Task N 是执行视图

canonical plan 继续 Txx。每票正文须有本票交付/范围、blocked_by、AC、验证命令与 Expected、全局约束/停止条件，明确当前共享接口。适配仅从映射 plan（development complex 则 Issue AC + synthetic T01）生成上游脚本识别的 Task N，本地视图携带原 Txx，不能由人独立编辑或变成第二份计划。

平台派生视图和回执放入既有 ignored 的 `.superpowers/aisoft/<Issue>/`，绑定 exact Issue/branch/owner、plan 路径/摘要和 provider。原版 SP 脚本另在 `.superpowers/sdd/<派生plan-basename>/` 写 scratch；派生 basename 必须包含 Issue、owner 和语义摘要的稳定标识以隔离会话，启动前核对 plan-path 与归属，绝不覆盖别票/别会话目录。两处均仅限当前 worktree、拒绝路径逃逸/符号链接，清理只处理自己记录的路径且先将必要证据归入 verification；不改 vendor 来强制输出位置。

同时记录原始 plan 全文摘要（审计用途）与规范化任务语义摘要（恢复判据）。语义摘要包含 Issue/branch、全局约束、Ticket ID/依赖及每票交付/范围/AC/命令/Expected/停止条件；仅排除明确的 Ticket graph Status 单元、更新时间与显式标识的执行证据区，不按任意文本启发式删段。无正式 plan 的路线使用规范化 Issue AC 与约束。正常状态推进/补证可在语义摘要不变且 commit/验证证据匹配时恢复；任务语义变化必须报告失配，不静默采纳。缓存可再生，持久证据仍写现有 plan/verification。

只执行依赖已经完成且有证据的 frontier。开始前保存 ticket_base 与起始工作树；恢复需要 plan 身份、branch/owner、BASE 祖先、提交和验证记录相符。仅有 SP complete 文本不能跳票。支持同票多 commit；Ticket ID 不按含糊前缀匹配。不得为 development complex 强加 production spec/plan。

### D3：F6 先形成完整本地候选，再审固定范围

适用使用 Matt implement/code-review 的执行单元。顺序固定：
记录 ticket_base → 实现和必要验证 → 唯一写者仅提交本票 → 固定 candidate_head → 检查范围/遗漏 → Standards 与 Spec 双轴 → 修复/重验/追加 commit → 按现合同复核新 HEAD。

candidate 必须有有效完整 SHA、BASE 为 HEAD 祖先、非空净 diff，包含本票全部 commit；不使用 HEAD~1 猜基线。最终整批另存 change_base，不能复用最后一票 BASE。非空提交历史而净 diff 为空不应派审并记 PASS。

候选检查保存 staged/unstaged/untracked 及相关 diff，结合起始状态、AC/范围和实际变更判定遗漏；原有无关文件保留，不能自动 add/stash/delete。同一脏文件被本票继续修改、范围外实际修改、必要 ignored 成果或归属不明，必须明确处置，不能默认无关。检查器仅证明确定性条件，不声称从路径自动理解所有语义或发现编辑器未保存内容。

Standards/Spec 接收相同 BASE/HEAD、commit 清单、spec/plan 和规范来源；审查中 HEAD/branch/owner 改变使旧候选失效。修复线性追加、真实重验并记录 fixed/residual/new；重审范围按现有合同。平台 complex 最终另一 provider 的新 HEAD 复审优先于 SP “一次修复不再 review”，不得重复叠加同义审查。small/SP 不因本条被新增 Matt 每票双轴义务。

### D4：适配权限、证据与治理生效

新 helper 只读取 Git/合同并生成本地执行缓存/候选包，不 add/commit/stash/reset/push、改 Issue 标签、开 PR、merge 或安装。提交和现平台状态流仍由唯一写者/已有入口负责；不新增 broker operation、owner schema 或调度服务。

共同规则放入 Claude/Codex 都能读取的 aisoft-platform / issue-session-flow 和共享 reference；Matt 入口仅引用同一合同，不复制第二套。保持源模板与平台 mirror 一致；修改 summary/plan 两个 canonical 模板要同批更新摘要，不触碰 spec/verification 模板。

明确授权的治理文件只可在 T01 独立受控步骤应用，commit 后 STOP。下一 fresh run 重新读取批准合同、治理 diff、当前规则、exact worktree/owner/HEAD 再执行 runtime。原批准持续有效，不再请求启动。若需要治理返修，同样受控提交/停止/fresh run；不在 runtime 步骤偷偷改技能来让测试通过。

不修改 AGENTS.md / CLAUDE.md；现有规则足够表达本期流程。source bundle 新成员/内容通过现有 release 工具追加新 minor 版本（基线最新 1.15.0，若无人占用则 1.16.0；有并发时顺延），记录兼容性，不重写已发布历史。新增 reference/adapter 的三端可用性用隔离导出 fixture 验证；不静默安装或替项目 adopt。

## Acceptance criteria

- [ ] AC-1：R1–R5 × 三 provider × 平台/项目 × production/development 组合按 D1 输出具体技能；优先级/修饰规则/两个确认点不变。缺失/未知 provider、空/重复/未知技能或冲突卡不得静默 PASS；历史卡保持只读兼容。
- [ ] AC-2：D2 的有效两票依赖图能生成原版 SP task-start/task-brief 消费的 Task N，AC/Expected/约束无损；重复 ID、未知依赖、环、缺正文、代码围栏内伪标题、T01/T010 混淆均拒绝。development complex 继续 synthetic T01。
- [ ] AC-3：仅 frontier 可启动；BASE 在改动前持久记录；恢复校验 Issue/branch/owner/计划语义摘要/祖先与完成证据，正常状态/补证变化可恢复而语义变更拒绝；错身份或只写 complete 不能跳票；失败或 NOT RUN 的必要验证不能完成票。
- [ ] AC-4：候选涵盖本票全部 commit/真实成果；缺 BASE、非祖先、空净 diff、相关 staged/unstaged/untracked 遗漏均阻断完整性声明；既有无关脏文件保留，ignored 不自动豁免，语义未知不虚构通过。
- [ ] AC-5：两轴使用共同 BASE/HEAD；移动 HEAD/branch/owner 或修复追加提交使旧结论失效；最终 change_base 覆盖第一票；保留平台 complex 另一 provider 实际最终 HEAD 审查且不以局部审查代替。
- [ ] AC-6：复用现有文档关联 AC→Txx→测试边界/实际结果→commit→review/finding，记录实际来源、模型与配置强度、上下文/范围；重要裁决可见，small/SP 不增加 Matt 每票义务。
- [ ] AC-7：治理 STOP/fresh run 真实留证；共同入口、template mirror/digest、source bundle 与适配版本记录一致；vendor 原文/pin、现默认、权限/CI context、既有两确认点不变；无真实安装/采用。
- [ ] AC-8：规定正负向 fixture、文档/范围检查与完整 smoke 通过，最终另一 provider exact-head 审查通过；所有结果按 source/local/CI/installed/session/live 分层，未知或未运行不得变 PASS。

## 反向证明矩阵

| 组 | 必须拒绝/不能误报的场景 | 归属 |
|---|---|---|
| N1 | Codex R3 同时硬要求两套执行；R2/R5 漏核验；未知 provider 回退；能力占位符充当技能；历史卡被猜为 Claude | T02 |
| N2 | policy 改动不影响生产解析；双份硬编码表漂移；风险 development 被静默升级/降级；项目 P1 丢失 | T02 |
| N3 | 重复/未知依赖/环/无正文/伪标题/T01 与 T010 混淆；依赖未完成先开后票 | T03 |
| N4 | 别 Issue/branch/owner/语义摘要的恢复缓存；BASE 不存在/非祖先；complete 无测试/commit 证据；上游 scratch 归属冲突或路径逃逸。配对正例：正常完成/补证后语义不变可恢复 | T03 |
| N5 | 前票提交非空而当前票未提交；staged/untracked 单独遗漏；同一原脏文件被本票继续修改 | T04 |
| N6 | 多 commit 首笔遗漏；BASE=HEAD；非空历史但净 diff 空；HEAD 移动后复用旧 PASS | T04 |
| N7 | 双轴不同 BASE/HEAD；两票终审只含末票；修复追加后旧 PASS；忽略必要 ignored 成果 | T04/T05 |
| N8 | 无关脏文件被自动提交/删除；small/SP 强加 Matt 双轴；fixture 改真实 HOME、push/PR 或改 vendor | T03/T04/T05 |

## 接口、数据与兼容性影响

新增 summary.route_provider 为本期有界元数据扩展；route 内仍八键，旧历史文档读取不迁移。新本地适配 CLI 使用现 aisoft 入口；只产本地派生物，语法和失败输出在 T01 共享 reference 锁定。无数据库/业务 API 变更；无凭据/主机/broker 扩权。现 triage mutation 工具缺口记录为 GAP，不夹带修复。

front matter 的 git_scope 是最大允许路径，未实际需要的路径不改。两个 `docs/changes/_template/` mirror 是 canonical 资源例外，按现 holder/scope 合同精确授权，不允许其他 Issue 文档或任意模板；不改 git scope guard。review-evidence-index 只追加本 Issue 行，无路线图/E2E 批次或项目采用事件。

## 风险与回滚约束

- 所有新增机器校验必须说明不能证明什么；semantic diff 判断仍由审查完成。
- 完成准备不意味着实现通过；source/fixture 不意味着安装/现场通过。
- 已提交历史不 rewrite；未发布源变更可受控 revert，合并后的回滚走新 Issue/PR 及新 bundle 版本，保留既有业务提交与证据，不 reset 数据。
- 分支仍只追加线性提交；只有确认点 2 之后才普通 fast-forward push/唯一最终 PR；人合并。

## 非目标

全面替换 SP、默认试点切换、vendor 升级、全套多 Agent 编排、并行写者、自动 merge/部署/UAT、下游采用、Wayfinder/grill-with-docs 新默认、自主 retro、全仓历史迁移、风险分类重写、模型优劣实验、triage broker 扩权。工程原则已由 #425 合并，本票不重写。

## 未决问题

无影响实现方向的未决问题。当前请求仅先形成合同与计划；等待原确认点 1 的合同/启动，不添加新确认。
