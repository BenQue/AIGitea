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
status: awaiting-merge
branch: change/73
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/74
created: 2026-08-09
updated: 2026-08-09
---

# Manifest-fixed Gitea remote verification

## Environment and live baseline

| Check | Result | Evidence |
|---|---|---|
| isolated worktree | PASS | `/Users/benque/.codex/worktrees/9338/AISoftPlatform`; canonical and Issue #65 dirty/untracked worktrees only read, never edited |
| fresh protected main | PASS | installed broker `git.fetch.main` fetched `origin/main=4e26ba063350579e7b2dfad633a2085e505243d0`; local detached baseline matched before `change/73` creation |
| Issue #73 | PASS / APPROVED | live broker read: open；triage Agent Brief comment id `2765` 已发布；合同 labels 已读回 `approved`、`complexity/complex`、`triage/enhancement`、`triage/ready-for-agent`、`type/platform` |
| label manifest | PASS | 用户精确批准后只创建缺失的 7 个 `triage/*` labels；readback 为 `created=7`、canonical `24/24`、live total `24`，未删除或修改既有 label |
| branch/PR de-dup | PASS | local/remote `change/73` absent before creation；installed-broker open PR read returned `[]` |
| #70/#72 merged baseline | PASS | Issue #70 closed；PR #72 closed+merged by `admin`，merge SHA equals fresh main；`/pulls/70` is 404 because 70 is the Issue, not its PR number |
| platform required CI | NOT CONFIGURED / NOT RUN | protection `enable_status_check=false`、contexts `[]`；PR #72 head and fresh main status both `total_count=0`/`statuses=null` |
| installed bytes | PASS | 15 installed runtime/config/wrapper targets byte-equal freshly fetched protected main；catalog 21 operations、9 projects、0 merge |
| AISoftPlatform aggregate access | PASS | protected-file metadata、three identities、exact scopes、manager Admin、project-agent Write、human-only protection all read back |
| NewEmaint aggregate access | PASS (baseline drift from Issue body) | protected credential now exists and validates `newemaint-agent` identity/scopes/Write plus required `CI / verify (pull_request)` |
| NewEmaint dual remote | PASS (read-only metadata) | canonical checkout has GitHub `origin` and exact internal `gitea=http://gitea-ci.orb.local:3000/admin/NewEMaint.git`; worktree clean on paused `change/4` |
| NewEmaint repo-local binding | MISSING / EXPECTED PRE-ADOPTION | `credential.useHttpPath`、Gitea URL-scoped helper and username are absent |
| defect reproduction | PASS (expected failure) | installed broker `git.fetch.main` returns sanitized `TARGET_MISMATCH` because runtime checks GitHub `origin`; no fetch/push/config mutation |
| `ci-bot` | NOT ACCESSED / NOT MODIFIED | no query or mutation performed |

## Candidate verification

| Command / check | Result | Evidence |
|---|---|---|
| contract resolver | PASS | `resolve_documents(Path.cwd(), 73)` 精确返回 summary/spec/plan/verification semantic basenames |
| focused host-access tests | PASS | TDD RED 为 5 个预期缺失；实现后 `44/44 PASS`，覆盖 origin compatibility、NewEmaint gitea fetch/change/push、GitHub origin unchanged、bind twice/no-op、onboarding 与 negatives |
| host-access shell/installer twice | PASS | `codex/tests/test-host-access-broker.sh`：22 operations、9 projects、0 merge，fake-root first install + second no-op、installed files/bytes checks 全部通过 |
| runner/helper/security integration | PASS (local) | fixed broker runner、credential protocol、caller field denial、cross-project/wrong URL/identity/permission/protection/helper drift 均通过；无 direct curl/security/generic push/merge surface |
| full platform smoke | PASS with inherited-mode normalization | fresh worktree 首轮准确暴露 #65 immutable evidence mode `0644`（bytes/SHA 与 `origin/main` 相同）；仅在当前隔离 worktree 临时规范为 #65 既定 `0444` 后完整 smoke `315/315 PASS`，随后恢复 `0644`，无 tracked #65 变化 |
| bash-n / ShellCheck / JSON / Secret / diff | PASS | modified shell `bash -n` + ShellCheck、strict JSON、diff check、source/output security negatives 与 semantic resolver 全通过 |

## Acceptance criteria results

- AC-1：`PASS`（strict optional field、origin default、unsafe/extra/caller fields fail closed）。
- AC-2：`PASS (local real Git)`（NewEmaint 只使用 `gitea`；GitHub `origin` 保持不变）。
- AC-3：`PASS (local real Git)`（main/change fetch 与 exact non-force same-name push 使用 resolved remote；既有 branch/worktree/ancestry/no-merge gates 回归通过）。
- AC-4：`PASS (local real Git)`（first bind updated、second no-op；remote 不变，config 无 token/path）。
- AC-5：`PASS (local/mock aggregate)`（access/protection/required-CI + canonical/remote/helper 聚合 readback 与 drift denial 通过；live candidate adoption 未运行）。
- AC-6：`PASS`（无 Keychain/Secret/ACL/protection mutation surface；`ci-bot` 未访问）。
- AC-7：`PASS (candidate local)`；live post-merge install/fresh-session project canary 仍按 AC-9 为 `NOT RUN`。
- AC-8：`PASS (pre-merge)`；唯一 branch/docs/PR 均已读回，remote CI 为
  `NOT CONFIGURED / NOT RUN`，merge/deploy 保持 `NOT RUN`。
- AC-9：`NOT RUN BY DESIGN`；只允许平台 PR 人工合并后逐项目执行。

## Remote PR and CI

- `change/73` remote push：`PASS`；installed broker 从 fresh `origin/main=4e26ba063350579e7b2dfad633a2085e505243d0`
  校验 clean exact branch、fresh ancestry 与 no merge commit 后非强制同名 push。
- unique `Closes #73` PR：`PASS`；PR
  [#74](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/74) 为 open、non-draft、
  `change/73 → main`、`merged=false`、`mergeable=true`，body 精确包含 `Closes #73` 与 semantic summary。
- final-head required CI：`NOT CONFIGURED / NOT RUN`；live protection
  `enable_status_check=false`、contexts `[]`，final metadata head status readback 为 `total_count=0`、
  `statuses=null`。不得把 Gitea aggregate `state=pending` 误写成已配置 CI。
- PR merge：`NOT RUN`；human only。

## Post-merge project adoption gate

- exact merged protected-main install + second no-op：`NOT RUN`。
- NewEmaint adoption Issue：`NOT RUN`；只允许平台 PR 人工合并后创建。
- NewEmaint credential bootstrap/provision：`NOT RUN`；当前 access audit 已 PASS，若未来缺失仍需独立明确审批。
- NewEmaint `mac.git.bind` / onboarding readback / typed canary / required CI：`NOT RUN`。
- other manifest projects：`NOT RUN`；逐项目 Issue/evidence，不批量启用。

## Forbidden-scope audit

- NewEmaint source/GitHub origin/history：`NOT MODIFIED`。
- credential contents、Keychain、`ci-bot`、account/PAT/ACL/permission/protection：`NOT ACCESSED / NOT MODIFIED`。
- Docker、VM lifecycle/profile、Secret contents、database、migration、Nginx、deployment、restart、prune、production：`NOT RUN`。
