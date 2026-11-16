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
| T01 治理应用与 bundle release | NOT RUN | 尚未开始 |
| T02 fresh run、完整 smoke、负向夹具、隔离三端导出 | NOT RUN | 尚未开始 |
| 实际补丁最终 cross-provider 审核 | NOT RUN | 前述方案审核不能替代 |
| 远端 required CI | NOT RUN | 未 push / PR |
| installed / 项目 adopt / live | NOT RUN | 不在本次范围 |

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
