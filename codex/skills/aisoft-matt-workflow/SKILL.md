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
   permission gate and the 24-label manifest must all read back successfully.
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
3. For complex work, run `$to-spec #N`. Publish to the mapped `spec` file and keep lifecycle `spec-drafting` until the
   complete contract is validated.
4. Run `$to-tickets #N`. Publish the approved `Txx` vertical-slice dependency graph to the mapped `plan` file. Default
   mode stays inside the parent Issue.
5. After contract validation sets `approved`, the Controller dispatches `$implement #N Txx` for one frontier ticket.
   The Agent owns tests, review and one or more atomic local commits; the Controller owns remote mutation.
6. Controller verification, fast-forward push, one final PR with exact readable head, mapped summary and one `Closes #N` line, then required CI follow. Stop at the human merge
   gate. Deployment is independent.

## Stable adapter interfaces

- Label projection: platform and Matt dimensions update independently while preserving unmanaged labels.
- Document resolution: use `python3 -m aisoft_loop.cli resolve-documents N --repo <checkout>`; never guess with a broad
  glob.
- Spec publication: update only the mapped `spec` document and link it from the existing Issue.
- Plan publication: update only the mapped `plan` document with `Txx`, `blocked_by`, AC and verification mappings.
- Ticket execution: include exact Issue, ticket, spec and plan paths in the explicit `$implement` prompt.

Never merge, deploy, rewrite history, force-push, or silently switch to a different tracker or repository.
