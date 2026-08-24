---
name: gitea-analyze-change
description: Analyze a Gitea Issue against the current repository and produce an evidence-backed named summary document with a deterministic change type, contract effect, and effective complexity classification. Use for needs-analysis Issues before spec/plan or Development Loop work; never modify product code or Gitea state.
---

# Analyze a Gitea change

1. Read `AGENTS.md`, the Issue title/body/comments, current `type/*` and complexity labels, repository structure, relevant code, and existing tests.
2. Stay read-only. Do not edit product code, workflows, deployment scripts, Git state, labels, comments, branches, or databases.
3. Ground impact claims in inspected files. Separate confirmed facts, assumptions, and unresolved questions.
4. Produce exactly these five level-two Markdown sections, in this order, with no additional `##` section:
   - `## 问题/需求总结`
   - `## 影响范围`
   - `## 初步方案与建议`
   - `## 风险`
   - `## AI 判级`
5. Name concrete files/modules and tests likely to change.
6. In `## AI 判级`, emit one YAML block using this schema and field order:

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

Allowed values are:

- `change_type`: `bugfix`, `feature`, `docs`, `test`, `refactor`, `maintenance`, or `platform`, corresponding to exactly one primary `type/*` label such as `type/feature`.
- `requested_complexity`: `auto`, `small`, or `complex`, derived from the Issue request; a missing request is `auto`.
- `assessed_complexity`: `small`, `complex`, or `needs-human-decision`.
- `effective_complexity`: `small` or `complex` when classification is safe.
- `contract_effect`: `restore`, `unchanged`, `add`, `change`, or `unclear`.
- `confidence`: `high`, `medium`, or `low`.

7. Classify contract effect before complexity:
   - `restore` or `unchanged` is only a `small` candidate;
   - `add` or `change` is always `complex`;
   - `unclear` is `needs-human-decision`.
8. Apply complexity in this priority order: forced-complex risk, explicit `complex`, validated explicit `small`, then AI assessment. Never downgrade an explicit `complex`. If explicit `small` conflicts with evidence, set `effective_complexity: complex` and explain the conflict in `override_reason`.
9. Force `complex` for a feature or functional behavior change, schema/data migration, external contract, authentication/authorization/security, shared core component, cross-module/service change, CI/artifact/deployment/rollback change, or Agent/platform governance change. Otherwise use `small` only for a clear, local, reversible restore/unchanged change with measurable acceptance criteria.
10. Use stable `risk_flags` names that directly identify every forced condition. Set semantic `required_docs` to `summary` for `small`, and to `summary`, `spec`, and `plan` for `complex`; append `verification` when the acceptance evidence cannot be reproduced by diff review and required CI. Deployment and migration always qualify, and so does any change whose acceptance depends on a real-environment or one-shot observation. Appending `verification` declares that the change owes a verification record; it never declares that the change deploys.
11. Return a meaningful `document_slug` with 2–4 lowercase ASCII `kebab-case` segments, at least one letter and at most 32 characters. Do not use reserved names or the `tmp-`, `temp-`, `legacy-` prefixes. The wrapper locks the tuple into `change/N-slug`, `docs/changes/N-slug/`, `issue-N-slug`, every document basename and front matter; it must stop on any conflicting existing name.
11. For `needs-human-decision`, set `assessed_complexity: needs-human-decision` and `contract_effect: unclear`, omit `effective_complexity`, and state the single decision needed in `reason`. The wrapper must omit that key from both summary front matter and the `## AI 判级` YAML block; it must not leave an empty value or placeholder. Do not choose a fallback complexity or emit multiple questions.
12. Identify missing acceptance criteria that must be resolved before `approved` can start a Development Loop. Do not claim tests ran unless they actually ran.

For automated runs, output only the Markdown body. The deterministic wrapper owns front matter, readable change-name projection, Git mutations, Gitea comments, type/complexity labels, and lifecycle labels.
