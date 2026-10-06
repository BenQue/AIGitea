---
issue: 342
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/342
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - rollback
depends_on:
  - 337
  - 339
branch: change/342-hsdb-login-recovery
created: 2026-10-05
updated: 2026-10-06
status: contract-drafting
---


## 2026-10-06 实际执行结果

当前终态：**ROLLED_BACK_FLAG / ACCESS_GAP / STOP**。本次批准的有限账号尝试和失败恢复已完成；访问恢复目标未达成，不再启用或追加认证修复。

- 批准绑定原卡 SHA256 `763aa652022da7f045220444087e14f81f5a098bfee5aa3b3404e210b2b31a21`、原doc head `1bd4d61e8992f4f93a21b17619be44ce671c05c0`、原Issue body SHA256 `a3bb337e9db57f328619eab8d5289e5f835b67d70cc079b6f0313674ae7a9619`；原卡及原正文快照保留，以下回填不追溯改写批准对象。
- 直接用户完整批准已收到；首次取消开关点击被CUA自动审核拒绝，账号未变。随后在总调度聊天直接人类答复“确认现在执行原卡单字段操作”，本owner通过read_thread核对userMessage `01a10e95-0a86-7782-89b4-3361c3dc2d3d`，满足操作当下确认后执行。
- 原窗口T0日本时间09:12:51；首次保存截止09:22:51、验收09:32:51、失败恢复09:42:51；未延长。09:21:34.788以现有admin UI保存UID5 `Disable Sign-In true→false`一次，fresh读回false。09:22:11三项固定typed after验收仍各exit20 `HTTP_401 / BLOCKED_EXTERNAL`，故访问恢复FAIL/GAP。
- 09:22:44.024仅同UID5同flag保存false→true恢复一次，随后fresh读回true；实际失败恢复PASS。共1次enable保存+1次restore保存，其它账号无写入。
- UID5其它可见字段与Password空输入保持；Email仅比较相等、不收集；Language UI前后均空且未选择，原始存储值仍NOT VERIFIED，不扩张为全量存储字段审计。UID3 flags、HSDB agent Write/manager Administrator、private、remote main `6114c912310bbaf281bbfe77743abd8cff99087d`和完整protection JSON未漂移；requiredCI仍为 `CI / test (pull_request)`。
- fresh source pin仍 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`；Mac installed相关源文件逐字相符。VM安装只沿用此前#339独立验收，本轮未再验或安装。PAT有效性与manager-mutation根因仍NOT VERIFIED，不由401推断。
- 本次只回填本票四文档、Issue正文及脱敏evidence。账号/PAT/password/ACL/protection/profile/binding/provider/timer、Secret/grant/DB、工具安装/服务/HSDB应用或公司部署、push/PR/CI/merge/UAT均未追加执行；provider未启动。冻结合同中的零写入与NOT RUN语句是准备阶段历史。

真实执行证据位于 `/Users/benque/.codex/visualizations/2026/10/05/01a10c83-389d-7ab3-b364-59e108f1ca46/hsdb-account-recovery` 的 `execution-handoff.json`、`execution-human-action-time-confirmation.json`、`execution-before-*.json`、`execution-after-*.json`、保存时间/AX/flags截图及 `账号执行与失败恢复回执.md`。

T02访问目标未通过，Ticket保持pending并因外部访问GAP停止；T03最终PR仍pending。账号窗口已结束，不借此票重试或修改凭据；进一步诊断/安全操作须单独确定具体scope。PR提交及人工合并仍是独立门。

## 批准时准备记录（历史快照）

以下保留原准备合同内容；其中“当前未批准/账号写入0/after NOT RUN”均描述2026-10-05准备阶段，不代表上述实际执行结果。原批准文档字节可从原doc head复核。
# #342 · 唯一账号flag恢复Spec

## Acceptance criteria

- [x] AC-1：平台exact Issue/owner/branch/claimed worktree/四角色映射一致，fresh typed去重；本地文档及Issue正文可sha256复核。
- [x] AC-2：给出精确admin UI入口、完整before/after、source安全政策证据与PAT影响、有界执行/同flag恢复窗口；所有账号动作NOT RUN。
- [ ] AC-3：获得绑定#342/branch/card hash/doc head/body hash的一次批准，fresh前置无漂移，唯一UID5 flag true→false，其它字段原样。
- [ ] AC-4：after typed repo.read/audit/onboarding分别PASS；HTTP401/未知时不修其它scope，按卡恢复同flag。
- [ ] AC-5：UID3非目标对照、UID5非flag字段、HSDB private/ACL/main protection/requiredCI/remote main零漂移；其它账号零操作，Secret零手工读写。
- [ ] AC-6：如发生实际失败，有限sameUID/sameflag恢复及读回；未发生则不制造故障，标NOT RUN/NOT TRIGGERED，不能报真实恢复PASS。
- [ ] AC-7：将操作/恢复/通道结果分层交T02；唯一最终文档PR须另经提交批准及人工合并，当前push/PR/CI/merge/UAT/deploy全部NOT RUN。

## 接口、数据与兼容性影响

不改任何source/API/CLI/schema/凭据/ACL，只有获批后Gitea已有用户UID5的一项账号状态拟改变。
本票平台tuple按readable命名；HSDB既有数字约定与adoption合同不变。
`contract_effect=restore`描述恢复既有通道目标，不断言原停用没有安全目的；security/rollback强制complex/manual。

## 未决问题与停止条件

审批决策待用户具体批准。历史#252停用的实际执行/当前设置来源、PAT有效性及manager-mutation根因NOT VERIFIED，
不能靠本票授权补建调查工具/读取Secret。若后续出现仍有效的明确`expected prohibit_login=true`安全政策、
同UID另有owner窗口或批准范围冲突，停止并报告具体证据，不执行本卡、不解除安全门。

## R2a exact账号操作卡 · 当前未批准

- Issue：#342；tracker `admin/aisoft-platform`；branch `change/342-hsdb-login-recovery`。
- 唯一writer/执行owner：聊天 `01a10c83-389d-7ab3-b364-59e108f1ca46`；worktree `/private/tmp/issue-342-hsdb-login-recovery`。
- 目标：local Gitea UI显示 `1.26.4`，project_id=`hsdb`，repository=`admin/HSDB`，exact UID5 / `hsdb-agent`。
- 入口：[UID5 edit](http://gitea-ci.orb.local:3000/-/admin/users/5/edit)。执行身份为现有已登录human-admin `admin` 的Chrome会话；
  仅在获得一次具体批准后由本owner以受控UI操作，或由批准中明确指定的人执行；不能换成manager/agent/PAT/helper/DB/raw API。
- 当前状态：`AWAITING_EXACT_ACCOUNT_CHANGE_APPROVAL`；审批准备不等于`approved`，本轮表单提交/账号flag修改=0。
- 风险须在一次批准中接受：#252存在历史退管停用意图而实际设置目的未知；恢复账号会恢复任何仍有效既有PAT/已存在登录方式及既有Write能力。
  现有PAT有效性和manager-mutation根因NOT VERIFIED；本票不同时修这些缺口。

### 完整before/after边界

| UID5字段/对象 | 本轮before | 拟after |
|---|---|---|
| UID/login | 5 / hsdb-agent | 同值 |
| Authentication Source | Local | Local |
| User visibility | Public | Public |
| Full Name / Website / Location | 空白 | 同值 |
| Email | 原UI值，脱敏不收集 | 原值，禁止编辑 |
| Password输入 | 空白，不收集隐藏值 | 保持空白，不输入/不自动填充；否则零写入STOP |
| Language | UI未显示选项文本 | 原选项原样；执行前须确认未动且fresh读回同值，不能猜选项 |
| Maximum Number of Repositories | -1 | -1 |
| User Account Is Activated | true | true |
| **Disable Sign-In / prohibit_login** | **true** | **false（唯一允许差异）** |
| Is Administrator | false | false |
| Is Restricted | false | false |
| May Create Organizations | true | true |
| Avatar/现有PAT/password/2FA/SSH/OAuth状态 | 不读取Secret、不编辑 | 保持，不操作 |
| HSDB collaborator | hsdb-agent Write；manager Administrator | 同值 |

UID3 `aisoft-platform-manager` Local / active=true / disable_sign_in=false / site_admin=false /
restricted=false / may_create_organizations=true 为非目标对照，禁止编辑。其它账号不枚举、不操作；
零非目标账号写入以唯一UID5表单操作轨迹证明，UID3是额外对照，不能把抽样扩展为全局状态审计。
完整表单保存可能提交未改变字段：执行前逐字段比较、只切该checkbox，执行后fresh比对；出现任何非目标字段漂移停止并升级，不能用本卡修它。

### 一次批准与有界执行/失败恢复窗口

一次批准绑定#342、exact branch、外部R2a卡SHA256、doc head、Issue body SHA256及本节动作/风险/窗口。
没有本批准不触碰checkbox、不提交。执行前再只读确认批准来自用户且绑定一致；批准文字如需转交，由总调度读取既有用户决策，本owner不发送其它聊天消息。

T0取**批准收到时间与本owner首次执行前核对开始时间的较早者**，均以Asia/Tokyo记账；
总窗口30分钟。批准必须在当前连续执行期间获得：如首次核对距批准>10分钟、到期、UI/目标/pin/合同有漂移，授权失效、零新增写入STOP，不能自动续窗。

1. T0至+10分钟：fresh重新打开Dashboard确认signed-in admin；确认目标URL/UID5/login/版本及上表全部before。
   只读读取UID3对照和HSDB collaboration，重跑typed protection/repo/audit/onboarding。核对source/installed pin仍为已接受pin，
   无其它owner同UID写入窗口，provider仍none、HSDB vm_profile:null。已有PAT/binding保持；只读核验不打开Secret/PAT页面。
   before中预期401不阻止本批准的单flag操作，但任何新状态/范围/身份/保护漂移都STOP。
2. 前置全部成立，且保留至少20分钟恢复余量：仅将UID5 `Disable Sign-In` 从checked(true)取消为false；
   以fresh AX/截图确认其它字段原样且Password仍空；点击 **Update User Account** 一次。不点击Delete/Avatar。
   checkbox未保存前发现问题，刷新丢弃未提交编辑并STOP。首次保存不得晚于T0+10分钟。
3. 保存后立即fresh reload同一UID5；仅差异是true→false时记 `ACCOUNT_FLAG_CHANGED`。
   timeout/错误/结果不明，先只读reload；不重复启用保存，不假设提交失败。若flag仍true，记未生效并STOP，恢复no-op。
4. 至T0+20分钟：依次运行下面三个fixed typed只读命令各一次，再读protection和UID3/HSDB ACL/remote main。
   三入口必须各exit0/PASS，且所有非目标字段/保护/requiredCI不漂移，才记 `RESTORED_ACCESS_PASS`；
   账号flag改变不能替代audit/onboarding。聚合HTTP401不能证明manager根因。
5. 任一after核验失败/401/未知/非目标漂移：至T0+30分钟，只在fresh确认**同UID5/login且flagfalse**时，
   将**同一个Disable Sign-In flag**设回true，保存一次、fresh读回其余字段不动。flag已true则零恢复写入。
   恢复后仅记 `ROLLED_BACK_FLAG`，重新保留访问GAP；不再次启用、不更换PAT/密码/ACL、不给新权限。
   只授权一个enable保存和至多一个same-flag恢复保存；未创建工具、不运行installer/grant/DB。
6. 同UID/当前flag无法确认、admin会话失效、恢复不可读或超时：`RECOVERY_NOT_VERIFIED / STOP`，
   保留脱敏证据升级用户；禁止盲写、自动延长、换身份或修非目标字段。窗口外任何新增写入须新具体批准。

本阶段不开启真实故障/恢复演练；不得为演示而反复禁用/启用。回滚计划可审阅，实际执行仍NOT RUN。
本卡是独立账号恢复安全决定，批准明确包含有限same-flag失败恢复；不产生Mac系统管理员/root弹窗。
以后如确需native管理员弹窗，必须先列用途/exact版本/具体命令/文件增删替换/影响账号项目服务/备份恢复；本卡无此操作。

### 固定typed验收与零漂移门

```bash
/usr/local/libexec/aisoft/host-access-broker --project hsdb --operation gitea.repo.read
/usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.access.audit
/usr/local/libexec/aisoft/host-access-broker --project hsdb --operation host.onboarding.check
/usr/local/libexec/aisoft/host-access-broker --project hsdb --operation gitea.protection.read
```

前三项当前before均exit20 HTTP_401，after尚未运行。manager-audit protection目前单独PASS；
保护完整JSON与操作前fresh baseline比较（服务器时间字段单独记录），required contexts精确为
`["CI / test (pull_request)"]`、enable_push=false、enable_force_push=false、
merge whitelist仅admin、block_admin_merge_override=true、status_check=true。
HSDB private/default main、ACL保持；remote main before=
`6114c912310bbaf281bbfe77743abd8cff99087d`。同窗口变化一律STOP，不能本票盲同步本地main。
不执行push/main-write/merge负向live探针；broker/readback验证安全门，不能以本票触发受禁止的写。

### 文件、备份、恢复和禁止项

账号动作不新增/替换/删除系统文件；只新增本票四文档和本聊天脱敏evidence/截图/审批回执。
备份是before完整字段对照与无Secret flags截图；**不是DB/Secret备份**。
账户恢复只允许同UID同flag回原true；git revert只能撤合同文档，不能恢复账号/PAT。

不修改AGENTS/runtime/CI/installer/manifest或HSDB应用。PAT/password/ACL/protection/profile/binding/provider/timer/
token/grant/DB/Secret/安装/服务/公司部署/push/PR/merge全部不在本次操作范围。保持IMPLEMENT_PROVIDER=none。
#333/#339/#340的Issue/owner/worktree/grant/安装窗口一律不借用。

## 证据层与前置

| 层 | 当前证据 | 边界 |
|---|---|---|
| source | 本owner typed `git.fetch.main` PASS 后平台 HEAD=origin/main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 | 没有runtime/脚本/AGENTS/manifest修改 |
| doc | 本票独立四文档、本地合同提交；exact doc head和逐文件SHA256见外部handoff | 不等于source main、PR或CI |
| installed | 总调度/#339已独立核验Mac+gitea-ci同pin安装、幂等、真实恢复、同pin再安装PASS | 本owner未重验安装、不复用installer窗口；helper:null不证明轮换能力 |
| credential | 本轮固定typed读操作内部认证；未手工读/散列/打印/复制Secret | 现有PAT有效性/撤销状态NOT VERIFIED；不提供grant |
| live before | fresh UI UID5停用、UID3未停用，exact HSDB ACL，typed protection PASS | 下表是before；账号写入/after均NOT RUN |
| access before | Mac hsdb repo.read/audit/onboarding均exit20 HTTP_401 | manager-audit protection单独PASS；manager-mutation根因NOT VERIFIED |
| UAT/部署 | NOT RUN | HSDB adoption/应用/公司现场仍由独立owner负责 |

#337已人工合并；#339技术安装退出门已独立PASS，文档最终PR/归档仍由#339 owner负责。summary的depends_on保留两票，不能借技术PASS宣称#339已closed，也不能绕过日后Controller的依赖门。
T02 owner保持 `01a1073b-42e6-7491-89d1-212d8b19636a`；本票不改变HSDB数字命名规则，不创建HSDB Issue/分支，不重置/rebase其本地main。
HSDB fresh remote main=`6114c912310bbaf281bbfe77743abd8cff99087d`；本地main=`8e7f5d19c0e7cdc627907dc0962f7285025fb860`来自总调度/T02，本owner未改动。

## 历史安全意图与Gitea版本行为

只读发现[#252 spec](../252-offboard-five-projects/spec-offboard-five-projects-260905.md) AC-12 与
[verification](../252-offboard-five-projects/verification-offboard-five-projects-260905.md) H-6 明确把
`hsdb-agent`列入退管待停用账号，但H-6仍NOT RUN；H-4撤销PAT亦NOT RUN。存在明确的历史退管安全意图，
而当前flag的实际设置人、时间、原因及该历史动作是否执行仍 **NOT VERIFIED**。不能由历史NOT RUN推断PAT仍有效或已撤销。
#337恢复source注册但明确不解除停用；本票将拟解除历史退管对象的单一flag作为独立安全决定请求具体批准。

当前pin的manifest/contract/bootstrap/strict identity verifier未发现`expected prohibit_login=true`：
`codex/tools/bootstrap-gitea-service-account.sh:314-341`创建bot并独立处理MustChangePassword；
`codex/runtime/aisoft_host_access/broker.py:2843-2864`仍验exact login与non-site-admin；
#219 spec AC-3允许`prohibit_login`作typed metadata，不把其值当权限决策。未修改或解除任何安全门。
这项结论限所查source/已发布合同，不等于当前停用原因已证实。

Context7 `/go-gitea/gitea`返回main分支概览；精确版本另以既有公开模块缓存
`/private/tmp/issue-316-build/gopath/pkg/mod/code.gitea.io/gitea@v1.26.4`只读核对，并交叉读官方
[Gitea v1.26.4 API source](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/api.go#L836-L855)。
该版本PAT解析先获得user；已signed user的IsActive/ProhibitLogin检查拒绝API请求（此分支403），
apiAuth认证错误路径401。故本轮HTTP401与禁用flag同时存在，**不能证明禁用是唯一故障原因**。
恢复false可能使仍有效的既有PAT重新获得既有Write能力；不重新签发、不承诺可用，不测试密码登录。
