# AISoft Platform · VM Codex Global Guidance v3

You run as the dedicated `coder` user for the AISoft Gitea delivery platform.

## Authoritative documentation

Read `/mnt/mac/Users/benque/Documents/AISoftPlatform/README.md`, then the relevant numbered document. Read `03` for Issue/spec/plan, `04` for Development Loop, `02` and `06` for deployments/incidents, and `08` for Codex-first validation.

## Non-negotiable rules

- Treat every change as an Issue linked to `change/N` and `docs/changes/N/00-summary.md`.
- Require an explicit project profile before any repository operation. Never infer the owner, repository, clone, state directory, ports, or deployment contract from rsDesign or another example.
- Treat one `type/*` label as an Issue-author input that AI validates against evidence, `complexity/*` as the AI's effective-complexity output, and the seven unprefixed labels as lifecycle state. Keep these dimensions separate.
- Classify product-contract effect before routing: restore/unchanged may be small; add/change and every forced risk are complex; unclear evidence requires human triage without a complexity label.
- Require clear Issue acceptance criteria for small work and complete `01-spec.md` plus `02-plan.md` for complex work.
- Treat `approved` as a Loop start signal, never as permission to merge or deploy.
- Keep final PR merge as the only delivery gate. Never push directly to protected `main` or merge a PR.
- Keep the accepted contract immutable during implementation. Escalate conflicts, scope expansion, destructive migration, security/permission/architecture decisions, and direct production changes.
- Let the Loop repair ordinary compile, lint, type, test, build, browser, and CI failures. Do not weaken validation or hide errors.
- Never print tokens, passwords, `.env`, auth files, agent environment files, or Git credentials.
- Keep Claude and Codex credentials independent. Share the outer controller, verifier, labels, and terminal-state contract.
- AI may help design and execute first deployments in development/test for applications that actually deploy. Documentation-only platform repositories do not need an application deployment flow. Production runs only pre-validated artifacts and scripts; AI never generates or executes ad hoc production commands.
- Report observed, changed, verified, and pending separately. Never claim an unrun test passed.

## Skill routing

- Use `$aisoft-platform` for the platform contract and onboarding.
- Use `$gitea-analyze-change` for read-only Issue analysis.
- Use `$gitea-spec-plan` for complex document-only planning.
- Use `$gitea-development-loop` for bounded implement-verify-repair iterations.
- Use `$gitea-implement-change` only for one controller-assigned implementation pass.
- Use `$gitea-platform-ops` for diagnostics, first non-production deployment, incident evidence, and rollback planning.

The shared v3 Codex Loop candidate has synthetic and one real complex pilot evidence, but each project profile remains disabled until that project's acceptance matrix passes. Keep `IMPLEMENT_PROVIDER=none` during documentation, skill work, and initial profile setup.
