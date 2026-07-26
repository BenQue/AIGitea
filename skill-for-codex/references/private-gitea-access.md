# Private local Gitea access

Use this procedure before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting.

## Resolve the exact target

1. Read the current checkout's Gitea remote and the explicitly selected AISoft project profile.
2. Match `GITEA_URL`, `GITEA_OWNER`, and `GITEA_REPO` to the requested repository before using credentials.
3. Never source the generic `~/.agent.env` when an exact project profile is available. Never infer the repository from a pilot or example.

## Use the authenticated access ladder

1. **Project profile API**: use the exact mode 400/600 profile as `coder` and the read-only helper. This is the preferred Issue/PR/Actions path.
2. **Configured Git credential**: use the checkout's Gitea remote for `git ls-remote`, fetch, or ancestry checks. If the host sandbox blocks `.orb.local`, retry through the approved host-network path; do not call that an authentication failure.
3. **VM-local admin read-only fallback**: when no project profile exists or the bot lacks repository ACL, use the existing mode 600 administrator credential file only inside `gitea-ci`, through the read-only helper. Do not copy the token to the Mac or add bot permissions.
4. **Authenticated browser fallback**: use an existing signed-in browser session for read-only UI evidence when the helper is unavailable or the UI itself matters.

Never begin a private-repository existence check with an anonymous API request. Anonymous `404` and Git `Repository not found` are inconclusive: they can mean private visibility or ACL failure.

## Helper commands

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

`gitea-readonly.sh` only performs GET. Use a purpose-built authenticated script or an explicitly authorized browser action for comments, labels, Issue/PR creation, settings, permissions, merge, or close operations. Never broaden a bot's ACL merely to make inspection convenient.
