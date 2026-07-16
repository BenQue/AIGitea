---
name: gitea-platform-ops
description: Diagnose or improve the documented Gitea, act_runner, PM2, artifact, deployment, and rollback platform. Use for service health, CI/deploy failures, first deployments in development or test, script design, incident evidence, rollback planning, or VM-to-intranet migration. Never let AI execute normal production deployment.
---

# Operate the Gitea platform

1. Read the relevant numbered platform documents. For deployment work, read `02-CI与自动部署流水线.md` and `06-运维手册与踩坑集.md` first.
2. Select and verify the explicit project profile before reading or mutating Gitea, Git, CI, runtime, or deployment state. Never assume rsDesign or any example repository is the target.
3. Start with read-only evidence: Issue/PR/SHA/run ID, failure step and exit code, logs, runner state, release symlink, PM2 state, migration/backup state, health endpoint, and rollback result.
4. Never print credentials. Use variable names and redacted status only.
5. Treat protected `main`, the required CI context, artifact immutability, environment separation, real verification, and rollback as invariants.
6. Only projects with application deployment scope need deployment acceptance. Documentation-only platform repositories do not need synthetic PM2, artifact, or rollback flows.
7. In development/test, participate interactively in first deployment design and execution. Convert every successful manual step into a versioned script.
8. Before accepting a deployment flow, run it twice from a repeatable state and deliberately exercise one failure/rollback path. Record commands and results in `03-verification.md`.
9. For SQLite, stop the app before migration, back up with `sqlite3 .backup` under WAL, switch the release symlink, use PM2 delete+start, assert online, then health-check.
10. In production, allow only pre-validated artifacts and scripts. Do not generate or execute ad hoc production commands, modify scripts in place, bypass checks, or auto-retry dangerous operations.
11. For production failures, stop/rollback first, analyze sanitized evidence, reproduce and fix in non-production, verify, and prepare a PR before a human reruns production scripts.
12. Report observed, changed, verified, and pending separately. Never claim an unrun check passed.
