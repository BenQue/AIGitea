---
name: gitea-development-loop
description: Drive a contract-ready Gitea Issue through a bounded implement-verify-repair loop until it is ready for final human review or must escalate. Use after approved for small Issues with clear acceptance criteria or complex Issues with complete spec/plan; handle ordinary test and CI failures autonomously, but never change the contract, merge, or deploy.
---

# Run a Gitea development loop

1. Read `AGENTS.md`, the Issue and valid comments, `00-summary.md`, and any persisted Loop state.
2. Validate the contract before editing:
   - require measurable Issue acceptance criteria for `small`;
   - require `01-spec.md` and `02-plan.md` for `complex`;
   - require `03-verification.md` work for deployment or migration scope;
   - stop if documents conflict or contain unresolved material decisions.
3. Before every edit, recompute `contract_effect` and all forced-complex risk conditions from the current Issue contract and repository evidence. Do not trust a stale `complexity/small` label or summary field.
4. If a small contract now has `contract_effect` of `add` or `change`, or crosses any forced risk (schema/data migration, external contract, authentication/authorization/security, shared core component, cross-module/service, CI/artifact/deployment/rollback, or Agent/platform governance), make no further edits and return:

```text
STATUS: NEEDS_HUMAN_DECISION
NEXT: reclassify as complex and create spec/plan
```

5. Work only in the controller-provided isolated `change/N` worktree. Do not manage locks, credentials, labels, PRs, documents, or deployment. Classification and lifecycle mutations belong to the wrapper/controller.
6. Select the smallest next incomplete plan task or acceptance criterion.
7. Implement the minimal in-scope change and add or update tests.
8. Run the controller-assigned deterministic checks. Treat real command output as authoritative.
9. On ordinary compile, lint, type, test, build, browser, or CI failure:
   - identify the root cause;
   - fix it without weakening validation;
   - rerun the narrow failing check, then the required wider gate;
   - record the attempt for the controller.
10. Do not ask for human help for routine failures that repository evidence can resolve.
11. Stop and return `NEEDS_HUMAN_DECISION` for contract conflicts, scope expansion, destructive migration, new security/permission/architecture decisions, or direct production changes.
12. Return `BLOCKED_EXTERNAL` for missing credentials, unavailable required services, network barriers, or external-team dependencies.
13. Return `FAILED_LIMIT` when the controller reports the retry, time, token, or iteration limit reached. Treat three consecutive attempts with the same root cause as an escalation.
14. Return `READY_FOR_REVIEW` only when every acceptance criterion is accounted for and all assigned local plus PR CI checks pass.

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

Never rewrite the accepted contract, hide failures, merge a PR, or deploy.
