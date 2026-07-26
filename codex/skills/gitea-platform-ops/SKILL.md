---
name: gitea-platform-ops
description: Diagnose or improve the documented Gitea, act_runner, PM2, artifact, deployment, and rollback platform. Use for private local Gitea repository, Issue, PR, Actions, branch-protection, or authentication inspection; service health; CI/deploy failures; first deployments in development or test; script design; incident evidence; rollback planning; or VM-to-intranet migration. Never let AI execute normal production deployment.
---

# Operate the Gitea platform

1. Read the relevant numbered platform documents. For deployment work, read `02-CI与自动部署流水线.md` and `06-运维手册与踩坑集.md` first.
2. Select and verify the explicit project profile before reading or mutating Gitea, Git, CI, runtime, or deployment state. Never assume rsDesign or any example repository is the target.
3. For a private repository, never begin with anonymous API access. Use this order:
   - exact mode 400/600 project profile as `coder` with `~/agent/gitea-readonly.sh`;
   - configured Git credential for refs and ancestry;
   - authorized VM-local administrator credential with the read-only helper when no profile/ACL exists;
   - existing authenticated browser session for read-only UI evidence.
4. Treat private `404` and Git `Repository not found` as identity/ACL-or-existence ambiguity. Verify authentication and ACL before concluding that an object was deleted or never existed.
5. Do not automatically create a profile, copy a token, or grant bot access to fix inspection. Keep API mutation in purpose-built scripts or explicitly authorized browser actions.
6. Start with read-only evidence: Issue/PR/SHA/run ID, failure step and exit code, logs, runner state, release symlink, PM2 state, migration/backup state, health endpoint, and rollback result.
7. Never print credentials. Use variable names and redacted status only; project output must not include profile, credential file, request header, or curl config contents.
8. Treat protected `main`, the required CI context, artifact immutability, environment separation, real verification, and rollback as invariants.
9. Only projects with application deployment scope need deployment acceptance. Documentation-only platform repositories do not need synthetic PM2, artifact, or rollback flows.
10. In development/test, participate interactively in first deployment design and execution. Convert every successful manual step into a versioned script.
11. Before accepting a deployment flow, run it twice from a repeatable state and deliberately exercise one failure/rollback path. Record commands and results in `03-verification.md`.
12. For SQLite, stop the app before migration, back up with `sqlite3 .backup` under WAL, switch the release symlink, use PM2 delete+start, assert online, then health-check.
13. In production, allow only pre-validated artifacts and scripts. Do not generate or execute ad hoc production commands, modify scripts in place, bypass checks, or auto-retry dangerous operations.
14. For production failures, stop/rollback first, analyze sanitized evidence, reproduce and fix in non-production, verify, and prepare a PR before a human reruns production scripts.
15. Report observed, changed, verified, and pending separately. Never claim an unrun check passed.
