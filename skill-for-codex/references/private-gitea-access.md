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

## #327 FF 能力与人本人 UI 自举

Agent/controller所有远端读写仍经canonicalproject-scopedbroker；本地provider无merge或凭据权限。
受控Controller只在批准合同构造`[已核验Issue第一父链末端, fresh manifest main]`可复算无冲突整合，
broker独立验证original/current tip祖先链、DAG/tree/scope与传输exacttip，只普通FF发表。
禁止force/lease-force、任意merge、冲突自动解决和身份fallback；remote不明先取证，不能猜absence。

新合同不证明旧installed已支持。旧leased首推亦不得执行；#327 first PR自举是负责人本人按映射spec
使用Gitea New File/Upload File、newbranch与唯一manualPR的人工执行卡，Agent不代UI写入、不调用
directGit/rawAPI、不安装unmergedbroker。human H必须独立核验tree/blob/mode、freshmain和exactheadCI，
不能把local L测试当remote H通过。该人工路线不开放Agent权限，也不是其他人工PR更新的hard前置。
source merge后两机安装各需exact批准与真实bytes/mode/owner、FF/no-op/rollback验收，#316旧授权不继承。

**#327 T04 可信证据治理合同（尚未实现/启用）**：trusted-critical Controller 的冻结上下文、受控执行/观察、限定整合和记录由固定 installed verification authority 保管；authority 实际 EUID=0，仅执行已审计平台代码。provider/项目 verifier 以登记非 root UID/GID 在真实 OS 隔离内运行，不能访问 protected ledger、broker credential 或控制入口；只降低 UID、root-owned 文件或 peer UID 不证明程序/批准身份。缺隔离、可信工具链或记录均 fail closed/GAP，不用环境、source wrapper 或身份 fallback。

人类合同/最终 PR 确认须经另获 exact 授权的非 Agent operator 登记为 protected grant/PR授权；local approved、owner marker、commit subject 和 caller PASS 均不是可信根。grant 冻结 exact tuple、scope/内容目的、graph、required verifier、source/policy pin 和 R0，记录由 authority 自己观察执行并逐对象验证；已有/未知或跨 Issue 对象须明确 adoption，来源只指已验证/采用对象，不声称物理创作分支。broker 仍独立重算完整 DAG/tree/delta，核对 sealed checkpoint、PR授权与 strict remote tip，再普通 FF；不重置 R0 或弱化原 per-push/readback 门。

新 public 操作仅 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`；`git.push.change(branch)` 参数不变。无 public approve/merge、自由 command/path/socket/UID/PASS 入口。代码/config/service 的 exact source 范围及固定路径以 #327 映射 spec 为准，默认 disabled、UID/GID 空、provider none、服务描述 inert。治理 T04 只应用映射文本、验证/local commit 后 STOP；后续 fresh run 重读才实施 T02。source 合并后的 I01 文件安装与 I02 每主机 exact 权限绑定、注册/启停、真实隔离/FF/rollback 各依独立 operator 卡；不继承 T01、路线选择或 #316，不自动 provision/启动。AC-7/AC-9 未闭合保持实际未完成，不把 mock/source/自动 closed 当 installed/live 验收。

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
