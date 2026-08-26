---
issue: 208
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/208
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - security
  - shared-core
  - ci
depends_on:
  - 207
status: approved
branch: change/208-routine-pr-auto-merge
created: 2026-08-26
updated: 2026-08-26
---

# Routine PR 受控自动合并规格

## 目标与原因

把日常交互式 Issue 会话的默认人工确认收敛为两个：

1. 本地实现与验证完成后，确认提交唯一最终 PR；若为 routine small 候选，该确认必须明确说明
   “当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，允许受控自动合并”。
2. merge、终态核对、文档检查与 worktree/本地分支清理完成后，确认归档会话。

complex/major、阶段或里程碑完结、安全、数据、共享核心、CI/制品/部署/回滚和平台治理继续
人工合并。`approved` 仍只启动 Development Loop；PR merge 不传递任何部署授权。

## Acceptance criteria

- [ ] AC-1：Codex 与 Claude 的 Issue 会话在 push/create PR 前输出同一份 PR candidate handoff；
  routine small 的确认文本明确包含“required CI 全绿后允许受控自动合并”，manual 路径不包含。
- [ ] AC-2：确认记录绑定 exact Issue、`change/N-slug` 与 merge policy，不绑定确认时 SHA；范围内
  CI 修复无需第三次确认。merge 调用必须携带并钉住最终 40 位 lowercase head SHA。
- [ ] AC-3：routine 候选必须同时满足 `effective_complexity=small`、`contract_effect` 为
  `restore|unchanged`、范围局部可逆、无 forced risk、非阶段/里程碑完结、repository 显式启用且
  required contexts 非空。分类仍只投影现有 `complexity/small|complex`，不得新增 merge-policy label。
- [ ] AC-4：功能新增/变化、major、阶段完结、`type/security`、`type/data`、共享核心、跨模块/服务、
  CI/制品/部署/健康检查/备份/回滚、Agent/平台治理一律形成 `complexity/complex` 并走 manual；
  #208 自身必须被测试证明不可自动合并。
- [ ] AC-5：新增独立 per-project routine merger：非 site-admin、不是 human admin、platform manager、
  project agent 或 shared bot；只对 exact repository 有最小 Write/merge 能力，禁止 ordinary Git 和
  cross-project write。project agent/provider 继续没有 merge credential 或 merge permission。
- [ ] AC-6：host-access broker 只新增一个 `gitea.pull.merge.routine` typed operation，调用方只传
  PR number 与 exact head SHA；owner/repo/base/identity/merge method/delete-branch/force policy 全由
  strict manifest 派生，禁止 URL、任意 ref/payload、force、scheduled merge 或 deploy 参数。
- [ ] AC-7：同一次 broker operation 在 POST 前按固定顺序 fresh 验证：submit authorization；
  summary/Gitea small 合同；exact Issue/branch/docs/PR 与唯一开放 PR；open/unmerged、base=`main`；
  PR head 等于 supplied SHA；live protection 与 manifest；required contexts 非空且对该 SHA 全绿；
  无有效拒绝 review；全部 `depends_on` closed 且为 `completed|deployed`；最终 diff 无范围扩张。
- [ ] AC-8：merge 固定调用 Gitea `POST /repos/{owner}/{repo}/pulls/{index}/merge`，请求为
  `do=merge`、`head_commit_id=<exact SHA>`、`force_merge=false`、
  `merge_when_checks_succeed=false`、`delete_branch_after_merge=true`；HEAD 漂移必须由 Gitea/本地
  双层校验拒绝，不能依赖 server-side 延迟 auto-merge。
- [ ] AC-9：每个 hard gate 失败只返回一个稳定 error code/reason，零 merge POST、零权限降级、
  零自动 fallback；CI failure、head drift、dependency block、rejected review 与 scope expansion 均有回归。
- [ ] AC-10：routine merge 成功只返回 merge receipt，不调用 deploy、不写 `deployed`、不启用
  production action。session 随后自动执行 deterministic terminal plan/apply、change document check 和
  worktree/local branch cleanup，完成后才请求第二个“归档”确认。
- [ ] AC-11：manual 路径在 PR 提交确认后继续处理 CI，但到 `READY_FOR_REVIEW` 停止等人合并；
  complex/major 和任一 routine hard-gate failure 不得自动转成拥有更宽权限的合并路径。
- [ ] AC-12：governance-only 合同提交与 runtime 实现由两个 fresh execution 分开；后者重读新
  `AGENTS.md` 后才修改 manifests、Controller、broker 或 CI/shell runtime。
- [ ] AC-13：相关 Python 单测、`bash codex/tests/smoke.sh`、所有修改 shell 的 `bash -n` 与可用时
  ShellCheck 真实通过；source/installed/live 分层记录，未安装、未 apply、未部署保持 `NOT RUN`/GAP。

## 接口、数据与兼容性影响

### 会话和 Controller

- 新增持久阶段/结果 `AWAITING_PR_CONFIRMATION`；在此阶段重复 poll 不再调用 provider 或创建 PR。
- 明确确认后才创建 PR。确认事实持久化 exact Issue、branch 和 `manual|routine-auto` policy；
  `routine-auto` 只有 AC-3 的候选可写入，PR body 带唯一、机器可读且人可读的授权 marker。
- manual PR 继续以 `READY_FOR_REVIEW` 结束；routine merge 成功返回 `AUTO_MERGED` receipt，由
  `issue-session-flow` 完成终态和清理后进入待归档。

### Governance 与身份

- `gitea-governance/v1` 增加固定 `routine_merge_agent_policy`，repository 条目显式声明
  `routine_auto_merge_enabled` 与 `routine_merge_agent`；无 required contexts 的仓库不得启用。
- 启用仓库的 `main` merge allowlist 精确为 human + 该仓 routine merger；未启用仓库仍只有 human。
- host-access identity binding 使用固定 protected-file 路径
  `projects/{project_id}/routine-merge-agent.token`，不把 token 放入仓库、argv、状态或日志。
- account/bootstrap、governance apply 与 live protection 变更仍需 merged source、独立授权和 read-back；
  本 Issue 的开发步骤只实现 source，不执行 live apply。

### Broker hard gate

- broker 必须读取 PR、Issue/labels、summary at final head、all/open PR inventory、protection、逐 context
  commit status、reviews、dependencies 和 PR files；分页有固定上限，未知/缺失 schema 一律失败。
- “无范围扩张”以最终 head 的完整 PR diff 加当前 small-path/forced-risk policy 重算，不信任 provider
  自述或旧 Controller cache；确认后允许的 CI 修复仍须通过相同 scope gate。
- hard gate 固定顺序，返回第一个失败码；merge 前最后一次重读 PR head，再把同一 SHA 交给 Gitea
  `head_commit_id`，关闭 TOCTOU 窗口。

### 兼容性

- 不新增 lifecycle/complexity/triage 标签；`pr-open` 同时覆盖 manual 和 routine-auto PR。
- 没有新 repository opt-in、credential 或 live protection 时，routine merge fail closed，manual 行为保留。
- 既有 legacy `change/N` 只读兼容不扩大；新 routine auto 只接受 readable `change/N-slug`。

本规格授权 governance-only fresh step 修改：

- `AGENTS.md`、`README.md`、`03-Issue-Spec-Plan与单闸门开发流程.md`、
  `04-Agent编排与定时任务.md`、`08-Codex双工具共存与实施.md`、
  `09-v3平台简化与Loop-Engineering文档改造规划.md`
- `codex/global-AGENTS.md`、`templates/project/AGENTS.md`、`templates/docs/agents/issue-tracker.md`
- `codex/skills/issue-session-flow/SKILL.md`、`codex/skills/aisoft-matt-workflow/SKILL.md`、
  `codex/skills/gitea-development-loop/SKILL.md`、`skill-for-codex/SKILL.md` 及其相关 references
- `skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`

该步骤不得修改 manifests、Python runtime、shell runtime 或 tests；提交后必须停止。

本规格授权后续 fresh runtime step 修改：

- `codex/config/gitea-governance.json`、`codex/config/host-access-broker.json`、
  `codex/config/gitea-labels.json`
- `codex/runtime/aisoft_gitea_governance/`、`codex/runtime/aisoft_host_access/`、
  `codex/runtime/aisoft_loop/` 中实现本规格所需的 contract/controller/state/CLI/broker/reconcile surface
- 对应 `codex/runtime/tests/`、`codex/tests/`、安装/bootstrap shell 与 `codex/tests/smoke.sh`
- 本 Issue 映射的 verification/summary/plan 收口状态。

## 风险与回滚约束

- Source rollback 是整体 revert 本 Issue 唯一 PR；live 未 apply 时无需 live rollback。
- 后续若独立授权 live apply，回滚必须先禁用 repository `routine_auto_merge_enabled`、恢复 human-only
  merge allowlist、撤销该仓 routine merger collaborator/token，再读回 main push/force/merge 边界。
- 任何身份、protection、required context 或 installed-byte GAP 都阻止 routine merge，不得临时使用 admin。
- 自动 merge 不包含部署、secret provision、live apply 或 production 授权。

## 非目标

- 不自动合并 #208 或任何 complex/major/阶段完结/强制风险变更。
- 不取消 protected `main`、required CI、review、可回滚、唯一 PR 或 readable naming 合同。
- 不让 provider、project agent、platform manager、shared bot 或 site admin 承担 routine merge。
- 不启用 Gitea server-side “checks success later自动合并”，不允许 force merge。
- 不在本 Issue 安装 runtime/skills、provision credential、apply live protection、部署或归档当前任务。

## 未决问题

无。
