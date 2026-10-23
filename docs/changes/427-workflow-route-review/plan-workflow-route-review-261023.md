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
---

# Plan：F1/F6 与必要流程适配

用户已确认本合同并启动 T01。下列新增接口仍是计划，不表示 runtime 已存在。
T01 只落实治理合同；提交后停止，T02–T05 交由 fresh run 继续原批准。同一 claimed worktree、同一 writer 顺序执行；
只读子代理可调查/审查，不写本分支。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 三端可见的路由/执行/候选治理合同，独立 commit 后 STOP | - | done |
| T02 | F1 显式 provider 路由解析、合同校验与历史兼容的可运行切片 | T01 | done |
| T03 | F2 Txx→Task N 无损执行、frontier、开始前 BASE 与恢复切片 | T02 | pending |
| T04 | F6 固定候选、遗漏检测与双轴/整批范围证据切片 | T03 | pending |
| T05 | 发布一致性、全量验证、最终独立审查与唯一 PR 候选 | T04 | pending |

## T01：治理合同受控应用

- **blocked_by**：无；前提是本 Issue 已经通过原确认点 1、summary.status=approved。
- **交付/范围**：把 spec D1–D4 写进唯一 route-policy 与共同 execution-adapter reference；入口只引用共享规则，Matt/Claude/Cursor 都能读到。明确 review 与 commit 顺序、SP 的 completion/裁决/清理条款受平台约束、两确认点不变。
- **AC**：AC-1、AC-6、AC-7；此票是治理切片，不宣称新 runtime 可用。
- **新接口合同**：`aisoft resolve-route N --provider codex|claude|cursor` 输出具体 route、provider、命中规则/摘要，读取映射 summary/仓库 change_control；`aisoft prepare-ticket N Txx --provider ... [--resume]` 生成/恢复绑定身份的派生视图与开始回执；`aisoft review-candidate N Txx --head <40位SHA>` 校验并输出固定范围包。统一使用现 `--repo` 入口/项目解析方式，不新增任意远端/凭据参数。完成/审查结论仍写已有文档，helper 不自行标 done。
- **模板**：summary 新增 route_provider；plan 新增可执行 Txx 正文结构（scope、blocked_by、AC、验证/Expected、约束），Txx 仍唯一身份；刷新 canonical digest，tracker 源与已有 mirror 同步。平台不持有 change 模板副本，不新增 docs/changes/_template。不给历史文档强制新格式。
- **验证**：`git diff --check`；`codex/tools/aisoft check-change-documents --porcelain`；对照批准 spec 逐条检查默认、两个确认点、STOP/fresh run、无 vendor/pin 修改；tracker mirror `cmp` 与 change-template `--verify-digest`。治理文本的新行为 fixture 将在 fresh run T02–T04 实现，不用旧测试绿色掩盖待适配项。
- **Expected**：治理 diff 完全在 spec.git_scope；只有有意识的新合同差异；无 runtime 功能实现；模板摘要正确；未引入第三确认点。
- **停止条件**：本票原子本地 commit 后 STOP。记录 exact HEAD 与应用文件。下一 fresh run 重读当前 AGENTS/技能、approved 合同、T01 diff、owner/branch/HEAD 后继续；原批准延续，不再请求启动。
- **返修**：若后续必须改已生效治理，回到独立受控应用步骤并再次 STOP/fresh run；不靠修测试顺带改控制自己的规则。

## T02：F1 可执行路由

- **blocked_by**：T01 完成且 fresh-run 重读已留证。
- **交付/范围**：薄 parser 从唯一 route-policy 取行/修饰/映射，供 resolve-route 与新合同校验使用；保留分类引擎与风险优先级。具体 skills 可被 validator 验证，不把抽象能力写入 skills。
- **AC**：AC-1；配合 AC-6/AC-7。
- **实现顺序**：先以真实缺口建立 RED（Codex R3/R4 冲突、R2/R5 核验、未知 provider 等），再接生产 resolver/CLI/校验；测试调用生产代码，不另抄表。新卡必需 provider；历史无 provider 卡只读兼容，执行时显式解析。
- **验证**：`PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_route_policy tests.test_contract tests.test_documents`；隔离 fixture 执行新增 resolve-route 命令，覆盖 R1–R5/三 provider/两仓库角色/change_control、M1/V1/S1/P1/G1；history compatibility。
- **Expected**：N1/N2 各故意失败命中；当前默认完全保留；未知/冲突返回非零和可解释原因；新 route 输出可由文档校验消费；不改历史文档或 labels。
- **约束/停止**：不解决 risk policy 的争议、不改 classification.py、不改 broker；若现表无法唯一解释，报告具体差异，不能偷偷选另一风险策略。

## T03：F2 单票执行与恢复

- **blocked_by**：T02。
- **交付/范围**：从映射 plan 提取准确 Txx 正文、依赖/AC/Expected/约束，生成原版 SP 可识别 Task N；前置核对 frontier、owner/branch，记录开始前 ticket_base、原始 plan 审计摘要与任务语义摘要。development complex 用 Issue AC + synthetic T01。平台缓存与上游 sdd scratch 分开，按 spec D2 绑定身份、隔离路径并保护别会话内容。
- **AC**：AC-2、AC-3、AC-6。
- **实现顺序**：真实临时 Git 仓中的两票依赖图，先测缺口；实现窄解析/缓存/恢复；实际调用固定 v7.0.0 的 task-start→task-brief，证据包显示上游 Task N 与原 Txx 对应。不编辑 vendor、canonical plan 不改成另一人工格式。
- **验证**：`PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_ticket_execution tests.test_documents`；tests 内子进程调用固定上游脚本，限制在临时 repo/HOME，不依赖真实用户安装。
- **Expected**：N3/N4 负例均失败；AC/Expected/停止条件逐项可读；未完成依赖不能启动；BASE 在实现前而非提交后抓取；wrong Issue/branch/owner/plan semantic hash/祖先/无测试凭据不能恢复完成；配对正例中正常 Status 推进或指定证据区补证可恢复，正文/AC/依赖变更仍拒绝；必要测试 FAIL/NOT RUN 不能 done；原无关脏文件保持；sdd scratch 不覆盖其他会话，路径逃逸被拒绝。
- **约束/停止**：本地缓存是可再生执行状态，不是第二套审批或审查数据库；只有唯一写者改本票源码/提交。接口可接受 test command 字符串但 helper 不擅自执行未经当前合同授权的任意命令；测试执行仍由会话负责。

## T04：F6 候选范围与审查闭环

- **blocked_by**：T03，复用其 ticket_base、身份、起始状态与缓存协议。
- **交付/范围**：本票实现/测试并由 writer 提交后，review-candidate 固定 HEAD，验证祖先、非空净 diff、全部 commit、相关 staged/unstaged/untracked 与已声明 necessary ignored 成果的处置，输出双轴共同范围包。语义归属由合同/diff审查确定，机械检查不自称全知。
- **AC**：AC-4、AC-5、AC-6。
- **实现顺序**：真实 Git fixture 先制造“有前票 commit、本票未提交”等反例，再实现校验；两轴必须绑定同候选；修复后追加提交与新 HEAD 的证据链、整批 change_base 范围可检查。candidate package 只读 Git，不帮用户 add/stash/delete。
- **验证**：`PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_review_candidate tests.test_ticket_execution tests.test_session_contract`；每个 N5/N6/N7 至少一项真实 Git 故意失败。
- **Expected**：任何相关遗漏不报告完整；两 commit 票首笔在范围内；非空历史/空净 diff 拒绝；候选 HEAD/branch/owner 改变、修复新 HEAD 不复用旧 PASS；两票最终范围覆盖第一票；无关用户文件原样保留；small/SP 无新增 Matt 每票审查。
- **约束/停止**：记录 review findings fixed/residual/new，修复按原合同收敛；不添加通用审批或完成状态、不替代平台最终另一 provider 审查。

## T05：发布、验证与最终候选

- **blocked_by**：T04。
- **交付/范围**：按真实改动更新 source bundle 与兼容说明、适配 Issue 来源；保留所有旧 release 与 vendor。新 shared reference 登记为分发成员，runtime/helpers 按当前分发路径验明，不能假定技能目录新增脚本在 Claude 可用。
- **AC**：AC-5–AC-8，闭合所有 AC。
- **验证**：
  - `git diff --check`、文档解析/check、classification --verify、scope/history 与 owner/branch 核对。
  - `AISOFT_USAGE_BASELINE_REF=dc1da41c6e6a51f85b1ec0464a97640a3ddb570e LC_ALL=C bash codex/tests/smoke.sh`。按实际集成基线如实更新并记录，不伪称旧 base 是最新。
  - 使用现 usage-bundle 的 verify/build 检查与隔离三端导出；修改 shell 则对应 `bash -n` 与 ShellCheck。既有 smoke 已覆盖的成功项不无故重复。
  - vendor manifest/pin 不变、N8 无写越界；adapter/ref/template 三端实际导出路径与字节核对。
  - 未参与实现的 Claude Code（用户要求 Fable 5 / high）对最终实际 HEAD、整批 BASE、spec/plan/证据只读复核；结果/调用配置如实留证，修复后按现合同复审新 HEAD。代码评议不同于研究方案 SUPPORT。
- **Expected**：所有 required local checks 与最终 cross-provider 审查真实 PASS；失败/NOT RUN 必需项不宣称通过。模型实调用不可得时如实阻塞，不擅自降低。
- **证据层**：本阶段验收 source/local 与隔离固定源码调用。真实已安装 provider session、Cursor现场、项目采用、部署/UAT不在第一阶段，写 NOT RUN；不因这个非目标向用户另索安装确认。PR 后 required CI 留待确认点 2 后 fresh readback，PR 前本地通过不冒充 CI。
- **停止条件**：只形成 AWAITING_PR_CONFIRMATION 候选；确认点 2 后 broker 普通 fast-forward push、唯一最终 PR、required CI；READY_FOR_REVIEW 由人合并，现确定性流程收尾。未获 PR 确认本票不 push/开 PR。

## Expected touch points

精确最大集合见 spec.git_scope；未需要的文件不改。下面按交付分配，不能据此扩 scope：

- T01：三个共同技能入口、route-policy、新 execution-adapter reference、03/04/08 的必要一致性说明、tracker template+mirror、canonical summary/plan template、change-template digest、适配 provenance。平台自身不持有 change 模板 mirror，初版两条无效 scope 已收窄。
- T02：aisoft_loop/route_policy.py、contract.py、cli.py、aisoft wrapper、route/contract/doc tests；本 Issue summary 补新 provider 元数据。
- T03：ticket_execution.py、documents.py/cli.py/wrapper 必要接口、ticket/doc tests；仅本 Issue 的执行记录。
- T04：review_candidate.py 与复用 ticket 接口、review/ticket/session tests。
- T05：smoke、usage bundle/相关测试、现 review-evidence-index 只追加本 Issue、四份本票文档。release 记录是源交付，不授权安装。
- spec/verification 公共模板、AGENTS.md、分类器、broker、vendor、其他 Issue 文档不在可写范围。

## 测试与验收映射

| Acceptance criterion | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T01/T02 | route/contract/doc 单测 + resolver CLI fixture，N1/N2 |
| AC-2 | T03 | 原版 task-start/task-brief 调用 fixture，N3 |
| AC-3 | T03 | 真实 Git frontier/start/resume fixture，N4 |
| AC-4 | T04 | candidate 实际 Git 范围/遗漏 fixture，N5/N6 |
| AC-5 | T04/T05 | 双轴范围一致性/新 HEAD/整批范围 fixture + 平台终审，N7 |
| AC-6 | T01/T03/T04/T05 | session 合同守卫 + 本票真实执行/裁决证据审查 |
| AC-7 | T01/T05 | 治理 STOP/fresh-run 记录、mirror/digest、bundle 三端导出与 vendor 不变，N8 |
| AC-8 | T05 | 全量 smoke、文档/scope、cross-provider exact-head 与真实证据分层 |

## 数据库迁移

无。

## 部署与回滚

无部署、安装或业务项目采用。源版本 rollback 采用受控 revert/后继修正版 bundle，保留旧 release 和业务提交，不 reset 数据或重写历史。回滚不在未发生变更时模拟实际部署成功。

## 计划状态与交接

确认点 1 已通过，summary=approved。T01 提交后按治理边界 STOP；fresh run 重读后继续 T02，
沿用本次启动批准，不再次请求确认。后续 runtime、完整 smoke、发布与最终审查仍未完成。
当前 triage 语义结论已记录；typed broker 缺少 triage 标签 mutation 的既有缺口不通过新 API/身份绕过，也不扩成本票 broker 开发范围。确认点数量不受它影响。

T01 的 done 随本治理提交生效，仅表示本票治理交付及规定的本地检查完成；不代表新 helper、
provider 语义校验、三端发布或 #427 整体通过。开始基线、两位只读预检、实际检查与 fresh-run 交接见 verification。
