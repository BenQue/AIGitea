# HSDB CURRENT PAT inventory · 目的限定共享治理规范

治理来源：`admin/aisoft-platform#344`，security/complex/add/manual，routine disabled。该source规范承接本票已审spec，G1须经具体人类确认独立应用、验证、本地commit并STOP；后续fresh run重读实际规则。本文没有工具入口或现场授权，不改变existing 38-op broker、canonical manifests、credential helper、Controller/provider或CI。

## 归属与分阶段授权

共享CURRENT工具/协议/治理留在`admin/aisoft-platform`，范围固定UID3/aisoft-platform-manager与UID5/hsdb-agent，不扩大任意账号。HSDB消费方一次性read、hsdb-agent恢复/flag/adoption、配置/业务/迁移/备份恢复/健康检查/部署/UAT/公司试运行归`admin/HSDB`；共享manager-mutation恢复另按平台security合同。

治理source声明、工具源/local/CI/merge、用户安装及现场CURRENT清单分别凭实际证据验收。G1只交付治理文本；source工具、安装和read须在各自具体阶段按既有合同门绑定目标/identity/TLS/pin/窗口。G1不创建或派发这些票，不新增helper/authority/grant，旧#342账号窗口不可复用，平台监控仍PAUSED。

`depends_on=[337,339]`。#342失败结果与#343卡只是exact证据输入，不代改其AC/依赖/标签，不以其closed或HSDB访问PASS作为CURRENT合同准备前置。旧PAT provenance/canonical映射继续null/NOT VERIFIED；清单一致性不证明ownership或ACCESS_PASS。

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

已先Context7 `resolve-library-id`、再`query-docs`，选择`/go-gitea/gitea`；返回main内容，不能作为1.26.4版本证据。另核[官方v1.26.4路由](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/api.go)、[列表实现](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/user/app.go)、[响应字段](https://github.com/go-gitea/gitea/blob/v1.26.4/modules/structs/user_app.go)与[模型](https://github.com/go-gitea/gitea/blob/v1.26.4/models/auth/access_token.go)，复核#343 public module SHA，见[固定公开源证据](../../docs/changes/344-hsdb-pat-inventory/evidence/api-source-evidence.json)。

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


## 适用前提与停止

当前现场operator UID/login、安全origin、工具source/installed pin及read window均未绑定（null/GAP）；实际身份输入、网络查询、PAT/Secret页面和DB均NOT RUN。缺安全transport或可信human identity时必须在输入/请求前拒绝，不能从服务账号PAT、旧grant或已登录浏览器猜测授权，也不能自动调整服务解决缺口。

规范全文及负例设计见[#344 spec](../../docs/changes/344-hsdb-pat-inventory/spec-hsdb-pat-inventory-261006.md)和[Q-01…Q-12计划](../../docs/changes/344-hsdb-pat-inventory/plan-hsdb-pat-inventory-261006.md)。它们当前是文档设计，runtime tests/真实清单均NOT RUN。若scope、identity、source pin或任何证据不一致，STOP并保留固定非Secret失败码，不自动重试、写安全状态或恢复原监控。
