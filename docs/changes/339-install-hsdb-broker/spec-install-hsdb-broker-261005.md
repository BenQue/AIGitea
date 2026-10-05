---
issue: 339
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
depends_on:
  - 337
status: contract-drafting
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 平台安装与注册识别 Spec

## Problem Statement / Solution

HSDB 已恢复merged source注册，但两端installed root broker仍不识别。消费同一已合并pin的完整受管安装面，实测HSDB项目解析恢复，并保护原六仓和其他owner。
本spec是未approved的具体现场合同。恢复方法采用独立observed-byte snapshot，而不是未知previous SHA。下方完整执行卡是本spec的一部分。

## User Stories

1. 作为HSDB调度负责人，我要AC-8 source与AC-9 installed独立成立后激活T02。
2. 作为本票唯一执行owner，我要exact source/current-main/权限闸门和同pin两端验收，不从文档branch安装。
3. 作为原六仓owner，我要共享runtime影响明确、窗口串行、既有identity/profile/routine边界不扩张。
4. 作为#333 owner，我要helper/receipt新变化导致STOP，既有现场权责和授权不被继承。
5. 作为人类授权者，我要一次审阅实际Issue、owner/OS身份、相对窗口、命令、失败恢复，且draft不代替批准。
6. 作为恢复执行owner，我要独立非Secret字节快照/absence/previous链证明，同时保留真实restore NOT RUN。
7. 作为T02 owner，我要注册PASS与账号/credential/onboarding GAP分开交接，不把安装升级为canary/UAT。

## Acceptance criteria

- [ ] AC-1：实际#339/exact tuple/唯一owner及explicit用户安装/恢复scope确认，采用本聊天执行owner、既有benque/sudo；确认后45分钟+失败限定恢复≤15分钟，或明确批准的替代。
- [ ] AC-2：fresh remote/current merged pin、source main clean、root进程safe.directory准确，guard非unknown/behind；source FF有授权。
- [ ] AC-3：两端25固定source目标+生成receipt完全匹配pin/mode/owner/entrypoint，source_sha/merged_main/four-hash/helper:null正确。
- [ ] AC-4：七仓/38操作/HSDB vm_profile:null、三VM profiles、原六仓权限/seal无越界；同pin第二次installer和独立readback一致。
- [ ] AC-5：installed broker不再HSDB unknown；access/account/credential/onboarding真实GAP保留；无其它副作用。
- [ ] AC-6：本窗口非Secret snapshots真实restore，验原字节/mode/owner/previous链/absence、六仓与原HSDB unknown；随后同pin再安装并最终验七仓/38操作和26目标/receipt/HSDB识别。不是事故或故障注入；未运行不得写PASS。
- [ ] AC-7：总调度fresh核T01门后另行激活T02；文档最终交付不自动证明installed或关闭现场未完成项。

## Testing Decisions / 可观察验收

最高验证seam是固定installed入口的项目识别、两端目标字节/provenance/mode/owner及独立快照恢复。复用现有installer/guard和typed只读操作，不新建runtimeseam。
已完成快照tarheader/hash与artifact回放，不是安装/故障恢复。两次真实installer、真实snapshot restore及同pin再安装闭环需获批窗口；不注入runtime/PAT/账号/服务故障。
若排他条件或窗口余量不足以安全完成明确的restore/reinstall闭环，保持AC-6 NOT RUN并交回授权者，不能以模拟根覆盖实际root。

## 文档PR/源pin gate

当前四件套仅本地和Issue正文，未push/PR。没有改source规范或runtime的合同准备不额外制造“此文档PR必须先merge”的安装门；installer本身和注册manifests必须是已人工合并的版本。
若未来要更改source治理/工具，必须按AGENTS独立治理应用→STOP→fresh run，并经源PR人工合并；若文档PR先合并使origin/main改变，也必须重选current pin、重审影响和卡，不沿用本票旧pin。本票最终PR保持唯一/manual，未得到提交批准。
现场完成条件以本票AC为准；docs source生命周期不覆盖installed字段，不在安装缺失时宣称T01完成或触发下游。

## 具体执行卡

# T01B 平台安装与 HSDB 注册识别执行卡

状态：**WAITING_INSTALL_APPROVAL**。准备时间：2026-10-05T21:15:26.823667+09:00（Asia/Tokyo）。
唯一准备 owner：本聊天 `01a10bea-8743-7d12-bd55-addf317088bc`；总调度 `01a1071e-d973-71a1-99a8-da35d447d1cd`。
实际安装、主机 restore、账号/Secret 操作均 **NOT RUN**；`IMPLEMENT_PROVIDER=none`。

本卡的完整候选是两端 25 个固定源目标及 1 份生成 receipt；不是仅拷贝两份 manifest。
尚未得到安装授权。以下命令用于审批，不能据此自动执行。

## 已核实事实

| 核验项 | 结果 | 证据边界 |
|---|---|---|
| fresh remote main / 候选 pin | PASS：`c9b5ef4e74592cbc68d6bdc6219568a1d51b6853` | installed broker `git.fetch.main`；sandbox TRANSPORT_ERROR 后同 request host 重试 PASS；本地 Git 对象是 fresh fetched source |
| 源码 predecessor | PASS：#337 closed/completed、PR #338 human admin merged | 原 source handoff；总调度已独立读回并确认 source 聊天归档；本轮没有重开 Issue |
| final head required PR CI | PASS：`45857164a29525d2921fee5beace82afeaed0af0`，`CI / verify (pull_request)`，run 1783/job 1989 success | 总调度独立 broker 证据已复制到本目录；source PR tree=merge tree；独立 main workflow 没有 run，**不是 main CI PASS** |
| primary source 与 VM 挂载 | GAP：clean main=`e2edb3e08194624a6647212571c6cc866298575b`，落后 5 提交 | Mac 与 VM 挂载各自只读确认。当前这个旧 checkout 不能安装；本轮未 FF、未 checkout |
| Mac / VM installed manifests | GAP：各六仓，无 HSDB | 本轮两端 fresh inventory、hash；两端 installed broker 实测 hsdb 均 exit20，REQUEST_DENIED / requested project is not explicitly managed |
| root-scoped 安装面 | PASS（当前 metadata） | 已存在受管目标均 uid=0/gid=0；runtime/manifests 0644、entrypoints 0755；目录 0755；受管目标无 symlink |
| helper / receipt | GAP：两端 helper、rotation operator、receipt 均不存在 | 不声明已具备轮换能力；没有可继承的 helper 声明；本候选不携带 `--pat-helper-artifact` |
| installed source SHA / previous SHA | NOT VERIFIED | 无 receipt，不能由六仓计数、mtime 或部分字节匹配反推整套 SHA；保留这个 GAP |
| 凭据 metadata | PASS（仅 metadata） | Mac canonical `projects/hsdb/project-agent.token` 存在、0600、benque 501:20、非 symlink；父目录 0700。未读值/未算 Secret 摘要 |
| hsdb-agent 当前状态 / 凭据有效性 | GAP | 上次 source owner 的 `prohibit_login=true` 是历史读回。本轮未调用账号 API或验证 token；不能声称恢复 |
| 非 Secret 当前安装快照 | PASS：archive 与 fresh inventory 的内容 hash、tar header mode/uid/gid相符；artifact 内解包回放相符 | 可用的是两端独立的 observed-byte snapshot。**真实主机 restore 仍 NOT RUN**，不是历史 merged-pin rollback |

## 单一 owner 与共享安装面

本轮 open Issues 恰为 #327、#333、#336，没有 HSDB 安装新 Issue。`list_threads(limit=50)` 加 #333 最近两轮读回没有发现同安装任务的第二 owner；这不是操作系统排他锁或永久完整性证明。
#333 `01a100d7-2f34-7932-923d-781f3f255e09` 保留 PAT/helper 现场范围，其 latest source 准备仍未发布/安装；#327/#336 source worktree 与权责保留。
在获批窗口开始前必须重新盘点独立 owner 与 helper/receipt；有新的 helper、receipt、installed hash 或并发安装即 STOP。总调度负责串行窗口；本聊天不发送其它聊天消息。

独立运维tracking已建立：[Issue #339](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339)。唯一branch/worktree为 change/339-install-hsdb-broker / /private/tmp/issue-339-install-hsdb-broker，仅写四份映射文档，owner已claim。
本Issue正文已发布实际编号合同；draft不等于批准。#337保持closed，#333 scope不接管。若文档PR或其它main变更先合并，重新审变化与source pin。

## 安装范围及原六仓影响

source 对 `e2edb3e…` 的 #337 增量：host-access 去掉唯一 hsdb 后原六仓和其余 policy 完全相同；governance 原六仓仅 NewEMaint `routine_live_pilot/non_target_repositories_sha256` 随非目标集合重 pin，其它五仓和全部权限声明保持。source pin VM profile仍只有 aisoft-platform/localwms/emaintenance（仓库 AISoftPlatform/LocalWMS/NewEMaint）；hsdb 的 `vm_profile=null`。

实际 installed 比较结果两端相同：

- operations 36→38，新增 `gitea.dependency.read`（manager-audit）和 `gitea.credential.rotate`（credential-operator）；属于已合并 source 既有合同的整体更新，不授权调用。
- 新增 `credential_rotation.py`、`dependencies.py`、`rotate-gitea-service-account`，以及生成 `credential-rotation-source.json`。
- 更新 broker.py/cli.py/contract.py/runner.py、两份 manifests；16 个其它固定源目标同字节。
- 原六仓经过共享 runtime，broker 校验、依赖解析及 operator 定义会变成 pin 的版本。不能称作“只影响 HSDB”；窗口需停止并发 typed 写入。
- installer 会覆盖变化目标的 `.previous`，故必须保留本轮快照的原 previous 链。它还会删除 `keychain-acl-audit` 和其 previous；两端本轮均不存在。若窗口前出现则 STOP，不能沿用本卡删除。
- 安装不调用 provision/rotation/binding/profile apply、服务或 timer；provider保持 none。helper:null 不代表 Mac/VM 轮换 capability PASS。

### 完整固定 source→target 清单

| Source（pin 的相对路径） | 目标（两端相同） | mode | 本轮 installed 比较 |
|---|---|---|---|
| codex/runtime/aisoft_gitea_governance/__init__.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/__init__.py | 0644 | 同字节 |
| codex/runtime/aisoft_gitea_governance/cli.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/cli.py | 0644 | 同字节 |
| codex/runtime/aisoft_gitea_governance/client.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/client.py | 0644 | 同字节 |
| codex/runtime/aisoft_gitea_governance/contract.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/contract.py | 0644 | 同字节 |
| codex/runtime/aisoft_gitea_governance/reconcile.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/reconcile.py | 0644 | 同字节 |
| codex/runtime/aisoft_gitea_governance/service_policy.py | /usr/local/lib/aisoft-host-access/aisoft_gitea_governance/service_policy.py | 0644 | 同字节 |
| codex/runtime/aisoft_host_access/__init__.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/__init__.py | 0644 | 同字节 |
| codex/runtime/aisoft_host_access/broker.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py | 0644 | 更新 |
| codex/runtime/aisoft_host_access/cli.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/cli.py | 0644 | 更新 |
| codex/runtime/aisoft_host_access/contract.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/contract.py | 0644 | 更新 |
| codex/runtime/aisoft_host_access/credential_rotation.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py | 0644 | 新增 |
| codex/runtime/aisoft_host_access/dependencies.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py | 0644 | 新增 |
| codex/runtime/aisoft_host_access/profiles.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/profiles.py | 0644 | 同字节 |
| codex/runtime/aisoft_host_access/runner.py | /usr/local/lib/aisoft-host-access/aisoft_host_access/runner.py | 0644 | 更新 |
| codex/runtime/aisoft_change_name.py | /usr/local/lib/aisoft-host-access/aisoft_change_name.py | 0644 | 同字节 |
| codex/runtime/aisoft_worktree_owner.py | /usr/local/lib/aisoft-host-access/aisoft_worktree_owner.py | 0644 | 同字节 |
| codex/config/host-access-broker.json | /usr/local/share/aisoft/host-access-broker.json | 0644 | 更新 |
| codex/config/gitea-governance.json | /usr/local/share/aisoft/gitea-governance.json | 0644 | 更新 |
| codex/config/gitea-labels.json | /usr/local/share/aisoft/gitea-labels.json | 0644 | 同字节 |
| codex/tools/host-access-broker.sh | /usr/local/libexec/aisoft/host-access-broker | 0755 | 同字节 |
| codex/tools/git-credential-aisoft-host.sh | /usr/local/libexec/aisoft/git-credential-aisoft-host | 0755 | 同字节 |
| codex/tools/project-profile-migration.sh | /usr/local/libexec/aisoft/project-profile-migration | 0755 | 同字节 |
| codex/tools/bootstrap-gitea-service-account.sh | /usr/local/libexec/aisoft/bootstrap-gitea-service-account | 0755 | 同字节 |
| codex/tools/rollback-gitea-routine-pilot.sh | /usr/local/libexec/aisoft/rollback-gitea-routine-pilot | 0755 | 同字节 |
| codex/tools/rotate-gitea-service-account.sh | /usr/local/libexec/aisoft/rotate-gitea-service-account | 0755 | 新增 |
| installation_metadata() 生成 | /usr/local/share/aisoft/credential-rotation-source.json | 0644 | 新增，source_sha=pin、merged_main=true、helper=null |

`source-scope.json` 固定每个源文件 SHA256、目标旧 SHA256、owner/mode 和两端差异。`source-review/` 只是由 git show 导出的审阅字节，没有 Git provenance，**不能作为安装 checkout**。

## Installer 与间接路径审查

`codex/install-host-access-broker.sh` 与 `codex/lib/install-source-guard.sh` 在 #337 中零 diff。本轮 source 导出字节 bash -n PASS；没有修改 shell/source，未重跑源码完整 smoke。最终 PR 的 CI 是上述明确证据。

执行顺序：source guard → source runtime 的 `installation_metadata()` → install -d → 25 个固定文件 → 可选 helper → receipt → legacy helper删除。
metadata 的非 artifact 路径只读 Git provenance并对四个源文件算公开摘要，没有 Secret/网络/账号副作用；没有额外 installer 被间接执行。
带 artifact 路径会执行已 pin Linux binary --version，要求 linux/arm64、Go 1.26.3、Gitea model 1.26.4、clean same source SHA、公开 provenance与 build-lock/hash 一致；本候选未请求该路径，故**不需要 helper artifact**。

`install-vm.sh` 是另外一条 user-scoped runtime/manifests 复制路径，并会间接执行 `install-skills.sh`、写 agent/unit模板等；不能替代 root installer，也不纳入本卡。其余 installer、global skills、host-role、架构/release/sync 安装面均没有因本候选形成必需依赖。
installer不会自动更新 user-scoped Loop runtime；若 T02 将来需要它，须单列 GAP、另有真实范围。

guard只读已存在 upstream，不会 fetch；落后 fail closed，detached/unknown 仅警告。故本卡明确要求 fresh fetch + clean main + exact HEAD=origin/main=pin，并要求 guard输出 `level with origin/main`；警告/未知状态不是成功。
root过程使用仅本次子进程的 exact `safe.directory`，解决 UID ownership 的 Git 判断；不修改 global Git 配置。receipt必须再次独立验证，installer exit0/no-op不足以验收。

## 建议的执行方式、窗口及批准绑定

| 字段 | 审阅候选 |
|---|---|
| 执行owner/OS身份 | 建议本T01B聊天作为唯一执行owner，通过Mac `benque` 与VM `benque`/sudo执行；人类用户是授权者。该方式未批准，不冒充人工operator或签署 |
| 环境 | Mac arm64 开发 host + OrbStack gitea-ci Linux aarch64。仅固定 /usr/local broker面；不包含 AppServer/公司服务器 |
| 窗口 | 建议明确确认后立即开始，安装/验收45分钟；失败时仅限定恢复顺延≤15分钟，总计≤60分钟。确认后记录Asia/Tokyo精确起止；目前未批准 |
| 写入范围 | clean primary main 的 exact FF 至pin；两端版本化 installer、同pin幂等第二次；本窗口snapshot真实恢复及同pin再安装闭环（需明确纳入）；证据只写本聊天目录 |
| tracking | 实际Issue #339，四角色语义合同已映射；正文合同未批准。建议本聊天为执行owner，供用户一次确认 |
| 授权不传递项 | 账号解除停用、PAT/Secret provision/grant/rotate、ACL/protection apply、Git binding、labels、canary、timer/provider/routine enable、部署全部另有对应阶段边界 |

## 获批后执行顺序和命令

1. 复读本卡与 Issue 合同；确认本聊天执行owner、两端benque/sudo与相对窗口及两端排他维护。盘点其它安装 owner，fresh typed fetch；remote main 若不是 pin则STOP，核 diff 后重新出卡。
2. 复核 primary branch/main clean、HEAD仍为本卡 base，无其它会话归属冲突；仅在这个范围获批时执行一次 FF。没有 reset、rebase、force、全局 safe.directory。

```bash
/usr/local/libexec/aisoft/host-access-broker --project aisoft-platform --operation git.fetch.main
git -C /Users/benque/MyDocs/AISoftPlatform status --porcelain
git -C /Users/benque/MyDocs/AISoftPlatform branch --show-current
git -C /Users/benque/MyDocs/AISoftPlatform rev-parse HEAD origin/main
# 必须是 clean main，HEAD=e2edb3e08194624a6647212571c6cc866298575b，origin/main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853
git -C /Users/benque/MyDocs/AISoftPlatform merge --ff-only origin/main
git -C /Users/benque/MyDocs/AISoftPlatform rev-parse HEAD origin/main
# 二者必须精确为 c9b5ef4e74592cbc68d6bdc6219568a1d51b6853
```

3. 两端再运行本目录只读 inventory，与本卡 active字节/metadata、helper/receipt、legacy helper及源pin比对；新 observation有差异即STOP。重新归档两端非Secret快照（Mac artifact目录）并校验 hash/tar owner/mode/文件列表。用新的 `window-backups/` 目录保存，不覆盖本轮准备快照。必须有有效 snapshot 后才写root；不依赖易被覆盖的 .previous。
4. 先 VM、再 Mac；两端安装过程不运行项目操作，不把半完成混合版本当作可用。以下 root命令均使用固定源路径，未带 helper artifact；env去除 test root和Python注入，并禁止新增 pycache。

```bash
orb -m gitea-ci -u benque sudo env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/mnt/mac/Users/benque/MyDocs/AISoftPlatform bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
sudo env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/Users/benque/MyDocs/AISoftPlatform bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
```

安装前还需在两端 root子进程下只读确认exactHEAD/upstream/clean，防止sudo环境导致guard未知；上述命令内没有任何 guard绕过。
任一 installer非零、source警告、sourcepin变化或第二端失败：停止typed操作，按已获批恢复卡处理两端，不扩大动作。
5. 重复相同两条installer命令一次，同pin应no-op；guard仍需打印真实pin及38操作。再次独立验25固定文件+receipt、目录、mode/owner、入口；不能仅看no-op。
6. 验 receipt：`source_sha=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`、`merged_main=true`、`helper=null`；四个声明文件实际摘要和source一致。两端 manifests七仓，源字节逐一匹配；HSDB Mac-only、操作38、VM profile精确三项。
7. 使用**installed** broker运行只读识别及access/onboarding；此时真实只读身份/scope验收会使用受保护凭据，本轮未执行。明确禁止fallback账号/API。

```bash
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation gitea.repo.read
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.access.audit
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.onboarding.check
```

账号或credential阻塞可能使上述exit20。需保存精确code，区分“识别项目后 credential/identity/onboarding GAP”与“仍 requested project is not explicitly managed”。后者是T01B FAIL；前者可满足注册门、仍使T02 access gate保持GAP。不能以exit20一概判断识别失败，也不能凭文件存在判断注册PASS。
原六仓 source policy +字节验收必须完整；独立授权窗口如需验证它们的只读访问，逐项目typed `gitea.repo.read`，不写凭据或调用routine。预存凭据问题单列，不把T01B变成其它项目修复。

## 已有恢复基线及失败恢复命令

当前没有已核实的previous merged-source pin；因此**不能宣称可从上一SHA重跑installer回退**，guard也会拒绝旧upstream。
本卡增加 observed-byte snapshot恢复候选，需要独立运维合同明确接受这个方法；它恢复原安装字节/权限和absence，不提供历史provenance，更不恢复PAT。

| 基线 | 本轮完整性结果 |
|---|---|
| Mac：`mac-current-installed-snapshot.tar.gz`，SHA256 `f072bca05787305d2721fcec4dc896890f3584d4e28e61045488ba51b6fc4831` | 34份非Secret文件，tar header uid/gid/mode与inventory一致；artifact回放PASS |
| VM：`vm-current-installed-snapshot.tar.gz`，SHA256 `9170fec5f029680aa39eaf0b849c6a0bf37daeb3bf1f2f8c062099543543adce` | 43份非Secret文件，含只读现存Python缓存；artifact回放PASS |

快照只含固定broker runtime、入口、三份public manifests及其 .previous链；不存在的helper/receipt/legacyhelper由absence清单记录。无credential/profile/账号/grant/service目录、无其它/usr/local工具。
`snapshot-installed.py` 仅归档这些路径，遇未知文件型或symlink拒绝；VM归档流直接写Mac artifact，VM不落盘。首次VM归档遇.pyc白名单外文件型拒绝，扩到已核实的__pycache__/*.pyc后重跑PASS；没有读取Secret、没有掩盖失败。

恢复时确认本窗口排他性及当前修改来自本候选；先校验选定window archive SHA256及路径白名单，再执行 **Mac→VM** 恢复（逆安装顺序）。若仅某端开始写入，可仅恢复写过的端，但必须最终读回两端均为baseline。
下列是本轮准备快照的准确命令候选；正式window重备份后把**精确文件名和已验hash**写入批准卡，不能静默使用过期快照。

```bash
sudo tar -xzpf '/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-preflight/mac-current-installed-snapshot.tar.gz' -C /
orb -m gitea-ci -u benque sudo tar -xzpf '/mnt/mac/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-preflight/vm-current-installed-snapshot.tar.gz' -C /
# 恢复归档不会删除首次新增路径。只在核实本候选创建、无并发owner后，分别在Mac/VM运行：
sudo rm -f -- '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py' \
  '/usr/local/libexec/aisoft/rotate-gitea-service-account' \
  '/usr/local/share/aisoft/credential-rotation-source.json' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py.previous' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py.previous' \
  '/usr/local/libexec/aisoft/rotate-gitea-service-account.previous' \
  '/usr/local/share/aisoft/credential-rotation-source.json.previous'
orb -m gitea-ci -u benque sudo rm -f -- '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py' \
  '/usr/local/libexec/aisoft/rotate-gitea-service-account' \
  '/usr/local/share/aisoft/credential-rotation-source.json' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py.previous' \
  '/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py.previous' \
  '/usr/local/libexec/aisoft/rotate-gitea-service-account.previous' \
  '/usr/local/share/aisoft/credential-rotation-source.json.previous'
```

复核整个baseline字节、mode/owner、原previous链、原absence及两份六仓manifest；installed platform typed `git.fetch.main`/`gitea.issue.list`应保持原读取能力，hsdb应恢复原unknown-project拒绝。rawbyte恢复不改变source mainpin。
禁止以source revert或source 7→6→7代替这项installed证据。生产临时命令原则仍适用：此卡仅是Mac/VM开发平台的审阅恢复候选；若环境归类或Issue合同要求版本化restore工具，先走该合同，不能现场扩展命令。
当前真实restore/失效恢复演练 **NOT RUN**。若恢复未授权或恢复前有其它owner改写，则只停止并保留证据，不擅自覆盖。

## AC-6：真实 snapshot restore 与同 pin 再安装闭环

这是主动安排的真实安装面恢复演练，不是实际事故，不注入故障。待确认许可明确包含两端 snapshot restore、八个允许目标的限定清除及同 pin 再安装；不涉及账号/PAT/Secret/grant/profile/service或其它owner安装面。

1. 窗口开始时重新inventory，固定非Secret范围归档到新的window-backups目录，核路径白名单、SHA256、tar root uid/gid/mode、原previous链和absence。本轮快照只是审阅基线；演练用本窗口精确新归档，路径/hash须落在执行回执，不静默替换。
2. 使用 c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 的已合并current-main installer，按VM→Mac安装；同样两条命令再跑一次。分别保存第一次、幂等第二次及26目标/receipt/HSDB识别结果。
3. 候选验收成立且owner排他、窗口余量足够后，主动恢复本窗口snapshots，按Mac→VM执行卡内tar命令。清除精确八个允许目标，仅限本候选确在窗口创建且未被其它owner改写的四个新目标及各自可能出现的.previous。实际不存在的不算曾创建，无glob、无递归删除。
4. 核恢复后全部原字节/mode/owner、原previous链、absence及两份六仓manifest；两端installed broker对hsdb须恢复原exit20、REQUEST_DENIED/requested project is not explicitly managed。核原平台typed读取能力，不读写Secret。此阶段unknown是预期恢复结果，不是最终注册PASS。
5. primary及origin/main仍须同一批准pin、clean。main/pin/helper/receipt/owner漂移即STOP，不重选pin、不从change/339或source导出字节安装。
6. 再消费相同pin的已合并installer，按VM→Mac再安装。这是演练后再安装，不冒充前面的幂等第二次。独立验26目标/receipt source_sha/merged_main/四摘要/helper:null、七仓/38操作和HSDB识别。最终必须停在七仓，不能把演练期间六仓作为终态。
7. restore/reinstall都有before/after/hash/owner/phase/exitcode证据才使AC-6 PASS；AC-3/4/5在最终再安装后仍成立，才交总调度核T01B退出/T02激活。账号/credential/onboarding GAP继续保留。

### 窗口控制及停止条件

建议确认后立即开始45分钟，记Asia/Tokyo精确T0/T0+45；额外≤15分钟只用于意外时的限定baseline恢复和读回，不授权新范围或过期再安装。
planned restore→同pin再安装→最终readback须在前45分钟内完成，开始第3步前至少保留30分钟。sudo认证、传输、owner排他或验证耗时导致余量不足时，不开始演练，保留已验候选、AC-6 NOT RUN和T01B未完成，另定具体窗口，不自动续时。
闭环开始后若无法安全完成或reinstall被pin/guard阻塞，停止项目操作；在已批准≤15分钟范围内确保恢复到已验baseline，不能声称最终七仓PASS。baseline恢复也不安全则STOP、保留证据并交人，不覆盖未知owner。
30分钟余量是保守边界，不是实测工期保证。sudo可用性本轮未执行验证；获批fresh run先核既有benque/sudo能力，不足即STOP，不把Gitea凭据当sudo授权，不在聊天接收密码。
这是平台安装面的真实restore验收；T04以后应用的受控失败、health、数据库/附件恢复独立验收，不能由本票代替。


## 成功、失败、下游 gate

**T01B PASS**：独立tracking/安装scope批准成立；同一执行owner/OS身份/窗口；两端source provenance及26目标验收成立；helper:null且无scope扩张；原六仓和exact三VM profiles/seal保留；installed HSDB解析不再unknown；完整before/after/idem证据及AC-6真实restore后同pin再安装最终七仓验收成立。
**FAIL / STOP**：pin/owner漂移、credential/账号写入、helper/receipt变化、guard unknown/behind、source/target/mode/owner不一致、任何installer非零、仍unknown-project、原六仓或profile扩大、restore不安全。
access/onboarding credential/account GAP按真实结果交T02，不转为PASS。

总调度 **T01完成 = #337 AC-8 source证据 + AC-9两端installed注册证据**。当前AC-8 PASS，AC-9 GAP / NOT RUN，T01尚未完成。
T02只在总调度fresh核实此门并单独激活后开展独立 adoption Issue、access/protection/binding/labels/canary；本卡安装批准不代替账号启用或Secret审批，不自动激活T02。本轮T02–T06仍WAITING_DEPENDENCY。

## 必要批准的确切依据

适用skill没有要求另指定一名现场人工operator；本卡不添加此推断门禁。直接范围来自本次T01B派发：“实际 Mac/VM 安装、账号启用、Secret 操作均未获本轮许可”。
已合并 #337 spec 第107行明确：“**安装和 installed rollback 都需要独立 exact pin/窗口授权。**”
文件：[spec-restore-hsdb-governance-261004.md](/Users/benque/.codex/visualizations/2026/10/04/01a10739-4622-7be1-ba10-0a92d8fc9905/hsdb-governance/merged-change-documents/spec-restore-hsdb-governance-261004.md:107)。
AGENTS第8/13/21行分别要求Issue追踪、平台/安全/共享核心按complex、运维说明回滚并用真实命令验证。本轮只准备草案和artifact证据，未改受管源码、root安装面、VM或账号/Secret。

待人操作项已收敛为：独立运维tracking/合同、**执行owner/既有OS身份、确认后45分钟窗口和≤15分钟限定恢复、是否批准本pin的FF+两端禁用式安装及具体snapshot恢复scope**。没有后台轮询。
