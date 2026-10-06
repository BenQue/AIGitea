---
issue: 344
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/344
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - authentication
  - security
  - platform-governance
depends_on:
  - 337
  - 339
status: approved
branch: change/344-hsdb-pat-inventory
created: 2026-10-06
updated: 2026-10-06
---

# #344 · 治理合同交付Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | fresh inventory/dedup、唯一Issue/claim、四角色/证据、本地文档候选与审阅卡后STOP | - | done |
| T02 | 人类具体确认exact六路径patch后，独立run应用/校验/一个本地commit/STOP | T01及G1具体确认 | done |
| T03 | fresh复核治理候选，投影已批准状态/既有范围并经qualified Controller整合main；形成唯一manual PR候选 | T02 | in-progress |

T01已由原owner准备完成并STOP，done只表示局部准备完成。G1已人类批准并应用/校验，原子commit dc66b448e231edc7f8a3438fbba20152547ea101 后STOP。fresh接续frontier为T03：必要四角色结果/已批准状态/既有路径投影、本地校验和qualified main整合。live Issue仍open/spec-drafting，仅local approved投影，不替代现场或运行批准。T02只治理，无runtime。T03只有新的最终PR授权才remote push/create；本轮没有该授权。人工merge、exact main/终态/cleanup另按确定性平台流程，无自动merge。

## Expected touch points

T01：spec列明的本目录四角色与五个公开evidence JSON；external本会话artifact。T02：仅spec列明G1六治理路径，不含evidence任意扩张、AGENTS或运行代码；需实际批准后在本owner claimed WT执行，不改shared primary。T03：四角色已批准状态/实际结果投影、spec exact git_scope（原9+G1六路径并集11）和manual candidate检查；不改共享reference或skill规范字节，不改原AC/Q矩阵/deps。qualified Controller只作本地[C,M]整合；remote发表待最终确认；新行为/路径或冲突停人审。

未来fresh R/source、共享工具安装有平台独立Issue/owner/spec；HSDB消费方read有HSDB独立项目合同，编号尚null；本表不把它们作为#344运行tickets、不自动创建或dispatch，不把本治理票runtime未运行写成AC失败。

## AC、Ticket与检查映射

| AC | Ticket | 本次check / future verification |
|---|---|---|
| AC-1 | T01/T03 | installed broker open issue/read/comments、main fetch；resolver/required-docs/classification route/claim/exact scope |
| AC-2 | T01/T02 | 对spec逐项manual review fixed target/GET/auth/transport/output allowlist/禁止项；后继fixture另验 |
| AC-3 | T01/T02 | 下表Q-01…Q-12与hard bounds审阅；当前设计检查而非runtime PASS |
| AC-4 | T01/T02 | git diff --check、四role mapping、9 tracked文件allowlist、no-sudo/路径/三恢复边界审阅 |
| AC-5 | T01/T02/T03 | approval-G1/null、独立G1 STOP记录/fresh读取证据、manual提交授权；source/install/read独立卡 |
| AC-6 | T01/T03 | fresh #337/#339终态及#342/#343证据/deps只读检查，无其它WT写入；无环review |

运行命令只使用既有受控CLI：`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 344 --repo <ownedWT>`、`resolve-required-documents 344`、`check-change-documents --repo <ownedWT>`及`bash codex/tools/apply-classification-labels.sh --repo <ownedWT> --verify 344`。本轮不运行Controller/provider或未知future CLI。

## 后继runtime隔离验收设计（全部NOT RUN）

| Test | 必需正负例与可观察结果 |
|---|---|
| Q-01 | 两固定UID正确；其它UID/login/URL/path/method/request/card/mixedhash拒绝；零网络 |
| Q-02 | Basic由human tty输入、禁回显/argv/env/log；cancel/EOF/SIGINT/TERM/输入time恢复echo/退出；无自动重试 |
| Q-03 | fixedTLS/version/人类admin身份/目标正例；HTTP/invalid证书/redirect/proxy/identity/version before-after漂移拒绝 |
| Q-04 | 0、1、50、51、短非终页、多页清单直到明确空页；两scan total=count与metadata一致 |
| Q-05 | 缺/错X-Total-Count、途中total漂移、末尾多/少、空页前漏项、后页重复ID拒绝；name重复正常保留 |
| Q-06 | 两scan ID/ordering/scopes/timestamps变化、同创建时间排序漂移拒绝，不宣称atomic |
| Q-07 | duplicate key/NaN/Infinity/non-array/坏ID(bool)/name/control/time/scope/异常field拒绝；strict output额外field拒绝 |
| Q-08 | fulltoken/sha1/token_last_eight/password/OTP/Authorization/rawerror注入到成功/错误/嵌套name等；stdout/stderr/cache/temp/traceback/receipt均无泄漏，failure无items |
| Q-09 | 单/累计body、pages/count/output上限、HTTP/整体monotonic deadline与window过期拒绝；clock回退不延时 |
| Q-10 | source/digest/interpreter/installer provenance/symlink/owner/mode/mixed版本/unknown previous拒绝；无global/root/credentials/VM写入 |
| Q-11 | public synthetic安装forward/no-op/restore；源delta forward/reverse/forward；每file bytes/mode及absence明确，非PAT恢复 |
| Q-12 | meaningful独立进程canary只访问fixture受控TLS；只GET固定路由，无PAT/password/flag/ACL写，current通过仍ownership/access NOT ASSESSED；existing broker38-op回归另证 |

future source shell修改按AGENTS运行bash -n、可用ShellCheck与完整smoke，不能测试跳过涂绿。不调用真实Gitea/PAT/Secret/DB/VM作为fixture。不使用#333/#336 runtime，回归仅从届时merged main独立获取。

## 按顺序的后继门与阻塞

1. 本轮T01合同候选→STOP；最小审阅决定只G1/T02的exact治理路径。
2. G1实际批准/应用/STOP；fresh读取该规范后才由独立source Issue准备工具合同。安全transport/humanUID/source信任缺口先明确，不能把null装入运行policy。
3. source独立contract/start→isolated implementation/local验证→最终PR确认→manual发布/required CI/人merge；source成功不提供install/read授权。
4. 新merged pin、完整public制品/解释器trust/previous/no-sudo paths→独立用户安装卡及窗口→真实install/second no-op/restore/reinstall；无root/broker重装。
5. 消费方`admin/HSDB`独立现场合同绑定人类identity/TLS/installed pin、exact read card/request/target/operator/≤600秒窗口和撤销机制→独立read批准→CURRENT单target查询。先UID3，下一独立exact请求UID5；任何失败STOP，不续期、不试服务PAT。
6. CURRENT完整结果仅交调度：共享manager-mutation恢复在平台独立security合同（含audit消费者和每未知ID处置）；hsdb-agent恢复/新flag窗口及adoption由`admin/HSDB`独立项目合同。后续命名B、产品、部署/UAT推进均属HSDB，本票不设计或派发项目实施。

#342文档处置由原owner先完成具体失败结果合同审阅；#343发布仍按原deps由调度顺序处理。它们是文档发表线，本能力source/install/read是独立能力线，不能互相等待HSDB访问PASS造成循环。

发布前需fresh查#327 FF/首次发表和#336完整唯一PR/namespace能力是否可用；#336当前#333-only不覆盖#344，若缺exact proof，BLOCKED且交owner或独立治理，不扩工具、不使用不完整PR列表证明唯一、不push绕过。

## 数据库、部署与恢复

无数据库迁移或部署。G1只治理文件可本地revert；本轮保留worktree/候选不清理他人。tool/user安装/read窗口三恢复边界见spec，由后继exact合同独立验收，全部NOT RUN。取消本票无权撤销/轮换PAT、改账号/服务或恢复PAUSED监控。

## 2026-10-06 人类补充的仓库归属边界

人类直接补充：“当前项目具体部署的问题，不要在 aisoft 平台创建。具体项目的推进在本项目里处理。”本票据此仅保留真实**共享平台能力**：共享manager与固定受管agent的CURRENT清单工具、版本/身份/分页/Secret剔除协议及平台治理例外；工具源规范/代码和共享用户安装合同属于`admin/aisoft-platform`。首个受控用例为UID3/UID5，允许范围仍固定两者，不借“共享”扩大为任意账户读取。

HSDB是该能力消费方。HSDB一次性现场read请求、hsdb-agent凭据/flag恢复与adoption、项目本地部署、环境/配置、迁移/备份/恢复、应用健康检查、业务修复、UAT和公司试运行均由`admin/HSDB`的对应既有聊天及独立项目合同追踪；不在AISoftPlatform新建或承接，不以平台completed取代HSDB验收。共享manager-mutation影响所有平台消费者的恢复另用平台security合同，不能与HSDB agent恢复合票。

本轮保留#344/owner/claim及原授权，既有#342/#343仅exact证据输入，不自行迁移/关闭/接管。未来若仅剩HSDB一次性现场处置而没有共享工具/协议/治理delta，停止该混入范围并交根拆分，不用平台票容纳项目推进。后继项目票号/owner/窗口均null；本轮不创建项目票，不使用未验收跨仓broker能力来投影项目状态。

## G1/T02 具体执行与恢复计划（实际批准前全部NOT RUN）

1. 独立受控步骤重读本票四角色、AGENTS和已确认仓外卡；核本会话claim、exact branch、card/patch SHA256、HEAD=`09084e19a8b1a3bb018f70d80e1a3b1cc3611a88`、clean及六路径before bytes。任何漂移先STOP，不自动rebase/接管或调整patch。cached base=`96ba8a17baad8e9854d4e8d0397d4162b8067b09`只是原候选锚；后续发布fresh main另验。
2. 先以`git apply --check <approved-patch>`核exact候选，再以`git apply <approved-patch>`只应用spec六路径。不得把仓外卡/校验脚本/fixture/receipt、evidence JSON、AGENTS、runtime或global安装面加入本票delta。
3. 运行既有CLI `resolve-documents 344`、`resolve-required-documents 344`、`check-change-documents --repo <ownedWT>`；核`git diff --check`与包含新reference的六路径scope、各candidate文件hash及skill/reference链接。保留6AC、deps[337,339]、security/complex/add/manual和Q-01…Q-12；runtime/smoke/bash-n/ShellCheck因零shell/runtime差量仍NOT RUN。public evidence manifest保持原T01快照原字节。
4. 只暂存六个明确路径并核staged hash/scope；创建一个本地原子commit `docs: apply issue 344 current PAT inventory governance`。写仓外实际结果/前后HEAD/tree/claim/clean/hashes/验证回执后立即STOP。实际人类确认仅此G1独立步骤，不运行Controller/provider、不写Issue标签/正文、不push/PR或派发后继。
5. commit前失败：核六路径仍等于candidate且无其它编辑后，`git apply --reverse --check <approved-patch>`再反向应用，验证五文件旧hash、新reference缺失、HEAD不变且clean。commit后失败：HEAD必须exact等于本次G1 commit且未push/无其它编辑才对该exact commit本地revert；不reset/rebase。遇漂移则STOP保留材料。恢复不涉及PAT/账号、安装或服务。

G1 card准备与隔离patch/document核验可以现在完成，不以尚无工具/TLS/human UID或#342/#343访问PASS作为前置。启动确认只审当前六路径；其它具体合同由其实际阶段处理，本轮不创建票或叠加审批链。

## T03 fresh执行记录与接续责任

T03 actual reads/qualification见verification；结果以仓外最终候选回执记录。原G1六路径patch及其STOP记录保持独立。本轮只提交四角色事实投影、执行本地文档gate及qualified main整合；不调用provider，不发表remote，不接管其它owner。

根已指定独立源码筹备聊天 `HSDB T02D：受控凭据清单工具源码开发`（session `01a110fd-3a28-77c3-8ffc-4f0a987a9940`）。它负责后继source合同筹备和获批实现，不能写本票WT；本票不另建第二源票、不改其claim或发送消息，交接由根负责。源码合同筹备不依赖HSDB访问恢复PASS。现规则要求G1独立批准/应用/STOP后fresh读取、独立source security/complex/manual合同和启动批准；未明文要求合同草拟先等#344合并。未来用户安装必须使用clean approved merged源码；现场receipt的governance_merge_sha必须有真实main合并证据，不能用local commit填充。当前未实现工具/安装/read，各层保持NOT RUN。
