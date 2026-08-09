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
status: implementing
branch: change/70
pr_url: null
created: 2026-08-09
updated: 2026-08-09
---

# Governed non-interactive host writes verification

## Baseline

| Check | Result | Evidence |
|---|---|---|
| isolated worktree | PASS | `/Users/benque/.codex/worktrees/fc5b/AISoftPlatform`; canonical and other worktrees untouched |
| fresh default baseline | PASS | `origin/main` fetched 2026-08-09 11:17:33 +08:00 to `7ef7fa23af202343335f99ea746b4dd7a64cbd71`; worktree created 11:31:49 and `change/70` created from that SHA |
| Issue #70 | PASS | installed broker live read: open, labels `approved` + `complexity/complex` + `type/platform`; body matches this contract |
| local/remote-tracking de-dup | PASS | before branch creation, local `change/70` and `origin/change/70` refs absent; live remote de-dup still pending aggregate audit |
| #35/#61/#67 ancestry | PASS (local fetched ref) | local `origin/main` contains merge commits `69251fd4`, `58daf44b`, `dd5b2b9`; live Issue/PR state read-back pending aggregate audit |
| installed source bytes | STALE CANDIDATE | installed bytes matched commit `ef4a295`; that third Keychain candidate failed live and is superseded by the uninstalled protected-file candidate |
| installed operation catalog | CONFIRMED DEFECT | 13 operations; no Issue/PR writes; `git.push.change` runs only in manifest canonical checkout |
| repo-local Git credential binding | PASS (local metadata) | fixed helper + `credential.useHttpPath=true` + `aisoft-platform-agent`; no token in config |
| sandbox broker credential | BLOCKED_EXTERNAL (historical) | old Keychain candidate returned `CREDENTIAL_UNAVAILABLE`; protected-file candidate is not installed/provisioned |
| host broker Issue read | PASS | same installed broker successfully read #70 through fixed project-agent binding |
| Codex repeated approval | FAIL | six parallel read-only broker invocations generated repeated host approvals; batch terminated, no mutation occurred |
| Keychain route | RETIRED BY CONTRACT | three candidates generated interactive access despite ACL metadata; user rejected remaining dialogs and explicitly approved complete Mac runtime Keychain removal |
| live accounts/token scopes/permission/protection/open PR | NOT RUN | deferred to one candidate aggregate audit to avoid repeated approval prompts |
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
- Full platform smoke: `PASS (protected-file candidate)` — 305 tests，最终输出
  `Codex platform static smoke checks passed.`。

## Live canary and delivery

- Protected-file candidate install/read-back/second no-op: `NOT RUN`.
- Exact manager/project credential-file provision/read-back: `NOT RUN`; installer 不创建/复制/更新 token。
- Issue #70 typed mutation/read-back: `NOT RUN`.
- exact `change/70` push/read-back: `NOT RUN`.
- unique `Closes #70` PR create/update/read-back: `NOT RUN`.
- final-head protection/required CI: `NOT RUN`.
- Historical Keychain prompt after exact-prefix approval: `FAIL (first candidate)` — aggregate exact ACL probe caused multiple
  per-item prompts and then `CREDENTIAL_UNAVAILABLE`; no Gitea mutation occurred。`FAIL (second candidate)` — native
  probe 已移除，但新增的 `default-keychain` path 仍导致一次 project-agent credential prompt，并在任何 Gitea
  request 前 fail closed。`FAIL (third candidate)` — 恢复 #61 exact binding 后仍弹窗，任务在用户授权前主动
  终止；用户拒绝全部遗留 dialogs。Final protected-file candidate 没有 Keychain runtime surface，live 结果
  仍为 `NOT RUN`。
- repeated Codex host approval after exact-prefix approval: `NOT RUN (final candidate)`.
- PR merge: `NOT RUN`; human only.

## Post-merge gate

- exact merged protected-main bytes: `NOT RUN`.
- merged-byte install + second no-op: `NOT RUN`.
- separate fresh-task follow-up canary: `NOT RUN`.

## Forbidden-scope audit

- protection/ACL/account/PAT/permission/merge mutation: `NOT RUN`.
- Docker/VM/profile/service/Secret/database/migration/Nginx/deployment/restart/prune: `NOT RUN`.
- NewEmaint, Issue #65 E2E or any business project: `NOT MODIFIED`.
