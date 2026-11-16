---
issue: 450
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/450
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: pending
branch: change/450-engineering-principles
created: 2026-11-16
updated: 2026-11-16
---

# Verification：共享工程原则的收敛改进

## 基线与范围

- change_base：`c14a86d4ad0d1fd5938ab31343f8d72acd486a71`。2026-11-16 固定 broker `git.fetch.main` 返回 PASS，`HEAD` 与 `origin/main` 读回一致，主干干净。
- exact worktree：`/private/tmp/issue-450-engineering-principles`，branch `change/450-engineering-principles`，owner session `01a1deda-7dba-7d80-8ce7-703794ceee24`，claim 返回 created。
- 本记录负责 AC-1 至 AC-6；准备阶段通过不代表这些实施 AC 已通过。实际 candidate_head / ticket_base 见执行结果。
- 以下“方案审核”“实施交接”两节是准备阶段快照：当时没有应用原则 patch、生成新 release、安装或执行项目采用。实施后的现状以执行结果、机器可读记录与 AC 表为准。

## 方案审核与资料链路（非实施审核）

- Herdr 空间 `AISoftPlatform #450 方案审核`，标签 `Claude Opus 5.5 High`，terminal `t3x`，session `58343b33-fb32-4f34-bec5-11cbedcdeddd`。
- 实际模型由当前会话响应确认 `claude-opus-5-5`；high 由启动 `--effort high` 及会话显示共同核实；最终 wait 为 `ended=true/status=done/turn=2`。审核 BASE = HEAD = change_base，没有代码 diff。
- 初审“调整后可采纳”；补充文章意见后提出一处落点方案；复核纠正初审中“漏算 reference 发版”“必然新增 verification”“字节分发校验等于执行硬门”等推断，确认收敛稿无阻断项。
- 本机完整原始产物目录：`/Users/benque/.codex/visualizations/2026/11/15/01a1deda-7dba-7d80-8ce7-703794ceee24/issue-450-review-261116/`。其中 proposal-v2 SHA-256 与报告摘要由 review-metadata.json 保存；正式候选以本票冻结 patch 为准。
- 主会话读完用户提供的 Notion 文章九节，Claude 仅读主会话归纳；未独立观看视频或核验数据，pstack 未安装或实跑。私有产物不是安装、CI、live 或长期效果证据。

## Claude Code 实施交接

- 负责人指定具体开发转交 Claude Code。首次文档提交为 `7f8360f57bdb6577a6a46b85d4728e01214913e3`；其后的交接提交只同步本票四份映射文档，不应用原则 patch 或变更 bundle。
- 原写者 Codex `01a1deda-7dba-7d80-8ce7-703794ceee24` 完成交接提交后停止写入并交回 worktree。owner 标记在实际接手前仍保留原值；接手方应以自己的 session 调用 `claim-worktree --takeover` 并记录回执，不能把“已准备交接”写成“新 owner 已认领”。
- 显式 provider 改为 claude，执行映射为 executing-plans / verification-before-completion；最终独立审核方改为未参与实现的 Codex。R3 / D4、全部 AC、冻结候选、scope 和权限边界不变。
- T01 / T02 仍 pending，尚未调用 prepare-ticket，也未启动任何开发代理。后续按新 provider 创建开始回执；不把旧文档准备检查视为新执行回执。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| fixed broker issue.read #450 | PASS（准备） | open / needs-analysis、comments=0，正文的旧授权边界由本轮用户同意补充 |
| fixed broker git.fetch.main 与本地 rev-parse | PASS（准备） | exact baseline 如上，不推送 |
| change-name 与 claim-worktree | PASS（准备） | exact branch / worktree / owner 如上 |
| pinned Matt manifest 目录摘要核对 | PASS（准备） | triage、to-spec、to-tickets 的目录 hash 与 v1.3.1 manifest 相符；未安装或更新 |
| 生成冻结 patch | PASS（准备） | patch 和候选摘要见 spec，原始原则文件仍与基线相同 |
| 文档解析、路由与文档预检 | PASS（准备） | 四角色解析正确；resolve-route 命中 R3 / D4，differences={}；check-change-documents 的两个检查 PASS；classify 文档预检 OK |
| 判级预览的宿主读回 | PASS（准备） | 沙箱首次返回 state-unreadable；同一固定 broker 宿主路径重跑成功，set-classification platform / complex，applied=false；不是服务或 Issue 不存在 |
| plan 语义解析与 bounded publisher | PASS（准备） | parse_plan 识别 T01 无前置、T02 依赖 T01，均 pending 且引用 AC-1 至 AC-6；本地 publish_spec / publish_plan 只校验并写既有映射文件，不调用 direct Gitea client |
| patch apply --check / 候选摘要验证 | PASS（准备） | 仓库仅做 apply --check；临时副本应用后的全文摘要等于 spec，reverse --check 成功；仓库原则文件保持基线字节 |
| classify --apply / --verify 450 | PASS（准备） | updated 后独立读回 result=projected，type/platform、complexity/complex；这是本地合同与 live 标签一致，不代表文档已推送或合并 |
| Claude 交接合同复核 | PASS（准备） | resolve-route --provider claude 命中 R3 / D4，differences={}；文档与 plan 解析通过、两票均 pending、无执行回执；原则、bundle 和冻结 patch 均未改变 |
| Claude 接管 worktree | PASS | 核对 branch / HEAD `4d4321de…` / 干净 / 原 owner `01a1deda-…` 与快照一致；`claim-worktree --takeover` 返回 taken-over，owner 改为 `f2cce2e4-3bb8-4160-87a4-9b9a1a5ee664`。会话实际为 Claude Opus 5.5，环境报告推理强度 medium，低于路由 frontier/max，如实记录 |
| 接手后合同复核 | PASS | broker issue.read：open / approved、type/platform、complexity/complex，1 条评论；resolve-documents 四角色正确；resolve-route --provider claude 命中 R3 / D4，differences={}；check-change-documents 两项 PASS |
| T01 prepare-ticket | PASS | status=prepared，ticket_base `4d4321dee233dc55116539f77799817595108167`，初始三类状态为空，receipt `.superpowers/aisoft/450/T01.json` |
| T01 patch 应用与摘要 | PASS | 应用前原则 `07c78311…`、patch `81d82720…` 与 spec 一致；apply --check 通过后应用，全文 `3dda6096…1d9d1811` 等于 spec；reverse --check 成功；引言“不增加确认点、流程状态或验证硬门”保留 |
| T01 bundle release 与 verify | PASS | broker git.fetch.main 后 origin/main 仍为 change_base，最新已发布 1.24.1，1.24.2 未占用；`--release 1.24.2 … --compatibility patch` 输出 RELEASED sha256:8db2e495…；`--verify --baseline-ref c14a86d4…` 输出 VERIFIED；members 与既有 releases 前缀、其他键均与基线相同，仅追加 1.24.2 |
| T01 diff / 文档 / 范围检查 | PASS | `git diff --check` 无输出；check-change-documents 两项 PASS；治理提交 `9358cdf5aff69c12dccb3acb140dc49d0cbedff1` 仅含原则与 bundle |
| T01 场景与反例文本审议 | PASS（实现方自审） | 四类关注点明写为提示、不要求每项任务执行四类验证；证据行区分独立运行 / 实现方结果 / 静态推导并保留未验证说明；学习条目保留归因与成本维度，结构优先为评估顺序。仅为实现方静态审议，不是独立审核 |
| T01 治理 STOP | 已执行 | 治理提交后停止本运行，T01 完成判定与 T02 交 fresh run；本运行未执行 T02 任何步骤 |
| fresh run 接管 | PASS | 新 Claude Code 会话 `b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86`（Opus 5.5；R1 审核后用 app 会话元数据 `get_session self` 核实 effort=medium，低于路由 frontier/max，处置待负责人裁决）。核对 branch / HEAD `4efe9516…` / 工作树干净，重读交接文件、spec、plan、verification、治理 diff 与 issue-session-flow 技能；`claim-worktree --takeover` 返回 taken-over，owner 由 `f2cce2e4-…` 改为本会话 |
| `prepare-ticket 450 T01 --provider claude --resume` | REFUSED（按设计） | 返回 resume identity/semantic contract mismatch。核对源码：plan semantic_hash 在三个提交均为 `3b445c7b…`，差异仅在 owner；runtime 规定未完成票的 resume 只限原 owner，继任者只能消费已完成依赖。经负责人在线程中授权继续，改为 fresh run 复核原执行证据并重跑可只读复现的 T01 检查、写入下方机器可读完成记录，再由 `prepare-ticket 450 T02` 的依赖校验判定 T01 |
| T01 完成判定（fresh run 复核） | PASS | 基线副本上 forward apply --check 通过（基线 `07c78311…`）；HEAD 上 reverse --check 通过、全文 `3dda6096…` 等于 spec；bundle `--verify` VERIFIED 1.24.2；31 条既有 release 字节前缀与 members 等非 release 键均同 change_base；`git diff --check c14a86d4..HEAD` 无输出；check-change-documents 两项 PASS。重读治理 diff，引言“不增加确认点、流程状态或验证硬门”保留，四类关注点为提示。记录中 AC 的 PASS 仅指 T01 负责的部分，AC-2/3/4 的独立审议由 T02 cross-provider 承担 |
| T02 prepare-ticket | PASS | 完成记录提交 `97b5f2ee2fd72b24c77b717ebb40dc9cfdfcfa60` 后 `prepare-ticket 450 T02 --provider claude` 返回 status=prepared，T01 依赖校验通过，ticket_base `97b5f2ee…`，初始三类状态为空 |
| `bash codex/tools/usage-bundle.sh --build <本票新建的隔离目录>` | PASS | 本会话 scratchpad 新建 `export-450-Utxz/out`，输出 BUILT 1.24.2 sha256:8db2e495…；`project/{.agents,.claude,.cursor}/skills/aisoft-platform/references/engineering-principles.md` 三份与源码 `cmp` 字节相同，SHA-256 均 `3dda6096…`。只是隔离导出，不是安装 |
| `AISOFT_USAGE_BASELINE_REF=c14a86d4ad0d1fd5938ab31343f8d72acd486a71 LC_ALL=C bash codex/tests/smoke.sh` | PASS | 在 `db32606ed67317dc35bbaa30c5fcb5e005a54a4f` 上 rc=0，末行 “Codex platform static smoke checks passed.”，日志 1134 行（本会话 scratchpad `smoke-db32606e.log`，sha256 `2d703055…`），无 FAIL/ERROR 行。其中 `usage-bundle.sh --verify` 与 `test-usage-bundle: PASS` 已执行，后者含重复发版拒绝、历史改写检测、`--baseline-ref` 已发布版本不可变及成员摘要漂移拒绝等负向夹具。日志另有一行 “test-aisoft-entry: platform checkout denied by sandbox-exec”，属该测试的环境说明，未计入通过项。4efe9516 上的一次提前运行因 HEAD 移动被主动中止，不计 |
| 推理强度偏离的负责人裁决 | 已记录 | R1 P2 后，实现方在本票线程给出两个选项，推荐项写明“切到更高强度继续，T01 跑在 medium 的事实照实保留，并在 override_reason 里写明 T01 以 medium 执行、经负责人认可”，负责人回复“推荐”选择该项；随后原话“我已经将模型调整为 xhigh，我认为已经足够，不需要 max”，并说明修改的是当前会话。本会话 15:23 与 15:24 两次用 `get_session self` 读回 effort 仍为 medium，T02 实际强度因此记为未核实。裁决与该事实写入 summary `override_reason`（front matter 与判级块两处）；路由卡未改，`resolve-route 450 --provider claude` differences={}，`check-change-documents` 两项 PASS，`classify --verify 450` 仍为 projected，`prepare-ticket 450 T02 --resume` 仍为 prepared |
| 完整 smoke（最新候选） | PASS | 同一命令在 `5c62da93751b3747c872bfb70bae2d48992b70fd` 上 rc=0，末行 “Codex platform static smoke checks passed.”，日志 1134 行（scratchpad `smoke-5c62da93.log`，sha256 `3f72710e…`），无 FAIL/ERROR 行，`test-usage-bundle: PASS`，同一 sandbox-exec 说明行。`540ae18f` 上的一次运行因修订 R2 时工作树变动被主动中止，不计 |
| `bash codex/tools/aisoft classify --apply 450` / `--verify 450` | PASS | apply 返回 result=no-op（标签已是 platform / complex）；独立 verify 返回 result=projected |
| 实际补丁最终 cross-provider 审核 | R1、R2 FAIL，R3 PASS（`5c62da93`） | 见交叉审查表；前述方案审核不能替代。本证据提交之后的 diff 另行审核，结果记入 PR 正文与 pr_url 回填提交 |
| 远端 required CI | NOT RUN | 未 push / PR |
| installed / 项目 adopt / live | NOT RUN | 不在本次范围 |

## 机器可读执行记录

`ticket_execution` 读取的唯一记录；T01 由 fresh run 判定完成。

```aisoft-execution
{
  "change_base": "c14a86d4ad0d1fd5938ab31343f8d72acd486a71",
  "tickets": {
    "T01": {
      "start": {
        "identity": {
          "issue": 450,
          "branch": "change/450-engineering-principles",
          "owner": "f2cce2e4-3bb8-4160-87a4-9b9a1a5ee664",
          "worktree": "/private/tmp/issue-450-engineering-principles",
          "provider": "claude",
          "plan_path": "docs/changes/450-engineering-principles/plan-engineering-principles-261116.md",
          "semantic_hash": "3b445c7b8a6c12f8807ca45328b2911dde272778c32a8512b236042b2a42058d"
        },
        "ticket": "T01",
        "ticket_base": "4d4321dee233dc55116539f77799817595108167",
        "raw_plan_sha256": "ad8a0eee555002734814d1bee82e9e235c42fab6530d753dc49e00e1a8f579ec",
        "scope": [
          "docs/changes/450-engineering-principles/summary-engineering-principles-261116.md",
          "docs/changes/450-engineering-principles/spec-engineering-principles-261116.md",
          "docs/changes/450-engineering-principles/plan-engineering-principles-261116.md",
          "docs/changes/450-engineering-principles/verification-engineering-principles-261116.md",
          "docs/changes/450-engineering-principles/proposals/engineering-principles.patch",
          "skills/aisoft-platform/references/engineering-principles.md",
          "usage/bundle.json",
          "docs/governance/review-evidence-index.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/450/issue-450-def31ffb46b2f99d-3b445c7b8a6c12f8.md",
        "scratch": ".superpowers/sdd/issue-450-def31ffb46b2f99d-3b445c7b8a6c12f8",
        "policy_sha256": "850b91ae60b311eb6a48e52f372d0bfe1945ba60d9ff5da7bc540ff59183885d",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, executing-plans, verification-before-completion",
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
      "base": "4d4321dee233dc55116539f77799817595108167",
      "head": "4efe9516dad7b5366ec8fa4c08f07363f0a1f5c1",
      "semantic_hash": "3b445c7b8a6c12f8807ca45328b2911dde272778c32a8512b236042b2a42058d",
      "validation_sha256": "26fd8b6e32e1c10f5a7e0c6611e42dc1c7a50794de6bd10a022e987dc26176d1",
      "ac": {
        "AC-1": "PASS",
        "AC-2": "PASS",
        "AC-3": "PASS",
        "AC-4": "PASS",
        "AC-5": "PASS",
        "AC-6": "PASS"
      },
      "checks": [
        {
          "command": "git apply --check --unidiff-zero docs/changes/450-engineering-principles/proposals/engineering-principles.patch",
          "result": "PASS",
          "evidence": "T01 owner f2cce2e4 ran before applying (exit=0); fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: re-ran against baseline copy of engineering-principles.md (sha256 07c78311…f456) exit=0"
        },
        {
          "command": "git apply --reverse --check --unidiff-zero docs/changes/450-engineering-principles/proposals/engineering-principles.patch",
          "result": "PASS",
          "evidence": "fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: exit=0 on HEAD 4efe9516; full-file sha256 3dda6096…1d9d1811 equals spec"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --release 1.24.2 --today <实施日> --compatibility patch --notes '细化共享工程原则的结果验证、证据来源与重复问题改进，不新增流程硬门（#450）'",
          "result": "PASS",
          "evidence": "T01 owner f2cce2e4 ran with --today 2026-11-16: RELEASED sha256:8db2e495…; fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: last release 1.24.2/patch/2026-11-16, prior 31 releases byte-equal prefix, non-release keys incl. members equal to c14a86d4"
        },
        {
          "command": "bash codex/tools/usage-bundle.sh --verify --baseline-ref c14a86d4ad0d1fd5938ab31343f8d72acd486a71",
          "result": "PASS",
          "evidence": "fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: VERIFIED 1.24.2 sha256:8db2e4951600ceb74210540df1e72fe9c2d285c518b9ce3dbe54c35036733777 exit=0"
        },
        {
          "command": "git diff --check",
          "result": "PASS",
          "evidence": "fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: git diff --check c14a86d4..4efe9516 no output exit=0"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain",
          "result": "PASS",
          "evidence": "fresh run b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86 2026-11-16: change-documents PASS, change-pr-url PASS exit=0"
        }
      ]
    }
  }
}
```

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 全文 `3dda6096…` 等于 spec，reverse --check 通过；实现方与 Codex R1 各自独立复现 |
| AC-2 | PASS（文本审议） | 实现方自审与 Codex R1 独立审议一致：四类为提示，无新增文档 / 轮次 / 工具义务；route、模板、execution-adapter 未改 |
| AC-3 | PASS（文本审议） | 同上，Codex R1 独立判定；不是模型行为实验 |
| AC-4 | PASS（文本审议） | 同上；不宣称效果已改善 |
| AC-5 | PASS | bundle verify 与历史 / members 比对由实现方与 Codex R1 各自复现；三端隔离导出为实现方结果，R1 未独立重建；真实安装与采用 NOT RUN |
| AC-6 | 未完成 | 范围、文档预检、完整 smoke、classify 读回已 PASS；治理 STOP / fresh run 已执行；cross-provider R1、R2 FAIL 经处置后 R3 PASS（`5c62da93`）；同一 HEAD 完整 smoke PASS；远端 required CI 待 PR 后运行，故整票 AC-6 待 CI 才算闭环 |

## 交叉审查

本表只记录实际补丁的最终候选审核，方案审核另列在上节。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| R1 | Claude Code（T01 `f2cce2e4-…`，fresh run `b2a67dee-…`，均 Opus 5.5 / medium） | Codex，Herdr 空间「AISoftPlatform #450 实施审核」terminal `t41`，`codex -m gpt-6-astra -c model_reasoning_effort="high" -s read-only -a never`，状态栏显示 GPT-6-Astra high；`hc wait` 返回 ended / done / turn 1 | BASE `c14a86d4…` .. HEAD `db32606ed67317dc35bbaa30c5fcb5e005a54a4f` | FAIL | P2：实施推理强度 medium 低于路由 max，summary `override_reason` 为空；已由负责人裁决并写入 override_reason，见执行结果。P3：本文件准备期表述与现状矛盾，已在后续提交修正。AC-1..5 判 PASS（AC-5 导出部分为实现方结果），AC-6 未完成；审核者未写文件 |
| R2 | 同 R1 | 同一 Herdr terminal `t41` 以 `hc send` 复用只读会话，`hc wait` 返回 ended / done / turn 2 | 增量 `db32606e..540ae18fe7afd74dc945c7c664b1ad9f9f00bb18` 及整批 `c14a86d4..540ae18f` | FAIL | P2：override_reason 中“T01 medium 经负责人认可”被认为缺少引用的裁决原文；处置为补引推荐选项原文与负责人“推荐”的选择，并把历史偏差与后续 xhigh 覆盖分开写。P3：执行表仍写最终审核 NOT RUN，已改为 R1 / R2 已执行 FAIL。R1 的 P3 判为基本闭合；原则、bundle、范围复核通过；审核者未写文件 |
| R3 | 同 R1 | 同一 terminal `t41`，`hc wait` 返回 ended / done / turn 3 | 增量 `540ae18f..5c62da93751b3747c872bfb70bae2d48992b70fd` 及整批 `c14a86d4..5c62da93` | PASS | R2 的 P2 判为闭合（推荐选项原文与负责人“推荐”构成直接依据，历史偏差与 xhigh 覆盖分开记录，未把 T02 强度写成已核实）；P3 闭合。新提 1 条非阻断 P3：AC-6 与遗留项仍写“待 R2”，已在本证据提交改正。原则、bundle、范围复核通过；审核者未写文件，报告称无法直接看到自身型号与强度 |
| R4 | 同 R1 | 同一 terminal `t41`，`hc wait` 返回 ended / done / turn 4 | 证据增量 `5c62da93..8780792d630c3c77cbbd7c8cd54e40cc31b13b98` 及整批 | FAIL | P2：plan 把 T02 标 done 却无机器可读完成记录，离线 `completed()` 复现 “T02: completion requires commit and validation evidence”。处置：T02 改回 in-progress，执行证据行写明原因。其余记录判为准确，原则、bundle、范围复核通过 |

## 遗留风险与未完成项

- T01 已完成；T02 本地候选已形成（plan 状态 in-progress），停在确认点 2（AWAITING_PR_CONFIRMATION）；push、PR、远端 required CI `CI / verify (pull_request)`、人工合并均未发生。T02 本会话实际推理强度未能读回为 xhigh，如实保留。
- 验证与来源限制、安装 / 采用边界见 spec；任何未运行项保持 NOT RUN。
- 治理应用后的 fresh run 已由新会话 `b2a67dee-…` 执行。runtime 依赖校验只证明记录、摘要、身份与提交关系一致，不能独立证明历史命令确实执行。
- Matt triage 标签未投影：当前安装的 broker 仅提供 lifecycle / classification / project-extension 标签写入，没有 triage 维度写入操作。本次不绕过 typed 边界或升级 broker；不得声称已写入 triage/ready-for-agent。该限制不影响已完成的本地文档与现行路由预检。
