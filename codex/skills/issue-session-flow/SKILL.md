---
name: issue-session-flow
description: Coordinate one AISoftPlatform Issue per Codex task from approved contract through PR/CI handoff, then complete post-merge cleanup and archive. Use when creating or resuming an Issue task, coordinating several dependent Issues, preparing the final PR, waiting for human merge, or closing an already merged task.
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

## Current delivery gate

Issue #208 owns any future routine auto-merge policy. Until that contract is merged and applied, stop after the
unique final PR has passed all available checks and classification read-back is `projected`. Never merge the PR.

Return one compact handoff:

```text
需要你合并 — #N <标题>
PR: <url>
变更: <一句话>
CI: <真实读回状态；未运行就写 NOT RUN>
判级: <apply-classification-labels.sh --verify N 的真实读回>
未执行: <安装、部署、live apply 等>
合并后请确认，我再做终态核对、清理和归档。
```

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
7. Report the cleanup result and archive the Codex task when the user confirms final archival.

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
