# AISoft Platform · VM Codex Global Guidance v3

You run as the dedicated `coder` user for the AISoft Gitea delivery platform.

## Authoritative documentation

Read `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/README.md`, then the relevant numbered document. Read `03` for Issue/spec/plan, `04` for Matt orchestration and the Development Loop, `02` and `06` for deployments/incidents, and `08` for provider-neutral validation. Resolve change documents from the mapped `summary` document's `documents` field; use legacy numeric basenames only for read compatibility.

## Non-negotiable rules

- Treat every change as an Issue linked to exact `change/N`, `docs/changes/N/`, and one final PR. New documents use `<role>-<short-slug>-<YYMMDD>.md`; the mapped `summary` is mandatory.
- Require an explicit project profile before any repository operation. Never infer the owner, repository, clone, state directory, ports, or deployment contract from rsDesign or another example.
- Treat one `type/*` label as an Issue-author input that AI validates against evidence, `complexity/*` as the AI's effective-complexity output, and the eight unprefixed labels as lifecycle state. Keep these dimensions separate. Use `completed` only after merge when deployment is explicitly unnecessary; reserve `deployed` for deterministic deployment and verification.
- Classify product-contract effect before routing: restore/unchanged may be small; add/change and every forced risk are complex; unclear evidence requires human triage without a complexity label.
- Require clear Issue acceptance criteria and a mapped `summary` for small work, and mapped `spec` plus `plan` documents for complex work. `00-summary.md`, `01-spec.md`, `02-plan.md`, and `03-verification.md` are read-only legacy fallbacks for Issues before #57, never new-writer targets.
- Treat `approved` as a Loop start signal, never as permission to merge or deploy.
- Keep final PR merge as the only delivery gate. Never push directly to protected `main` or merge a PR.
- Treat `triage/ready-for-agent` as a Matt workflow state, never as a substitute for platform `approved`.
- Keep the accepted contract immutable during implementation. Escalate conflicts, scope expansion, destructive migration, security/permission/architecture decisions, and direct production changes.
- Let the Loop repair ordinary compile, lint, type, test, build, browser, and CI failures. Do not weaken validation or hide errors.
- The Agent may create local atomic commits only on exact `change/N` for the controller-assigned frontier `Txx`. Only the Controller may validate and fast-forward push that branch, create or update the single final PR, read CI, and project remote state. Only a human may merge; deployment requires separate authorization.
- Never force-push, silently install or update global skills, mutate live labels outside an accepted contract, auto-merge, or deploy without separate authorization.
- Never print tokens, passwords, `.env`, auth files, agent environment files, or Git credentials.
- Keep Claude and Codex credentials independent. Share the outer controller, verifier, labels, and terminal-state contract.
- AI may help design and execute first deployments in development/test for applications that actually deploy. Documentation-only platform repositories do not need an application deployment flow. Production runs only pre-validated artifacts and scripts; AI never generates or executes ad hoc production commands.
- Report observed, changed, verified, and pending separately. Never claim an unrun test passed.

## Skill routing

- Start repository onboarding with `$aisoft-matt-workflow` to verify the platform contract and boundaries. Then call `$setup-matt-pocock-skills`, select tracker `Other`, and use the existing `templates/docs/agents/issue-tracker.md`, `templates/docs/agents/triage-labels.md`, and `templates/docs/agents/domain.md`; do not create a second Gitea template set.
- Use `$triage #N` → `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx` as the primary per-Issue development path. Platform-approved small work may skip spec/plan only after triage, mapped summary, classification, and `approved` revalidation.
- Use `$aisoft-matt-workflow` as the platform adapter around the complete Matt skills. Keep `$gitea-analyze-change`, `$gitea-spec-plan`, `$gitea-development-loop`, and `$gitea-implement-change` only as compatibility adapters for Gitea labels, semantic document resolution/publication, Controller integration, and legacy callers; they do not define a competing development workflow.
- Keep `$gitea-platform-ops` independent for diagnostics, first non-production deployment, incident evidence, and rollback planning.

The shared v3 Codex Loop candidate has synthetic and one real complex pilot evidence, but each project profile remains disabled until that project's acceptance matrix passes. Keep `IMPLEMENT_PROVIDER=none` during documentation, skill work, and initial profile setup.
