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
status: awaiting-merge
branch: change/70
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/72
created: 2026-08-09
updated: 2026-08-09
---

# Governed non-interactive host writes verification

## Baseline

| Check | Result | Evidence |
|---|---|---|
| isolated worktree | PASS | `/Users/benque/.codex/worktrees/fc5b/AISoftPlatform`; canonical and other worktrees untouched |
| fresh default baseline | PASS | task started from fetched `7ef7fa23af202343335f99ea746b4dd7a64cbd71`; immediately before delivery the broker fetched new `origin/main` `6a4b7e77aea84b69c28be3abb21966957857a174` and the unpushed branch rebased without conflict |
| Issue #70 | PASS | installed broker live read: open, labels `approved` + `complexity/complex` + `type/platform`; typed comment mutation/read-back produced exactly one comment |
| local/remote de-dup | PASS | before branch creation, local/remote `change/70` refs were absent; typed open-PR read returned `[]` immediately before delivery |
| #35/#61/#67 merged facts | PASS | live PR read-back: #36 from `change/35`, #63 for Issue #61 and #68 from `change/67` each returned `state=closed`, `merged=true`; the three Issues are closed |
| installed source bytes | PASS | all installed runtime/config/wrapper bytes equal the rebased candidate; exact legacy `keychain-acl-audit` and `.previous` paths are absent |
| installed operation catalog | PASS | exact 21 operations; strict Issue/PR/status/audit and linked-worktree Git operations are present; merge operation count is zero |
| repo-local Git credential binding | PASS (local metadata) | fixed helper + `credential.useHttpPath=true` + `aisoft-platform-agent`; no token in config |
| protected-file credential route | PASS | fixed bindings resolve as owner `benque`, directory mode `700`, file mode `600`, regular non-symlink single-hardlink files; credential bytes/path are redacted |
| host broker Issue read | PASS | two consecutive installed-broker reads of #70 succeeded through `aisoft-platform-agent`, followed by typed comment mutation and read-back |
| Codex exact-prefix approval | PASS (current fresh task) | after the single purpose-built broker prefix grant, repeated read/audit/comment operations completed without another host-execution approval |
| Keychain route | RETIRED / ABSENT | three historical candidates prompted despite ACL metadata; final runtime/manifest/installed bytes contain no Keychain lookup surface or legacy helper |
| live accounts/token scopes/permission/protection | PASS | aggregate audit validated all three identities and exact scopes, manager `admin`, project-agent `write`, protected-file metadata and human-only protected-main merge boundary |
| `ci-bot` | NOT ACCESSED / NOT MODIFIED | no query or mutation performed |

## Candidate tests

- T01: `PASS (protected-file candidate)` — Issue create/read/update/comment、PR create/read/update、SHA status read、
  identity/scope/permission/protection audit 的 public seam 与 fail-closed negatives 通过；resolver 使用 fixed
  repo-external root、fixed relative binding、directory fd + `O_NOFOLLOW`，拒绝 missing/mode/owner/type/symlink/
  hardlink/multiline drift，错误不含 path 或 token。
- T02: `PASS` — real temporary canonical + linked worktree 验证同一 Git common-dir、同名 `change/N`、
  clean HEAD、fresh `origin/main` ancestry 与 exact ref；wrong repo/detached/dirty/other N/merge/refspec 均拒绝。
- T03: `PASS (focused protected-file candidate)` — `GovernedHostRunner` 两个 fresh instances 只生成 fixed
  installed broker argv；无 direct `curl`/credential-store command/`git push` fallback、无 merge surface。
  fake-root installer 精确移除 legacy Keychain helper，二次 byte-identical 且明确 `no-op`，不创建 credential。
- Focused host-access suite: `PASS` — 39 tests。
- Keychain surface scan: `PASS` — runtime/manifest 无 `/usr/bin/security`、Security.framework、
  `find-generic-password` 或 `macos-keychain`；legacy C helper source 已删除。
- `bash -n` / ShellCheck / strict JSON / `git diff --check`: `PASS`。
- Pre-rebase full platform smoke: `PASS (305 tests)` on the #70 candidate before Issue #65 was merged to `main`。
- Final fresh-main full platform smoke: `FAIL (inherited Issue #65 gate)` — both final runs stop at
  `FAIL: Issue #65 final evidence bytes or mode are invalid`。The evidence SHA-256 equals the exact expected
  `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89`, but `origin/main` stores the file as
  Git mode `100644`/worktree mode `644` while the newly merged #65 test requires `444`。The #70 diff does not touch
  `docs/changes/65/` or either #65 lifecycle test; the explicit #70 boundary forbids changing or bypassing that E2E。

## Live canary and delivery

- Protected-file candidate install/read-back/second no-op: `PASS`; both user-run installer invocations completed and
  final installed bytes were compared to the repository candidate。
- Exact manager/project credential-file provision/read-back: `PASS`; one approved provision copied only the three fixed
  manifest bindings from the existing VM protected store, then metadata/read audit passed without credential output。
- Issue #70 typed mutation/read-back: `PASS`; comment id `2743`, read-back `comments=1`, state remains open。
- exact `change/70` push/read-back: `PASS`; first delivery head
  `d643cd286ea28b42b6fcea95c14a7fde6e681989` was fetched back from `origin/change/70` and matched local HEAD。
- unique `Closes #70` PR create/read-back: `PASS`; PR #72 is the only open PR, `head=change/70`, `base=main`,
  `merged=false`, `mergeable=true`。The final documentation commit is pushed through the same exact operation and
  read back again before handoff; its SHA is external evidence because a commit cannot contain its own SHA。
- live protection: `PASS`; direct/force push disabled, merge allowlist is only `admin`, admin override blocked。
- final-head required CI: `NOT CONFIGURED / NOT RUN`; live protection has `enable_status_check=false`, empty
  `status_check_contexts`, and the commit-status read returned `total_count=0`/`statuses=null`, so its aggregate
  `pending` is not a required-CI failure or PASS, and local tests cannot be presented as remote CI PASS。
- Historical Keychain prompt after exact-prefix approval: `FAIL (first candidate)` — aggregate exact ACL probe caused multiple
  per-item prompts and then `CREDENTIAL_UNAVAILABLE`; no Gitea mutation occurred。`FAIL (second candidate)` — native
  probe 已移除，但新增的 `default-keychain` path 仍导致一次 project-agent credential prompt，并在任何 Gitea
  request 前 fail closed。`FAIL (third candidate)` — 恢复 #61 exact binding 后仍弹窗，任务在用户授权前主动
  终止；用户拒绝全部遗留 dialogs。Final protected-file candidate 没有 Keychain runtime surface，live 结果
  现已由 protected-file candidate 取代，且 installed runtime 没有 Keychain access surface。
- repeated Codex host approval after exact-prefix approval: `PASS (current fresh task)`; subsequent typed operations did
  not request per-command approval。A separate post-merge fresh task remains required before this becomes a post-merge PASS。
- PR merge: `NOT RUN`; human only.

## Post-merge gate

- exact merged protected-main bytes: `NOT RUN`.
- merged-byte install + second no-op: `NOT RUN`.
- separate fresh-task follow-up canary: `NOT RUN`.

## Forbidden-scope audit

- protection/ACL/account/PAT/permission/merge mutation: `NOT PERFORMED`.
- Docker/VM/profile/service/database/migration/Nginx/deployment/restart/prune: `NOT PERFORMED`.
- Secret mutation: `PERFORMED ONLY WITH EXPLICIT APPROVAL` for the exact three-file protected-store provision; no token
  creation/rotation/revocation, output or repository write occurred。
- NewEmaint, Issue #65 E2E or any business project: `NOT MODIFIED`.
