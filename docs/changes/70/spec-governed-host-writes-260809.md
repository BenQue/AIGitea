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

# Governed non-interactive host writes spec

## Problem Statement

Codex cannot complete the normal AISoftPlatform Issue → change branch → PR handoff through the installed broker.
The missing typed Gitea mutation surface and canonical-checkout-only Git implementation force new sessions back to
direct `curl`, `git` or `security`, so the user receives repeated host execution approvals even though the fixed
Keychain item may already trust `/usr/bin/security` without a password prompt.

## Solution

Extend the purpose-built broker into the only Mac host interface for governed Gitea reads/writes and change-branch
pushes. Every operation has a fixed identity route, target, HTTP method/path or Git argv, and strict typed fields.
Add one aggregate read-only audit that validates manifest identities, token scopes, repository permission, fixed
Keychain item metadata/ACL and protection without emitting credential data. Make the Loop/controller runner invoke
the broker adapter instead of reconstructing host commands.

## User Stories

1. As a Codex user, I want a new task to create and update a project Issue through one fixed broker, so that I do not approve generic host commands.
2. As a Codex user, I want comments and lifecycle handoff updates to use typed operations, so that raw HTTP bodies and URLs are never accepted.
3. As a Codex user, I want an isolated worktree to push only its same-numbered `change/N`, so that canonical and parallel worktrees remain protected.
4. As a Codex user, I want the broker to create and update one final PR with fixed `main` base and `change/N` head, so that merge remains a separate human action.
5. As a platform owner, I want account, token scope, permission, Keychain and protection drift to fail closed before mutation, so that a stale credential cannot silently broaden access.
6. As a platform owner, I want credential values excluded from every observable surface, so that auditability does not leak authentication material.
7. As a human merger, I want the broker to have no merge operation, so that protected `main` can only be merged in Gitea by `admin`.
8. As a future Codex task, I want repeated exact-prefix calls to require no Keychain prompt and no per-command host approval, so that the daily governance flow is non-interactive.

## Implementation Decisions

- Keep `host-access-broker/v1`; extend its exact catalog rather than add a second broker method or generic HTTP adapter.
- Add typed operations for Issue create/read/update/comment, PR create/read/update, aggregate governance access audit,
  fresh main/change fetch and exact change push. Operation definitions remain byte-exact between source and live manifest.
- Typed text fields reject NUL/CR, leading/trailing ambiguity where unsafe, invalid state values, oversized content and
  unexpected fields. The interface never accepts URL, owner, repository, HTTP method/path, raw JSON body, shell,
  command, credential path, refspec, force, delete or merge.
- `gitea.issue.update` permits title/body changes but does not close an Issue in this Change. `gitea.pull.update`
  permits title/body changes but cannot change head/base/state or merge.
- `gitea.pull.create` derives head=`change/<issue>` and base=`main`, requires `Closes #N` plus the mapped semantic
  summary path, and de-duplicates an existing open PR before POST.
- Resolve an interactive worktree from broker process `cwd`, then require exact normalized directory, same Git
  common-dir as manifest checkout, exact origin URL, branch=`change/N`, clean index/worktree for push, and local HEAD
  based on freshly fetched `origin/main`. No caller-supplied checkout path is accepted.
- Aggregate audit uses only fixed manifest credentials. It validates each credential through `/api/v1/user`, checks
  expected declared scopes using Gitea token metadata where supported, checks the project-agent's exact repository
  permission, and reads protected `main`. Unsupported scope introspection is `NOT CONFIGURED`, never `PASS`.
- Keychain ACL audit uses a compiled Security.framework helper whose project/account catalog is byte-checked against
  the manifest. It performs exact `kSecClassGenericPassword` + service/account queries, requests item references but
  never `kSecReturnData`, and inspects only the matching decrypt ACL. It rejects missing/duplicate/allow-any items and
  returns only item class/permanence/trusted application/password-required shape; `dump-keychain`, `security -A`,
  password export and any `ci-bot` query are absent.
- The controller/runner adapter invokes only the broker executable and typed fields. No fallback to direct `curl`,
  `/usr/bin/security`, generic `git fetch/push`, or broad host command is permitted.

## Testing Decisions

- Test the public broker CLI/`HostAccessBroker.execute()` seam using a fake Gitea transport and real temporary Git
  repositories/worktrees; do not assert private helper call counts except at external security/Gitea/Git boundaries.
- Use one RED→GREEN vertical slice at a time: Issue mutation, audit drift, worktree push, PR mutation, runner integration.
- Security negatives assert rejection occurs before credential resolution or network/Git mutation and error messages
  contain no token, Authorization header, Keychain data or submitted secret-shaped content.
- Shell integration tests exercise the installed wrapper/native ACL helper layout twice, fake Keychain metadata/ACL, fresh-session
  approval contract, no-op install and absence of direct fallback commands.
- Static/fake tests are candidate evidence only. Live Issue/branch/PR/protection and prompt behavior remain separate.

## Acceptance criteria

- [ ] **AC-1** operation catalog provides project-agent scoped Issue create/read/update/comment and PR create/read/update with strict fields and no raw URL/body/owner/repository/method/path input.
- [ ] **AC-2** worktree push accepts only the current same-numbered `change/N`; main, detached, other branch/refspec, force, delete, merge, dirty/cross-project/cross-common-dir targets fail before push.
- [ ] **AC-3** exact broker prefix is the only persistent Codex host authorization; direct `security`, generic `curl`, broad Git push and candidate wrapper prefixes are not persisted.
- [ ] **AC-4** Keychain binding stays fixed service/account with minimal trusted application ACL; `-A`/allow-any is rejected and credential data never reaches observable outputs or fixtures.
- [ ] **AC-5** aggregate audit validates manifest manager/project-agent identity, declared token scope evidence, repository permission, Keychain credential/ACL and protection; absence/drift is nonzero fail closed and `ci-bot` is never accessed.
- [ ] **AC-6** a fresh Codex task uses the broker to mutate/read Issue #70, push exact `change/70`, create one PR and read back Issue/PR/head/protection with zero Keychain prompt and zero repeated host approval after the single exact-prefix grant.
- [ ] **AC-7** no merge/protection/ACL/account/PAT/permission/deploy mutation surface is added; PR creation stops at human merge.
- [ ] **AC-8** contract, broker, credential helper, controller/runner, security negatives, fresh-session integration, installer twice/no-op and full smoke all pass; live and static evidence remain distinct.
- [ ] **AC-9** final-head required CI is classified from live protection as `PASS`, `NOT CONFIGURED`, `NOT RUN` or failure without borrowing local smoke results.
- [ ] **AC-10** after the human merge only, exact merged-main bytes install/no-op and a new-task follow-up canary are performed; before merge they remain `NOT RUN`.

## Out of Scope

- Automatic merge/close, protection/ACL/permission changes, account/PAT bootstrap/rotation/revocation or `ci-bot` access.
- Docker, VM lifecycle/profile, Secret management, database, migration, Nginx, deployment, restart, prune or production.
- NewEmaint, Issue #65 E2E, any business project, second Issue or second final PR.

## Further Notes

Candidate installation and live canary are bootstrap evidence for #70, not post-merge delivery proof. The post-merge
gate must be repeated from exact merged protected-main bytes in a separate fresh task.
