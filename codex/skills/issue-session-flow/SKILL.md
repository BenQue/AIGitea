---
name: issue-session-flow
description: Coordinate one AISoftPlatform Issue per Codex task through contract/start confirmation, final-PR confirmation, manual or eligible routine merge, and deterministic post-merge cleanup. Use when creating or resuming an Issue task, coordinating dependent Issues, preparing the final PR, waiting for human merge, following routine hard gates, or closing an already merged task.
---

# Coordinate an AISoftPlatform Issue task

Use one Codex task for one Issue. Open it in the target project's checkout and keep all implementation in the
Issue's exact isolated worktree. A coordination task may sequence several Issues, but it never implements them.

## Default autonomy after approval

Once the user approves the Issue contract or an explicit implementation plan, continue without intermediate
confirmation through:

- evidence gathering and deterministic classification;
- contract document completion;
- in-scope implementation and local commits;
- tests, ordinary repair and required wider gates;
- classification projection.

After final-PR submission confirmation, continue through branch push, the one final PR and in-contract PR CI
repair without another confirmation. Contract/start approval alone does not authorize push or PR creation.

Pause only for a contract conflict, scope expansion, destructive migration, a new security/permission/architecture
decision, a direct production action, a missing external dependency, unreliable verification, or three consecutive
attempts with the same root cause. A sandbox/network approval required by the host is an execution permission, not
a new product decision.

## Single-writer ownership of a change worktree

**A change worktree has exactly one writer: the session that owns its Issue.** Another session
that notices it needs a rebase, a conflict resolution or a re-run may **notify** that session or
**hand it back** — never do it for them, even when the change itself is right. `git rebase`,
`git commit` and `git checkout` never reach the broker, so work done on someone else's behalf
leaves no trace on the platform at all.

Claim the worktree right after `git worktree add`, and carry the same session id on every broker
push:

```bash
AISOFT_SESSION_ID=<this session id> PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli \
  claim-worktree --branch change/N-short-description --worktree /private/tmp/issue-N-short-description
```

**For the first push, compare `pushed_head` with the exact head verified in the final-PR candidate at
confirmation point 2. For each subsequent push after PR summary-only backfill or in-contract CI repair,
compare it with the exact head freshly verified and recorded for that push.** Every comparison is mandatory;
do not reuse the first candidate's old SHA or skip the read-back. Before each subsequent push, check this
session's ownership, the exact branch, the new diff against the approved contract, required local validation
and a clean worktree, then record the current 40-character lowercase head SHA. `previous_head` is audit
information, not the current comparison anchor. Submission authorization remains bound to exact
Issue/branch/policy; legitimate backfill and in-contract CI commits do not require a new confirmation each.
The ownership marker checks who pushes; it does not replace the broker's independent provenance,
ancestry, full-content and FF validation. Stop on scope expansion, another session's rewrite or any
`pushed_head` mismatch and investigate before proceeding; never adopt an unexplained head as a new anchor.
If the first candidate changes after confirmation, stop and update candidate validation evidence first.

When cross-session interference is suspected, scan read-only (it writes nothing):

```bash
PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli scan-worktrees --repo <checkout>
```

`rewritten`, `unclaimed` and `claim-invalid` count as GAP; `ahead` and `unpushed` are the normal
state during implementation and are listed without counting.

## #327 当前收缩合同（2026-10-05）

本票只交付保留 original/current remote tip 祖先关系的 main 整合、普通 FF、非法/并发漂移拒绝、required CI 与可恢复收尾。以 [#327 spec](../../../docs/changes/327-broker-ff-integration/spec-broker-ff-integration-261002.md) 的当前合同为准；T01/T04–T10 为历史治理步骤，原 FAIL/GAP/NOT RUN 保留。

Agent/provider 只追加本 Issue 的线性本地 commit。合格现有 Controller 可按合同整合；本票首次自举明确允许**负责人本人**用标准 Git 在原 owner worktree 临时保全/park WIP、构造 `[已核验 Issue tip, fresh manifest main]` 并留恢复证据，Agent 不代执行。它不再等待未交付 R02、root authority、OS observer 或 protected grant。仅无冲突标准整合；冲突停止并保留 stash/前态，不自动覆盖内容。

最终唯一 PR 的第二确认仍绑定 exact Issue/branch/manual。确认前不发表；确认后本票可由本人使用已绑定的普通 Git credential helper、经过本票测试的固定 pre-push guard 和 exact SHA 单 ref 普通 FF 完成首次发表，不调用旧 lease-force broker、不装 unmerged broker，Agent 不借此绕 broker。来源/DAG/tree/范围、R0/R/M/H、guard 执行和真实 readback 必须核对；main 禁直推/force、required CI、本人 manual merge 不变。实际首次发表/installed 验收未运行仍为 GAP/NOT RUN。

root authority、begin/verify、ES/kernel/signing、完整 OS/解释器闭包、scratch/resource 隔离及其 I01/I02/AC-9～11 延期，不作为本票当前 source 整合/PR 的前置；不宣称这些安全能力已交付，也不以本地 receipt/owner marker 证明不可伪造授权或同 UID 隔离。Mac/VM 安装均需 source 合并后另获授权。本轮仅治理文本与证据应用、校验、本地 commit 后 STOP；下一 fresh run 重读后才续 T02。

## Two default confirmation points

The first point is contract/start confirmation. After triage, classification, and every required semantic document
are complete, present the exact Issue contract and ask once to start the Development Loop. Persist that decision as
the validated `approved` state. It authorizes in-scope implementation and repair, not PR submission, merge, or deploy.

The second point is final-PR submission confirmation. After local verification, the Controller persists
`AWAITING_PR_CONFIRMATION`. Repeated polls in that state must not
call a provider, push, or create a PR. Return exactly one policy-specific candidate handoff.

For `manual`:

```text
🟠 准备提交最终 PR —— #N <标题>
Branch: change/N-<slug>
Policy: manual
变更: <一句话>
验证: <真实结果；未运行写 NOT RUN>
判级: <classification read-back>
未执行: <install、credential、protection apply、deploy 等>

请确认提交唯一最终 PR。确认后可继续当前合同内的 PR CI 修复；required CI 全绿后停在
READY_FOR_REVIEW，等待你人工审核并合并。部署不在本次授权内。
```

For an eligible `routine-auto` candidate:

```text
🟠 准备提交最终 PR —— #N <标题>
Branch: change/N-<slug>
Policy: routine-auto
变更: <一句话>
验证: <真实结果；未运行写 NOT RUN>
判级: <classification read-back>
未执行: <install、credential、protection apply、deploy 等>

请确认提交唯一最终 PR。你的确认明确包含：
“当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，允许受控自动合并。”

该授权绑定 exact Issue #N、change/N-<slug> 与 routine-auto policy，不绑定当前 SHA；实际合并必须钉住
最终 40 位 lowercase head SHA。部署不在本次授权内。
```

The `判级:` line must come from a real read-back with
`codex/tools/apply-classification-labels.sh --repo <checkout> --verify N`, using the exact Issue number, never
`--range`. Enter the final-PR candidate state only when both classification dimensions read back as `projected`.
For `projection-missing` or `projection-mismatch`, repair the in-contract projection and re-read it; report a
`broker-operation-missing` or other unreadable result as a blocker. Merge permanently closes the projection
window: `projection-window-closed` is evidence of an omission, never permission to backfill or override it.

The manual text must not contain the controlled-auto-merge marker. A routine hard-gate failure returns one stable
reason with zero merge POST and no silent fallback. Manual work stops at `READY_FOR_REVIEW`. A routine
`AUTO_MERGED` receipt immediately enters deterministic post-merge completion without a third confirmation.

Do not ask again about choices already fixed in the approved contract. Do not turn every ticket, test command,
commit or CI retry into a confirmation point.

## Post-merge completion

After proving the manual merge or receiving a routine `AUTO_MERGED` receipt:

1. Fetch and prove that the exact merge commit is on `origin/main`.
2. Dry-run `codex/tools/mark-completed-issues.sh --repo <checkout> --range <range>`. Check the first
   `selector: range` row's `commits` and each Issue row's `commit` against the exact merge from step 1; a moving
   `origin/main~N` range is not evidence by itself. Stop if the plan targets another merge. Run classification
   read-back again with `codex/tools/apply-classification-labels.sh --repo <checkout> --verify N`, using the Issue
   number. Report `projection-window-closed` truthfully; do not backfill closed Issues or add an override.
3. The proved merge or routine receipt authorizes deterministic terminal reconciliation. Apply the checked plan
   with `codex/tools/mark-completed-issues.sh --repo <checkout> --apply <pinned>`, using the plan's immutable Issue
   numbers; never re-use `--range` for the apply. Let the tool decide from mapped summary `required_docs` and the
   manifest's `deployment_lifecycle`. Read an unfamiliar reason's detail rather than guessing a lifecycle label;
   never infer deployment.
4. Run `check-change-documents` against the merged checkout.
5. Leave and remove the Issue worktree, then delete the merged local change branch.
6. Record any genuinely separate acceptance criterion as a new Issue instead of extending the closed one.
7. Report exact merge/receipt, terminal state, document check, cleanup, and every unrun action, then archive the
   completed task without another confirmation. If any deterministic completion step fails, report the stable blocker
   and keep the task available; do not claim archival or completion.

## Multi-Issue coordination

Create a coordination task only for a phase that must split, a batch of newly created Issues, or several existing
Issues with dependencies. Persist every dependency in the Issue body and summary `depends_on`; do not rely on task
memory. Dispatch only unblocked Issues and keep their branches, worktrees and PRs separate.

Dependency identity (#286 source/local fixtures verified; installed/live pending): legacy numeric
`depends_on` entries refer only to the source repository. Cross-repository dependencies require exact
`owner/repo#N`, never a bare foreign number. The new read must be manifest-bound before GET, with
`dependency_read_targets` defaulting to local only and the sole new edge `sfm-digital-board → aisoft-platform`.
Controller and routine merger must share identity/terminal checks; a local same-number Issue never
satisfies a foreign dependency. Cross-repository reads use only the broker's manager-audit read-only
route, with zero credential/ACL/direct-client fallback. An unsupported or unreadable dependency is a
blocker; do not replace it with a number or `[]`. Document the full reference in the Issue body until the
runtime is implemented and independently installed. A documentation example is not live enablement.

## Open-Issue sweep

The coordination task's second duty. Sweep the open Issues every time the task wakes up, and again after a batch of
Issues has been dispatched. A sweep judges and dispatches; it never implements an Issue.

Enumeration: one `gitea.issue.list --state open` (#222). It pages through the whole tracker, excludes pull
requests and carries no bodies, giving `number`, `title`, `state` and `labels` per Issue -- enough to compare
titles for duplicates; read one Issue's text by number with `gitea.issue.read`. A `REQUEST_DENIED` means this
machine's broker operation table is stale: reinstall on both hosts and retry, do not chase it as a permission
problem.

Entry label: a new Issue carries its entry label from the same write that creates it, `needs-analysis` or
`triage/needs-triage`. An older Issue may carry no label at all; backfill it with
`gitea.issue.labels.set --number N --lifecycle needs-analysis`.

Report one row per open Issue in a fixed six-column table: number, title, owning repository, duplicate-of,
judgement, next step. The judgement is exactly one of `dispatch`, `duplicate`, `blocked by #M`, or `needs a human
decision`. "Leave it for now" is not a judgement -- it is the action that let the open Issues pile up.

Summarise every `needs a human decision` row in fixed three-part lines:

```text
需裁决（n 条）
- #N <one-line question> —— 选项 A：<consequence> / 选项 B：<consequence>；不裁决的后果：<one line>
```

Do not pick a default on the user's behalf, and do not dispatch an Issue that is waiting on one.

## Invariants

- All Gitea and remote Git access uses the project-scoped host-access broker.
- A task never implements another Issue opportunistically.
- A session never writes in a change worktree it does not own; it notifies or hands back (#298).
- A push is not done until `pushed_head` has been compared with the verified sha.
- `approved` starts development; it does not authorize merge or deployment.
- An open PR is not delivery, a green workflow is not deployment, and an unrun check is never PASS.
- Never print credentials or copy Claude/Codex authentication between providers.
