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

# Verification：合同准备证据

本文件仅记录实际观察。实施计划和预期结果不是已通过的验收。

## 当前证据

| 检查 | 结果 | 证据与限制 |
|---|---|---|
| main 基线 | PASS | 2026-10-24 经 broker fresh-fetch，`origin/main=08aac8d5b9af4d334c53bcf34029870f09e50bf0`；本票从该点建分支 |
| 开放 Issue 查重 | PASS | 创建前开放项为 #429 与 #417；均非本需求，未修改 |
| Issue 创建 | PASS | broker 返回 open Issue #430，入口标签 needs-analysis；后续标签以最后读回为准 |
| exact worktree/claim | PASS | `change/430-greenfield-planning`，`/private/tmp/issue-430-greenfield-planning`，owner session `01a16e1b-1085-7712-b5a8-c100d9f74629`；尚无 push |
| 现行合同核对 | PASS | 已读 README、ADR 0001/0002、03/04/08、route-policy、issue-session-flow、aisoft-matt-workflow、getting-started 与 usage 合同/分发实现；这是设计依据，不是新方法运行证据 |
| 受限 publisher | PASS | 使用现有 `publish_spec`/`publish_plan`，输入 broker fresh-read 的 open Issue #430，在 exact branch 首次生成两个映射目标；未跳过路径、日期或 Ticket graph 检查 |
| 文档检查与角色解析 | PASS | `aisoft check-change-documents --porcelain`：change-documents/change-pr-url 均 PASS；`resolve-documents 430` 返回本票四个语义角色映射 |
| 路由解析 | PASS | `aisoft resolve-route 430 --provider codex`：R3 + G1，differences={}；policy SHA256 `184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40` |
| 草稿结构检查（修订前） | PASS（已过时） | 修订前一次性本地校验：15 个唯一 scope 路径、11 个 AC 均映射、3 个 pending Txx、10 个场景；非 summary 无 status/pr_url。该校验未运行平台 parse_plan，修订后由下方「plan 可执行性」行取代 |
| 判级与生命周期读回 | PASS | `classify --apply 430` 后另行 `classify --verify 430`；broker fresh-read 返回 open，且恰有 type/platform、complexity/complex、spec-drafting 三标签，没有 approved |
| Issue 完整正文读回 | PASS | 已通过 broker 回填完整 summary/spec/plan、精确路径/摘要与 Claude 委托，再 fresh-read 逐字相等；初次完整发布 36280 bytes，SHA256 `a6e5355b52e28569df89c1e070b972a83c34047262b3870be97273a0c87d546e`，标签仍为 spec-drafting；此摘要仅指该次发布，不冒充随后提交信息回填后的正文摘要 |
| 新方法实现 / T01–T03 | NOT RUN | 修订已提交、Issue 同步读回且已 approved；尚未 prepare-ticket，当前全部 pending |
| 完整 smoke / 隔离发布包 / 场景核验 | NOT RUN | 属于实施后的验收，本轮不把基线测试冒充新功能验证 |
| Claude 内部材料评估 | PASS | 2026-10-24 初评；2026-10-25 反证复核（7 个只读核对：4 组逐条反驳、3 个补查视角）与修订稿复核（4 个只读核对：覆盖、一致性、精简度、可执行性），结论发在负责人的项目线程；评估本身只读。复核发现原 plan 不能被平台 parse_plan 解析（缺 T02「验证」字段），另有写入路径、恢复锚点、技能边界等问题 |
| 合同修订 | 已起草，未提交 | 负责人 2026-10-25 在项目线程要求按 Claude 意见直接修订（项目消息 02:24 与 02:26 UTC），并说明最终确认后交 Codex 侧实施。Claude 会话 `63a7ad7e-1b6f-4272-b7a6-a3b5baa39523` 按此在本 worktree 起草修订，只改本票四份文档，未提交、未改 owner marker、未 push、未改 Issue、未设 approved。这是负责人授权的单写者例外，限于起草；修订交回 owner 会话 `01a16e1b-1085-7712-b5a8-c100d9f74629` 审阅 3800ec2d 之上的未提交 diff 后提交。主要修订：plan 票型改为可解析（T02 补「验证」字段、命令逐条行内、每票逐条列 AC、AC-11 拆出 AC-12、T02 承接 AC-3/5/7/11 的场景与 fresh run 证据、执行证据加成对标记、T01 commit 前跑完整 smoke、版本在 prepare-ticket 前定、T03 补 classify 与固定 FRESH_MAIN 的 bundle verify）；场景改为 S1–S11（新增 S11，改写 S1、S5、S6、S8、S9）；spec 补规划资料写入路径（实现 Issue 不改规划资料）、AGENTS「项目规则」恢复锚点及其治理步骤、技能边界（只用 §5 表列技能）、wayfinder 位置、访谈深度收口、接入前边界、决定落点、子 Issue 路由以 resolve-route 为准、调整以评论记到受影响 Issue、smoke 守卫清单、未决问题节；去掉里程碑层；git_scope 由 15 收窄为 13（去掉 04 与 aisoft-matt-workflow） |
| plan 可执行性 | PASS | 修订后以 worktree 内 `codex/runtime` 的 parse_plan 只读解析本 plan：T01 AC-3/5/7/11，T02 AC-1 至 AC-11（逐条列出），T03 AC-12；依赖 T01→T02→T03；必跑命令 6/6/5 条，均为完整命令行，无代码围栏碎片。修订前的 plan 在同一解析器上报 `ticket missing field: 验证|validation`。只证明计划可被现行 runtime 解析，不证明实施结果 |
| prepare-ticket 就绪模拟 | PASS（模拟） | 在 scratchpad 里新建本分支的一次性 clone，放入修订稿并只在该 clone 里把 summary 改为 approved、以模拟会话 id claim。CLI `aisoft prepare-ticket 430 T01 --provider codex` 经 broker 只读取真实 Issue 后拒绝：`open approved Issue required; triage is not startup approval`，符合当前 spec-drafting 状态。改用 runtime 的 prepare_ticket 并传入合成的 approved Issue：T01 返回 prepared，路由 skills 与 summary 一致；T02 按预期拒绝 `dependency is not complete: T01`。真实 Issue、本 worktree 与标签均未改动；真实启动仍需最终确认后的 approved |
| 修订后文档与路由 | PASS | 修订后 `git diff --check` 无输出；`aisoft check-change-documents --porcelain`：change-documents、change-pr-url 均 PASS；`aisoft resolve-route 430 --provider codex`：R3 + G1，differences={}，policy SHA256 `184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40` 不变 |
| 路由必用技能满足情况 | 已补跑，合同现已确认 | 路由 skills 含 grill-me、to-spec、to-tickets。to-spec 与 to-tickets 经平台 publisher 发布映射文档（见上方「受限 publisher」行）。2026-10-25 负责人明确选择补跑 grill-me 并沿用已有结论；owner 会话按平台 pin 的 grill-me → grilling 核对一次决策树，新增问题为 0，未伪造新的用户回答，详见下节。保留 route.skills，不申请豁免；批准来自后续明确确认，不来自技能记录 |
| 确认点 1 | 已明确确认 | 负责人于 2026-10-25 明确指示：“确认 #430 修订合同。提交修订、同步 Issue 并读回核对，设为 approved 后启动 T01；治理文件提交后停止，交 fresh run 继续。确认点 2 前不 push、不建 PR。”批准范围为本票 13 个文件、12 条 AC 与 T01–T03；当前执行到 T01 治理 commit 为止 |
| 修订提交与 Issue 正文同步 | PASS | 修订提交 `a847e70889e0abcd3cd565620e38e13372c2eec5`；broker 回填四份完整合同后 fresh-read 逐字一致，正文 56415 bytes，SHA256 `edc4b4a909c844be4fdeb582a86fe4ee3fb7ce93432f001c95e937fcce9222c0`。远端正文作为该次合同快照保留，后续执行证据不改写获批 spec/plan 语义 |
| approved 投影与读回 | PASS | 完整合同同步读回成功后，broker 设置 approved 并再次读取；真实标签恰为 approved、complexity/complex、type/platform，Issue open，正文未变；本地 summary 随后同步 approved |
| T01 发布基线 | PASS | broker fresh-fetch main 后固定 RELEASE_BASE=`2454b0c2519b0145aca4f1d289efb09ed8ac46d8`，main 与本分支最新发布包均 1.16.0；NEXT_MINOR=1.17.0，RELEASE_DATE=2026-10-25。main 新增 #429 的核对代码/测试、合同、索引，不涉及 T01 触点；未重写历史或导入无关修改 |
| 最终实现独立审查 / PR CI | NOT RUN | 没有实施提交或 PR |
| 全局安装 / 下游项目采用 / live / 部署 / UAT | NOT RUN | 不在本票实施范围 |

## grill-me 补跑记录

- **时间、请求与执行者**：2026-10-25，负责人明确要求“补跑 grill-me，已有结论直接沿用，只问 #430 修订后尚未明确的决策”；owner session `01a16e1b-1085-7712-b5a8-c100d9f74629` 执行。
- **技能来源**：平台 vendor Matt v1.3.1，commit `24fe0ef7737efae15c87225755e9f6f5965e4888`；先以现有 `verify_snapshot` 校验整个 snapshot 与 manifest 一致（PASS），再按 manifest 读取 `skills/productivity/grill-me/SKILL.md` 及其委托的 `skills/productivity/grilling/SKILL.md`。本 provider 没有名为 Skill 的调用工具，按已验证原文直接执行其决策树/轮次方法；没有声称调用不存在的工具，也没有改动 vendor。
- **输入**：负责人已确认的项目方向、Claude 修订的四份合同、owner 对 `3800ec2d` 上未提交 diff 的只读复核，以及当前现行路由/治理事实。
- **轮次**：第 1 轮核对全部与本票实施相关的决策分支；已有结论逐项沿用。本轮待提问 frontier 为空，新增问题 0、用户新回答 0。以下是沿用的合同候选，不将其写成已经获得实施批准。

| 决策分支 | 沿用结论与依据 | 本轮结果 |
|---|---|---|
| 目标与规划深度 | spec §1、§4.1–4.2：当前详细、下一轮廓、远期方向；访谈按深度收口 | 无新增待决项 |
| 启动入口与项目类型 | spec §2：登记与采用前只整理本地笔记；已有方案复用，已有代码转现行对齐；小项目可合并资料 | 无新增待决项 |
| 文档归属、写者与恢复 | spec §3：AGENTS 项目规则指向唯一规划入口；规划/收口 Issue 写规划资料，实现 Issue 不并行修改；术语、决定与业务规则各归原合同 | 无新增待决项 |
| 阶段转换与变更 | spec §4.3–4.4：负责人决定阶段转换；结果和进入证据作为依据；受影响的已批准 Issue 经评论通知其 owner 处理 | 无新增待决项 |
| 技能与交付衔接 | spec §5：保留 Matt、issue-session-flow 和现行路由；不接入新技能包；Issue 内技能按其路由选择 | 无新增待决项 |
| 本票交付与验收 | spec §6–8、plan：13 个允许文件、12 条 AC、T01–T03、S1–S11；治理 commit 后 STOP/fresh run，最终由 Claude 只读审查；不含真实项目采用或部署 | 无新增待决项 |

**收口状态**：本轮未发现需要继续追问的决策。负责人随后明确确认完整合同及上述共识，现依确认点 1 的授权固定修订并同步 Issue，保持现有两个确认点。

## 后续记录方式

按 plan 的 AC—任务—场景矩阵追加真实结果及证据位置。每条区分 source/local/isolated export/installed/live/UAT；失败和未运行保持原义。独立审查绑定实际 BASE、HEAD、文件范围、审查 provider 与 finding 处理结果。

本票仅准备合同，未发最终 PR，也未授予任何部署或安装权限。修订前的完整 spec/plan 已放入同一 Issue 正文；2026-10-25 的修订只在本地分支，Issue 正文待最终确认后回填（见「Issue 正文同步」行）。3800ec2d 提交后已回填 exact candidate commit 与文档摘要，并经 broker fresh-read 核对正文和标签；修订稿的 Issue 回填见「Issue 正文同步」行（完整 spec/plan 回填，fresh-read 后再写 approved）。最终回执保留在本次准备证据目录，交付报告引用实际结果。

本次准备证据目录：`/private/tmp/aisoft-greenfield-contract-261024-h029jbgw`。其中 broker 响应与一次性校验结果是本地辅助证据，不是需要下游安装的制品；Issue 正文和本票文件是评估所需的正式内容。

2026-10-25 启动与 T01 原始回执目录：`/private/tmp/aisoft-430-t01-261025-4qzk18d6`。已保存合同提交、正文同步及读回、approved 投影及读回、fresh-fetch 与版本依据。重要执行事实继续回填本票文档，临时目录不替代持久证据。
