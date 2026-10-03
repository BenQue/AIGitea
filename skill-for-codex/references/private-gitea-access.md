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

新 public 操作仅 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`；`git.push.change(branch)` 参数不变。无 public approve/merge、自由 command/path/socket/UID/PASS 入口。代码/config/service 的 exact source 范围及固定路径以 #327 映射 spec 为准，默认 disabled、UID/GID 空、provider none、服务描述 inert。原治理 T04 只应用映射文本、验证/local commit 后 STOP；后续 fresh run 重读才实施 T02。source 合并后的 I01 文件安装与 I02 每主机 exact 权限绑定、注册/启停、真实隔离/FF/rollback 各依独立 operator 卡；不继承 T01、路线选择或 #316，不自动 provision/启动。AC-7/AC-9/AC-10/AC-11 未闭合保持实际未完成，不把 mock/source/自动 closed 当 installed/live 验收。

**#327 T05 资源与工具链治理合同（source 已批准；installed/live 未验收）**：critical 入口由固定 installed native bootstrap 在任何 Python 平台模块导入前核验完整 toolchain closure 与角色绑定；范围包括 interpreter/stdlib/late import/native loader/library/Git transport/helper/OS delegate、OS alias 与 Mac dyld shared cache/subcache。完整目录/build dependency inventory及静态/显式动态解析为基线，loaded-module集合或一次trace不能证明完整；未知依赖/漂移/未注册一律GAP。严格清env/FD、canonical regular最终程序、无source/PATH/未知shim fallback；bootstrap自身OS loader为冻结TCB，不声称main前无库执行。exact source、固定incoming path/FD、build/descriptor与默认disabled空host registry遵映射spec，不自动安装新工具链或以root构建项目。

Mac scratch固定64 MiB UDIF/UDRW/HFSX无分区模板，root Git暂存256 MiB；模板create仅未来exact I02 operator，runtime不格式化任意设备。真实ownership/容量/nodev/nosuid/noexec/nobrowse与镜像→device→mount映射须读回，单scratch/单readonly input、最多两个对象卷；CONTEXT/temp/复制双份窗口全部创建前预留并计入8 GiB保留预算、64 MiB平台元数据上限，input≤256 MiB/4096entries/depth16。Linux同等scratch/对象tmpfs上限及inode/namespace隔离须真实验收。每verifier新own-lease，descendant未退出、busy、device复用、未知映射、崩溃/断电均保留预算/证据并quarantine；不force/resize/hosttmp fallback/盲重试/递归清理user卷/自动删除历史。只依protected exact FD清单和确认own detach后的readback回收；R0不重pin。Mac noexec不支持scratch中新产native binary执行，能力不足明确GAP，不泛称SDK/build可用。

public policy仍`change-verification/v1`四key、public仅begin/verify且push仅branch；private grant/record/operator为v2并绑定closure/resource/lease digest，v1只作历史只读，不自动迁移/清空。publish先持久pending再transport，断线/重启/重入只poll既有attempt、不重复推送；真实possible-write/已落地H保留，不能把传输失败写为零mutation。T05仅原14治理文本+四角色（18文件）独立应用/验证/local commit后STOP，后续fresh重读才继续既有T02 WIP；不混runtime。I01只惰性文件安装/hash-mode-owner、installer no-op与文件失败rollback；I02每主机exact卡独立批准registry/模板/own-device/服务启停/真实权限、FF/publish no-op/reject与运行资源rollback，AC-7要求不减。默认none/disabled，不provision账户/凭据/grant/全局SDK/provider。AC-7/9/10/11未闭合不把source/mock/自动closed当实际完成，不提前cleanup/归档，不继承#316或路线选择权限。

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
