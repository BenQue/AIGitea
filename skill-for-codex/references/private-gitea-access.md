# Private local Gitea access

Use this procedure before inspecting a private repository, Issue, PR, Actions run, branch protection, or repository setting.

## Resolve the exact target

1. After Issue #61 is released, select the exact project and an allowlisted operation through
   `/usr/local/libexec/aisoft/host-access-broker`; target and identity come from the strict manifests.
2. Broker Git operations resolve the remote name only from the project manifest. Missing
   `git_remote_name` means `origin`; a declared value such as `gitea` is fixed and cannot be supplied by
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

## #327 当前收缩合同（2026-10-05）

本票只交付保留 original/current remote tip 祖先关系的 main 整合、普通 FF、非法/并发漂移拒绝、required CI 与可恢复收尾。以 [#327 spec](../../docs/changes/327-broker-ff-integration/spec-broker-ff-integration-261002.md) 的当前合同为准；T01/T04–T10 为历史治理步骤，原 FAIL/GAP/NOT RUN 保留。

Agent/provider 只追加本 Issue 的线性本地 commit。合格现有 Controller 可按合同整合；本票首次自举明确允许**负责人本人**用标准 Git 在原 owner worktree 临时保全/park WIP、构造 `[已核验 Issue tip, fresh manifest main]` 并留恢复证据，Agent 不代执行。它不再等待未交付 R02、root authority、OS observer 或 protected grant。仅无冲突标准整合；冲突停止并保留 stash/前态，不自动覆盖内容。

最终唯一 PR 的第二确认仍绑定 exact Issue/branch/manual。确认前不发表；确认后本票可由本人使用已绑定的普通 Git credential helper、经过本票测试的固定 pre-push guard 和 exact SHA 单 ref 普通 FF 完成首次发表，不调用旧 lease-force broker、不装 unmerged broker，Agent 不借此绕 broker。来源/DAG/tree/范围、R0/R/M/H、guard 执行和真实 readback 必须核对；main 禁直推/force、required CI、本人 manual merge 不变。实际首次发表/installed 验收未运行仍为 GAP/NOT RUN。

root authority、begin/verify、ES/kernel/signing、完整 OS/解释器闭包、scratch/resource 隔离及其 I01/I02/AC-9～11 延期，不作为本票当前 source 整合/PR 的前置；不宣称这些安全能力已交付，也不以本地 receipt/owner marker 证明不可伪造授权或同 UID 隔离。Mac/VM 安装均需 source 合并后另获授权。本轮仅治理文本与证据应用、校验、本地 commit 后 STOP；下一 fresh run 重读后才续 T02。

## Helper commands

### Approved #286 dependency contract — source/local verified

`depends_on` integers mean Issues in the source repository only. The approved `owner/repo#N`
extension must use a new typed dependency read with only a reference argument and a source project binding.
Resolve the target through canonical `dependency_read_targets` before any GET; no caller-supplied URL,
host, credential or arbitrary repository route. The only new cross-repository edge approved here is
`sfm-digital-board → aisoft-platform`; all other projects default to local dependencies.

Cross-repository reads stay inside the broker's manager-audit read-only route. Never use the source
project-agent or routine merger credential outside its repository, and never fall back to admin,
mutation tokens, a direct GiteaClient or broader ACL. Validate repository identity/number and reject PRs;
unverifiable or unauthorized reads never satisfy a dependency. Controller and routine merger must share
this boundary. Source/local fixtures are verified; the full smoke and post-#289 integration pass under LC_ALL=C.
Installed bytes and live reads are NOT RUN. Do not issue an unsupported operation against the currently installed broker.

The general inspection fallback ladder above does not apply to dependency gates. Installation,
credential provisioning and live apply require separate authorization and read-back.

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
