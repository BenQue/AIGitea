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
status: pending
---

# Verification：合同准备、T01 治理与后续实施证据

## 基线与范围

- Issue：`admin/aisoft-platform#427`。
- source base / change_base：`dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`。
- 当前阶段：用户已批准合同，T01 治理交付及规定本地检查完成，独立提交后 STOP；T02–T05 未执行。准备检查与治理文本检查不冒充 runtime 验收。
- 环境：Mac Codex；唯一 writer/worktree 见 summary；当前源码 Matt v1.3.1 / SP v7.0.0。
- 本记录承接 AC-1–AC-8 的实现证据，另保存无法靠最终 diff/CI 重放的原始调用来源、治理交接和审查范围。

## 合同准备历史结果

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.list --state open | PASS | 查重时只有 #417，凭据轮换；未操作该票 |
| broker git.fetch.main + git rev-parse HEAD origin/main | PASS | 二者均为上述 base；主仓 git status --short 空 |
| broker gitea.issue.create + gitea.issue.read 427 | PASS | exact admin/aisoft-platform#427，open，needs-analysis 入口；project-agent 身份 |
| aisoft change-name / claim-worktree | PASS | exact tuple、唯一 session 已核对 |
| Matt manifest 三个目录 hash | PASS | triage、to-spec、to-tickets 按现 _directory_hash 算法匹配；单文件 hash 不能拿来比较目录摘要 |
| 语义 triage | PASS | bug / ready-for-agent；问题已由源码核实，无需重复采访 |
| triage category/state 标签投影 | GAP | 当前 typed broker 仅 lifecycle/classify/extension，无 triage mutation；没有尝试越权、直连 API 或冒用标签 |
| check-change-documents --porcelain / resolve-documents 427 | PASS | change-documents、change-pr-url 均 PASS；四个映射 basename 正确 |
| type/platform + complexity/complex 投影与独立读回 | PASS | classify plan→--apply→--verify，result=projected；wrapper 的 merged summary 固定措辞不表示本地草稿已合并 |
| broker lifecycle set spec-review | PASS | after=[complexity/complex,spec-review,type/platform]；未设 approved |
| AC/Txx/范围声明预检 | PASS | 准备时 8 AC、5 pending tickets、37 个唯一 git_scope；只校验形状/唯一性，未验证 canonical holder；T01 实测后收窄至 35 条 |
| 准备阶段 T01–T05 实现测试 / 完整 smoke | NOT RUN | 准备阶段未实施；T01 本轮结果见下节 |
| required CI / installed / live / provider fresh session | NOT RUN | 未 push、安装或现场执行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | T01 已改规则源；生产解析与矩阵测试待 T02 |
| AC-2 | NOT RUN | T03 待实施 |
| AC-3 | NOT RUN | T03 待实施 |
| AC-4 | NOT RUN | T04 待实施 |
| AC-5 | NOT RUN | T04/T05 待实施 |
| AC-6 | NOT RUN | T01 已明确证据协议；真实逐票运行和终审待 T03/T04/T05 |
| AC-7 | NOT RUN | T01 源码/模板检查已完成；fresh run 与发布验收待后续完成 |
| AC-8 | NOT RUN | T05 待实施 |

## 每票执行与范围证据

本节是现有 verification 的增量，不另建状态权威。每票执行时记录：
Issue/Txx、provider/实际入口及 pin、branch/owner、plan 摘要、ticket_base、起始 staged/unstaged/untracked、授权范围；
实际命令/Expected/结果、commit 清单、candidate_head、净 diff、遗漏处置；
Standards/Spec 的共同 BASE/HEAD、实际模型/强度/上下文和 findings 的 fixed/residual/new。
缓存仅辅助恢复，不能凭 complete 文本宣告验收。整批审查另用 change_base。

T01 独立治理提交包含本记录和 plan 的 done；提交后只读回 Git 并交接，不接续 runtime。
实际 40 位提交 SHA 由本次 Issue 交接评论记录；可用 `git log -1 --format=%H -- skills/aisoft-platform/references/execution-adapter.md`
在交接时读回。fresh run 的重读 session/head 仍为 NOT RUN，承接者执行后在此追加。

## T01 实际执行与验证（2026-10-23）

- 用户批准原文：“确认 #427 合同，启动 T01，保持现有技能默认分工和两个确认点。T01 提交后按治理规则停止并交接 fresh run，后续在本次批准范围内继续推进，不重复请求启动确认。”
- 批准对象 / ticket_base：`5b16b9a706e9e79fc69dff27a119b9b4ca351954`。开始前 staged/unstaged/untracked 均空。
- change_base / fresh origin/main：`dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`。
- branch：`change/427-workflow-route-review`；owner：`01a16423-3e17-73b0-a723-76adc045218e`，沿用原认领，未 takeover 其他 worktree。
- 实际执行：Codex 唯一写者，读取并校验固定 Matt v1.3.1 implement / code-review；仅按批准的 T01 治理步骤写入，
  没有调用未实现的 helper。两位 Codex 子代理只读预检不是 Matt 固定候选双轴终审或 Claude cross-provider 验收。

| 实际检查 | 结果 | 证据与边界 |
|---|---|---|
| broker read #427 / git.fetch.main / owner read_marker | PASS | Issue open，基线未前进，owner/branch/worktree 匹配 |
| summary=approved / broker lifecycle approved | PASS | 原确认点 1 已明确通过；after=[approved,complexity/complex,type/platform] |
| `aisoft classify --verify 427` | PASS | projected；未修改 triage category/state |
| Matt implement / code-review 目录摘要 | PASS | 当前 vendored manifest 的 _directory_hash 匹配；没有修改 vendor |
| `change-template-sync.sh --refresh-digest --today 2026-10-23` | PASS（刷新）；GAP（下游） | 新摘要 sha256:fe938bc1bad625dd6e5b0290273547f30a1c4dfc4cfb76ba07d3aa6a3f1b3862；退出 3 来自 4 stale / 2 unverified holders，只广播、未写项目 |
| `change-template-sync.sh --verify-digest` | PASS | pinned 与 canonical 四模板聚合摘要相同 |
| tracker 源/mirror `cmp` | PASS | templates/docs/agents/issue-tracker.md 与 docs/agents/issue-tracker.md 字节一致 |
| 平台 change 模板 mirror | N/A | git ls-tree 无此目录；governance.vendors_change_templates=false；不新建无消费者副本 |
| `check-change-documents --porcelain` / `resolve-documents 427` | PASS | 四角色正确、change-documents/change-pr-url PASS；只证明现有格式检查 |
| Git 空白与范围预检 | PASS | git diff --check；NUL 分隔路径对照 35 条 scope；所有修改均在范围内 |
| R1–R5 与版本/权限边界 | PASS（源码比较） | 非技能列逐格与基线相同；保留 G1 OR 语义；runtime/vendor/AGENTS/CLAUDE/bundle 未改；SP adapted_version 仍 7.0.0 |
| 新接口行为 / 完整 smoke / bundle release/build | NOT RUN | T02–T05；当前未发布内容与旧 bundle 摘要未闭合，不宣称发布或全量通过 |
| 安装 / 真实 provider session / CI / 部署 | NOT RUN | 本阶段非目标或后续 PR 时执行 |

| 本轮 finding | 处置 | 复核 |
|---|---|---|
| T01-1：初版假设平台有 change 模板 mirror | fixed | 证实非 holder；spec.git_scope 从 37 收窄至 35，仅 canonical + 实际 tracker mirror；未改 guard/holder |
| T01-2：“空净 diff 不派审并记 PASS”文字歧义 | fixed | shared reference/spec 明确“拒绝候选，不派审、不得记 PASS”；两位只读审查者限定复核均 PASS，无残留阻断 |

## Fresh run 交接

1. 只承接 `admin/aisoft-platform#427`，worktree 为 `/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review`，
   branch 与 owner 如上；T01 当前 writer 在独立提交后停止并将本票交回 fresh run。
   同一会话恢复保持 owner；不同会话承接时仅对这个明确交回的 worktree 使用既有 claim/takeover 流程，不能跳过归属校验。
2. 先读用户本次批准、AGENTS/README、四份映射合同、T01 治理 diff、当前三个技能/route-policy/execution-adapter；
   typed broker fresh-read #427 与主干，核对 exact HEAD、干净状态及原批准范围。写入前记录承接 session/HEAD。
3. 原批准已涵盖 T01–T05，不再问启动；下一任务 T02，从单一 policy 解析 provider 到具体技能，保留风险顺序与旧卡兼容。
   按计划再执行 T03/T04/T05，保持唯一写者和线性 commit。
4. 三个新 CLI 尚未实现；当前文档 PASS 不证明 provider 语义生效。新 reference 尚未加入 usage bundle，
   T05 必须显式注册三端 skill 成员并追加新 minor、验证导出，不能提前安装或批量 adopt。
   外部适配记录 issue=427 目前只表示治理来源，SP 7.0.0 运行适配待 T02–T05，不是安装证明。
5. 下游模板广播 4 stale / 2 unverified 仅为本次 source 盘点，不操作这些项目；triage mutation 缺口仍 GAP。
6. T01 后的固定提交范围审查与最终 Fable 5/high 终审尚未做；不能把本轮提交前文案预检当成它们。
   最终按平台 complex 对真实新 HEAD 独立审查；确认点 2 前不 push/PR，人合并、部署独立。

## 合同准备只读预检

本次两个 Codex 只读调查者审阅四文件；这不是 Claude 实现终审，也未运行实施测试。

| Finding | 结论 | 处置 |
|---|---|---|
| C1：原版 SP 还会写 sdd scratch，不能声称只写 aisoft 缓存 | fixed / 复核闭合 | spec D2 / plan T03 区分两目录，绑定身份、路径与清理归属，不改 vendor |
| C2：计划全文 hash 会因合法状态更新失效 | fixed / 复核闭合 | 原始审计摘要与语义恢复摘要分开，规定排除范围；正常补证可恢复/语义改变拒绝均有用例 |
| F6/治理/证据边界预检 | PASS | AC-4/5、N5–N8、STOP/fresh run、small/SP 与 installed 非目标均无阻断缺陷 |

未来若实施变化，不能把本节合同预检当作实现 PASS。

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 实施终审 | Codex | Claude Code Fable 5 / high（实际调用待记录） | 待实施候选 | NOT RUN | 研究方案 SUPPORT 不替代本票实现终审 |

## 遗留风险与未完成项

- 本轮交付 T01 治理源码，未证明任何新 runtime 行为或安装采用；整体 AC 仍待 T02–T05 闭合。
- triage 标签 mutation 缺少现有 typed 入口，语义结论与未投影事实均已保留。不得以 needs-analysis/spec-review/approved 冒充 triage 状态；该既有工具缺口不夹带为本票 broker 扩权。
- fixture 可以证明固定源码调用链，不能证明当前 Codex 6.4.2 插件与平台 7.0.0 等价；实际来源必须分层。
- 本轮不部署，故无部署验收章节；后续未运行的实现/CI/真实会话项保持 NOT RUN。

## Fresh run 接收与 T02 开始

- 用户明确要求本轮以 fresh run 接续 T02–T05，沿用原批准。已重读 AGENTS/README、四合同、T01 diff、当前源码三个平台技能、route-policy/execution-adapter、03/04/08、ADR 0002 与工程原则；不依赖旧安装副本。
- 承接 session：`01a16423-3e17-73b0-a723-76adc045218e`，与原 owner 相同，原认领保持。
- fresh broker Issue read：open / approved / complexity/complex / type/platform。第一次两项读操作在执行前自动许可审核超时，各按工具许可重试一次后 PASS。
- fresh origin/main：`dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`；T02 ticket_base：`9e03f834456b3e684ef921b8e91b5da8538befde`；起始 staged/unstaged/untracked 均空。
- 映射 plan：`docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md`；开始原始 SHA256：`67c75f364d84a56506a51b56fe1e67b3d6c60ecc0c301f12f812a21388132cd6`。T03 helper 尚未实现，此记录是开始前人工审计证据。
- 执行入口：固定 Matt v1.3.1 implement / tdd（目录摘要已核对）；测试 seam 和 Expected 取已批准 plan T02，无新增确认。provider=Codex；本会话模型/推理沿当前宿主配置，不将档位等同未读回的具体型号。
- 授权最大集合：spec.git_scope 35 条；T02 仅路由 runtime/CLI、必要合同检查、对应测试与本票证据。

### T01 提交后补充双轴审查

Standards / Spec 分别由独立 Codex 只读子代理对 `5b16b9a706e9e79fc69dff27a119b9b4ca351954...9e03f834456b3e684ef921b8e91b5da8538befde` 复核；唯一 commit 9e03f83，两轴均 VERDICT PASS、零 findings。上下文为已提交 diff、AGENTS/工程原则、映射 spec/plan 与 T01 阶段边界；不是 Claude 终审。

### T02 实施记录

- RED：新增生产 resolver seam 首次执行失败 `ModuleNotFoundError: aisoft_loop.route_policy`。
- GREEN：引入同一 policy 的薄解释器，接 resolve-route CLI 与 provider-aware summary 校验；历史无 provider 只读兼容，显式重新解析输出差异，不写文档。已批准覆盖保留且具体字段须在 override_reason 中可识别。
- 单测覆盖 policy 字节变化影响运行结果与摘要、三 provider/两环境/两仓库角色、R1–R5 与 M1/V1/S1/P1/G1、未知/空/重复/未展开技能、新卡冲突、历史 CLI 只读。
- 一次矩阵测试 fixture 自身违反旧 classifier 的 unclear 必须省略 effective_complexity 条款，修正 fixture，分类器未改。
- 本票 summary 仅补显式 route_provider=codex；运行输出 R3 / frontier-max / 两确认点，与原已批准具体技能一致（differences={}）。
- 文档门、bash -n、ShellCheck、git diff --check PASS。完整 smoke 留到 T05；新模块分发资产亦在 T05 注册，不宣称已安装。

T02 required targeted suite：62 tests PASS；scope/branch/owner 本地复核 PASS。候选先提交后派两轴，固定 HEAD 在后续证据记录。

T02 第一候选 `1052738150c2d2e9154b1bad2c5c8ad4c88b77f8` 的独立双轴发现：
- T02-Spec-1（P2）：历史 `03-verification.md` 未触发 V1。已复用原 required_roles 规范化，新增三provider与CLI历史正例。
- T02-Standards-1（P2）：高风险类型/修饰动作未完全从 policy 读出或拒绝未知。已从 policy 提取类型、显式拒绝未知动作/闭集，并补漂移反例。
两项先 RED 后修复；fixed 待新 HEAD 复核，未重写历史或修改治理 policy。

### T02 闭合 / T03 开始前回执

T02 两轴对新 HEAD `b5414a9236aebec65e8e8cbb51996da626eaeda4` 限定复核均 VERDICT PASS。Spec-1 / Standards-1 fixed，residual/new 均无。required 定向测试 65 PASS。

T03 ticket_base：`b5414a9236aebec65e8e8cbb51996da626eaeda4`；开始前 staged/unstaged/untracked 均空（在更新本段前读取）。同一 owner/branch/worktree、provider=codex；固定 Matt v1.3.1 implement/tdd。原计划 raw SHA256：`67c75f364d84a56506a51b56fe1e67b3d6c60ecc0c301f12f812a21388132cd6`。本回执在实现前记录，helper 尚不存在；不冒充 helper 自举运行。继承 spec 35 条范围与原批准的测试 seam/Expected。

### T03 实施与本地验证

- RED：生产 seam 首次失败 ModuleNotFoundError: ticket_execution；随后 fixture 的 owner claim 参数和必填文档元数据按现合同修正，未放松合同。
- 新 prepare-ticket 只读 Git/合同，经现 project resolver + typed gitea.issue.read 读批准状态；只写 worktree ignored cache/sdd 登记。无 add/commit、网络变更或 HOME 写入。
- 精确 Txx 图/正文、依赖环/未知/重复/围栏伪正文/ID 混淆拒绝；派生 Task N 携带全局与本票合同；原版 SP v7.0.0 task-start→task-brief 在临时 Git/HOME 实际调用 PASS。
- 开始回执绑定 Issue/branch/owner/provider、原始/语义摘要、source pin、scope、BASE 与三类起始状态。完成证据采用映射 verification 中 aisoft-execution JSON fence；逐 AC、验证摘要/commands/result/evidence 及真实 Git range 必须匹配。不是另建完成数据库。
- 正常 Status/updated/指定 JSON 证据区变化可恢复；语义/owner/BASE/foreign scratch/symlink 反例失败；无关用户文件保留。development synthetic T01 不要求 production plan；small 维持原入口。
- `PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_ticket_execution tests.test_documents`：30 tests PASS；bash -n / ShellCheck wrapper、文档门、git diff --check PASS。完整 smoke/导出与终审待 T05。
- 候选提交后派同一 BASE/HEAD 双轴；未以测试 PASS 代替审查。

T03 首轮双轴对 `9d08506a48e6165b0e1a544ab22549b2b7cfbf01` 均发现同两项：
- T03-1（P1）：完成范围未绑定开始回执，可能把旧票 range 当成本票。已要求持久 start 回执包含同票 identity/semantic/scope/BASE，且有缓存时须与原回执完全一致；无回执、旧票 range、HEAD=本票起点、错 owner 负例拒绝。
- T03-2（P2）：marker 与 T01 canonical 不一致。runtime 采用批准的 `execution-evidence` 成对标记，支持模板普通审计文本；只允许独立执行证据区，不能包任务/图/约束；正常 NOT RUN→PASS 补证 resume 正例通过。
修复未动治理；required targeted suite 33 tests PASS。fixed 待追加提交后的同 HEAD 复核。
