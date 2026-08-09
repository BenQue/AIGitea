---
issue: 73
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/73
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
depends_on: []
status: approved
branch: change/73
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

# Manifest-fixed Gitea remote and project onboarding spec

## Problem Statement

`host-access-broker/v1` assumes that every canonical checkout names its internal Gitea remote `origin`. That
assumption is not part of the project manifest and conflicts with NewEmaint's deliberate dual-remote model: GitHub
remains `origin`, while internal Gitea is `gitea`. The broker therefore rejects a valid manifest project before fetch,
push or repo-local credential binding. Existing access audit also cannot prove that a checkout's remote and helper
binding are safe for governed Git operations.

## Solution

Let each manifest project optionally declare one strict `git_remote_name`, resolved to `origin` when absent. Declare
NewEmaint's remote as `gitea`. Route all broker Git operations through the resolved name while deriving the only
allowed URL from the existing governance manifest. Add a read-only project onboarding check that combines the current
credential/access/protection audit with canonical checkout, exact remote fetch/push URL and repo-local helper binding.
Keep binding, credential provision, platform merge and project adoption as separate gates.

## User Stories

1. As an AISoftPlatform user, I want existing projects without a remote declaration to keep using `origin`, so that the v1 upgrade is compatible.
2. As a NewEmaint maintainer, I want GitHub `origin` preserved while governed operations use `gitea`, so that internal delivery does not rewrite external history.
3. As a Codex caller, I want remote name and URL to come only from the manifest, so that I cannot accidentally or maliciously redirect credentials.
4. As a project agent, I want fetch and push to use the same exact manifest-derived Gitea target, so that read and write identities cannot diverge.
5. As a human merger, I want same-number `change/N`, fresh main, clean worktree, no merge commits and non-force push rules preserved, so that `main` remains protected.
6. As a platform owner, I want onboarding to fail closed on credential, identity, scope, permission, protection, required CI, checkout, remote or helper drift, so that partial setup is never treated as ready.
7. As an operator, I want onboarding checks and repo binding to be separate, so that a read-only audit never mutates Git config or credentials.
8. As a project owner, I want credential provisioning to require separate explicit approval, so that Issue approval cannot create or rotate Secrets.
9. As a future project adopter, I want one project Issue and evidence set at a time, so that another project's passing canary cannot authorize my project.
10. As an auditor, I want installer and runtime output to exclude token bytes, credential paths and helper protocol values, so that verification remains secret-safe.

## Implementation Decisions

- Keep `host-access-broker/v1`; extend each project object with optional `git_remote_name`. Missing means `origin`.
  A declared value must match the existing safe identifier grammar, remain unique only within its checkout, and cannot
  contain path separators, URL syntax, whitespace, refspec syntax or command fragments.
- Extend `ProjectContract` with the resolved remote name. Source manifest declares `git_remote_name: gitea` only for
  NewEmaint; all other current rows omit it and exercise compatibility.
- Do not add any CLI argument for remote name, remote URL, owner, repository, checkout, refspec, raw body, command or
  shell. Operation argument lists remain exact.
- Derive the allowed Git URL solely as `<base_url>/<owner>/<repository>.git`. Before credential resolution or Git
  network mutation, require the resolved remote's `get-url --all` and `get-url --push --all` to each contain exactly
  that one URL.
- Make `git.fetch.main`, `git.fetch.change`, `git.push.change` and `mac.git.bind` use the resolved remote name.
  Fetches request only `main` or the validated exact `change/N`. Push constructs one non-force, non-delete, same-name
  refspec and relies on freshly fetched protected main plus Git's non-fast-forward rejection.
- Preserve existing worktree gates: same Git common-dir as the manifest canonical checkout, exact current
  `change/N`, clean index/worktree, HEAD equals its branch, fresh main ancestry, and no merge commit between main and
  HEAD. No operation targets `main` or a different project.
- `mac.git.bind` never creates, removes, renames or edits a remote. It only writes repo-local
  `credential.useHttpPath=true`, exact Gitea-URL scoped username and helper list `['', fixed-helper]`; it writes no
  token or credential path and is idempotent.
- Add read-only `host.onboarding.check` with no typed arguments. It first executes the existing access audit, then
  requires a manifest canonical checkout, exact top-level/common repository, unique exact remote fetch/push URL and
  exact repo-local helper binding. Missing or drift returns sanitized nonzero `ONBOARDING_MISMATCH`.
- Keep `host.access.audit` available as the pre-binding credential/access gate. The intended adoption sequence is
  access audit → separately approved credential provision only if missing → `mac.git.bind` → onboarding check →
  typed live canary.
- Extend `GovernedHostRunner` only with the read-only onboarding operation. It continues to invoke the fixed installed
  broker with no direct curl, credential-store or generic Git fallback.
- Installer remains source-byte-only, preserves `.previous`, and creates no credentials, remotes, Git config,
  profiles, services, timers or deployments. Two identical runs must report no-op and remain byte-identical.
- Documentation names the project-level post-merge sequence. This platform Change does not create the NewEmaint
  adoption Issue because that Issue is only valid after human merge makes the new bytes authoritative.

## Testing Decisions

- Test `HostAccessBroker.execute()` and the public CLI seam with strict manifest fixtures plus real temporary Git
  canonical checkouts/worktrees. Prefer this single high seam over unit-testing private argv construction alone.
- Add compatibility tests proving an undeclared project still uses `origin` and NewEmaint uses only `gitea` while a
  GitHub `origin` remains byte-identical.
- Add remote negatives for unsafe identifiers, missing remote, wrong/multiple fetch or push URLs, cross-project URL,
  caller argument mismatch, main/other branch, merge commit, dirty tree and non-fast-forward push.
- Add onboarding tests for every credential/access/protection and checkout/remote/helper field; assert failure occurs
  before config/network mutation and errors contain no credential path, token, Authorization header or helper values.
- Add binding first-run/second-run tests and installer first-run/second-run byte manifests. Verify no remote config,
  token, profile, service, timer or business repository files are created.
- Extend runner/helper/fresh-session integration tests to prove only the fixed broker prefix and manifest-derived
  Gitea URL are used. Run focused tests frequently and the full platform smoke once at final head.

## Acceptance criteria

- [ ] **AC-1 Manifest contract**：project schema 接受缺省或 strict `git_remote_name`，调用方不能提供 remote
  name/URL/owner/repository/refspec；unsafe/extra/cross-project input 在 credential/Git 前失败。
- [ ] **AC-2 Compatibility and target**：未声明项目 byte-compatible 使用 `origin`；NewEmaint 固定使用
  `gitea`，fetch/push URL 都唯一匹配 manifest-derived
  `http://gitea-ci.orb.local:3000/admin/NewEMaint.git`，GitHub `origin` 不变。
- [ ] **AC-3 Git operations**：`git.fetch.main`、`git.fetch.change`、`git.push.change`、`mac.git.bind` 全部
  使用 resolved manifest remote，且只允许 exact same-number `change/N`、fresh main、clean worktree、no merge
  commit、non-force/non-delete same-name fast-forward push；main/other/cross-project 全拒绝。
- [ ] **AC-4 Repo binding**：binding 只写 repo-local fixed helper chain、exact username 与
  `credential.useHttpPath=true`，不创建/改写 remote，不写 token/path；第二次为 no-op。
- [ ] **AC-5 Onboarding check**：read-only gate 聚合 protected-file metadata、token identity/scope、repository
  permission、protected main、required CI、canonical checkout、remote fetch/push URL 与 helper binding；任一缺失
  或 drift 非零 fail closed，`ci-bot` 永不访问。
- [ ] **AC-6 Secret and mutation boundary**：禁止 Keychain、generic curl/security/broad Git push、credential
  output、token creation/rotation/revocation、account/PAT/ACL/permission/protection mutation；credential provision
  保持独立明确审批。
- [ ] **AC-7 Integration matrix**：contract/runtime/helper/controller、installer twice/no-op、security negatives、
  fresh-session integration、focused suites、full smoke、syntax/ShellCheck/JSON/Secret/diff gates 全部通过；mock、
  local、live、remote CI 证据分开记录。
- [ ] **AC-8 Delivery gate**：唯一 `change/73`、四份 semantic docs 与唯一 `Closes #73` PR；final-head CI 按
  live protection 分为 `PASS`、`NOT CONFIGURED`、`NOT RUN` 或 `FAIL`，随后停在人工 merge，不部署。
- [ ] **AC-9 Post-merge adoption**：本 PR 中保持 `NOT RUN`；人工合并后才创建独立 NewEmaint adoption Issue，
  逐项目执行 credential bootstrap（仅在需要且另获批准时）、binding、onboarding readback、typed mutation/
  exact change push/唯一 PR/required CI canary；其它项目不得批量启用。

## Risk and rollback constraints

Candidate rollback is a normal revert. A future post-merge host installation retains `.previous` bytes and must be
run twice/read back before project adoption. A repo-local binding rollback restores the exact pre-binding local Git
config snapshot; it never edits remotes or Git history. Missing or drifted credentials stop onboarding and require a
separate human decision—there is no automatic token recovery.

## Out of Scope

- Modifying NewEmaint source, branch/history, GitHub `origin`, Docker, VM lifecycle/profile, Secret contents,
  database, migration, Nginx, deployment, restart, prune or production.
- Pushing internal Gitea merge history to GitHub or using GitHub as the internal merge target.
- Creating/rotating/revoking credentials, changing account/PAT/ACL/permission/protection or accessing `ci-bot`.
- Automatic merge/close/deploy, a second platform Issue/PR, or bulk onboarding of manifest projects.

## 未决问题

无。所有 implementation direction、authority boundary 与 post-merge adoption 顺序均已由 Issue、用户批准和
live evidence 明确。
