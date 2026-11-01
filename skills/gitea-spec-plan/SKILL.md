---
name: gitea-spec-plan
description: Turn an analyzed Gitea Issue into its mapped testable spec, and the ordered plan where the route policy's 文档义务 table requires one, on the shared readable change branch. Use for every classified Issue; keep the run document-only and do not create a separate spec PR or implement code.
---

# Draft the spec and plan

1. Read `AGENTS.md`, the Issue and valid comments, then resolve the one evidence-backed `docs/changes/<N>-<short-description>/` and its `documents` mapping. Stop on legacy/readable or multi-slug conflict. Only use a numeric directory and the four fixed legacy basenames when repository/remote history proves a legacy contract.
2. Every Issue gets a mapped spec (#436). Look up the route policy's `文档义务` table: for small and development complex without a high-risk flag write only the short spec (goal, scope and non-scope, measurable acceptance, needed risk and rollback, `git_scope`) and no plan; otherwise write the full spec below and the plan.
3. Ask one decision-focused question at a time when a material choice remains.
4. Keep the run document-only. Do not change product code, schema, workflows, deployment scripts, labels, or PR state.
5. For the full form, write the mapped `spec-<short-slug>-<YYMMDD>.md` with goal, rationale, measurable acceptance criteria, interface/data/migration/compatibility effects, risks, and explicit non-goals.
6. Only where the `文档义务` table requires a plan, write the mapped `plan-<short-slug>-<YYMMDD>.md` with ordered tasks, exact likely files, migration steps, test changes, verification commands, and rollback work when applicable.
7. Preserve the shared classification metadata in front matter: `change_type`, `requested_complexity`, `assessed_complexity`, `effective_complexity` (the summary's value: `effective_complexity: complex`, or `small` for a small change), `contract_effect`, `confidence`, and `risk_flags`. Also use Issue `N`, the exact `branch: change/N-short-description`, matching directory/document slug, and an honest status. Do not add a legacy unnamespaced `complexity:` field.
8. When a plan is written, map every acceptance criterion to at least one planned deterministic check or final human review item.
9. Require a mapped `verification` whenever acceptance evidence cannot be reproduced by diff review and required CI. Deployment and migration always qualify; only actual deployment/migration requires two repeat deployments and one deliberate failure/rollback exercise.
10. Stop after the documents and list unresolved decisions. Do not open a docs-only PR; `approved` may be set only after the contract is complete.
