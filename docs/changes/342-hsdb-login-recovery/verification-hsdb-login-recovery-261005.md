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
status: pending
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
# #342 · 合同准备验证记录

当前状态 **AWAITING_EXACT_ACCOUNT_CHANGE_APPROVAL**；账号启用/恢复/after验收NOT RUN。
本轮只证明准备材料和fresh before，不证明目标通道恢复。

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

## 实际命令与观测

| Command / check | Result | Evidence |
|---|---|---|
| sandbox typed open issue.list | BLOCKED_EXTERNAL / TRANSPORT_ERROR，exit20 | 执行路径失败，不证明不存在 |
| 同一typed命令经host boundary重复 | PASS，open #327/#333/#336/#339/#340，无同目标恢复票 | 本票dedup/readback artifact |
| #333/#339 typed issue.read | PASS，只读区分credential与安装owner范围 | 已有窗口不借用 |
| 平台typed git.fetch.main；git rev-parse HEAD origin/main | PASS，均为c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 | baseline-typed-0.json / source readback |
| hsdb typed gitea.protection.read | PASS，human admin merge，direct/force禁止，requiredCI精确集合 | hsdb-protection-before.json |
| hsdb typed repo.read / host.access.audit / host.onboarding.check | GAP：各exit20 HTTP_401 / BLOCKED_EXTERNAL | baseline-typed-2/3/4.json |
| human-admin UI UID5 edit | PASS before：login/source/flags/现有表单核对；14:51:49.513Z fresh再次确认 | ui-before.json；uid5-before-flags.png |
| UID3及HSDB collaborator/main只读UI | PASS before：UID3未停用；agent Write/manager Administrator；remote main6114c912… | ui-before.json；非全局用户审计 |
| source-policy搜索与精确Gitea1.26.4公开源码只读 | PASS：#252退管H-6仍NOT RUN；当前strict无expected=true；API禁止signed user | policy-findings.json / source-policy-evidence.json |
| typed issue.create #342 | PASS，entry triage/needs-triage，exact tracker | issue-create-receipt.json |
| 本地worktree add / claim | PASS，exact branch/WT/session；初次sandbox ref lock被拒后同本地动作host执行 | owner/source本地证据；无push |
| typed classification | PASS，type/security + complexity/complex | 后续真实labels读回 |
| semantic resolver / classification / Ticket graph / diff /正文一致性 | 结果见final-checks.json；本地准备不提升为live PASS | 最终归档结果填在artifact，不伪造提前通过 |

orbstack-access-diagnostics调用=0；native管理员弹窗=0；账号checkbox改变=0、账号表单提交=0、
PAT/password/token/grant/DB/Secret手工读写=0；非目标owner/worktree修改=0。固定broker内部认证只用于已授权typed入口。
UI一次导航typeText漏首字母被Chrome作为Google搜索，已setValue修正并fresh核对exact ACL URL；没有Gitea表单提交。
本轮未新增或运行credential helper，不调用rotate/bootstrap等mutation工具。

## Acceptance criteria结果

| AC | 当前结果 |
|---|---|
| AC-1 | 准备本地文档/Issue身份等已执行；最终manifest/body/head及校验见handoff |
| AC-2 | PASS：完整可审阅单flag操作卡、风险及30分钟有限窗口；不是账号批准 |
| AC-3 | NOT RUN：用户exact账号批准与写入 |
| AC-4 | after NOT RUN；before三入口HTTP_401 GAP |
| AC-5 | before PASS；after零漂移NOT RUN，非目标全局用户未枚举 |
| AC-6 | 真实sameflag失败恢复NOT RUN；只有计划 |
| AC-7 | 准备分层handoff；live执行/最终PR/merge等未完成 |

## 全部未执行项

账号flag true→false、sameflag恢复、after repo/audit/onboarding、PAT有效性/manager-mutation根因、
live主分支写入/agent merge负向探针、账号密码/PAT/ACL/protection/binding/profile/provider/timer修改、
Secret/grant/DB访问、工具安装/服务/HSDB应用/公司部署/UAT、push/PR/本票requiredCI/merge、清理归档：
全部NOT RUN或NOT VERIFIED并保持独立scope。文档-only未改shell脚本，bash -n/ShellCheck/smoke本轮NOT RUN；
真实可审阅合同通过semantic/Ticket graph/classification/diff等针对性本地检查后记录。
