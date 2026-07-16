---
name: aisoft-platform
description: Operate or onboard projects to the AISoft self-hosted Gitea delivery platform. Use for Issue analysis, small-or-complex routing, spec/plan contracts, Development Loop work, Codex/Claude provider coexistence, CI/deployment incidents, first non-production deployments, rollback planning, or production script boundaries.
---

# AISoft self-hosted delivery platform

## Read the contract

Read `README.md` and the relevant numbered document before acting. On Mac the authoritative root is `~/Documents/AISoftPlatform/`; on gitea-ci it is `/mnt/mac/Users/benque/Documents/AISoftPlatform/`.

Use:

- `03` for Issue, complexity, documents, labels, and the final PR gate.
- `04` for analyzer, Development Loop, verifier, terminal states, and provider adapters.
- `02` and `06` for deployments and incidents.
- `08` for Codex-first validation and later Claude parity.
- `09` for migration scope and unimplemented boundaries.

## Apply the v3 workflow

Select the target project explicitly before any Gitea or Git mutation. A project profile binds one profile name to `GITEA_URL`, `GITEA_OWNER`, `GITEA_REPO`, `AGENT_REPO_DIR`, provider selection, and a namespaced state/worktree root. Never infer the target repository from rsDesign or another example, and never reuse one project's state directory for another project.

Treat every request, defect, or platform change as a Gitea Issue `N` linked to `change/N`, `docs/changes/N/`, and a final PR with `Closes #N`.

- Require `00-summary.md` for every Issue.
- Treat `type/*` labels as Issue-author inputs describing what the change is; AI verifies or corrects one primary type from repository evidence.
- Treat `complexity/*` labels as AI classification outputs describing which path is required, never as an Issue-author override of contract impact or forced risk.
- Treat the seven unprefixed lifecycle labels as workflow state, separate from type and complexity.
- Classify contract impact first: `restore`/`unchanged` is only a `small` candidate, `add`/`change` is `complex`, and `unclear` requires human triage.
- Route a clear, local, reversible restore/unchanged change with no forced risk as `small`; route feature/functional behavior, schema/data, external contract, security, shared core, cross-module/service, CI/artifact/deployment/rollback, and Agent/platform governance changes as `complex`.
- Respect an explicit complex request, but never let a requested small value bypass AI validation or forced-complex rules.
- Require `01-spec.md` plus `02-plan.md` for effective complexity `complex`; do not create ceremonial spec/plan for validated `small` work.
- Require `03-verification.md` for deployment and migration work.
- Treat `approved` as permission to start the Development Loop, not permission to merge or deploy.
- Keep final PR merge as the only delivery gate.

Use the narrow skill for the task:

- `$gitea-analyze-change` for read-only evidence analysis and effective complexity classification.
- `$gitea-spec-plan` for complex document-only planning.
- `$gitea-development-loop` for repeated implement-verify-repair work.
- `$gitea-implement-change` only for one controller-bounded implementation pass.
- `$gitea-platform-ops` for platform evidence, first non-production deployment, incidents, and rollback.

## Preserve the Development Loop boundary

Let the Loop handle ordinary compile, lint, type, test, build, browser, and CI failures. Escalate contract conflicts, scope expansion, destructive migrations, new security/permission/architecture decisions, missing external dependencies, unreliable verification, three same-root-cause attempts, or configured limits.

Accept only `READY_FOR_REVIEW`, `NEEDS_HUMAN_DECISION`, `BLOCKED_EXTERNAL`, or `FAILED_LIMIT` as final states. Never describe unrun checks as passed.

## Preserve the deployment boundary

For an onboarded application that has deployment scope, help design and execute the first real development/test deployment, convert manual steps into versioned scripts, run twice from a repeatable state, and exercise one deliberate failure/rollback path. Documentation-only platform repositories such as AISoftPlatform do not need an application deployment pipeline.

In production, run only pre-validated artifacts and scripts. For failures, stop/rollback, collect sanitized evidence, reproduce and fix in non-production, verify, and prepare a PR. Never generate or execute ad hoc production commands.

## Protect the platform

- Never push directly to protected `main` or merge a PR.
- Preserve `CI / test (pull_request)`, immutable artifacts, environment separation, real health checks, and rollback.
- Never print tokens, passwords, `.env`, auth files, or Git credentials.
- Keep Claude and Codex configuration independent while sharing the outer controller and verifier contract.
- Do not describe the v3 Loop as deployed until the Codex validation matrix in `08` passes.

For a new project, read [references/onboarding-runbook.md](references/onboarding-runbook.md) before changing infrastructure.
