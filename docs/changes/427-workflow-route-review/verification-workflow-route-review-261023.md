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
- 当前阶段：T01 独立治理提交后 STOP；用户 fresh-run 接续，T02–T04 已完成且双轴 PASS。T05 source/local 检查部分通过，唯一旧 fixture 范围补正已获用户明确授权，正在完成补正后验证；完整 smoke 与 Claude 最终评议未完成。历史准备/治理检查保留为审计，不冒充整体完成。
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
| AC-1 | PASS（source/local） | T02 provider/policy 矩阵、legacy/V1/风险漂移负例；65 route/contract/doc tests 与三端独立导出 CLI |
| AC-2 | PASS（source/local） | T03 原版 SP task-start/task-brief 无损消费及 parser 负例；固定 vendor 不变 |
| AC-3 | PASS（source/local） | T03 实际 Git frontier/receipt/resume；T05 明确 scope 增补保留开始快照正负例 |
| AC-4 | PASS（source/local） | T04 实际 Git 多提交、遗漏/净空diff/起始脏文件/必要ignored负例；实际 wrapper/broker 候选链 |
| AC-5 | PENDING | T04 双轴包/新HEAD/整批范围回归 PASS；T05整批另一provider终审待完成 |
| AC-6 | PENDING | 已记录逐票 BASE/HEAD、双轴 findings fixed/residual/new；待 T05 指定模型实际终审 |
| AC-7 | PASS（source/local） | T01治理STOP后fresh-run真实重读；mirror/digest、1.16.0三端导出及旧release/vendor保持检查通过；无安装采用 |
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

T03 修复复核：原 T03-1/2 两轴均 fixed；Standards 新报 T03-3（P2）：整体 identity 对比会阻塞合法 successor 消费前 owner 的已完成依赖。已以真实 claim/takeover fixture 复现并修复：依赖保留历史合法 owner，当前调用仍须通过 owner marker；当前票 resume 不放松 exact owner。34 tests PASS。真实 #427 的 context→现项目解析→typed broker Issue read 也已 PASS；无远端写入。

### T03 闭合与结构化旧记录承接

T03 在 56e5503fa23fd9f78a780380ca8ecada5b865582 两轴均 PASS；T03-1/2/3 fixed，无 residual/new。以下将已在开始前记录的 T01–T03 BASE/身份/起始干净状态与实际结果转换为 helper 可读结构。原始开始事实来自上文；plan/route 元数据在 T03 后按批准现合同补齐，不宣称旧票曾运行尚不存在的 helper。AC PASS 仅表示对应票的已批准切片。

```aisoft-execution
{
  "change_base": "dc1da41c6e6a51f85b1ec0464a97640a3ddb570e",
  "tickets": {
    "T01": {
      "base": "5b16b9a706e9e79fc69dff27a119b9b4ca351954",
      "head": "9e03f834456b3e684ef921b8e91b5da8538befde",
      "start": {
        "identity": {
          "issue": 427,
          "branch": "change/427-workflow-route-review",
          "owner": "01a16423-3e17-73b0-a723-76adc045218e",
          "worktree": "/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review",
          "provider": "codex",
          "plan_path": "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934"
        },
        "ticket": "T01",
        "ticket_base": "5b16b9a706e9e79fc69dff27a119b9b4ca351954",
        "scope": [
          "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
          "skills/aisoft-platform/references/route-policy.md",
          "skills/aisoft-platform/references/execution-adapter.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/aisoft-matt-workflow/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "04-Agent编排与定时任务.md",
          "08-双工具共存与实施.md",
          "templates/docs/agents/issue-tracker.md",
          "docs/agents/issue-tracker.md",
          "templates/docs/changes/_template/summary.md",
          "templates/docs/changes/_template/plan.md",
          "codex/config/change-template-sync.json",
          "codex/config/external-skill-adaptation.json",
          "codex/runtime/aisoft_loop/route_policy.py",
          "codex/runtime/aisoft_loop/ticket_execution.py",
          "codex/runtime/aisoft_loop/review_candidate.py",
          "codex/runtime/aisoft_loop/contract.py",
          "codex/runtime/aisoft_loop/documents.py",
          "codex/runtime/aisoft_loop/cli.py",
          "codex/tools/aisoft",
          "codex/runtime/tests/test_route_policy.py",
          "codex/runtime/tests/test_contract.py",
          "codex/runtime/tests/test_documents.py",
          "codex/runtime/tests/test_ticket_execution.py",
          "codex/runtime/tests/test_review_candidate.py",
          "codex/runtime/tests/test_session_contract.py",
          "codex/tests/smoke.sh",
          "codex/tests/test-usage-bundle.sh",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, implement, issue-session-flow",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "raw_plan_sha256": "9bbb98488e771b052003cd7c97b22ba147478a4bb1bbe5821de8e9108970ae21",
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "origin": "manual-pre-helper: BASE/state contemporaneously recorded above; structured contract metadata reconstructed after T03, not a claim of earlier helper execution"
      },
      "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934",
      "validation_sha256": "89fded3eb6a106fe8857669bbb8fb90e2f287f7c576000e8934ea4de8705c91d",
      "ac": {
        "AC-1": "PASS",
        "AC-6": "PASS",
        "AC-7": "PASS"
      },
      "checks": [
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "T01 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        },
        {
          "command": "codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "T01 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        },
        {
          "command": "cmp",
          "result": "PASS",
          "evidence": "T01 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        },
        {
          "command": "--verify-digest",
          "result": "PASS",
          "evidence": "T01 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        }
      ]
    },
    "T02": {
      "base": "9e03f834456b3e684ef921b8e91b5da8538befde",
      "head": "b5414a9236aebec65e8e8cbb51996da626eaeda4",
      "start": {
        "identity": {
          "issue": 427,
          "branch": "change/427-workflow-route-review",
          "owner": "01a16423-3e17-73b0-a723-76adc045218e",
          "worktree": "/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review",
          "provider": "codex",
          "plan_path": "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934"
        },
        "ticket": "T02",
        "ticket_base": "9e03f834456b3e684ef921b8e91b5da8538befde",
        "scope": [
          "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
          "skills/aisoft-platform/references/route-policy.md",
          "skills/aisoft-platform/references/execution-adapter.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/aisoft-matt-workflow/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "04-Agent编排与定时任务.md",
          "08-双工具共存与实施.md",
          "templates/docs/agents/issue-tracker.md",
          "docs/agents/issue-tracker.md",
          "templates/docs/changes/_template/summary.md",
          "templates/docs/changes/_template/plan.md",
          "codex/config/change-template-sync.json",
          "codex/config/external-skill-adaptation.json",
          "codex/runtime/aisoft_loop/route_policy.py",
          "codex/runtime/aisoft_loop/ticket_execution.py",
          "codex/runtime/aisoft_loop/review_candidate.py",
          "codex/runtime/aisoft_loop/contract.py",
          "codex/runtime/aisoft_loop/documents.py",
          "codex/runtime/aisoft_loop/cli.py",
          "codex/tools/aisoft",
          "codex/runtime/tests/test_route_policy.py",
          "codex/runtime/tests/test_contract.py",
          "codex/runtime/tests/test_documents.py",
          "codex/runtime/tests/test_ticket_execution.py",
          "codex/runtime/tests/test_review_candidate.py",
          "codex/runtime/tests/test_session_contract.py",
          "codex/tests/smoke.sh",
          "codex/tests/test-usage-bundle.sh",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, implement, issue-session-flow",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "raw_plan_sha256": "67c75f364d84a56506a51b56fe1e67b3d6c60ecc0c301f12f812a21388132cd6",
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "origin": "manual-pre-helper: BASE/state contemporaneously recorded above; structured contract metadata reconstructed after T03, not a claim of earlier helper execution"
      },
      "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934",
      "validation_sha256": "bf5840bdb056d28c6092a76327e7de401648a3e46fc55a570c9b80fd1283f632",
      "ac": {
        "AC-1": "PASS",
        "AC-6": "PASS",
        "AC-7": "PASS"
      },
      "checks": [
        {
          "command": "PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_route_policy tests.test_contract tests.test_documents",
          "result": "PASS",
          "evidence": "T02 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        }
      ]
    },
    "T03": {
      "base": "b5414a9236aebec65e8e8cbb51996da626eaeda4",
      "head": "56e5503fa23fd9f78a780380ca8ecada5b865582",
      "start": {
        "identity": {
          "issue": 427,
          "branch": "change/427-workflow-route-review",
          "owner": "01a16423-3e17-73b0-a723-76adc045218e",
          "worktree": "/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review",
          "provider": "codex",
          "plan_path": "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934"
        },
        "ticket": "T03",
        "ticket_base": "b5414a9236aebec65e8e8cbb51996da626eaeda4",
        "scope": [
          "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
          "skills/aisoft-platform/references/route-policy.md",
          "skills/aisoft-platform/references/execution-adapter.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/aisoft-matt-workflow/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "04-Agent编排与定时任务.md",
          "08-双工具共存与实施.md",
          "templates/docs/agents/issue-tracker.md",
          "docs/agents/issue-tracker.md",
          "templates/docs/changes/_template/summary.md",
          "templates/docs/changes/_template/plan.md",
          "codex/config/change-template-sync.json",
          "codex/config/external-skill-adaptation.json",
          "codex/runtime/aisoft_loop/route_policy.py",
          "codex/runtime/aisoft_loop/ticket_execution.py",
          "codex/runtime/aisoft_loop/review_candidate.py",
          "codex/runtime/aisoft_loop/contract.py",
          "codex/runtime/aisoft_loop/documents.py",
          "codex/runtime/aisoft_loop/cli.py",
          "codex/tools/aisoft",
          "codex/runtime/tests/test_route_policy.py",
          "codex/runtime/tests/test_contract.py",
          "codex/runtime/tests/test_documents.py",
          "codex/runtime/tests/test_ticket_execution.py",
          "codex/runtime/tests/test_review_candidate.py",
          "codex/runtime/tests/test_session_contract.py",
          "codex/tests/smoke.sh",
          "codex/tests/test-usage-bundle.sh",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, implement, issue-session-flow",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "raw_plan_sha256": "67c75f364d84a56506a51b56fe1e67b3d6c60ecc0c301f12f812a21388132cd6",
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "origin": "manual-pre-helper: BASE/state contemporaneously recorded above; structured contract metadata reconstructed after T03, not a claim of earlier helper execution"
      },
      "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934",
      "validation_sha256": "ee9e4bd128d602f28e617e2c35f64d3e698de9a3e57b81358aa79aa30950c495",
      "ac": {
        "AC-2": "PASS",
        "AC-3": "PASS",
        "AC-6": "PASS"
      },
      "checks": [
        {
          "command": "PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_ticket_execution tests.test_documents",
          "result": "PASS",
          "evidence": "T03 actual checks and fixed/residual/new ledger above; AC PASS here is this ticket slice, not whole-Issue acceptance"
        }
      ]
    },
    "T04": {
      "dirty_dispositions": {
        "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md": "本writer将T03补证及T04开始事实随本票提交；起始已记录，无用户成果。",
        "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md": "仅推进T03 Status=done；本writer必要执行状态，随本票提交。"
      },
      "base": "56e5503fa23fd9f78a780380ca8ecada5b865582",
      "head": "ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5",
      "start": {
        "identity": {
          "issue": 427,
          "branch": "change/427-workflow-route-review",
          "owner": "01a16423-3e17-73b0-a723-76adc045218e",
          "worktree": "/Users/benque/MyDocs/AISoftPlatform/worktrees/issue-427-workflow-route-review",
          "provider": "codex",
          "plan_path": "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934"
        },
        "ticket": "T04",
        "ticket_base": "56e5503fa23fd9f78a780380ca8ecada5b865582",
        "raw_plan_sha256": "b86ceb77a1e1fc502258a3225a206c21dbb806dfdec61722c06ece982db1847f",
        "scope": [
          "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
          "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
          "skills/aisoft-platform/references/route-policy.md",
          "skills/aisoft-platform/references/execution-adapter.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/aisoft-matt-workflow/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "04-Agent编排与定时任务.md",
          "08-双工具共存与实施.md",
          "templates/docs/agents/issue-tracker.md",
          "docs/agents/issue-tracker.md",
          "templates/docs/changes/_template/summary.md",
          "templates/docs/changes/_template/plan.md",
          "codex/config/change-template-sync.json",
          "codex/config/external-skill-adaptation.json",
          "codex/runtime/aisoft_loop/route_policy.py",
          "codex/runtime/aisoft_loop/ticket_execution.py",
          "codex/runtime/aisoft_loop/review_candidate.py",
          "codex/runtime/aisoft_loop/contract.py",
          "codex/runtime/aisoft_loop/documents.py",
          "codex/runtime/aisoft_loop/cli.py",
          "codex/tools/aisoft",
          "codex/runtime/tests/test_route_policy.py",
          "codex/runtime/tests/test_contract.py",
          "codex/runtime/tests/test_documents.py",
          "codex/runtime/tests/test_ticket_execution.py",
          "codex/runtime/tests/test_review_candidate.py",
          "codex/runtime/tests/test_session_contract.py",
          "codex/tests/smoke.sh",
          "codex/tests/test-usage-bundle.sh",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {
            "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md": "b86ceb77a1e1fc502258a3225a206c21dbb806dfdec61722c06ece982db1847f",
            "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md": "f32e5b5e2d293a288994b46bb60195fed77b5ad4837cd4215a813a7f03dc3605"
          },
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/427/issue-427-558cfcdc81c21745-19e3f170c9828c91.md",
        "scratch": ".superpowers/sdd/issue-427-558cfcdc81c21745-19e3f170c9828c91",
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, implement, issue-session-flow",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "model_configuration": "not observed by helper; caller records actual model/effort in verification"
      },
      "semantic_hash": "19e3f170c9828c917bd0084f74fff81847c3ea3ec2b4bbe4d56e478ba7f7c934",
      "validation_sha256": "7e8345e4b45beda5367d549870fcb8f7394da7780427e2ecf2b76f84a28c2b10",
      "ac": {
        "AC-4": "PASS",
        "AC-5": "PASS",
        "AC-6": "PASS"
      },
      "checks": [
        {
          "command": "PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_review_candidate tests.test_ticket_execution tests.test_session_contract",
          "result": "PASS",
          "evidence": "41 required tests PASS; same candidate Standards/Spec PASS; actual wrapper/broker candidate package digest b6c8e831abc426aa06039fd073439ec6fc1cb862f75057bc94499bb56e0f665f"
        }
      ]
    },
    "T05": {
      "dirty_dispositions": {
        "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md": "本writer将T04闭合与T05开始证据随最终候选提交，无用户成果。",
        "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md": "仅推进T04 Status=done；本writer本Issue执行记录。"
      }
    }
  },
  "scope_amendments": [
    {
      "from_scope": [
        "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
        "skills/aisoft-platform/references/route-policy.md",
        "skills/aisoft-platform/references/execution-adapter.md",
        "skills/aisoft-platform/SKILL.md",
        "skills/aisoft-matt-workflow/SKILL.md",
        "skills/issue-session-flow/SKILL.md",
        "03-Issue-Spec-Plan与单闸门开发流程.md",
        "04-Agent编排与定时任务.md",
        "08-双工具共存与实施.md",
        "templates/docs/agents/issue-tracker.md",
        "docs/agents/issue-tracker.md",
        "templates/docs/changes/_template/summary.md",
        "templates/docs/changes/_template/plan.md",
        "codex/config/change-template-sync.json",
        "codex/config/external-skill-adaptation.json",
        "codex/runtime/aisoft_loop/route_policy.py",
        "codex/runtime/aisoft_loop/ticket_execution.py",
        "codex/runtime/aisoft_loop/review_candidate.py",
        "codex/runtime/aisoft_loop/contract.py",
        "codex/runtime/aisoft_loop/documents.py",
        "codex/runtime/aisoft_loop/cli.py",
        "codex/tools/aisoft",
        "codex/runtime/tests/test_route_policy.py",
        "codex/runtime/tests/test_contract.py",
        "codex/runtime/tests/test_documents.py",
        "codex/runtime/tests/test_ticket_execution.py",
        "codex/runtime/tests/test_review_candidate.py",
        "codex/runtime/tests/test_session_contract.py",
        "codex/tests/smoke.sh",
        "codex/tests/test-usage-bundle.sh",
        "usage/bundle.json",
        "docs/governance/review-evidence-index.md"
      ],
      "to_scope": [
        "docs/changes/427-workflow-route-review/summary-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/spec-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/plan-workflow-route-review-261023.md",
        "docs/changes/427-workflow-route-review/verification-workflow-route-review-261023.md",
        "skills/aisoft-platform/references/route-policy.md",
        "skills/aisoft-platform/references/execution-adapter.md",
        "skills/aisoft-platform/SKILL.md",
        "skills/aisoft-matt-workflow/SKILL.md",
        "skills/issue-session-flow/SKILL.md",
        "03-Issue-Spec-Plan与单闸门开发流程.md",
        "04-Agent编排与定时任务.md",
        "08-双工具共存与实施.md",
        "templates/docs/agents/issue-tracker.md",
        "docs/agents/issue-tracker.md",
        "templates/docs/changes/_template/summary.md",
        "templates/docs/changes/_template/plan.md",
        "codex/config/change-template-sync.json",
        "codex/config/external-skill-adaptation.json",
        "codex/runtime/aisoft_loop/route_policy.py",
        "codex/runtime/aisoft_loop/ticket_execution.py",
        "codex/runtime/aisoft_loop/review_candidate.py",
        "codex/runtime/aisoft_loop/contract.py",
        "codex/runtime/aisoft_loop/documents.py",
        "codex/runtime/aisoft_loop/cli.py",
        "codex/tools/aisoft",
        "codex/runtime/tests/test_route_policy.py",
        "codex/runtime/tests/test_contract.py",
        "codex/runtime/tests/test_documents.py",
        "codex/runtime/tests/test_ticket_execution.py",
        "codex/runtime/tests/test_review_candidate.py",
        "codex/runtime/tests/test_session_contract.py",
        "codex/tests/smoke.sh",
        "codex/tests/test-usage-bundle.sh",
        "codex/tests/test-aisoft-entry.sh",
        "usage/bundle.json",
        "docs/governance/review-evidence-index.md"
      ],
      "authorization": "2026-10-23 本会话用户回答 call_240eb83c17174d81bea82acd9eea5fcf：允许这一项范围补正，继续完成 T05。仅 test-aisoft-entry.sh 一行 ROUTE_PROVIDER → claude；原启动批准和两个确认点不变。"
    }
  ]
}
```

### T04 开始

T04 在实现前实际运行 prepare-ticket，开始 BASE `56e5503fa23fd9f78a780380ca8ecada5b865582`；回执位于 `.superpowers/aisoft/427/T04.json`。起始仅 plan 状态和 verification 补证两项本 writer 文档改动，已保留在 initial_state；它们属于本票必要证据，后续仅随本 Issue 提交。无用户无关脏文件。来源/pin/范围/摘要/身份随回执；沿用原批准。

### T04 实施与验证

- RED：review_candidate 生产 seam 缺失。新增生产 CLI/helper 不执行 add/commit/stash/push，只读 Git/合同并输出 JSON 包。
- 必须使用开始回执的全 SHA BASE 与当前完整 HEAD；祖先/非空净 diff/线性 history；全部 commit 与独立 change_base 范围。原始三类工作树变化、范围外提交、相关遗漏与必要 ignored 处置按确定性条件拒绝；无关原脏文件保留。
- Standards/Spec 绑定共同 package digest/base/head；追加修复、移动HEAD或身份变化后旧声明失效。语义范围 NOT REVIEWED、未保存编辑器内容 UNKNOWN；不把机械 PASS 称审查通过。SP route axes=[]，small仍不进入票适配。
- `PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_review_candidate tests.test_ticket_execution tests.test_session_contract`：37 tests PASS；N5–N7 含真实 Git 故意失败；整个fixture只写临时目录。
- source/local evidence；最终 Claude、完整 smoke、bundle/installed/CI仍按T05和非目标分层。候选提交后对实际 #427 运行新检查器，再派双轴。

T04 首轮 4f88de42ba745502d523ea335df5023b632b5974 双轴 FAIL，三项 P1 已补 RED 并修复：
- T04-1：P1 项目路由 code-review 义务未进入 axes。现覆盖 Matt implement/code-review；实际默认入口另从同 policy provider 映射读取，不把 R2 必用集合当入口。普通 SP 无新增双轴，显式执行覆盖保留。
- T04-2：传入包改 axes/BASE 可保留旧摘要。现先重算 payload 摘要，再以 fresh 共同包作为审查字段事实源。
- T04-3：丢前票证据可截短 change_base。现重新核对已完成票的原开始证据，当前依赖状态倒退也拒绝；不能只循环幸存记录。
`review/ticket/session/route` 54 tests PASS，另执行入口区分正例 1 PASS；git diff --check PASS。修复线性追加，fixed 待新 HEAD 复核。

### T04 闭合 / T05 开始

T04 在 ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5 双轴 PASS，T04-1/2/3 fixed、无 residual/new。41 required tests PASS；真实 wrapper/broker/candidate 链 PASS。T05 在任何发布/适配修改前开始，当前 BASE 同该 HEAD；只有本 writer 的 plan Status/verification 补证，按本 Issue 必要执行记录承接。

### T05 分发与检查进展

- fresh fetch 后 origin/main 仍为 dc1da41c6e6a51f85b1ec0464a97640a3ddb570e，已发布最新 1.15.0；新增 1.16.0 minor source bundle，digest `9e62624a85c2df021e3b707e6ea53f6a028aeb29f1f34a1e9f061c73a6833dd0`，保留所有旧 release。新增 execution-adapter reference 与三个 runtime 模块的分发成员。
- 真实独立导出反例：Claude-only 项目缺少本来由官方插件提供的必用 skills，旧 known_skills 拒绝合法 route。已使用发布包锁定摘要的 policy 词汇补齐必用技能名称，额外技能仍需可见 SKILL 或源 manifest；不查询 HOME，不冒充安装/调用验证。
- 三个独立单端项目：route CLI 与 prepare-ticket API（隔离 Issue fixture）PASS；三端 shared reference 字节一致；已篡改导出 policy 的摘要反例拒绝。完整源码固定 SP task-start→task-brief 已在 T03 真实临时 Git/HOME 验证。
- 必需本地检查包括 65 route/contract/doc tests PASS，bash -n/ShellCheck 通过。完整 smoke 第一次停在既有 sandbox-exec 嵌套沙箱限制（sandbox_apply Operation not permitted），保留失败日志；原样同命令在受控环境重跑，结果待回读。
- 本票不改变 vendor/pin、broker、AGENTS/CLAUDE、既有 CI context，不安装/采用/部署。真实 provider session、Cursor现场、CI、live 仍为 NOT RUN。

### T05 当前阻塞：精确 git_scope 漏列旧入口 fixture

- 受控环境原样完整 smoke 已排除嵌套沙箱限制；实际随后失败：`change 7-demo-change: route_provider requires a concrete provider and route card`。根因是 codex/tests/test-aisoft-entry.sh 的模板实例化漏替换新 ROUTE_PROVIDER；不是生产 validator 应放松的条件。
- 最小修复是在 make_project 的 sed 增加 `-e 's/ROUTE_PROVIDER/claude/'`，与其已有 SP verification-before-completion 路由一致。该文件不在本 spec.git_scope 35 项内，因此实际工作树保持未改，未扩大合同。已通过异步问题请求仅补正这一项，原启动批准/两个普通确认点保持。
- 隔离源码副本应用该一行补丁后，整项 test-aisoft-entry PASS（含原生 sandbox-exec 拒绝读取平台仓的检查）；这是 proposed fixture 证据，不能冒充实际工作树完整 smoke PASS。补丁在本会话附件 427-fixture-scope-correction.patch。
- 完整 runtime unittest discover：742 tests PASS（110.204s）。bundle --verify --baseline-ref dc1da41c6e6a51f85b1ec0464a97640a3ddb570e：VERIFIED 1.16.0。完整 smoke 仍 FAIL；其余未走到的 shell/static 项不能被这两项替代。
- T05 当前未提交；HEAD 仍 ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5。Claude Code Fable 5/high 最终实际 HEAD 审查仍 NOT RUN；不生成假 PASS 或提前请求 PR 确认。没有 push/PR/merge/安装/部署。

### T05 已批准的唯一范围补正

2026-10-23 用户明确回复“允许这一项范围补正，继续完成 T05”。spec.git_scope 从35条增加为36条，新增的 test-aisoft-entry.sh 仅改变一行 provider fixture；未新增普通确认点。历史开始回执不改写，T05原始BASE仍ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5。结构化证据 scope_amendments 同时保存精确旧/新范围与授权来源；helper只接受有此记录的严格增补，未记录漂移/缩减仍拒绝，不把文字记录称为自动批准证明。原回执与缓存逐字保留；相关恢复/历史完成/候选回归已补。

本地未发布的1.16.0候选因必要 runtime 修正重新生成；从main已发布的1.15.0及更早release保持字节语义不变。早先预览摘要只描述当时工作副本，最终有效摘要以下次真实verify为准。

### T05 补正后本地核实

- 实际 prepare-ticket 427 T05 --provider codex --resume：prepared，ticket_base 保持 ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5，原 receipt.scope 仍35条；当前 spec 36条由有界授权记录衔接。
- check-change-documents --porcelain：change-documents / change-pr-url PASS。classify --verify 427：projected，type/platform + complexity/complex，applied=false；该工具固定的 merged-summary 文案不证明本分支已合并。
- shell bash -n / ShellCheck 通过；git diff --check 通过。已发布 release 历史与基线完全相同，vendor diff 为空。
- 本地未发布 source bundle 1.16.0 重建摘要：9af59dcad1e39f5d1e474b08031ba80a65036f452ebffa5c4895d161b365ceb6。导出是源验证，不是installed/live。
- 进展评论尝试被宿主自动审批拒绝（其将目标视为未明确受信任、担心内部元数据外发）；未通过其他身份/API/通道绕过。用户授权范围已在本Issue文档保留。只读 broker 恢复/分类调用正常。

上述评论审批问题已解决：只读核对受治理 manifest 的本地 Gitea URL、aisoft-platform repo/checkout 映射与 origin 完全一致后，将同一 typed broker 操作重新送审，获准并成功写入。未更换通道或身份。授权增补的同票证据：<http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/427#issuecomment-15369>。

### T05 首轮完整 smoke 与区间修复

完整 smoke 原样受控运行 exit 0，含744项 runtime测试（124.131s）、三端导出、真实入口沙箱隔离、安装器临时fixture及全部静态门，日志 /private/tmp/aisoft-427-smoke-final.log。随后最终核对发现 AC-5–AC-8 区间只取端点；新增故意失败fixture并修复为有界区间展开，倒序与超大范围拒绝。T05实际AC现完整包含AC-5/6/7/8，canonical plan语义摘要未改变；历史T01–T04均为枚举不受影响。修复后44项 ticket/review/session 测试PASS。未知技能负例改为在policy篡改前检查明确unknown错误，单项bundle suite及bash-n/ShellCheck PASS。

区间修复后的未发布1.16.0最终源候选摘要为 9dd1b42bae18cae0dea3231ff27764c8d7e1cc754d0f401d0e256c1f7a9cbfc0；旧release未改。对这版完整smoke正在重新执行，候选固定后继续双轴与Claude实际终审。之前744项结果不冒充最终745项结果。

## 交叉审查

### R1：Claude Code Fable 5 / high（实际调用）

- 整批 BASE dc1da41c6e6a51f85b1ec0464a97640a3ddb570e → HEAD 0c879cec3c53b77cfd2f75ff14996ad284575e02。session `6e3a7fe3-3c42-438a-8a2e-6d2326541a9a`；init.model 与 result.modelUsage 均为 claude-fable-5；命令指定 --effort high。safe-mode / Read,Glob,Grep / dontAsk / 禁hooks/MCP；对固定Git blob导出快照只读。未参与实现，不运行测试。
- 实际 verdict FAIL：F1(P1) 被审HEAD的最终smoke/T05补证未闭合；F2(P2) 索引新增行前空行断表；F3(P2) 反引号/波浪线混合围栏转换可能泄漏示例内容。完整报告与stream在本会话附件 review-427-0c879cec3c53/。
- 双轴：同票 BASE ac689e5210a12709b1e59bc6ccafe7d9f9b0b9b5 → 同HEAD，package 49950f55d4b9564caca6e56cae408f68bdb3263908dc36c2ee6ee8d93da9a4f8，Standards/Spec均PASS，已用 validate_reviews + fresh broker读回校验。不是本次Claude终审的替代。

### R1 finding 处理

| ID | 处理 | 当前状态 |
|---|---|---|
| F1 | 接受最终证据必须入候选。0c879 源码实际完整smoke已在审查期间完成：745 runtime + 46 installed-drift fixture + 全静态门PASS，日志sha256 8ea8758f1501bf82185ca29596f37f8cf81871a9afc142661f6461cafba35c8c。本票未提前宣告完成/进入确认点2。F3修复后再跑完整smoke并记录新结果，待下一固定HEAD复核。 | 待最终补证 |
| F2 | 仅删除 #427 行前本票新增空行，保留其他行。 | 已修，待新HEAD复核 |
| F3 | RED证实混合围栏可静默转换；派生前识别原围栏状态，任何内部非合法结束分隔符均按既有 unsupported 路径拒绝。覆盖两种混合方向和短于外层的分隔符；普通tilde/backtick围栏保持可用。45项 ticket/review/session PASS，额外普通围栏正例PASS。 | 已修，待新HEAD复核 |

该修复不改治理文本/计划语义/vendor，不新增确认点。尚未发布的1.16.0源候选在本地线性追加提交中重建，未重写Git历史；已发布1.15.0及更早release不变。本次新摘要22476c52a747e7de9150bb7f5ac0b599bb77c053b5b7e7da657714211a586749。F3后完整smoke正在进行；T05保留pending直到实际另一provider复核通过。最终审查回执自身不嵌入被审HEAD，避免SHA自引用；先记录已有结果，最后证据提交做限定复核并在同Issue归档实际HEAD。
