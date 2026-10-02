---
issue: 318
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/318
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/318-provider-skill-parity
created: 2026-10-02
updated: 2026-10-02
---

# Spec：修齐 Codex/Claude 技能执行合同

## 目标与原因

把 Claude 已明确的既有治理步骤同步到 Codex，并修正两侧共享的旧接入说明。只恢复平台已有合同，不新建开发方法，不变更确定性 runtime。源码基线 `480d1d2`，完整审查见 verification。

## Acceptance criteria

- [x] AC-1：Codex 自主列表明确区分两确认点；第一点仅批准合同内本地工作，push/唯一最终 PR 需第二点，routine-auto 授权仍在第二点。
- [x] AC-2：Codex 明确 `apply-classification-labels.sh --verify N` 必须读回 `projected`；closed Issue 不补写；收尾 dry-run 核对 exact merge 的 `commits`/`commit`，apply 只用返回 `pinned`，禁止复用浮动 `--range`；终态交给工具读取 `required_docs` 与 `deployment_lifecycle`。
- [x] AC-3：Codex 区分 Controller 自动 backfill 与 Mac 交互显式 `backfill-pr-url`；只有 summary 携带 `pr_url`，PR 创建前为空，创建后单 summary commit 并 broker push。
- [x] AC-4：共享 runbook 修正第二确认点授权、manifest 终态判据、所选 provider 的独立验收；08 补齐 `claim-worktree`、`AISOFT_SESSION_ID`、`pushed_head`、`scan-worktrees`。
- [x] AC-5：新增关键指导语义的负向合同测试，在旧 source 上显式失败、提案 source 上通过；既有 provider parity 与完整 smoke 通过，环境/fixture 阻塞如实记录，不伪称全绿。
- [ ] AC-6：本 Issue 独立 worktree/branch 与单写者归属有效，治理源应用为独立受控步骤；source 验证与提交前用户确认遵守现行规则。合并后从 exact main 更新两侧受管技能并读回 CLEAN，fresh run 采用新指导。

## 精确授权目标（确认此 spec 后生效）

1. `codex/skills/issue-session-flow/SKILL.md`
2. `skill-for-codex/SKILL.md`
3. `skill-for-codex/references/onboarding-runbook.md`
4. `08-双工具共存与实施.md`
5. `codex/runtime/tests/test_routine_merge.py`：只增加 SessionContractTests；不修改 runtime 行为。

修订以 `proposals/provider-skill-parity.patch.gz` 为可审阅候选；其通过 apply-check 仅证明可应用，不代表已批准或已安装。Claude 会话 skill 作为对照，当前规则无需重写。治理指导应用后停止该受控步骤，fresh run 再读取指导并完成验证/候选；不会改本轮 AGENTS.md。

## 接口、数据与兼容性影响

无 schema/API/CLI 接口变更。Controller 的自动 backfill、broker 单写者闸门、判级 projector 与终态工具按现有接口调用。保留工具原生 UI、配置、认证与 Claude-owned plugins 的独立性。

## 风险与回滚约束

source 通过原子 commit revert/PR 回滚；合并后技能安装保留版本化源与安装前目录备份，重装已确认版本并验证 CLEAN。本次已完成的稳定源安装备份为 `/private/tmp/aisoft-managed-skills-before-20261002.tar.gz`；只包含平台受管技能。不得把 source parity 写成真实模型/业务/公司部署验收。

## 非目标

AGENTS.md/CLAUDE.md 修改、runtime/controller 变更、CI workflow、权限/凭据、broker 重装、PAT 轮换、provider/timer 启用、部署、合并或下游项目变更均不在范围。后续新项目各自通过 onboarding/project-align 与 provider acceptance，不能继承中央 PASS。完整 smoke 暴露的独立 fixture 问题另行记录，不顺手扩大本 Issue。

## 未决问题

技术方向无未决；用户于 2026-10-02 已确认合同/启动。最终 PR Policy 固定 manual，提交确认仍独立。

## 当前验收边界

AC-1 至 AC-5 的 source/local 验证已通过，记录于 mapped verification；完整 smoke 的 PASS 限定 LC_ALL=C。AC-6 本地 branch/claim、受控 T01 与 fresh T02 已通过，提交前确认、required CI、人工合并及合并后 exact-main 安装/fresh adoption 仍待 T03，不把本地 PASS 写成最终交付完成。
