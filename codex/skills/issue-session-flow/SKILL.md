---
name: issue-session-flow
description: Coordinate one AISoftPlatform Issue per Codex task through final-PR confirmation, manual or eligible routine merge, deterministic post-merge cleanup, and archival confirmation. Use when creating or resuming an Issue task, coordinating dependent Issues, preparing the final PR, waiting for human merge, following routine hard gates, or closing an already merged task.
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
- classification projection, branch push, the one final PR and PR CI repair.

Pause only for a contract conflict, scope expansion, destructive migration, a new security/permission/architecture
decision, a direct production action, a missing external dependency, unreliable verification, or three consecutive
attempts with the same root cause. A sandbox/network approval required by the host is an execution permission, not
a new product decision.

## Two default confirmation points

After local verification, the Controller persists `AWAITING_PR_CONFIRMATION`. Repeated polls in that state must not
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

The manual text must not contain the controlled-auto-merge marker. A routine hard-gate failure returns one stable
reason with zero merge POST and no silent fallback. Manual work stops at `READY_FOR_REVIEW`. A routine
`AUTO_MERGED` receipt immediately enters deterministic post-merge completion without a third confirmation.

Do not ask again about choices already fixed in the approved contract. Do not turn every ticket, test command,
commit or CI retry into a confirmation point.

## Post-merge completion

After the user confirms merge:

1. Fetch and prove that the exact merge commit is on `origin/main`.
2. Dry-run the terminal lifecycle tool and verify classification projection.
3. Apply a terminal label only with the authority required by the current platform contract; never infer deployment.
4. Run `check-change-documents` against the merged checkout.
5. Leave and remove the Issue worktree, then delete the merged local change branch.
6. Record any genuinely separate acceptance criterion as a new Issue instead of extending the closed one.
7. After merge, terminal reconciliation, document checks and cleanup all complete, return the second confirmation:

```text
🟢 #N 已完成
Merge: <manual|routine-auto> · <merge receipt / exact merge SHA>
终态: <completed|deployed|真实阻塞状态>
文档: <check-change-documents 真实结果>
清理: <worktree 与本地 change branch 真实结果>
未执行: <deploy、live apply 等>

本 Issue 的 merge、终态核对、文档检查与本地清理已完成。是否确认归档本会话？
```

Archive the Codex task only after that explicit archival confirmation.

## Multi-Issue coordination

Create a coordination task only for a phase that must split, a batch of newly created Issues, or several existing
Issues with dependencies. Persist every dependency in the Issue body and summary `depends_on`; do not rely on task
memory. Dispatch only unblocked Issues and keep their branches, worktrees and PRs separate.

## Invariants

- All Gitea and remote Git access uses the project-scoped host-access broker.
- A task never implements another Issue opportunistically.
- `approved` starts development; it does not authorize merge or deployment.
- An open PR is not delivery, a green workflow is not deployment, and an unrun check is never PASS.
- Never print credentials or copy Claude/Codex authentication between providers.
