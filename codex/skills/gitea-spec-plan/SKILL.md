---
name: gitea-spec-plan
description: Turn a complex analyzed Gitea Issue into a testable 01-spec.md and ordered 02-plan.md on the shared change/N branch. Use when complexity is complex or material decisions remain; keep the run document-only and do not create a separate spec PR or implement code.
---

# Draft the spec and plan

1. Read `AGENTS.md`, the Issue and valid comments, `docs/changes/<N>/00-summary.md`, document templates, relevant code, and current tests.
2. Require the analyzed metadata to contain `effective_complexity: complex`. Reject validated `effective_complexity: small` work instead of generating ceremonial spec/plan documents; improve its Issue acceptance criteria through the owning workflow if needed.
3. Ask one decision-focused question at a time when a material choice remains.
4. Keep the run document-only. Do not change product code, schema, workflows, deployment scripts, labels, or PR state.
5. Write `01-spec.md` with goal, rationale, measurable acceptance criteria, interface/data/migration/compatibility effects, risks, and explicit non-goals.
6. Write `02-plan.md` with ordered tasks, exact likely files, migration steps, test changes, verification commands, and rollback work when applicable.
7. Preserve the shared classification metadata in front matter: `change_type`, `requested_complexity`, `assessed_complexity`, `effective_complexity: complex`, `contract_effect`, `confidence`, and `risk_flags`. Also use Issue `N`, `complexity: complex`, `branch: change/N`, and an honest status.
8. Map every acceptance criterion to at least one planned deterministic check or final human review item.
9. For CI, deployment, migration, backup, health-check, or rollback changes, require a planned `03-verification.md` with two repeat deployments and one deliberate failure/rollback exercise.
10. Stop after the documents and list unresolved decisions. Do not open a docs-only PR; `approved` may be set only after the contract is complete.
