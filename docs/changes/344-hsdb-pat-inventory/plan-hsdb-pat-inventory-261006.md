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
status: contract-drafting
branch: change/344-hsdb-pat-inventory
created: 2026-10-06
updated: 2026-10-06
---

# #344 · 治理合同交付Plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | fresh inventory/dedup、唯一Issue/claim、四角色/证据、本地文档候选与审阅卡后STOP | - | done |
| T02 | 新人类决定绑定G1六治理路径；独立run应用/校验、本地commit后STOP | T01 | blocked |
| T03 | fresh只读审查治理候选、exact范围/required docs/分类；形成唯一manual PR候选 | T02 | blocked |

T01是本轮唯一frontier；done只表示局部准备完成，Issue仍contract-drafting/open，G1和其后均未批准。T02只治理，无runtime。T03只有新的最终PR授权才remote push/create；本轮没有该授权。人工merge、exact main/终态/cleanup另按确定性平台流程，无自动merge。

## Expected touch points

T01：spec列明的本目录四角色与五个公开evidence JSON；external本会话artifact。T02：仅spec列明G1六治理路径，不含evidence任意扩张、AGENTS或运行代码；需实际批准后在本owner claimed WT执行，不改shared primary。T03：必要verification/summary结果投影和exact manual candidate检查；范围变化停人审。

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
