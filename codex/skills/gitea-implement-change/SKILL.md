---
name: gitea-implement-change
description: Execute one bounded implementation pass for a contract-ready Gitea change with tests and honest evidence. Use as a compatibility or controller-invoked worker for one task; use gitea-development-loop for repeated implement-verify-repair behavior. Never merge or deploy.
---

# Implement one bounded change pass

1. Read `AGENTS.md`, the Issue contract, `00-summary.md`, and for complex work `01-spec.md` plus `02-plan.md`.
2. Refuse to guess when the contract is missing, contradictory, or requires a new material decision.
3. Implement only the assigned task or smallest next incomplete plan item.
4. Keep the diff inside Issue scope. A normal implementation worker must never edit any `AGENTS.md` that governs its current run, even when a complex spec names that file. A complex spec may authorize this worker only to produce a reviewable governance patch/proposal artifact; an independent controlled governance step that is not governed by the target file must apply it, and a fresh run must then validate and adopt it.
5. Other protected files—including non-governing Agent behavior, controller, CI/deployment scripts, or shared platform instructions—may be modified only when an `effective_complexity: complex` spec explicitly lists the exact files and authorizes their change, verification, and rollback.
6. Add or update tests for changed behavior. Preserve the existing test runner and CI context.
7. For Prisma schema changes, create a backward-compatible migration; never use `prisma db push` or edit database files.
8. Run the assigned verification commands and return their real output summary.
9. Fix failures caused by this pass when the cause is clear and remains in scope. Do not weaken tests or hide errors.
10. Return changed files, commands/results, remaining failures, root-cause hypothesis, and whether another Loop iteration is needed.
11. Do not commit, push, change labels, open/merge PRs, or deploy unless the deterministic outer controller explicitly owns that action.
