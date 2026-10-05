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
status: awaiting-triage
branch: change/339-install-hsdb-broker
created: 2026-10-05
updated: 2026-10-05
---

# #339 平台安装与注册识别 Spec · Revision 2

原完整合同已批准并实际执行首次安装；新发现的installed策略差异导致STOP，真实恢复两端baseline已PASS。下面修正版尚未批准，禁止重新开窗。

## Acceptance criteria

- [ ] AC-1：保留原合同授权证据；总调度审阅Revision 2后取得SFMDigitalBoard依赖只读边/完整共享面声明、Mac原生root入口和下一完整窗口的明确批准。
- [ ] AC-2：fresh pin/current main/clean/root upstream/guard均匹配c9b5ef4e74592cbc68d6bdc6219568a1d51b6853；primary本窗口已FF，不重复伪造source动作。
- [ ] AC-3：两端25固定目标+生成receipt完全匹配pin/mode/root owner；receipt source_sha/merged_main/four-hash/helper:null正确。
- [ ] AC-4：七仓38操作；原六仓仅允许完整卡明确的SFMDigitalBoard依赖边及NewEMaint非目标seal变化，其余字段及原36操作定义/labels保持；HSDB Mac-only、三VM profiles、同pin第二次installer及独立字节/previous链一致。
- [ ] AC-5：installed HSDB解析不再unknown，credential/account/onboarding阻塞保留真实GAP；本票不修Secret/账号或调用新增dependency/rotation操作。
- [ ] AC-6：下一完整窗口同pin两端两次安装验收→本窗口新snapshot真实restore→原六仓36/字节/metadata/previous/absence/HSDB unknown→同pin再安装→最终七仓38/26目标/receipt/识别。旧窗口的安全恢复PASS仅为子证据，不替代该完整闭环。
- [ ] AC-7：总调度fresh核T01门后单独激活T02；本票文档准备/原窗口首次安装/恢复不等于已完成注册或UAT。

## 固定工具与发布边界

不改installer/runtime/governance规则，不从change branch安装；消费已有merged source无需制造本运维文档PR先merge门。最终文档仍走唯一manual PR确认/required CI/人工merge。main变化必须重审新pin及scope。

## 具体执行卡

# #339 安装与恢复执行卡 · Revision 2

状态：**STOP_BASELINE_RESTORED / WAITING_INCREMENTAL_SCOPE_WINDOW_APPROVAL**。原合同及原卡已经人类批准；本修正版尚未批准，不重启旧窗口。
唯一owner：01a10bea-8743-7d12-bd55-addf317088bc；branch/worktree：change/339-install-hsdb-broker / /private/tmp/issue-339-install-hsdb-broker。
source pin：**c9b5ef4e74592cbc68d6bdc6219568a1d51b6853**。本票只改四份运维文档，不改installer/manifest/runtime/AGENTS，不从文档branch或artifact导出字节安装。

## 本窗口真实结果

原T0：2026-10-05 21:54:55+09:00；原45分钟截止22:39:55，限定意外baseline恢复截止22:54:55。本窗口已因scope描述不准确STOP，不消费剩余时间再安装。
source primary已授权exact FF，当前clean main=origin/main=pin。两端首次installer均exit0，guard显示c9b5ef4/level with origin/main/operations38；25固定目标及receipt公开摘要/pin已核实，但完整AC-4策略断言失败。
同pin第二次installer、候选HSDB注册/身份读回、演练后再安装和最终七仓门均NOT RUN。
真实Mac→VM snapshot restore完成于22:09:45/22:09:46；两端独立读回于22:11:31/22:11:32验证字节/mode/root owner/previous链/absence/六仓36操作；HSDB installed entry均exit20，REQUEST_DENIED / requested project is not explicitly managed。Mac凭据metadata未变，未读Secret值。
这是因scope不符触发的真实恢复，不是成功完成AC-6计划演练：没有同pin第二次及最终再安装，AC-6整体仍未完成。两端installed previous source SHA仍NOT VERIFIED；snapshot证明observed-byte基线，不证明历史merged SHA。
Mac sudo-n最初要求密码；采用原生macOS管理员界面授权root进程，再执行固定sudo命令。恢复第一请求60秒超时后独立核Mac仍exact候选，重试同一恢复成功；没有接收或打印密码。

## 实际 installed 与候选的完整共享面差异

比较基线是本窗口两端真实非Secret snapshots，不是旧source SHA。Mac与VM结果相同；逐字段全量比较见 `full-installed-policy-diff.json`。

| 对象 | 实际 installed → exact pin 候选 | 影响/批准边界 |
|---|---|---|
| 原六仓 host项目项 | 仅 `sfm-digital-board/dependency_read_targets` absent → `["aisoft-platform"]` | 新增受管跨仓Issue依赖只读边；原卡遗漏，必须明确纳入修正版范围 |
| 原36项 operations | 全部定义同字节/同字段，无删除或更改 | 既有操作声明保持 |
| 新operations | `gitea.dependency.read`：manager-audit、mutating=false、reference；`gitea.credential.rotate`：credential-operator | 安装声明；本票不调用这两项 |
| host顶层 | 新增 `credential_rotation_policy` | UID0、固定grant/receipt/helper/operator/Gitea路径和Gitea1.26.4约束；不创建grant/Secret、不启用轮换 |
| 原六仓 governance | 仅 NewEMaint `routine_live_pilot/non_target_repositories_sha256`：4969422f72782de90155881cc4a92720dfd1ee5f468e940bd30ac7a666b0df85 → d45a20abb3224a5e02b1e22c338429017c9ff88d80fd5fc597bffb97a90e9334 | HSDB加入非目标集合后的seal重pin；routine policy和启用状态不变 |
| 新项目/仓库 | host `hsdb`、governance `HSDB` | Mac-only、vm_profile:null |
| labels / 其它顶层 / 其余原六仓字段 | 全部相同 | 无其它遗漏或删除 |
| VM profiles | 精确 aisoft-platform/localwms/emaintenance；newemaint是project_id，emaintenance是profile name | HSDB不进入VM profile；保留IMPLEMENT_PROVIDER=none |

字段来源：`f98c90ee0a34aa2c90b217c1c69a29b3be8386a7`，`feat(#286 T02): resolve manifest-bound dependency references through audit reads`。它在旧source e2edb3e已存在，但两端实际installed尚未包含，所以相对旧source无变化不能推出相对installed无变化。
源码 `resolve_target()` 只允许canonical owner/受管repo及显式source→target edge；`_read_dependency()` 用manager-audit，要求精确非site-admin身份、禁止redirect、限制response大小；返回repository/number/reference/state/labels，不返回Issue正文。这个字段不增加sfm-board-agent的Gitea collaborator权限、Git写入或merge/deploy授权，但确实新增broker允许的跨仓只读边，因此不能继续宣称原六仓policy完全不变。
本窗口没有实际调用SFMDigitalBoard依赖读取，也没有调用credential rotation；上述影响来自exact pin源码和manifest，不冒充live capability验收。

## 下一次需明确纳入的范围及窗口候选

修正版增量是：接受上表SFMDigitalBoard→AISoftPlatform依赖只读边和完整共享面声明；采用下面既有root执行方式；另行授权下一次完整45分钟安装/真实restore/再安装窗口。原卡的批准保留为历史，不覆盖本次新说明的权限边或自动续时。
建议仍由本聊天唯一执行owner，通过既有Mac benque原生管理员授权→sudo/root及gitea-ci benque/sudo执行。人类用户是授权者，不另增人工operator姓名；密码仅在系统UI输入。原生授权不足或超时必须STOP/保存实际状态，不能假定sudo-n缓存有效。
新T0仅在用户确认修正版后开始；现在没有新T0。前45分钟完成全部计划闭环；开始真实restore前保留至少30分钟。余量不足不开始，保留实际状态/AC-6 NOT RUN。额外≤15分钟仅意外baseline恢复与读回，不允许过期再安装或scope扩张。

## 安装目标与副作用边界

两端25固定source目标+生成receipt共26；四新增、六更新、十六同字节。下表与旧卡目标清单相同，新的变化是准确披露整体候选相对installed的policy差异。

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

不携带--pat-helper-artifact；helper必须null，gitea-pat-helper、keychain-acl-audit及previous仍absent。新helper/receipt/其它owner写入或baseline漂移即STOP，不清空未知声明。
只消费已合并版本化codex/install-host-access-broker.sh；不运行install-vm/install-skills等其它installer，不写账号/PAT/Secret/grant/profile/binding/protection/labels/service/timer/provider/routine，不push/PR/merge，不部署应用/公司服务器。

## 下次执行顺序及固定命令

1. fresh核其它owner/两端sudo/native root能力、source main和26目标基线；installed typed git.fetch.main，remote main变化即STOP/重新出卡。primary现在已是pin，不能重复宣称本轮新FF；future HEAD变化不reset/force。
2. fresh重备份两端固定非Secret安装面到本聊天新的 `window-2-backups/`，公开文件SHA/mode/owner/previous/absence需与本次恢复终态一致；重新核tarheader/文件列表/hash，记录两端exact归档路径/SHA。不能静默复用旧快照或覆盖本窗口归档。根写之前两端快照必须有效。
3. root进程复核clean main、HEAD=origin/main=pin、upstream精确origin/main；sudo子进程only safe.directory；guard必须level with origin/main，unknown/behind/warning不是PASS。
4. VM→Mac首次安装，独立验26目标/receipt/七仓38/完整policy差异/三VM profile；相同命令第二次installer应no-op，再做独立读取。

```bash
orb -m gitea-ci -u benque sudo -n env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/mnt/mac/Users/benque/MyDocs/AISoftPlatform bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
/usr/bin/osascript -e 'do shell script "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin sudo -n env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/Users/benque/MyDocs/AISoftPlatform bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh" with administrator privileges'
```

5. receipt必须source_sha=pin、merged_main=true、四公开目标SHA相同、helper:null；两端非Secret目标mode/uid/gid和目录核验。用installed broker执行HSDB只读repo/access/onboarding；可能credential/account阻塞，必须区分注册识别与access GAP，不修Secret或fallback账号。

```bash
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation gitea.repo.read
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.access.audit
env -u PYTHONPATH -u PYTHONHOME PYTHONDONTWRITEBYTECODE=1 /usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.onboarding.check
```

6. 开始planned restore前余量≥30分钟；再次核owner/候选全部固定字节及新snapshot摘要。Mac→VM真实tar -xzpf <本新窗口已记录exact归档> -C /；归档不含Secret。仅核为本候选新建且基线absent时清除以下八个精确目标，不用glob或递归删除。Mac用同原生root入口执行sudo-n tar/rm，VM用既有benque/sudo。路径集合为：

```text
/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py
/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py
/usr/local/libexec/aisoft/rotate-gitea-service-account
/usr/local/share/aisoft/credential-rotation-source.json
/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py.previous
/usr/local/lib/aisoft-host-access/aisoft_host_access/dependencies.py.previous
/usr/local/libexec/aisoft/rotate-gitea-service-account.previous
/usr/local/share/aisoft/credential-rotation-source.json.previous
```

7. 独立验baseline字节/mode/owner/previous/absence、六仓/36、SFMDigitalBoard字段恢复absent及HSDB unknown。只有全PASS才用同pin既有installer按VM→Mac再安装；不能重新选pin或从change/339安装。
8. 最终再验26目标/receipt、完整已批准policy差异、七仓/38、HSDB非unknown。每个phase保存exact时间、命令、exitcode、before/after和摘要。T01B退出要求完整AC成立；不能以本次真实恢复子项替代完整计划闭环。T02仍由总调度fresh核T01门后另行激活。

## 本窗口可用恢复证据（历史，不是下次自动使用）

| host | 本窗口snapshot SHA256 | 真实恢复读回 |
|---|---|---|
| Mac | 2cfa3e2623446d9fab5b3be2cd4dd95897711543dff27ffe1aef49b069bdcf62 | PASS，34归档文件/63 inventory路径；metadata及absence一致 |
| VM | 3aec3f3c47709f16c7e793bc2f966027a0ba3753553cc43b9f9545f1b6072af8 | PASS，43归档文件/75 inventory路径；metadata及absence一致 |

证据：/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-execution/baseline-restoration-verification.json、original-six-policy-diff.json、full-installed-policy-diff.json、dependency-field-source-history.txt、两端real-restore.json和restored.json。
直接原批准仍绑定exact #339/c9b5ef4e/原T0。本修正版必须由总调度先审阅，之后仅询问具体增量与新窗口，不重问原same-scope门禁；本聊天不发送其它聊天消息。
