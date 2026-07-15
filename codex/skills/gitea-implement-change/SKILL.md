---
name: gitea-implement-change
description: Execute one bounded implementation pass for a contract-ready Gitea change with tests and honest evidence. Use as a compatibility or controller-invoked worker for one task; use gitea-development-loop for repeated implement-verify-repair behavior. Never merge or deploy.
---

# Implement one bounded change pass

1. Read `AGENTS.md`, the Issue contract, `00-summary.md`, and for complex work `01-spec.md` plus `02-plan.md`.
2. Refuse to guess when the contract is missing, contradictory, or requires a new material decision.
3. Implement only the assigned task or smallest next incomplete plan item.
4. Keep the diff inside Issue scope. Modify protected governance files—including `AGENTS.md`, Agent behavior, controller, CI/deployment scripts, or other shared platform instructions—only when an `effective_complexity: complex` spec explicitly lists the exact files and authorizes their change.
5. Never modify a governing `AGENTS.md` and immediately adopt the modified instructions in the same worker run. Finish the bounded run under the instructions loaded at startup; a later fresh run may load an approved change.
6. Add or update tests for changed behavior. Preserve the existing test runner and CI context.
7. For Prisma schema changes, create a backward-compatible migration; never use `prisma db push` or edit database files.
8. Run the assigned verification commands and return their real output summary.
9. Fix failures caused by this pass when the cause is clear and remains in scope. Do not weaken tests or hide errors.
10. Return changed files, commands/results, remaining failures, root-cause hypothesis, and whether another Loop iteration is needed.
11. Do not commit, push, change labels, open/merge PRs, or deploy unless the deterministic outer controller explicitly owns that action.
