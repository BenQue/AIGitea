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
| installed source bytes | PASS | broker/helper/access+governance manifests/runtime broker+contract are root-owned and byte-equal to baseline source; hashes recorded in task evidence |
| installed operation catalog | CONFIRMED DEFECT | 13 operations; no Issue/PR writes; `git.push.change` runs only in manifest canonical checkout |
| repo-local Git credential binding | PASS (local metadata) | fixed helper + `credential.useHttpPath=true` + `aisoft-platform-agent`; no token in config |
| sandbox broker credential | BLOCKED_EXTERNAL | `CREDENTIAL_UNAVAILABLE`; sandbox Keychain path unavailable |
| host broker Issue read | PASS | same installed broker successfully read #70 through fixed project-agent binding |
| Codex repeated approval | FAIL | six parallel read-only broker invocations generated repeated host approvals; batch terminated, no mutation occurred |
| Keychain ACL shape | PASS, INTERACTIVE ONLY | first installed candidate reached all three exact ACL checks, proving default-user generic-password items with `/usr/bin/security` and no require-password; however custom helper access generated per-item prompts and is therefore forbidden from the final runtime path |
| live accounts/token scopes/permission/protection/open PR | NOT RUN | deferred to one candidate aggregate audit to avoid repeated approval prompts |
| `ci-bot` | NOT ACCESSED / NOT MODIFIED | no query or mutation performed |

## Candidate tests

- T01: `PASS (revised candidate)` — Issue create/read/update/comment、PR create/read/update、SHA status read、
  identity/scope/permission/protection audit 的 public seam 与 fail-closed negatives 通过；runtime 不调用 native
  ACL reader、`default-keychain` 或 `dump-keychain`，credential resolver 恢复 Issue #61 已验证的固定
  `find-generic-password -s <service> -a <account>` 形状，不附加 Keychain path。
- T02: `PASS` — real temporary canonical + linked worktree 验证同一 Git common-dir、同名 `change/N`、
  clean HEAD、fresh `origin/main` ancestry 与 exact ref；wrong repo/detached/dirty/other N/merge/refspec 均拒绝。
- T03: `PASS (candidate/static)` — `GovernedHostRunner` 两个 fresh instances 只生成 fixed installed broker
  argv；无 direct `curl`/`security`/`git push` fallback、无 merge surface。fake-root installer 两次 byte-identical，
  第二次明确 `no-op`；native helper catalog 与 9 个 manifest project-agent byte-exact，unknown project 在
  Keychain query 前 exit 20。
- Focused host-access suite: `PASS` — 38 tests。
- C hardening: `PASS` — `clang -Wall -Wextra -Werror`；兼容 helper 是无 Security.framework/query surface 的
  exit-20 tombstone。
- `bash -n` / ShellCheck / strict JSON / `git diff --check`: `PASS`。
- Full platform smoke: `PASS` — 304 tests，最终输出 `Codex platform static smoke checks passed.`。

## Live canary and delivery

- Candidate install/read-back/second no-op: `NOT RUN`.
- Issue #70 typed mutation/read-back: `NOT RUN`.
- exact `change/70` push/read-back: `NOT RUN`.
- unique `Closes #70` PR create/update/read-back: `NOT RUN`.
- final-head protection/required CI: `NOT RUN`.
- Keychain prompt after exact-prefix approval: `FAIL (first candidate)` — aggregate exact ACL probe caused multiple
  per-item prompts and then `CREDENTIAL_UNAVAILABLE`; no Gitea mutation occurred。`FAIL (second candidate)` — native
  probe 已移除，但新增的 `default-keychain` path 仍导致一次 project-agent credential prompt，并在任何 Gitea
  request 前 fail closed。Third candidate 同时移除 native probe 与 Keychain path，恢复 #61 exact binding；live
  结果仍为 `NOT RUN`。
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
