---
name: gitea-development-loop
description: Drive a contract-ready Gitea Issue through a bounded implement-verify-repair loop until its final-PR candidate is ready or it must escalate. Use after approved for small Issues, production complex Issues with complete spec/plan, or development complex Issues with measurable Issue acceptance criteria; handle ordinary test and CI failures autonomously, but never change the contract, choose merge policy, merge, or deploy.
---

# Run a Gitea development loop

1. Read `AGENTS.md`, the Issue and valid comments, resolve the active summary from its strict name and `documents` mapping, and read the session's own progress notes. For production complex work, also read the mapped spec and plan in full before making any edit. For development complex work, read measurable acceptance criteria from the Issue. Fall back to fixed legacy basenames only for legacy summaries.
2. Validate the contract before editing:
   - require measurable Issue acceptance criteria for `small`;
   - for production `complex`, require both mapped `spec` and `plan`; validate that their metadata says `effective_complexity: complex`, the spec has measurable acceptance criteria and no unresolved material decisions, and the plan maps in-scope tasks and deterministic verification to those criteria;
   - for development `complex`, require measurable acceptance criteria in the Issue and no mapped spec/plan; use synthetic `T01` while keeping every forced-complex safety rule;
   - require mapped `verification` work whenever the mapped summary's `required_docs` includes that role; declaring it means the change owes a verification record, not that the change deploys, so never re-derive the requirement from deployment scope;
   - stop if the Issue, summary, route-required documents, or plan conflict, omit required scope, or contain unresolved material decisions.
3. Before every edit, recompute `contract_effect` and all forced-complex risk conditions from the current Issue contract and repository evidence. Do not trust a stale `complexity/small` label or summary field.
4. If a small contract now has `contract_effect` of `add` or `change`, or crosses any forced risk (schema/data migration, external contract, authentication/authorization/security, shared core component, cross-module/service, CI/artifact/deployment/rollback, or Agent/platform governance), make no further edits and return:

```text
STATUS: NEEDS_HUMAN_DECISION
NEXT: reclassify as complex and create spec/plan
```

5. Work only in the session's own claimed `change/N-short-description` worktree whose basename is `issue-N-short-description`. Credentials, labels, PRs and deployment stay outside this loop: push, PR creation and the `pr_url` backfill happen only after the second confirmation, through the broker, as `aisoft-platform` describes.
   - Never edit an `AGENTS.md` that governs the current run. If a complex contract changes that governance file, produce only a patch/proposal for an independent controlled governance step; after it is applied, a fresh run must validate and adopt the new rules.
6. Select the first unblocked `Txx` frontier task from the mapped plan; for a legacy, small, or development-complex contract without a ticket graph use the synthetic `T01`.
7. Dispatch the complete Matt `$implement Issue #N ticket Txx` flow. It implements, tests, reviews and commits locally; every commit subject contains `#N` and `Txx` and the worktree must be clean.
8. Run the deterministic checks the contract assigns. Treat real command output as authoritative.
9. On ordinary compile, lint, type, test, build, browser, or CI failure:
   - identify the root cause;
   - fix it without weakening validation;
   - rerun the narrow failing check, then the required wider gate;
   - record the attempt in the session's progress notes.
10. Do not ask for human help for routine failures that repository evidence can resolve.
11. Stop and return `NEEDS_HUMAN_DECISION` for contract conflicts, scope expansion, destructive migration, new security/permission/architecture decisions, or direct production changes.
12. Return `BLOCKED_EXTERNAL` for missing credentials, unavailable required services, network barriers, or external-team dependencies.
13. Return `FAILED_LIMIT` when the retry, time, token, or iteration limit is reached. Treat three consecutive attempts with the same root cause as an escalation.
14. Local completion only means a PR candidate is ready. The session then produces the confirmation handoff and
    enters `AWAITING_PR_CONFIRMATION`; it never receives merge credentials. (The VM Loop controller and routine merge
    left main in #391.)
15. Return `READY_FOR_REVIEW` only after every acceptance criterion is accounted for and all assigned local plus PR CI
    checks pass; a human merges.

End every iteration with this structure:

```text
STATUS: CONTINUE | READY_FOR_REVIEW | NEEDS_HUMAN_DECISION | BLOCKED_EXTERNAL | FAILED_LIMIT
TASK:
CHANGED:
VERIFIED:
FAILED:
ROOT_CAUSE:
ATTEMPTS:
NEXT:
HUMAN_DECISION:
```

Never rewrite the accepted contract, hide failures, push before the second confirmation, merge a PR, or deploy.
