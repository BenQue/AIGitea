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

## #327 保留历史的整合、FF 与生效边界

provider只追加本Issue线性本地commit，不创建mergecommit。只有外层Controller在批准合同、
本人worktree内可构造精确`[已核验Issue第一父链末端, fresh manifest main]`的可复算无冲突整合。
original/current remote tip必须始终为候选祖先；broker独立核验来源、完整DAG/tree/scope、fresh main、
本次exact head与传输remote tip，随后只普通FF发表。已发表rebase/amend、force/lease-force、
任意/跨Issue/octopus merge、自动解冲突与身份fallback均拒绝；仍要逐push核对真实remote与本次SHA锚。

#298 AC-5/AC-6与06/#136的历史重写口径由#327覆盖；历史文档保留，single-writer与回执义务保留。
新治理不证明runtime/installed支持；旧installed leased push包括首推均不可沿用。治理应用独立commit
后立即停止，fresh run重读后才可runtime。#327自身first PR只按其映射spec由负责人本人Gitea UI
发表到exactbranch、保留唯一manualPR；Agent不代UI、不directGit/API、不安装unmerged代码。
两机安装各需exact版本批准、完整前后bytes/mode/owner、realFF与rollback实证，#316授权不继承。
installed AC未闭合不把source merge/自动closed当实际完成、不提前cleanup/归档；原owner的人工PR更新
独立验收，不机械等待#327。

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
