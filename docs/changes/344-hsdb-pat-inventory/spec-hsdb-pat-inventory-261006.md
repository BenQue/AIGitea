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

# #344 · 固定身份 CURRENT metadata 读取治理规范

## 成功定义与批准范围

本票只交付目的限定工具的治理规范。以下“必须”是待批准的未来规则，不能被当前run用于扩大授权。本轮只T01准备；G1必须在独立受控步骤实际批准、应用、校验、本地commit并STOP。后继fresh run重读当前AGENTS、已生效规范及映射spec/plan后，另立唯一源实现security/complex/manual Issue，才可按其已批准合同实施runtime。不得用#333/#336未合并代码、fixture、旧安装批准或本草稿自举。

## 固定target/request与人类身份

| 项 | 未来约束 | 当前证据 |
|---|---|---|
| target | 仅 `manager`→UID3/aisoft-platform-manager；`hsdb-agent`→UID5/hsdb-agent | 输入/既有合同；现场fresh identity NOT RUN |
| 单次请求 | 一张exact read card只含一个target和唯一request ID；不能批量两UID或枚举其他用户 | read card=null |
| 调用者 | 独立人类site-admin；固定canonical human login候选为`admin`，现场UID/login必须在独立read卡实际绑定和独立验收 | actual UID/login=null；不推定既有浏览器身份 |
| 认证 | 人在独立本地终端经`/dev/tty`无回显输入Basic密码；若2FA有要求同样安全输入OTP；不经聊天、CUA、argv、env、管道或普通文件 | 输入NOT RUN |
| 身份通道 | v1默认安全human Basic；仅已独立验收的固定人类通道可替代，必须先独立修订规范，不能自动fallback | 通道null/GAP |
| transport | 仅已绑定同一canonical实例、TLS证书验证通过的固定origin；禁止redirect、代理/环境override与明文Basic；禁止skip-verify、Sudo header/query | existing manifest origin为HTTP；安全origin=null/GAP，输入/网络调用前拒绝 |
| 服务账号 | UID3/5只是目标；不要求UID5可登录，不修改target flag，不用其password/PAT认证 | #342恢复true且窗口已关闭 |

接口只能接受source policy固定enum target、符合固定格式的opaque request ID/approved-card digest，不接收URL/username/path/HTTP方法或credential路径。record从工具独立固定用户目录解析，不能传caller路径。approval记录不是root grant；同用户记录的存在不能证明人批准，必须用独立审阅的read card及核验receipt绑定exact request/目标/pin/时间。缺证据即拒绝。

允许的网络方法只有GET；固定路由集合是`/api/v1/version`、`/api/v1/user`（调用者）、`/api/v1/users/aisoft-platform-manager`或`/api/v1/users/hsdb-agent`（目标）、同一fixed目标的`/tokens?page=N&limit=50`。version GET仅用于身份/版本闸门，不授予其它端点。禁止POST/PATCH/PUT/DELETE、Secrets/Applications页面、DB、任意admin route、`sudo`与任何host/VM shell中继。fresh身份/version前后核对；任何变化全部拒绝。

安全transport与人类身份未绑定时，源代码可在合成HTTPS/身份fixture中验证拒绝行为，但不得发真实请求或收密码。future runtime合同必须固定实际policy origin/人类UID与可信来源；不能以nullable配置、caller注入或环境变量把未知目标变成生产入口。若需要配置新安全通道，另立受控前置合同，不在本票安装/改服务。

## 固定版本API证据及证明边界

已先Context7 `resolve-library-id`、再`query-docs`，选择`/go-gitea/gitea`；返回main内容，不能作为1.26.4版本证据。另核[官方v1.26.4路由](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/api.go)、[列表实现](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/user/app.go)、[响应字段](https://github.com/go-gitea/gitea/blob/v1.26.4/modules/structs/user_app.go)与[模型](https://github.com/go-gitea/gitea/blob/v1.26.4/models/auth/access_token.go)，复核#343 public module SHA，见[evidence](evidence/api-source-evidence.json)。

源码结论：tokens路由要求self或site-admin及Basic或显式启用的reverse-proxy API auth；列表按ContextUser UID查询并给X-Total-Count。响应包含ID/name/scopes/created_at/last_used_at和token_last_eight，不能直接保存原响应。`sha1`即使通常为空也必须丢弃。更新时间代表服务器报告的最后使用时间，不能证明调用者、消费者、canonical绑定或当前token仍被使用。

从源码推断独立人类admin可查询停用目标的metadata，不能写成现场成功。该版按创建时间排序，未承诺原子snapshot或稳定同时间排序；两次扫描不一致就STOP，不放宽为ID子集或猜测缺项。本票不使用更新main的`GET /token`。

## 严格输出allowlist与Secret处置

成功receipt schema提案`aisoft.hsdb.current-pat-inventory/v1`，仅包含固定结构：

- `schema/result/request_id/approved_read_card_sha256/observed_start/observed_end/window`。
- `scope={project: aisoft-platform,purpose: hsdb-current-pat-inventory,target_uid,target_login}`。
- `identity={operator_uid,operator_login,is_admin,target_uid,target_login}`；只投影这些验证后的值，不留email/name/avatar/raw用户对象。
- `version={expected: 1.26.4,observed_before,observed_after}`；完全相等才成功。
- `source={governance_issue:344,governance_merge_sha,source_issue,source_sha,installed_sha,tool_digest,public_install_receipt_digest,api_source_tag:v1.26.4}`；未产生字段不能伪造。
- `collection={items:[{id,name,scopes,created_at,last_used_at}],count,server_total,scans:[{pages,end_page,empty_end,count}],two_scans_equal:true,proof:OBSERVED_CONSISTENCY_NONATOMIC}`。
- `canonical_ownership=NOT ASSESSED`、`hsdb_access=NOT ASSESSED`。不得额外输出自动恢复建议、token后八位、原始query/body/header或错误文本。

在受限内存里解析原始响应后立即按allowlist投影；**在stdout/stderr、日志、缓存、文件、hash和错误处理之前**丢弃完整token、`sha1/token/token_last_eight/Authorization`、Cookie/OTP/password/secret及原始错误body。不得raw response缓存/抓包/调试dump；不产生pyc/core dump，不调Secret logger，不保存原body hash。禁用HTTP/debug traceback和自动请求重试。

字段须strict类型：正整数ID拒绝bool；name最多128 UTF-8 bytes、拒绝控制字符、超长及Secret形态；scopes只接受固定版本公开词表，array去序前检查重复/非法值，不过滤有效`all/public-only`来隐藏风险。字符串字段必须对输入密码/OTP及响应中禁字段值做内存泄漏检查；若Secret伪装在name/scopes/时间/嵌套字段则整个操作拒绝，不返回部分清单。未知字段丢弃但输出schema额外字段拒绝。允许重复name，禁止重复ID；不能按name推定canonical。

created_at/last_used_at保留服务器RFC3339语义；已定义never-used sentinel只能按固定版本规则映射null并说明，不能补今日时间；缺/坏时间拒绝。目标不同UID不共用清单或receipt。

失败仅固定码：`INPUT_CANCELLED/AUTHORIZATION_INVALID/AUTHORIZATION_EXPIRED/TRANSPORT_UNVERIFIED/IDENTITY_MISMATCH/VERSION_MISMATCH/AUTH_FAILED/HTTP_FAILED/SCHEMA_INVALID/TOTAL_MISMATCH/DUPLICATE_ID/COLLECTION_DRIFT/LIMIT_EXCEEDED/READ_TIMEOUT/SECRET_OUTPUT_BLOCKED/SOURCE_UNVERIFIED`。stdout无items/partial receipt；stderr只固定码与已验证的非Secretrequest ID，未知字段不填造。失败raw body读到有界内存即丢弃，不打印exception文本。程序取消/SIGINT/SIGTERM/EOF关闭连接、恢复tty echo、清除可释放认证buffer，禁止重用或自动再尝试；托管语言不能承诺所有内存副本物理清零，record限制。

## 分页、身份、范围、时间与资源硬门

一个操作完成两次独立全扫描，逐页从1开始limit=50直到**明确空终页**。短页或满页都继续；所有页X-Total-Count须非负整数，跨页跨scan相等；最终收集count等于total。IDs全局唯一、目标UID/login正反核对、身份/site-admin及version前后相同；两扫描完整metadata（含顺序、scopes、time）完全相等。丢失header、重复JSON key、NaN/Infinity、错类型/范围、ID重复、identity/total/metadata漂移、未知版本全部失败关闭。

| 固定边界 | 值 |
|---|---|
| 每scan页数（含空终页） | ≤20 |
| 实例总数 | ≤950 |
| 两scan收到的所有body bytes | ≤2MiB；单body≤256KiB |
| 成功序列化receipt | ≤256KiB |
| connect / 单HTTP总time | ≤5秒 / ≤10秒，服从整体余时 |
| 查询总期限 | ≤60秒；monotonic硬截止，不随clock回退延长 |
| 人类输入期限 | ≤60秒，且服从窗口余时 |
| exact read window | ≤600秒，固定not_before/expires_at，无自动续期 |
| redirect/retry/fallback | 全部0 |

name/scopes大小、item/page/bytes/总数上限同时满足才返回；20页仍未见空页保持GAP。CURRENT只证明时间窗内两次观测一致，不能证明跨页原子性或抵御服务器恶意伪造。查询本身不修改目标账号、PAT、ACL或canonical文件；服务器可能记录访问审计、认证相关元数据，不能宣称服务器/磁盘零写入。

## Mac-only、路径、影响与恢复

tool提案为新的独立用户工具，**不**修改existing 38-op broker/canonical manifests/credential helper/installer/provider/Controller/CI。固定用户`benque`，程序候选根`/Users/benque/.local/lib/aisoft-hsdb-current-pat-inventory/<source_sha>/`；固定launcher候选`/Users/benque/.local/bin/aisoft-hsdb-current-pat-inventory`；非Secretread-card/state根候选`/Users/benque/Library/Application Support/AISoftPlatform/current-pat-inventory/`。禁touch既有`credentials/`、canonical token、grant/marker、global skills、root路径及VM。候选路径是未来安装审阅面，当前未创建。

用户路径同owner不能单靠mode保证可信执行。future安装卡须绑定clean approved merged源码、独立公开provenance、exact全部文件digest、解释器及source/installed receipt，拒绝symlink/mixed-version/unverified launcher/unknown previous；不从credential store或root helper借信任。不安装依赖到系统/global site-packages，不需sudo；verified独立人类身份通道与TLS缺口不能靠installer解决。

- 输入/查询停止：中断/EOF/超时，close FD/restore echo/discard认证buffer；不改账号，不创造凭据“回滚”动作。
- source恢复：本票仅文档可revert；未来runtime delta的fixture forward/reverse/forward独立验证。merged源修改经另一个受控revert/manual PR，不能重写main。
- 安装恢复：未来窄用户installer只处理exact tool files/launcher/public receipt，安装前保留可验snapshot和previous pin；独立窗口真实restore/no-op验证。无previous若明确fresh install，恢复仅删除已证本候选新增文件；unknown previous STOP。restore不恢复/撤销任何PAT。
- 实际清单失败：保留GAP和固定码，窗口关闭，不改密码/UID5 flag/ACL，不重新启用、不自动issue/revoke/rotate/PAT发布；清单成功也不授予这些动作。

## AC与可审范围

| AC | 本Issue治理交付标准 | 本轮状态 |
|---|---|---|
| AC-1 | fresh查重/唯一tuple/claim/四角色/security-complex/manual/deps[337,339]可复核 | 待最终check |
| AC-2 | fixed UID3/5/单request/GET-only/human auth/安全transport/严格输出与Secret边界完整 | 合同已写；现场NOT RUN |
| AC-3 | 分页/总数/重复/漂移/identity/version/time/bytes/Secret负例矩阵可执行设计 | 合同已写；runtime tests NOT RUN |
| AC-4 | Mac-only/no-sudo/候选路径/输入/source/安装恢复独立；文档diff/scope真实检查 | 待最终check |
| AC-5 | G1独立批准/应用/STOP与fresh R/source/install/read门分开，无自举 | 本轮只T01；其余NOT RUN |
| AC-6 | #342发表处置和清单能力分开，不代改#343依赖，不以访问PASS作清单前置 | deps未改；后继NOT RUN |

本轮exact tracked allowlist：本目录四角色与`evidence/`五个JSON（installed-catalog/api-source-evidence/deduplication/inputs/manifest），无其它路径。外部审阅卡、receipt、diff/check输出只在本会话visualizations目录保存。

未来G1 exact六个治理路径（需新实际批准）为本目录四角色、`skill-for-codex/references/hsdb-current-pat-inventory.md`（新规范）和`codex/skills/gitea-platform-ops/SKILL.md`（增加仅本规范的目的限定读取指针）。不改AGENTS、global安装skills、runtime/catalog/manifests。G1 commit后STOP；其后fresh run再读，不用本run的规则变更实现runtime。

未来源码提案（当前未授权、未创建Issue）独立新目录`codex/tools/hsdb-current-pat-inventory/`八路径：README.md、policy.json、query.py、authorize.py、install.sh、hsdb-current-pat-inventory.sh、tests/test_query.py、tests/test_install.py。只是待该source spec审阅的建议；不能按本proposal直接改这八文件。安全origin、人类UID、解释器/发布信任及新source Issue须实际绑定，`null`不能进入运行policy。既有 broker/runtime、Controller、CI与其它owner仍无改动许可。

## 非目标与未运行层

runtime/CLI/tool/manifests/AGENTS/global skill实现；push/PR/merge；install/root/sudo/helper/grant；实际PAT/Secret页面或list API/DB；canonical内容/hash；签发/撤销/轮换/发布凭据；密码/flag/ACL/保护；服务/VM/部署/UAT/后台任务；代写#327/#333/#336/#342/#343或向其它聊天发消息，全部排除。

共享平台源实现和工具安装分别后继平台具体合同；HSDB read现场及hsdb-agent恢复归HSDB独立项目合同。共享manager-mutation恢复属于平台独立security合同；两者分别owner/窗口，不合票。旧ID/name/scopes/provenance=null/NOT VERIFIED，CURRENT不得推断canonical；未知旧PAT每ID保留/处置和共享audit消费者影响留给恢复合同。#344不能代解除#342 AC-4 FAIL、关闭#343、推进命名B治理或业务UAT。

## 2026-10-06 人类补充的仓库归属边界

人类直接补充：“当前项目具体部署的问题，不要在 aisoft 平台创建。具体项目的推进在本项目里处理。”本票据此仅保留真实**共享平台能力**：共享manager与固定受管agent的CURRENT清单工具、版本/身份/分页/Secret剔除协议及平台治理例外；工具源规范/代码和共享用户安装合同属于`admin/aisoft-platform`。首个受控用例为UID3/UID5，允许范围仍固定两者，不借“共享”扩大为任意账户读取。

HSDB是该能力消费方。HSDB一次性现场read请求、hsdb-agent凭据/flag恢复与adoption、项目本地部署、环境/配置、迁移/备份/恢复、应用健康检查、业务修复、UAT和公司试运行均由`admin/HSDB`的对应既有聊天及独立项目合同追踪；不在AISoftPlatform新建或承接，不以平台completed取代HSDB验收。共享manager-mutation影响所有平台消费者的恢复另用平台security合同，不能与HSDB agent恢复合票。

本轮保留#344/owner/claim及原授权，既有#342/#343仅exact证据输入，不自行迁移/关闭/接管。未来若仅剩HSDB一次性现场处置而没有共享工具/协议/治理delta，停止该混入范围并交根拆分，不用平台票容纳项目推进。后继项目票号/owner/窗口均null；本轮不创建项目票，不使用未验收跨仓broker能力来投影项目状态。

## Acceptance criteria

- [ ] AC-1：fresh查重/唯一Issue/claim/tuple/四角色/security-complex/manual/deps[337,339]真实验证。
- [ ] AC-2：固定UID3/5、single request、GET/human auth、安全transport和Secret-free输出治理合同完整。
- [ ] AC-3：Q-01…Q-12明确分页/总数/重复/漂移/身份/版本/timeout/Secret剔除与失败关闭验收设计。
- [ ] AC-4：Mac-only/no-sudo候选路径、输入/source/install恢复独立，文档diff/scope真实PASS。
- [ ] AC-5：G1独立批准/受控apply/STOP→fresh successor读取与source/install/read分别授权，禁止自举。
- [ ] AC-6：#342发表处置与共享能力前置不同；不改#343依赖，不以HSDB访问PASS作清单前置；项目消费方归admin/HSDB。

## 未决问题

无本票治理文档方向待决。G1实际人类批准尚未取得；future安全origin、人类UID、工具pin、后继票号及现场窗口均null/GAP，必须在各自后继具体合同绑定，不能作为本票runtime授权或替本票设置approved。本轮T01 STOP不提前验收G1应用。
