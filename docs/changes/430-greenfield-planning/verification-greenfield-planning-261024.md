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

# Verification：合同与 T01 执行证据

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
| 新方法实现 / T01–T03 | T01 done；T02 验证通过、待固定候选审查；T03 pending | 治理 commit `2e54d7e0c85810cbcff2d5878d82c849e76b6144` 后前一轮已停止；本轮 fresh run 重读并核对，固定候选机械检查、Standards/Spec 两轴均 PASS；T01 完成证据已补齐；T02 六命令、S1–S11 与隔离导出通过，固定候选审查待提交后进行 |
| 完整 smoke / 隔离发布包 / 场景核验 | PASS（source/local） | 首次 BASE_STALE 失败保留；恢复后原样完整 smoke exit 0，383.62s，含 746 项 runtime 测试（110.909s）、project-leak 与最终静态门。T02 另行运行完整 smoke 并通过，隔离分发字节/链接与 S1–S11 均已核对，见 T02 结果 |
| Claude 内部材料评估 | PASS | 2026-10-24 初评；2026-10-25 反证复核（7 个只读核对：4 组逐条反驳、3 个补查视角）与修订稿复核（4 个只读核对：覆盖、一致性、精简度、可执行性），结论发在负责人的项目线程；评估本身只读。复核发现原 plan 不能被平台 parse_plan 解析（缺 T02「验证」字段），另有写入路径、恢复锚点、技能边界等问题 |
| 合同修订（交接历史） | 已由 owner 审阅并提交 | 负责人 2026-10-25 在项目线程要求按 Claude 意见直接修订（项目消息 02:24 与 02:26 UTC），并说明最终确认后交 Codex 侧实施。Claude 会话 `63a7ad7e-1b6f-4272-b7a6-a3b5baa39523` 按此在本 worktree 起草修订，只改本票四份文档，未提交、未改 owner marker、未 push、未改 Issue、未设 approved。这是负责人授权的单写者例外，限于起草；修订交回 owner 会话 `01a16e1b-1085-7712-b5a8-c100d9f74629` 审阅 3800ec2d 之上的未提交 diff 后提交。主要修订：plan 票型改为可解析（T02 补「验证」字段、命令逐条行内、每票逐条列 AC、AC-11 拆出 AC-12、T02 承接 AC-3/5/7/11 的场景与 fresh run 证据、执行证据加成对标记、T01 commit 前跑完整 smoke、版本在 prepare-ticket 前定、T03 补 classify 与固定 FRESH_MAIN 的 bundle verify）；场景改为 S1–S11（新增 S11，改写 S1、S5、S6、S8、S9）；spec 补规划资料写入路径（实现 Issue 不改规划资料）、AGENTS「项目规则」恢复锚点及其治理步骤、技能边界（只用 §5 表列技能）、wayfinder 位置、访谈深度收口、接入前边界、决定落点、子 Issue 路由以 resolve-route 为准、调整以评论记到受影响 Issue、smoke 守卫清单、未决问题节；去掉里程碑层；git_scope 由 15 收窄为 13（去掉 04 与 aisoft-matt-workflow） |
| plan 可执行性 | PASS | 修订后以 worktree 内 `codex/runtime` 的 parse_plan 只读解析本 plan：T01 AC-3/5/7/11，T02 AC-1 至 AC-11（逐条列出），T03 AC-12；依赖 T01→T02→T03；必跑命令 6/6/5 条，均为完整命令行，无代码围栏碎片。修订前的 plan 在同一解析器上报 `ticket missing field: 验证|validation`。只证明计划可被现行 runtime 解析，不证明实施结果 |
| prepare-ticket 就绪模拟 | PASS（模拟） | 在 scratchpad 里新建本分支的一次性 clone，放入修订稿并只在该 clone 里把 summary 改为 approved、以模拟会话 id claim。CLI `aisoft prepare-ticket 430 T01 --provider codex` 经 broker 只读取真实 Issue 后拒绝：`open approved Issue required; triage is not startup approval`，符合当前 spec-drafting 状态。改用 runtime 的 prepare_ticket 并传入合成的 approved Issue：T01 返回 prepared，路由 skills 与 summary 一致；T02 按预期拒绝 `dependency is not complete: T01`。真实 Issue、本 worktree 与标签均未改动；真实启动仍需最终确认后的 approved |
| 修订后文档与路由 | PASS | 修订后 `git diff --check` 无输出；`aisoft check-change-documents --porcelain`：change-documents、change-pr-url 均 PASS；`aisoft resolve-route 430 --provider codex`：R3 + G1，differences={}，policy SHA256 `184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40` 不变 |
| 路由必用技能满足情况 | 已补跑，合同现已确认 | 路由 skills 含 grill-me、to-spec、to-tickets。to-spec 与 to-tickets 经平台 publisher 发布映射文档（见上方「受限 publisher」行）。2026-10-25 负责人明确选择补跑 grill-me 并沿用已有结论；owner 会话按平台 pin 的 grill-me → grilling 核对一次决策树，新增问题为 0，未伪造新的用户回答，详见下节。保留 route.skills，不申请豁免；批准来自后续明确确认，不来自技能记录 |
| 确认点 1 | 已明确确认 | 负责人于 2026-10-25 明确指示：“确认 #430 修订合同。提交修订、同步 Issue 并读回核对，设为 approved 后启动 T01；治理文件提交后停止，交 fresh run 继续。确认点 2 前不 push、不建 PR。”批准范围为本票 13 个文件、12 条 AC 与 T01–T03；当前执行到 T01 治理 commit 为止 |
| 修订提交与 Issue 正文同步 | PASS | 修订提交 `a847e70889e0abcd3cd565620e38e13372c2eec5`；broker 回填四份完整合同后 fresh-read 逐字一致，正文 56415 bytes，SHA256 `edc4b4a909c844be4fdeb582a86fe4ee3fb7ce93432f001c95e937fcce9222c0`。远端正文作为该次合同快照保留，后续执行证据不改写获批 spec/plan 语义 |
| approved 投影与读回 | PASS | 完整合同同步读回成功后，broker 设置 approved 并再次读取；真实标签恰为 approved、complexity/complex、type/platform，Issue open，正文未变；本地 summary 随后同步 approved |
| 首次 T01 发布基线（历史） | PASS | broker fresh-fetch main 后固定 RELEASE_BASE=`2454b0c2519b0145aca4f1d289efb09ed8ac46d8`，main 与本分支最新发布包均 1.16.0；NEXT_MINOR=1.17.0，RELEASE_DATE=2026-10-25。main 新增 #429 的核对代码/测试、合同、索引，不涉及 T01 触点；该次准备尚未整合 main，后因 source guard 阻断获得明确恢复授权，见下节 |
| 最终实现独立审查 / PR CI | NOT RUN | 最终实现独立审查留待 T03，T01 提交不等于独立审查；确认点 2 前没有 push 或 PR |
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

本票修订已提交并同步同一 Issue 的完整正文，经 broker fresh-read 核对后设为 approved，现执行 T01；不包含最终 PR、合并、部署或安装授权。上表保留的创建、初稿发布及修订模拟为历史证据，当前授权以「确认点 1」「修订提交与 Issue 正文同步」「approved 投影与读回」三行为准。后续执行证据写回本文件，不改写远端获批合同快照。

本次准备证据目录：`/private/tmp/aisoft-greenfield-contract-261024-h029jbgw`。其中 broker 响应与一次性校验结果是本地辅助证据，不是需要下游安装的制品；Issue 正文和本票文件是评估所需的正式内容。

2026-10-25 启动与 T01 原始回执目录：`/private/tmp/aisoft-430-t01-261025-4qzk18d6`。已保存合同提交、正文同步及读回、approved 投影及读回、fresh-fetch 与版本依据。重要执行事实继续回填本票文档，临时目录不替代持久证据。

## T01 受控执行与交接

- 实际执行者：Codex，owner 与原始开始回执一致；实际模型/强度未由当前工具暴露。回执中的 frontier/max 是所需路由配置，不冒充运行配置实测。技能来源为平台 pin 的 Matt v1.3.1 implement 与平台 execution-adapter；source pin 见下方原始回执。
- 真实 prepare-ticket 在已批准 Issue、干净工作树上成功；起点、原文摘要、语义摘要、范围、路由及 source_evidence 全部按缓存原始回执持久保存。
- 发布变量：RELEASE_BASE=`2454b0c2519b0145aca4f1d289efb09ed8ac46d8`，NEXT_MINOR=`1.17.0`，RELEASE_DATE=`2026-10-25`；在 prepare-ticket 之前固定。
- 当前保存开始证据和真实检查结果，未声明 T01 完成。治理 commit 后本 run 立即 STOP；fresh run 重读规则、合同和实际 diff，使用下方 ticket_base 与治理 commit 的 HEAD 完成固定候选核对及 Matt 双轴审查，补写 T01 AC、head 与完成状态后才准备 T02。
- T02 的 S1–S11、隔离分发、fresh run 验证以及 T03 最终 Claude 交叉审查均 NOT RUN。

### 已中止的第一次 T01 尝试（历史原始回执与结果）

本节 JSON 只保存恢复前证据，不作为当前执行记录。

```json
{
  "change_base": "08aac8d5b9af4d334c53bcf34029870f09e50bf0",
  "tickets": {
    "T01": {
      "start": {
        "identity": {
          "issue": 430,
          "branch": "change/430-greenfield-planning",
          "owner": "01a16e1b-1085-7712-b5a8-c100d9f74629",
          "worktree": "/private/tmp/issue-430-greenfield-planning",
          "provider": "codex",
          "plan_path": "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea"
        },
        "ticket": "T01",
        "ticket_base": "89aef55c739fe296156ee6ad7cf322a3e900a867",
        "raw_plan_sha256": "324ec5cc6dad95465cf418fd45d89ef28cdec1e7f2709495bf8b24feb1e7a39f",
        "scope": [
          "docs/changes/430-greenfield-planning/summary-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/spec-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/verification-greenfield-planning-261024.md",
          "skills/aisoft-platform/references/greenfield-planning.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "skills/aisoft-platform/references/getting-started.md",
          "usage/USER-GUIDE.md",
          "usage/CONTRACT.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/430/issue-430-358643271815a468-02f0716d1747f497.md",
        "scratch": ".superpowers/sdd/issue-430-358643271815a468-02f0716d1747f497",
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "grill-me, to-spec, to-tickets, implement, issue-session-flow",
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
      "base": "89aef55c739fe296156ee6ad7cf322a3e900a867",
      "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea",
      "validation_sha256": "82078592a279b0942451537d94531ff6c7cf9be8b96f66086e741cd047720137",
      "checks": [
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:22:57.457969+00:00; duration=0.02s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-1.log; log_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:22:57.458135+00:00; duration=1.71s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-2.log; log_sha256=b5ab2d302d4234ab51dbe58b5e1ab9ec654b961057d21a4ba3e7c3d337dc2683; change-documents=PASS; change-pr-url=PASS"
        },
        {
          "command": "bash codex/tools/aisoft resolve-route 430 --provider codex",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:22:57.457067+00:00; duration=0.11s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-3.log; log_sha256=5fa974d984df330913a2b47a52a827ac7f21a5811ed85bef666f25e1b6b124d1; R3+G1; differences={}; policy unchanged"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --release \"$NEXT_MINOR\" --today \"$RELEASE_DATE\" --compatibility minor --notes '新增全新项目需求发现与滚动阶段规划方法及入口'",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:22:52.932722+00:00; duration=0.11s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-4.log; log_sha256=17f132fadda66c4bedbddcab6e84ce5b525fcedfd68cbd5755a900f2501dfb42; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; release_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --verify --baseline-ref \"$RELEASE_BASE\"",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:22:57.457855+00:00; duration=0.14s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-5.log; log_sha256=860971d9f11e6dd3d466cd92595996a820bf4896da01ef287d0bbf30a35e4adb; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; release_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137"
        },
        {
          "command": "AISOFT_USAGE_BASELINE_REF=\"$RELEASE_BASE\" LC_ALL=C bash codex/tests/smoke.sh",
          "result": "BLOCKED",
          "evidence": "exit=1; UTC=2026-10-25T05:23:09.693632+00:00; duration=4.42s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-6.log; log_sha256=62fb2f0e29e044a885c8d1171db3c20951a27f36696afe087339533c8d1a6542; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; source guard rejected 7 commits behind origin/main; later tests NOT REACHED; no check was disabled"
        }
      ]
    }
  }
}
```

## T01 基线阻断与恢复授权（历史）

2026-10-25 原样运行完整 smoke，4.42s 后 exit 1：`architecture/install: source checkout is 7 commit(s) behind origin/main`。该项只向测试临时前缀安装，但现有 source guard 仍要求来源不落后 upstream。没有禁用 guard、更改 upstream、隐藏 main、在无历史副本中绕过检查或将局部检查冒充 smoke PASS。

只读核对得到当前 HEAD `89aef55c739fe296156ee6ad7cf322a3e900a867` 与固定 main `2454b0c2519b0145aca4f1d289efb09ed8ac46d8` 分叉（ahead 3 / behind 7）。main 新增的 #429 七个文件与本次 T01 变更路径没有交集，但“触点无冲突，所以 T01 无需整合”的先前判断遗漏了 installer source guard。T01 必须先解除此基线阻断，不能将必要整合推迟到 T03。

现行 AGENTS/03 要求只追加线性本地提交；execution-adapter 不允许通过重写历史保持旧回执，`review_candidate.range_data` 还明确拒绝含 merge commit 的候选。因此既不能默默 rebase，也不能仅以 broker 接受双亲 main integration 为由加入 merge commit。此处是合同/执行路径冲突，非网络故障；未更改治理规则、runtime、owner 或远端。

当时提出的精确例外如下；负责人随后明确选择“允许恢复并继续（推荐）”，实际结果见下节：

1. 保全当前三笔提交、全部未提交 diff、开始回执及验证日志，记录新旧 SHA 对应关系。
2. 仅将尚未推送的 #430 三笔提交重放到固定 fresh main；不改 main、不推送、不改其它会话或项目。冲突则停止，不自动取舍。
3. 将旧 T01 开始回执作为历史保留，明确本轮为中止的尝试；在新线性基线上重新形成干净的 T01 开始回执，保留获批 spec/plan 语义与 13 文件范围，必要的 SHA 更新经 broker 同步并读回。
4. 恢复同一批 T01 修改，重新核定发布版本并运行全部必需检查；通过后独立提交治理文件，立即 STOP，再由 fresh run 继续。确认点 2 前仍不 push、不建 PR。

该次明确授权仅解决未推送分支的基线与回执恢复，不改变 spec/plan 语义、范围或测试硬门；仍须通过 T01 检查后治理 commit 并 STOP。

## 2026-10-25 已授权基线恢复

- 授权原文：负责人选择“允许恢复并继续（推荐）”，对应问题明确说明“当前提交和改动已备份，将尚未推送的 3 笔提交重放到已核对的 main，重新建立 T01 开始回执并重跑检查”。该授权覆盖本次历史调整；确认点 2 前仍不 push、不建 PR。
- 原提交 bundle 与全部未提交 diff 已保全，bundle 验证通过；保全目录 `/private/tmp/aisoft-430-t01-261025-4qzk18d6`，原始 receipt/cache 与 scratch 分别保存为 attempt1-cache、attempt1-scratch；对应字节也已持久化在上节历史 JSON。
- 备份 bundle SHA256 `3f998fbb11fed571c6f1fa58c9a4bb38a3da1a528421016b7443b1236bf0af93`（前提 original base `08aac8d5b9af4d334c53bcf34029870f09e50bf0`）；全部 diff patch SHA256 `6500b466178a3bf951aecfd1858654a248c26fd4980d79d8be9afccfa2e57db5`。另保留 owned stash `8dcebedc5ccb8dad7cc8b8334e80b5e7b40a3b46`，没有应用或删除其它 stash。
- 原分支 3 笔提交重放到 fixed main `2454b0c2519b0145aca4f1d289efb09ed8ac46d8`，无冲突；每一笔前后 diff 字节逐一相等。重放后 HEAD `9a90242d400ff49f057f0fedecbaf14d6cdb8ed7`，工作树干净，ahead 3 / behind 0。main、owner marker、受保护分支和其它 worktree 未改。

| 原提交 | 重放后提交 | 字节核对 |
|---|---|---|
| `3800ec2dd84da101e61dc9b3c2ad69431c028ea5` | `4b182d47f17d9bf41b97ab36df48ce5a416997d5` | diff 相同；SHA256 `dc5ca9b436f7b05d77b09648f9b9f6aaa574b2bce518d7879a05e490ef1b7104` |
| `a847e70889e0abcd3cd565620e38e13372c2eec5` | `561f87cda4ac44c2794b494dd15c56a9dbf3a2dd` | diff 相同；SHA256 `bc3bd2f67f19bd193a919858076ead0aa234577966182a125def490886d84035` |
| `89aef55c739fe296156ee6ad7cf322a3e900a867` | `9a90242d400ff49f057f0fedecbaf14d6cdb8ed7` | diff 相同；SHA256 `39b910d4fa712b6f23ec0322217980c7432c4f075291d310cc37daa6a66e2eb6` |

恢复后当前 change_base 与 RELEASE_BASE 均为 `2454b0c2519b0145aca4f1d289efb09ed8ac46d8`；原 change_base 和旧 T01 起点只作为历史保留。新 main 与恢复后的本分支最新发布均为 1.16.0，NEXT_MINOR 仍为 1.17.0，RELEASE_DATE 仍为 2026-10-25。spec/plan 语义、13 个允许路径、R3+G1 和 policy SHA256 均不变；新 T01 启动必须在恢复后的干净基线重新调用真实 prepare-ticket。

基线恢复记录已通过 broker 回填同一 Issue 并 fresh-read 逐字核对：正文 57790 bytes，SHA256 `cda8dfd36b87ceb80634e0afb93dcce9981a09ed3301a1d7259a23cb31edb829`；标签仍恰为 approved、complexity/complex、type/platform，Issue open。原获批正文完整保留，新增内容仅为恢复授权与 SHA 对应关系。

### 当前执行记录（恢复后）

新 prepare-ticket 返回 prepared，ticket_base=`817f988ddd59d507cfcfa2437747c7f96d9c33b0`，起始 staged/unstaged/untracked 均为空；原始回执如下。T01 尚未完成；治理 commit 后必须 STOP，fresh run 才能固定该提交、执行双轴审查并补写 AC/head/Status。

```aisoft-execution
{
  "change_base": "2454b0c2519b0145aca4f1d289efb09ed8ac46d8",
  "tickets": {
    "T01": {
      "start": {
        "identity": {
          "issue": 430,
          "branch": "change/430-greenfield-planning",
          "owner": "01a16e1b-1085-7712-b5a8-c100d9f74629",
          "worktree": "/private/tmp/issue-430-greenfield-planning",
          "provider": "codex",
          "plan_path": "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea"
        },
        "ticket": "T01",
        "ticket_base": "817f988ddd59d507cfcfa2437747c7f96d9c33b0",
        "raw_plan_sha256": "cba4ec14b5b1969e738150eacab814e1a8757bf326771e5d5ed9dbe9a207afb0",
        "scope": [
          "docs/changes/430-greenfield-planning/summary-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/spec-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/verification-greenfield-planning-261024.md",
          "skills/aisoft-platform/references/greenfield-planning.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "skills/aisoft-platform/references/getting-started.md",
          "usage/USER-GUIDE.md",
          "usage/CONTRACT.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/430/issue-430-358643271815a468-02f0716d1747f497.md",
        "scratch": ".superpowers/sdd/issue-430-358643271815a468-02f0716d1747f497",
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "grill-me, to-spec, to-tickets, implement, issue-session-flow",
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
      "base": "817f988ddd59d507cfcfa2437747c7f96d9c33b0",
      "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea",
      "validation_sha256": "82078592a279b0942451537d94531ff6c7cf9be8b96f66086e741cd047720137",
      "checks": [
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:41.491195+00:00; duration=0.02s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-1-restarted.log; log_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:41.491198+00:00; duration=1.55s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-2-restarted.log; log_sha256=b5ab2d302d4234ab51dbe58b5e1ab9ec654b961057d21a4ba3e7c3d337dc2683; change-documents=PASS; change-pr-url=PASS"
        },
        {
          "command": "bash codex/tools/aisoft resolve-route 430 --provider codex",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:41.491189+00:00; duration=0.11s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-3-restarted.log; log_sha256=5fa974d984df330913a2b47a52a827ac7f21a5811ed85bef666f25e1b6b124d1; R3+G1; differences={}; policy_sha256=184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --release \"$NEXT_MINOR\" --today \"$RELEASE_DATE\" --compatibility minor --notes '新增全新项目需求发现与滚动阶段规划方法及入口'",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:24.772515+00:00; duration=0.1s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-4-restarted.log; log_sha256=17f132fadda66c4bedbddcab6e84ce5b525fcedfd68cbd5755a900f2501dfb42; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; release_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --verify --baseline-ref \"$RELEASE_BASE\"",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:41.491191+00:00; duration=0.13s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-5-restarted.log; log_sha256=860971d9f11e6dd3d466cd92595996a820bf4896da01ef287d0bbf30a35e4adb; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; release_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137"
        },
        {
          "command": "AISOFT_USAGE_BASELINE_REF=\"$RELEASE_BASE\" LC_ALL=C bash codex/tests/smoke.sh",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T05:34:49.098024+00:00; duration=383.62s; log=/private/tmp/aisoft-430-t01-261025-4qzk18d6/T01-check-6-restarted.log; log_sha256=be3e0c1bb7af2caba655453629b71389ebdca5a6b76da22463605dd50734197b; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; NEXT_MINOR=1.17.0; RELEASE_DATE=2026-10-25; full smoke PASS; 746 runtime tests OK (110.909s); project-leak PASS; Codex platform static smoke checks passed; temporary fixtures only"
        }
      ],
      "head": "2e54d7e0c85810cbcff2d5878d82c849e76b6144",
      "ac": {
        "AC-3": "PASS",
        "AC-5": "PASS",
        "AC-7": "PASS",
        "AC-11": "PASS"
      }
    },
    "T02": {
      "start": {
        "identity": {
          "issue": 430,
          "branch": "change/430-greenfield-planning",
          "owner": "01a16e1b-1085-7712-b5a8-c100d9f74629",
          "worktree": "/private/tmp/issue-430-greenfield-planning",
          "provider": "codex",
          "plan_path": "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea"
        },
        "ticket": "T02",
        "ticket_base": "b2ab5720773b374319b80117960c67667f66100f",
        "raw_plan_sha256": "10c8b673006e3ddade498d1d7d306b4aa15bba3d7fa5801bf1f67857256c4be2",
        "scope": [
          "docs/changes/430-greenfield-planning/summary-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/spec-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md",
          "docs/changes/430-greenfield-planning/verification-greenfield-planning-261024.md",
          "skills/aisoft-platform/references/greenfield-planning.md",
          "skills/aisoft-platform/SKILL.md",
          "skills/issue-session-flow/SKILL.md",
          "skills/aisoft-platform/references/getting-started.md",
          "usage/USER-GUIDE.md",
          "usage/CONTRACT.md",
          "03-Issue-Spec-Plan与单闸门开发流程.md",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/430/issue-430-358643271815a468-02f0716d1747f497.md",
        "scratch": ".superpowers/sdd/issue-430-358643271815a468-02f0716d1747f497",
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "grill-me, to-spec, to-tickets, implement, issue-session-flow",
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
      "base": "b2ab5720773b374319b80117960c67667f66100f",
      "semantic_hash": "02f0716d1747f4971f3bfa07868bee5861c6cc698b615a5735585a194e383aea",
      "validation_sha256": "0c7a555a240f90866eff277988cce54231115c72b9ff2dd0731fb3a7efb73116",
      "checks": [
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:33.495416+00:00; duration=0.02s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-1.log; log_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:33.495317+00:00; duration=1.86s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-2.log; log_sha256=b5ab2d302d4234ab51dbe58b5e1ab9ec654b961057d21a4ba3e7c3d337dc2683; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8"
        },
        {
          "command": "bash codex/tools/aisoft resolve-route 430 --provider codex",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:33.494883+00:00; duration=0.11s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-3.log; log_sha256=5fa974d984df330913a2b47a52a827ac7f21a5811ed85bef666f25e1b6b124d1; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --verify --baseline-ref \"$RELEASE_BASE\"",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:33.494866+00:00; duration=0.15s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-4.log; log_sha256=860971d9f11e6dd3d466cd92595996a820bf4896da01ef287d0bbf30a35e4adb; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; version=1.17.0; bundle_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --build \"$ISOLATED_BUNDLE\"",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:05.020511+00:00; duration=0.21s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-5.log; log_sha256=2bf530d7254c134dc7828f63a25e510f6a1b7115d4f6beefc8ef59d32d32ca98; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; version=1.17.0; bundle_digest=sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137; ISOLATED_BUNDLE=/private/tmp/aisoft-430-t02-261025-eobeoqs9/isolated-bundle; 12 files byte-equal; 42 links resolve; 3 provider reference copies equal"
        },
        {
          "command": "AISOFT_USAGE_BASELINE_REF=\"$RELEASE_BASE\" LC_ALL=C bash codex/tests/smoke.sh",
          "result": "PASS",
          "evidence": "exit=0; UTC=2026-10-25T07:02:09.429481+00:00; duration=425.08s; log=/private/tmp/aisoft-430-t02-261025-eobeoqs9/T02-check-6.log; log_sha256=6787a42c6cfa2e65f1001df5ac3dfe47a5708a383d0b77d4845c8c3ca8f94501; RELEASE_BASE=2454b0c2519b0145aca4f1d289efb09ed8ac46d8; full smoke PASS; 746 runtime tests OK (134.060s); static/project-leak PASS; fixture evidence only"
        }
      ]
    }
  }
}
```

## T01 提交前结果与 fresh run 交接

恢复后的六条计划命令均为 PASS；当前机器记录保留计划中的完整命令字符串，实际变量和原始日志 SHA256 见各 checks.evidence。smoke 于 2026-10-25T05:34:49.098024+00:00 开始，383.62s 后 exit 0，输出 `Ran 746 tests in 110.909s` / `OK`、`PASS: project-leak` 与 `Codex platform static smoke checks passed.`；日志 SHA256 `be3e0c1bb7af2caba655453629b71389ebdca5a6b76da22463605dd50734197b`。旧 BASE_STALE 结果没有覆盖或删除，新 PASS 不表示真实安装、采用、CI、部署或 UAT。

本次 source/local 核对：

| T01 对应 AC | 已观察的实现与本地证据 | 尚待后续切片 |
|---|---|---|
| AC-3 | reference §2、§7 明确唯一入口、可合并三种资料、规划/收口 Issue 写入、实现 Issue 只链接；11 个实际改动文件均在 13 路径允许集合内 | T02 S2/S8/S11 与固定候选审查 |
| AC-5 | reference §4 回链现行路由；当前 resolve-route 返回 R3+G1、differences={}，policy 字节未变 | T02 S5 三 provider/路由场景 |
| AC-7 | reference §6 限定已有技能入口与 wayfinder 位置；实际 diff 未改任何 vendor、pin、manifest、runtime 或安装器 | T02 S9 与最终独立复核 |
| AC-11 | 治理提交前六命令通过，完整 smoke 包含已跟踪的新 reference；恢复后的发布包成员与恢复前逐字一致 | 本次独立治理 commit 与 STOP 由 fresh run 核实，再补 T01 完成记录；T02 证明 fresh run 切片 |

1. 本次仅提交 T01 方法、入口、1.17.0 发布包及本票证据，随后立即 STOP；不在当前 run 执行 T02 或 review-candidate。
2. fresh run 先重读 AGENTS、批准 spec/plan、变更后的两个技能与新 reference、verification；核对 exact branch/worktree/owner、真实 HEAD 和本次治理 diff。原合同授权继续有效。
3. 当前整批 change_base=`2454b0c2519b0145aca4f1d289efb09ed8ac46d8`，真实 T01 ticket_base=`817f988ddd59d507cfcfa2437747c7f96d9c33b0`；候选 HEAD 取本次治理 commit 的完整 SHA，不用 HEAD~1 推断起点。旧 `89aef55c` 回执只作已中止尝试的历史证据。
4. 使用真实治理 commit 执行 `review-candidate 430 T01 --head <完整 SHA>`，按现行执行适配完成同一固定候选的 Standards/Spec 两轴核对，记录 commit/STOP/遗漏/AC 证据；需要治理修复时再次受控提交并 STOP。
5. fresh run 才把 T01 的 Status 改 done，并在上方当前 aisoft-execution 中补齐 head、AC 与相应完成证据，再 prepare-ticket 430 T02。这里故意不预写 head 或 AC 全通过，避免在 commit/STOP 前伪造完成。T02 的 S1–S11、独立隔离分发核对和 T03 的 Claude 最终审查仍 NOT RUN。
6. 备份 bundle、patch 与 owner 的专用 stash 保留用于恢复，不动其它会话数据。确认点 2 前不 push、不建 PR；本票没有安装新技能或修改真实项目。

## 2026-10-25 fresh run：T01 完成核对

负责人在上一轮治理提交与明确 STOP 后发送“继续”。本轮重新读取 AGENTS、README 相关合同、execution-adapter、aisoft-matt-workflow、两个受改技能、新 reference、获批 spec/plan 和实际治理 diff。HEAD=`2e54d7e0c85810cbcff2d5878d82c849e76b6144`，branch/worktree/owner 与原回执相同，工作树干净；与上一轮停止回执逐项相符。Matt v1.3.1 snapshot 再次通过 verify_snapshot，未加载新技能包或真实安装。

真实 `review-candidate 430 T01 --head 2e54d7e0c85810cbcff2d5878d82c849e76b6144` 返回机械 PASS，候选包摘要 `29efaa732eeff9be6b4ec6a3e621d5b0f712810d1fa27ee384ba31b13c87d1fe`。ticket range=`817f988ddd59d507cfcfa2437747c7f96d9c33b0..2e54d7e0c85810cbcff2d5878d82c849e76b6144`，唯一提交为该治理提交，11 文件；ticket diff SHA256 `9574234214d3d827462fcd5695ed3c8a27403b5d145a0907ff39dc26e423fe0f`。整批 range 仍从 `2454b0c2519b0145aca4f1d289efb09ed8ac46d8` 起，12 文件，diff SHA256 `f88620845e4ff5994b4f8a601bae2c94326640b649ac3e63f5ab14ca4041c5f6`。没有 staged/unstaged/untracked 遗漏；原始辅助日志已按 SHA 存入 verification 的 checks，未依赖被忽略成果补足交付。编辑器未保存缓冲无法由工具证明，保持 UNKNOWN。

按 Matt code-review 明确要求，两个只读子代理同时接收相同固定 BASE/HEAD 与提交清单。执行 provider 为 Codex（实际模型/强度未暴露），这两项是逐票审查，不代替 T03 Claude 跨 provider 审查。

### Standards

审查者 `/root/t01_standards`：PASS，明确规范违规 0、启发性问题 0。reference 保持 Issue/Txx、两确认点、单写者及治理 STOP/fresh run 边界；项目事实与阶段决定留在项目侧。技能、指南与合同使用薄指针，未形成第二套授权或执行状态。正文与模板的适度重复有用途，未发现需处理的重复或分散改动问题。证据保留失败与获准恢复过程，未将 source/local 提升为 T02/T03、安装、部署或 UAT 结果。

### Spec

审查者 `/root/t01_spec`：缺失/部分满足 0、越界 0、实现错误 0。方法、三个模板、入口、技能边界、资料所有权与滚动规则符合 spec。1.17.0 与新参考已入发布清单，历史不变。专项核对 USER-GUIDE 不在发布包成员内，其链接在维护仓有效；CONTRACT 下发指针没有错误的 Markdown 路径。结论只覆盖 T01 源文件语义，T02 隔离导出和场景、T03 Claude 独立审查仍待执行。

两轴总计各 0 finding，无待修复项。T01 的 AC-3/5/7 仅完成其 source/local 切片；AC-11 完成提交前检查、独立治理 commit 与 STOP 切片。所需 head、四条 AC 和既有六条 checks 已写入当前 aisoft-execution，Status 改 done；T02 继续覆盖场景与 fresh run 证据。

本轮证据目录：`/private/tmp/aisoft-430-t02-261025-eobeoqs9`。

## T02 开始

T01 的真实 --resume 返回 done-evidence-verified，完成补证提交为 `b2ab5720773b374319b80117960c67667f66100f`。其后真实 prepare-ticket 430 T02 返回 prepared，ticket_base 为同一 SHA，staged/unstaged/untracked 均为空，owner/路由/plan 语义与 T01 一致。当前只保存开始回执，不提前声明 T02 完成。

## T02 场景与隔离分发实际结果

证据层次为 source/local/isolated export。以下场景是明确输入的静态推演或临时夹具检查，不声称真实 provider 新会话执行、真实项目采用、live、安装或 UAT。S6 没有给其它 Issue 实际发送评论。所有生成材料均在本票临时证据目录，未进入真实项目或技能目录。

| 场景 | 输入 | 观察与位置 | 反例核对 | 层次 / 结果 |
|---|---|---|---|---|
| S1 | 未接入的 Codex 用户仅有一句想法 | 沿 reference §1 与 getting-started，输出本地笔记并进入登记/采用；不启动本方法或 tracker | 反例：直接运行 to-spec/triage/wayfinder、写 .scratch 地图；被 §1 的明确前置条件排除 | source 静态推演 / PASS |
| S2 | 单阶段且一张 Issue 足够 | reference §2/§7 允许三类资料合成一文件、该 Issue 兼任规划者；恢复夹具 README 示范合并入口与简报 | 反例：强制三文档、调度会话或阶段批准；文本未设这些要求 | source + local 合成资料 / PASS |
| S3 | 当前身份/核心数据，下一业务流程，远期分析 | §3 深度表和 §7 模板把当前边界/退出证据展开；夹具 P2 仅轮廓与待补证据、P3 仅方向；远期访谈停在假设 | 反例：P2 详细工期/任务及 P3 已承诺顺序；§3 明确排除 | source + local 合成路线图 / PASS |
| S4 | 分别输入既有需求材料与已有实现 | §1 前者复用事实、冲突与缺口；后者链接 project-align 或增量 Issue；没有重建/覆盖旧资料的步骤 | 反例：把已有代码当空项目重新初始化；被入口分流排除 | source 静态推演 / PASS |
| S5 | production/development、small/complex、三 provider；阶段内 maintenance+change 子 Issue | 12 格 resolver 读取通过；3 provider 的真实 CLI resolve-route 与文档检查共6条 PASS；R4 无自动 G1，忠实沿用输出；3 个擅加 grill-me 反例均产生拒绝/差异 | 反例：按阶段背景手填 G1、要求 development 生成 plan、同时选两个执行器；记录的当前政策与 actual route 排除 | local 临时 Git 夹具 + 静态政策核对 / PASS |
| S6 | 新发现影响某 approved Issue 的 AC | §5 明确经评论记录，由该 Issue owner 停止受影响部分并处理合同；无关工作可继续；此处只推演，不写真实 Issue | 反例：调度者改 approved 正文或他人 worktree；§5 明确禁止 | source 静态推演 / PASS |
| S7 | 取消远期集成，当前阶段独立 | §3/§5 要保留阶段 ID、原因、证据及依赖影响；更新后续方向，不自动阻断独立当前工作 | 反例：重批全项目或为了远期未知停止独立阶段；对应文本排除 | source 静态推演 / PASS |
| S8 | 仅给合成项目 AGENTS.md，不给原聊天 | 实际路径追踪 AGENTS→docs/planning/README→roadmap/current，恢复 P1/P2/P3、当前未知/缺证与规划 Issue 701 归属；S8-recovery-traversal.json 记录访问顺序 | 反例：只靠聊天、专有缓存或阶段级 Txx 表恢复；夹具只使用文件链接，当前目标仍未证实 | local 合成路径追踪 / PASS |
| S9 | 本机存在会自建阶段状态的其他技能包 | §6 仅允许表内已有入口；wayfinder 明确不是入口，其余包另立适配 Issue；USER-GUIDE 显式 Matt grill-me | 反例：可见即调用、自动安装或用其他计划状态覆盖 Issue；范围 diff 无 pin/vendor/runtime 改动 | source 静态推演 + 范围读取 / PASS |
| S10 | Issue 已合并，但集成/业务观察未提供 | §5 按 Issue、集成、阶段观察、假设四方面核对；只能记录目标未证实和证据缺口 | 反例：将 merge/CI/可达当 UAT 或阶段成功；§5 明确区分 | source 静态推演 / PASS |
| S11 | 两张并行实现 Issue 都发现路线图要改 | §2/§5 指定两实现者在自己的 Issue 记录发现，只链接规划资料；调度者起草，由单一规划/收口 Issue 范围持有人写入 | 反例：两实现者并行改路线图或 dispatcher 进入其 worktree；写入归属明确排除 | source 静态推演 / PASS |

S5 临时 Git 仓为 `/private/tmp/aisoft-430-t02-261025-eobeoqs9/route-fixture`，合成 `change/701-routing-sample` / `example.invalid/fixture/fixture-project/issues/701`，使用专属临时 governance manifest 的 production 声明；没有创建远端 Issue。对 codex/claude/cursor 分别运行当前真实 CLI resolve-route 与 check-change-documents，6 条 exit 0，正向 route.differences 均为空；错误地插入 grill-me 的 3 个反例均被拒绝或返回 differences。该 maintenance/change 子 Issue 得到 R4，不根据阶段背景手填 G1。另只读调用现行 resolver 核对 12 格 production/development × small/complex × provider：small 保持 small-direct，development complex 保持 complex-development 且不追加 to-tickets，各格 confirm=2。development 文档不另造计划，按政策静态核对 Issue AC / 合成 T01 的约定。

S8 合成项目从唯一给定的 AGENTS.md 读取「项目规则」，实际访问顺序为 AGENTS.md → docs/planning/README.md → roadmap.md / current.md；恢复 P1 身份/核心数据、P2 业务流程轮廓、P3 分析方向、数据来源假设和缺失的完成证据；规划 Issue 701 拥有资料，其他实现 Issue 只链接。本记录不把文件遍历等同于真实新模型会话行为。

### 隔离发布包

`usage-bundle --build` 在空目录 `/private/tmp/aisoft-430-t02-261025-eobeoqs9/isolated-bundle` 成功导出 1.17.0，摘要 `sha256:499d72a5a8c15e26bb766cc58793d38fef8e74628f9f76b7add33f243f710137`。新 reference 的三份落点如下，均与源逐字相等，SHA256 均为 `fca0193e1bf04eb22a0b76ab8b473eceb3fd330e83ab455c3d0c8a91e621271e`：

- project/.agents/skills/aisoft-platform/references/greenfield-planning.md
- project/.claude/skills/aisoft-platform/references/greenfield-planning.md
- project/.cursor/skills/aisoft-platform/references/greenfield-planning.md

同时按现有 skills.manifest 的实际映射，核对新 reference、两个受改 SKILL 和 getting-started 的三端合计 12 文件字节及 42 个相关链接（含 runbook §6 锚点），均 PASS。导出的 `.aisoft/platform-usage.md` 与 CONTRACT 字节相等；Codex/Cursor 的显式 grill-me 路径存在。USER-GUIDE 不是发布包成员，源码内新链接有效；Claude 独立插件是否已安装和实际发现不在该导出证明内。发布历史 verify 使用固定 RELEASE_BASE，原已发布条目未改。

### 完整回归与范围

T02 六条命令均 exit 0。完整 smoke 于 2026-10-25T07:02:09.429481+00:00 开始，425.08s 完成，含 746 项 runtime 测试（134.060s）和最终静态/项目泄漏检查；日志 SHA256 `6787a42c6cfa2e65f1001df5ac3dfe47a5708a383d0b77d4845c8c3ca8f94501`。T02 未改方法、技能、发布成员、runtime、shell、CI、模板或真实项目，只追加本票计划状态及执行证据。

T02 的 AC-1..AC-11 source/local 切片均已有上表与导出/命令证据；完成标记与实际候选 head 留待本次证据提交、固定范围两轴审查后再写入。最终 AC-12 仍须 T03 Claude 审查，当前 NOT RUN。

辅助证据摘要（正式观察已写在上文，不以临时路径代替结论）：

| 文件 | SHA256 |
|---|---|
| T02-scenarios.json | `6a65b1bdbec14e2fde43f46158ab7ade53b69111835c3544675d6303c92aead6` |
| T02-isolated-export.json | `0dc3bf1d63a1d4dc9071190865a420971485f71842a29ab92f361f53d0aa7b1c` |
| S5-routing-results.json | `ef33db82d9c1892214cb6afdf1041dfeea4039f71ae0273ef56addd5aea14604` |
| S5-route-matrix.json | `075c057c63ac649b387927b736f8425c6eee4f03e3c0f01c74ad94a65c4d2e6b` |
| S8-recovery-traversal.json | `ec6dd9ddb45db2851c1005baa684ca9134ed9e7bab72866e2e5c5edb8b547e96` |
