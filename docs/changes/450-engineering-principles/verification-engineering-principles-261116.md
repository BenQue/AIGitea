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
- 本记录负责 AC-1 至 AC-6；准备阶段通过不代表这些实施 AC 已通过。实际 candidate_head / ticket_base 待执行时记录。
- 本轮负责人要求先补齐 spec / plan，当前没有应用原则 patch、生成新 release、安装或执行项目采用。

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
| fresh run 接管 | PASS | 新 Claude Code 会话 `b2a67dee-88df-4a7a-baa1-e1a2b5eb5a86`（Opus 5.5；本会话无法读取实际推理强度，记为未核实，路由要求 frontier/max）。核对 branch / HEAD `4efe9516…` / 工作树干净，重读交接文件、spec、plan、verification、治理 diff 与 issue-session-flow 技能；`claim-worktree --takeover` 返回 taken-over，owner 由 `f2cce2e4-…` 改为本会话 |
| `prepare-ticket 450 T01 --provider claude --resume` | REFUSED（按设计） | 返回 resume identity/semantic contract mismatch。核对源码：plan semantic_hash 在三个提交均为 `3b445c7b…`，差异仅在 owner；runtime 规定未完成票的 resume 只限原 owner，继任者只能消费已完成依赖。经负责人在线程中授权继续，改为 fresh run 复跑 T01 检查、写入下方机器可读完成记录，再由 `prepare-ticket 450 T02` 的依赖校验判定 T01 |
| T01 完成判定（fresh run 复跑） | PASS | 基线副本上 forward apply --check 通过（基线 `07c78311…`）；HEAD 上 reverse --check 通过、全文 `3dda6096…` 等于 spec；bundle `--verify` VERIFIED 1.24.2；31 条既有 release 字节前缀与 members 等非 release 键均同 change_base；`git diff --check c14a86d4..HEAD` 无输出；check-change-documents 两项 PASS。重读治理 diff，引言“不增加确认点、流程状态或验证硬门”保留，四类关注点为提示。记录中 AC 的 PASS 仅指 T01 负责的部分，AC-2/3/4 的独立审议由 T02 cross-provider 承担 |
| T02 prepare-ticket | PASS | 完成记录提交 `97b5f2ee2fd72b24c77b717ebb40dc9cfdfcfa60` 后 `prepare-ticket 450 T02 --provider claude` 返回 status=prepared，T01 依赖校验通过，ticket_base `97b5f2ee…`，初始三类状态为空 |
| `bash codex/tools/usage-bundle.sh --build <本票新建的隔离目录>` | PASS | 本会话 scratchpad 新建 `export-450-Utxz/out`，输出 BUILT 1.24.2 sha256:8db2e495…；`project/{.agents,.claude,.cursor}/skills/aisoft-platform/references/engineering-principles.md` 三份与源码 `cmp` 字节相同，SHA-256 均 `3dda6096…`。只是隔离导出，不是安装 |
| 完整 smoke、负向夹具 | NOT RUN | 在 candidate_head 上运行，结果待记录（4efe9516 上的一次提前运行因 HEAD 移动被主动中止，不计） |
| 实际补丁最终 cross-provider 审核 | NOT RUN | 前述方案审核不能替代 |
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
| AC-1 | NOT RUN | 仅冻结候选，实际原则未改 |
| AC-2 | NOT RUN | 方案已有审核，实施 diff 尚不存在 |
| AC-3 | NOT RUN | 同上 |
| AC-4 | NOT RUN | 同上；不宣称效果已改善 |
| AC-5 | NOT RUN | 未 release / build |
| AC-6 | NOT RUN | 仅合同准备，后续验证与最终审核未做 |

## 交叉审查

本表只记录实际补丁的最终候选审核，方案审核另列在上节。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 待执行 | Claude Code | Codex（Herdr 可见独立审核） | 待执行时固定 | NOT RUN | 无实际补丁候选 |

## 遗留风险与未完成项

- 后续仍须完成 T01 / T02 及既有最终 PR 确认，不能把本轮 spec / plan 完成写成实施验收通过。
- 验证与来源限制、安装 / 采用边界见 spec；任何未运行项保持 NOT RUN。
- 治理应用后需真实 fresh run，不能以同一进程继续调用工具替代。
- Matt triage 标签未投影：当前安装的 broker 仅提供 lifecycle / classification / project-extension 标签写入，没有 triage 维度写入操作。本次不绕过 typed 边界或升级 broker；不得声称已写入 triage/ready-for-agent。该限制不影响已完成的本地文档与现行路由预检。
