---
name: gitea-implement-change
description: Compatibility adapter that delegates one contract-ready Gitea ticket to the complete Matt implement skill, including tests, review, and an auditable local commit. The Controller owns push, PR, CI, and state; only a human merges. Never deploy.
---

# Implement one bounded change pass

1. Read `AGENTS.md`, the Issue contract and its mapped summary; for complex work read the mapped spec and plan. Use fixed legacy basenames only for legacy summaries.
2. Refuse to guess when the contract is missing, contradictory, or requires a new material decision.
3. Invoke `$implement` for exactly the Controller-assigned `Txx`; preserve its TDD, typecheck/test, full-suite and code-review workflow.
4. Keep the diff inside Issue scope. A normal implementation worker must never edit any `AGENTS.md` that governs its current run, even when a complex spec names that file. A complex spec may authorize this worker only to produce a reviewable governance patch/proposal artifact; an independent controlled governance step that is not governed by the target file must apply it, and a fresh run must then validate and adopt it.
5. Other protected files—including non-governing Agent behavior, controller, CI/deployment scripts, or shared platform instructions—may be modified only when an `effective_complexity: complex` spec explicitly lists the exact files and authorizes their change, verification, and rollback.
6. Add or update tests for changed behavior. Preserve the existing test runner and CI context.
7. For Prisma schema changes, create a backward-compatible migration; never use `prisma db push` or edit database files.
8. Run the assigned verification commands and return their real output summary.
9. Fix failures caused by this pass when the cause is clear and remains in scope. Do not weaken tests or hide errors.
10. Commit verified changes on the current `change/N`. Every commit subject contains `#N` and the assigned `Txx`;
    do not amend published history, create merge commits, rebase or change branches. Leave the worktree clean.
11. Return changed files, commands/results, remaining failures, root-cause hypothesis, commit SHA and whether another Loop iteration is needed.
12. Do not push, change labels, open/merge PRs, or deploy. The deterministic Controller owns remote mutation and only a human owns merge.
