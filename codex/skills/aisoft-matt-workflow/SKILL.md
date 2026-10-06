---
name: aisoft-matt-workflow
description: Configure and run the complete Matt Pocock engineering workflow inside AISoftPlatform Gitea governance. Use during repository initialization or when dispatching triage, to-spec, to-tickets, and implement without weakening protected-main, contract, PR, CI, or deployment controls.
disable-model-invocation: true
---

# AISoftPlatform Matt workflow adapter

This skill adapts the complete vendored Matt skills to AISoftPlatform. It does not replace or edit their upstream
`SKILL.md` files.

## Repository initialization

1. Finish AISoftPlatform repository onboarding first: exact Gitea profile, protected `main`, required CI, project Agent
   permission gate and the 27-label manifest must all read back successfully.
2. Explicitly invoke `$setup-matt-pocock-skills` once. Select **Other** for the tracker and use the three files under
   `templates/docs/agents/` as the Gitea, triage and domain configuration.
3. Add the upstream skill's `## Agent skills` block only in the repository instruction file selected by that skill. If
   the current run is governed by that same file, produce a reviewable proposal and apply it in a separate authorized
   governance step.
4. Confirm `docs/agents/issue-tracker.md`, `triage-labels.md` and `domain.md` exist before the first Issue flow.

## Per-Issue flow

1. `$triage #N` — preserve Matt's complete verify/grill/brief flow. Mutate triage labels through the platform label
   projector; `ready-for-agent` never implies `approved`.
2. Run the platform analyzer. It validates one immutable slug and creates the exact `change/N-short-description`, `docs/changes/N-short-description/`, `issue-N-short-description` tuple plus mapped summary. Existing legacy names are discovered from evidence, never selected by a caller flag.
3. For production complex work, run `$to-spec #N`. Publish to the mapped `spec` file and keep lifecycle `spec-drafting`
   until the complete contract is validated. Development complex uses measurable Issue acceptance criteria and skips
   ceremonial spec/plan.
4. For production complex work, run `$to-tickets #N`. Publish the approved `Txx` vertical-slice dependency graph to
   the mapped `plan` file. Development complex uses synthetic `T01`. Default mode stays inside the parent Issue.
5. After contract validation sets `approved`, the Controller dispatches `$implement #N Txx` for one frontier ticket.
   The Agent owns tests, review and one or more atomic local commits; the Controller owns remote mutation.
6. Controller verification first produces the policy-specific final-PR candidate handoff and enters
   `AWAITING_PR_CONFIRMATION`. Only after explicit confirmation may it fast-forward push and create the one final PR
   with exact readable head, mapped summary and one `Closes #N` line, then follow required CI. Manual work ends at
   `READY_FOR_REVIEW`; eligible routine-small work may reach `AUTO_MERGED` only through the independent merger and
   final-head hard gates. Deployment is independent.

## #327 当前收缩合同（2026-10-05）

本票只交付保留 original/current remote tip 祖先关系的 main 整合、普通 FF、非法/并发漂移拒绝、required CI 与可恢复收尾。以 [#327 spec](../../../docs/changes/327-broker-ff-integration/spec-broker-ff-integration-261002.md) 的当前合同为准；T01/T04–T10 为历史治理步骤，原 FAIL/GAP/NOT RUN 保留。

Agent/provider 只追加本 Issue 的线性本地 commit。合格现有 Controller 可按合同整合；本票首次自举明确允许**负责人本人**用标准 Git 在原 owner worktree 临时保全/park WIP、构造 `[已核验 Issue tip, fresh manifest main]` 并留恢复证据，Agent 不代执行。它不再等待未交付 R02、root authority、OS observer 或 protected grant。仅无冲突标准整合；冲突停止并保留 stash/前态，不自动覆盖内容。

最终唯一 PR 的第二确认仍绑定 exact Issue/branch/manual。确认前不发表；确认后本票可由本人使用已绑定的普通 Git credential helper、经过本票测试的固定 pre-push guard 和 exact SHA 单 ref 普通 FF 完成首次发表，不调用旧 lease-force broker、不装 unmerged broker，Agent 不借此绕 broker。来源/DAG/tree/范围、R0/R/M/H、guard 执行和真实 readback 必须核对；main 禁直推/force、required CI、本人 manual merge 不变。实际首次发表/installed 验收未运行仍为 GAP/NOT RUN。

root authority、begin/verify、ES/kernel/signing、完整 OS/解释器闭包、scratch/resource 隔离及其 I01/I02/AC-9～11 延期，不作为本票当前 source 整合/PR 的前置；不宣称这些安全能力已交付，也不以本地 receipt/owner marker 证明不可伪造授权或同 UID 隔离。Mac/VM 安装均需 source 合并后另获授权。本轮仅治理文本与证据应用、校验、本地 commit 后 STOP；下一 fresh run 重读后才续 T02。

## Stable adapter interfaces

- Label projection: platform and Matt dimensions update independently while preserving unmanaged labels.
- Document resolution: use `python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`; never guess with a broad
  glob.
- Spec publication: update only the mapped `spec` document and link it from the existing Issue.
- Plan publication: update only the mapped `plan` document with `Txx`, `blocked_by`, AC and verification mappings.
- Ticket execution: include the exact Issue and ticket in the explicit `$implement` prompt; include spec/plan paths
  only when the route requires them.

The Matt skill, provider and project agent never merge or receive the routine merger credential. Never deploy,
rewrite history, force-push, or silently switch to a different tracker or repository.
