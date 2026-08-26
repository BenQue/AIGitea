# Private local Gitea access

Use this procedure before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting.

## Resolve the exact target

1. After Issue #61 is released, select the exact project and an allowlisted operation through
   `/usr/local/libexec/aisoft/host-access-broker`; target and identity come from the strict manifests.
2. Broker Git operations resolve the remote name only from the project manifest. Missing
   `git_remote_name` means `origin`; a declared value such as NewEmaint's `gitea` is fixed and cannot be supplied by
   the caller.
3. Match `GITEA_URL`, `GITEA_OWNER`, and `GITEA_REPO` to the requested repository before using credentials.
4. Never source the generic `~/.agent.env` when an exact project profile is available. Never infer the repository from a pilot or example.

## Use the authenticated access ladder

1. **Project profile API**: use the exact mode 400/600 project-agent profile as `coder` and the read-only
   helper. This is the preferred Issue/PR/Actions path and must bind only one repository.
2. **Configured Git credential**: use the checkout's Gitea remote for `git ls-remote`, fetch, or ancestry checks. If the host sandbox blocks `.orb.local`, retry through the approved host-network path; do not call that an authentication failure.
3. **Platform manager audit PAT**: Issue #35 live reconciliation 后，跨项目 settings/protection inventory
   使用 manager 的独立 read-only PAT 和 `gitea-governance.sh check`；不得用 mutation PAT 或普通 Git
   代替。
4. **VM-local admin read-only fallback**: when no project profile/manager exists or ACL blocks the exact
   target, use the existing mode 600 administrator credential file only inside `gitea-ci`, through the
   read-only helper. Do not copy the token to the Mac or add bot permissions.
5. **Authenticated browser fallback**: use an existing signed-in browser session for read-only UI evidence when the helper is unavailable or the UI itself matters.

Never begin a private-repository existence check with an anonymous API request. Anonymous `404` and Git `Repository not found` are inconclusive: they can mean private visibility or ACL failure.

The normal post-#61 path does not run `orbstack-access-diagnostics`. That skill is emergency-only when the
broker itself fails and sanitized host/sandbox evidence still contradicts. Normal acceptance must record zero
diagnostics invocations. The broker never accepts a URL, owner/repository, checkout/credential path, shell,
force/refspec, or merge argument.

For project onboarding, keep access, Secret mutation, binding, and acceptance separate. Run
`host.access.audit`; if a protected credential is missing, stop for separate explicit approval. Then run
`mac.git.bind` and read back with `host.onboarding.check`. The final check fails closed on credential metadata,
identity/scope, permission, protection/required CI, canonical checkout, manifest remote fetch/push URL, or exact
repo-local helper drift. It is read-only and does not provision credentials or alter remotes.

## Helper commands

Preferred post-#61 host command:

```bash
/usr/local/libexec/aisoft/host-access-broker \
  --project <manifest-project-id> \
  --operation gitea.issue.read \
  --number <issue-number>
```

Project onboarding readback takes no target overrides:

```bash
/usr/local/libexec/aisoft/host-access-broker \
  --project <manifest-project-id> \
  --operation host.onboarding.check
```

The following helpers are compatibility/fallback paths, not the normal host entrypoint.

With an exact project profile:

```bash
orb -m gitea-ci -u coder bash -lc '
  AGENT_ENV_FILE=/home/coder/.config/aisoft/projects/<profile>.env \
  GITEA_EXPECT_OWNER=<owner> \
  GITEA_EXPECT_REPO=<repo> \
  /home/coder/agent/gitea-readonly.sh "issues?state=all&type=issues&limit=50"
'
```

If the installed helper is not yet present, use the authoritative mounted source:

```text
/mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/gitea-readonly.sh
```

For an authorized VM-local administrator read-only fallback:

```bash
orb -m gitea-ci -u benque bash -lc '
  GITEA_URL=http://127.0.0.1:3000 \
  GITEA_OWNER=<owner> \
  GITEA_REPO=<repo> \
  GITEA_EXPECT_OWNER=<owner> \
  GITEA_EXPECT_REPO=<repo> \
  GITEA_CREDENTIAL_FILE=/home/benque/gitea-ci-credentials.txt \
  /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/tools/gitea-readonly.sh \
    "issues?state=all&type=issues&limit=50"
'
```

Pipe the JSON to a narrow `jq` projection. Do not print environment files, credential files, curl configuration, request headers, or raw logs that may contain secrets.

## Mutation boundary

`gitea-readonly.sh` only performs GET. Issue/comment/label/branch/PR 使用 exact project agent；跨项目
settings/permissions/protection mutation 只能由已合并 Issue #35 的 purpose-built governance 命令一次
处理一个 manifest repository。manual merge 保留给 human identity；routine merge 只允许 broker 的
`gitea.pull.merge.routine` typed operation，调用方只传 PR number 与 exact 40-character lowercase head SHA。
owner/repo/base/identity/method/delete-branch/force/schedule/deploy policy 全由 strict manifest 派生；普通
project API、Git credential、manager PAT 或 admin fallback 都不得代替 routine merger。Never broaden a
bot's ACL merely to make inspection convenient.
