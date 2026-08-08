---
name: aisoft-platform
description: Operate or onboard projects to the AISoft self-hosted Gitea delivery platform. Use for private local Gitea repository, Issue, PR, Actions, branch-protection, or authentication inspection; Issue analysis; small-or-complex routing; spec/plan contracts; Development Loop work; Codex/Claude provider coexistence; CI/deployment incidents; first non-production deployments; rollback planning; or production script boundaries.
---

# AISoft self-hosted delivery platform

## Read the contract

Read `README.md` and the relevant numbered document before acting. On Mac the authoritative root is `~/MyDocs/AISoftPlatform/`; on gitea-ci it is `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/` (readable as both `benque` and `coder`, verified 2026-07-19).

⚠️ **Not `~/Documents/AISoftPlatform/` — that was the location until 2026-07-19 and it is unreachable from the VM.** macOS TCC blocks `/mnt/mac` access to `~/Documents`, `~/Desktop` and `~/Downloads`, and `sudo` does not help (`Operation not permitted` as both `benque` and `root`). The repo was moved to `~/MyDocs/` precisely so the mount works; see 01 §1.

Use:

- `03` for Issue, complexity, documents, labels, and the final PR gate.
- `04` for analyzer, Development Loop, verifier, terminal states, and provider adapters.
- `02` and `06` for deployments and incidents.
- `08` for Codex-first validation and later Claude parity.
- `09` for migration scope and unimplemented boundaries.

## Apply the v3 workflow

Select the target project explicitly before any Gitea or Git mutation. A project profile binds one profile name to `GITEA_URL`, `GITEA_OWNER`, `GITEA_REPO`, `AGENT_REPO_DIR`, provider selection, and a namespaced state/worktree root. Never infer the target repository from rsDesign or another example, and never reuse one project's state directory for another project.

After AISoftPlatform Issue #35 is merged and its live rollout is explicitly authorized, every local Gitea
software repository must first exist in the strict `codex/config/gitea-governance.json` manifest. Validate the
manifest, bootstrap the non-site-admin platform manager for one exact repository, run read-only governance
`check`, then apply one exact repository with the manifest-declared project agent. Unknown repositories are
report-only; never infer visibility, ownership, or permissions from discovery.

Every mutation requires the exact repository, Issue #35, a byte-identical merged platform SHA, the manager
mutation credential, and a new evidence directory. The tool must read back private/public visibility,
manager=Admin, project-agent=Write, no cross-project Write/Admin, merge-after-branch cleanup, and protected
`main`. Direct/force push is disabled and the merge allowlist contains only the human identity. Manager,
project agent, and shared bot never merge.

The following fixed `ci-bot` gate is migration compatibility only for profiles that already use it. Do not use
it to onboard a new project:

```text
AISOFT_ONBOARDING_MODE=software-repository \
GITEA_URL=<exact-url> \
GITEA_OWNER=<exact-owner> \
GITEA_REPO=<exact-repo> \
GITEA_EXPECT_URL=<exact-url> \
GITEA_EXPECT_OWNER=<exact-owner> \
GITEA_EXPECT_REPO=<exact-repo> \
GITEA_ADMIN_CREDENTIAL_FILE=<vm-local-credential-file> \
GITEA_BOT_CREDENTIAL_FILE=<vm-local-credential-file> \
/mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/ensure-gitea-collaborator.sh
```

The legacy gate is fixed to the platform-managed `ci-bot` identity and exact `write` permission. It must read
back the API permission, verify real `ci-bot` repository access, and prove the existing `main` branch protection
is unchanged and still excludes `ci-bot` from push, force-push, and merge allowlists. It never grants `admin`
or enables merge. On any failure, stop the migration flow and report `BLOCKED_EXTERNAL`.

Resolve these non-secret coordinates from the exact project profile first, then run the gate in the VM operator context that can read the existing administrator and `ci-bot` credential file. Do not copy either token into the project profile, Mac, command arguments, or output.

Do not use either mutation path as an inspection shortcut. Prefer the exact project profile; for cross-project
settings/protection use the manager audit PAT and `gitea-governance.sh check`. Retire `ci-bot` only after the
new project agent has exact PASS evidence for private read, Issue/comment/label, feature push, PR, main push
denial, and main merge denial.

## Access private Gitea deterministically

Before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting, read [references/private-gitea-access.md](references/private-gitea-access.md).

- Resolve and verify the exact Gitea remote or project profile first.
- Do not start with an anonymous API request. A private-repository `404` or Git `Repository not found` is inconclusive.
- Prefer the exact project profile and minimum-privilege identity. For Git refs, reuse the configured Git credential helper.
- After Issue #35 live rollout, use the independent platform-manager audit PAT for cross-project read-only
  settings/protection inventory; do not substitute the mutation PAT or ordinary Git.
- If no profile/manager exists or ACL blocks the exact target, use the VM-local administrator credential only
  for an authorized, sanitized, read-only helper call. Do not copy credentials to the Mac or broaden bot access.
- Use an existing authenticated browser session as a read-only fallback when the helper is unavailable or UI evidence is required.
- Report network, credential availability, repository ACL, and object existence as separate facts.

Treat every request, defect, or platform change as a Gitea Issue `N` linked to `change/N`, `docs/changes/N/`, and a final PR with `Closes #N`.

- Require `00-summary.md` for every Issue.
- Treat `type/*` labels as Issue-author inputs describing what the change is; AI verifies or corrects one primary type from repository evidence.
- Treat `complexity/*` labels as AI classification outputs describing which path is required, never as an Issue-author override of contract impact or forced risk.
- Treat the eight unprefixed lifecycle labels as workflow state, separate from type and complexity. `completed` means merged with no deployment required; `deployed` requires deterministic deployment and verification.
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
- Never add a project profile or collaborator permission merely to make read-only inspection convenient;
  account and repository mutation is reserved for the merged governance manifest and exact-repository tools.
- Keep Gitea manager/project PATs, OrbStack host control, VM operator accounts, and per-project deploy identities
  separate. A Gitea credential never authorizes SSH, sudo, VM lifecycle, database, or production access.
- Keep Claude and Codex configuration independent while sharing the outer controller and verifier contract.
- Do not describe the v3 Loop as deployed until the Codex validation matrix in `08` passes.

For a new project, read [references/onboarding-runbook.md](references/onboarding-runbook.md) before changing infrastructure.
