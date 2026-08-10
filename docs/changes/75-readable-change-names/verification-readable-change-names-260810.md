---
issue: 75
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/75
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
depends_on: []
status: contract-ready
branch: change/75-readable-change-names
pr_url:
created: 2026-08-10
updated: 2026-08-10
---

# Readable issue-scoped Change naming verification

## Live baseline

| Check | Result | Evidence |
|---|---|---|
| private Gitea Issue #75 | PASS | installed project-scoped broker read：open，title `feat(governance): require readable issue-scoped change names`，0 comments，no labels |
| fresh protected main | PASS | installed broker `git.fetch.main`；`origin/main=2c39fbcf4380824584dec5843ae9c0234206bfd2` |
| canonical checkout protection | PASS | canonical remains on stale `main` with user `.DS_Store` files untouched；development uses isolated `/private/tmp/aisoft-change-75-readable-change-names` |
| readable branch de-dup | PASS | no local/remote `change/75*` existed before creation；isolated branch created from exact `origin/main` |
| GitHub mirror Issue #75 | NOT FOUND / NOT AUTHORITATIVE | connector returned 404；private Gitea remains authority |
| current installed broker readable push | FAIL AS EXPECTED | installed contract regex is exact `change/N` only；candidate bootstrap is required and explicitly constrained by spec |
| Issue labels / approved lifecycle | NOT CONFIGURED FOR #75 | live Issue currently has no labels；this contract run did not bypass label ownership |
| remote PR / final-head CI | NOT RUN | branch not pushed and PR not created during contract-only run |
| merge / exact-main install / downstream migration | NOT RUN | human merge and post-merge gates remain independent |

## Contract validation

| Check | Result | Evidence |
|---|---|---|
| complexity classification | PASS | platform governance + shared controller + authorization/external contract forces `complex` |
| Issue AC coverage | PASS | spec AC-1..AC-9 preserve all Issue criteria and make grammar/legacy/rename/bootstrap decisions measurable |
| AC-to-plan mapping | PASS | plan table maps every AC to deterministic tests or final review/readback |
| governing AGENTS isolation | PASS | current run did not edit root `AGENTS.md`；spec explicitly authorizes a future fresh implementation run |
| semantic directory self-hosting | FAIL AS EXPECTED (bootstrap baseline) | branch/docs use exact `75-readable-change-names`；current protected-main resolver exits 2 with `exactly one new summary document is required` because it only searches `docs/changes/N/`；T02 owns the fix |
| unresolved decisions | PASS | spec declares none；no implementation started in this contract-only run |

## Candidate implementation results

- AC-1 Shared parser：`NOT RUN`。
- AC-2 New default and legacy compatibility：`NOT RUN`。
- AC-3 Single active name：`NOT RUN`。
- AC-4 Controller and worktree：`NOT RUN`。
- AC-5 Broker Git boundary：`NOT RUN`。
- AC-6 PR binding：`NOT RUN`。
- AC-7 Documentation and scaffolding：`NOT RUN`；root `AGENTS.md` intentionally deferred to fresh run。
- AC-8 Verification matrix：`NOT RUN`。
- AC-9 Governed delivery and install：local isolated branch `PASS`；push/PR/CI/merge/install/downstream `NOT RUN`。

## Forbidden-scope audit

- canonical checkout tracked/untracked files：`NOT MODIFIED`。
- `ci-bot`、credential/token contents、Keychain、PAT/ACL/permission/protection：`NOT ACCESSED / NOT MODIFIED`。
- remote branch/Issue/PR mutation：`NOT RUN`。
- VM/service、Docker、Secret、database、migration、deployment、restart、prune、production：`NOT RUN`。
- automatic merge、historical rename/delete/cleanup：`NOT RUN`。

## Post-merge gates

- unique readable branch/PR final-head readback：`NOT RUN`。
- human merge：`NOT RUN`。
- exact protected-main install + second no-op + byte readback：`NOT RUN`。
- `.previous` rollback availability：`NOT RUN`。
- downstream project migration Issues：`NOT RUN`。
