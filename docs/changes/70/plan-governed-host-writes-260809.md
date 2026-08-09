---
issue: 70
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/70
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
depends_on:
  - 35
  - 61
  - 67
status: approved
branch: change/70
pr_url: null
created: 2026-08-09
updated: 2026-08-09
---

# Governed non-interactive host writes plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | strict audit + Issue typed mutation/readback tracer bullet | - | complete |
| T02 | isolated worktree exact change push + broker-only runner tracer bullet | T01 | complete |
| T03 | PR typed lifecycle + installer/fresh-session/security/full-smoke closure | T01, T02 | complete |
| T04 | single live canary, push, unique PR and final-head handoff | T01, T02, T03 | in-progress |

## T01 — Access audit and Issue operations

- Extend the exact manifest/contract with aggregate access audit and Issue create/update/comment typed fields.
- Verify fixed manager/project-agent credentials, live identities, declared scope evidence, exact repository permission,
  fixed Keychain item metadata/ACL through exact Security.framework item references, and protection without exposing Secret data.
- Add public-seam tests for successful Issue create/read/update/comment and early rejection of unknown/raw fields,
  wrong identity/scope/permission, missing/duplicate/allow-any Keychain item and unsafe text.

## T02 — Isolated worktree push and runner

- Resolve the broker execution worktree from `cwd`; verify same common-dir/remote/project, freshly fetched main,
  exact same-number branch, clean tree/index and fixed source/destination ref.
- Add real temp-repository/worktree tests and negatives for detached/main/other N/force/delete/refspec/dirty/cross-project.
- Add a controller/runner adapter that invokes the fixed installed broker only; forbid direct curl/security/git fallback.

## T03 — PR lifecycle and integration gate

- Add PR create/read/update typed operations with fixed base/head, `Closes #N`, semantic summary link and de-dup.
- Cover current credential-helper protocol, Secret redaction, fake Keychain audit and broker-only fresh-session behavior.
- Run installer twice in a fake root and assert byte-identical/no-op, no credentials/ACL/profile/service/timer/deploy state.
- Run focused Python/shell, `bash -n`, ShellCheck, strict JSON, document resolver, Secret scan, diff and full smoke.

## T04 — Delivery canary

- Re-fetch and read back exact protected `main`, Issue #35/#61/#67 merged facts, open PR de-dup, required CI,
  installed bytes, repo binding, manifest and access audit through the broker.
- Install the candidate through one explicit bootstrap step, then use only the exact installed broker prefix.
- Mutate/read back Issue #70, push exact `change/70`, create/update/read one final `Closes #70` PR, read final head,
  protection and required status contexts.
- Stop at the human merge gate. Record post-merge exact-byte install/no-op/new-task canary as `NOT RUN`.

## Expected touch points

- `docs/changes/70/` semantic documents.
- `codex/config/host-access-broker.json`.
- `codex/runtime/aisoft_host_access/{contract,broker,cli,runner}.py` and `keychain_acl_audit.c`.
- `codex/runtime/tests/test_host_access.py` and `codex/tests/test-host-access-broker.sh`.
- broker-only controller/runner adapter under `codex/agent/` and its runtime test.
- `codex/install-host-access-broker.sh`, `README.md`, `06-运维手册与踩坑集.md`.

This list is scope guidance, not authorization to modify root `AGENTS.md`, protected-main policy, credentials, ACL,
accounts, permissions, `ci-bot`, VM/profile/service/runtime, business projects or deployment state.

## Verification mapping

| Acceptance criterion | Verification |
|---|---|
| AC-1 | public broker CLI/transport tests for strict Issue/PR operations and unknown/raw input negatives |
| AC-2 | real temp Git repository + linked worktree exact push and denial matrix |
| AC-3, AC-6 | fresh-task exact-prefix live canary; approval prompts recorded separately from Keychain ACL |
| AC-4, AC-5 | fake security output parser/command argv tests plus live redacted aggregate audit |
| AC-7 | catalog/schema assertions: zero merge/protection/ACL/account/PAT/permission mutation operations |
| AC-8 | focused unit/shell, installer twice, runner integration, full platform smoke, syntax/ShellCheck/JSON/Secret/diff |
| AC-9 | live branch protection + final-head status readback |
| AC-10 | pre-merge `NOT RUN`; separate post-merge task only |

## Rollback

Candidate code rollback is a normal revert. Candidate host install preserves `.previous` source/runtime/manifest/wrapper
bytes and the bootstrap records exact hashes; if health or canary fails, restore only those previous broker bytes and
re-run read-only validation. No credential, ACL, account, permission, protection, Issue/PR deletion, branch rewrite,
merge or deployment rollback action is authorized by this plan.
