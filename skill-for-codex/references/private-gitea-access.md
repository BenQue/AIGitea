# Private local Gitea access

Use this procedure before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting.

## Resolve the exact target

1. Read the current checkout's Gitea remote and the explicitly selected AISoft project profile.
2. Match `GITEA_URL`, `GITEA_OWNER`, and `GITEA_REPO` to the requested repository before using credentials.
3. Never source the generic `~/.agent.env` when an exact project profile is available. Never infer the repository from a pilot or example.

## Use the authenticated access ladder

1. **Project profile API**: use the exact mode 400/600 project-agent profile as `coder` and the read-only
   helper. This is the preferred Issue/PR/Actions path and must bind only one repository.
2. **Configured Git credential**: use the checkout's Gitea remote for `git ls-remote`, fetch, or ancestry checks. If the host sandbox blocks `.orb.local`, retry through the approved host-network path; do not call that an authentication failure.
3. **Platform manager audit PAT**: Issue #35 live reconciliation 后，跨项目 settings/protection inventory
   使用 manager 的独立 read-only PAT 和 `gitea-governance.sh check`；不得用 mutation PAT 或普通 Git
   代替。候选 PR 合并前该身份仍是 `NOT RUN`。
4. **VM-local admin read-only fallback**: when no project profile/manager exists or ACL blocks the exact
   target, use the existing mode 600 administrator credential file only inside `gitea-ci`, through the
   read-only helper. Do not copy the token to the Mac or add bot permissions.
5. **Authenticated browser fallback**: use an existing signed-in browser session for read-only UI evidence when the helper is unavailable or the UI itself matters.

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

`gitea-readonly.sh` only performs GET. Issue/comment/label/branch/PR 使用 exact project agent；跨项目
settings/permissions/protection mutation 只能由已合并 Issue #35 的 purpose-built governance 命令一次
处理一个 manifest repository。merge 永远保留给人工身份。Never broaden a bot's ACL merely to make
inspection convenient.
