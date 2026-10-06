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

# #344 · T01治理准备Verification

## 基线、归属与证据层

- fresh `origin/main/base=96ba8a17baad8e9854d4e8d0397d4162b8067b09`；shared primary `main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`，未写shared primary文件。
- owner/session `01a10ebe-7d29-73d0-9151-51fd09f71b49`；exact branch/WT见summary。claim实际created，last_push_head=null。
- 输入#343卡hash实际匹配；#342/#343 heads与独立owner工作树只读确认，无编辑；输入见[inputs](evidence/inputs.json)。
- 本轮fixed-v1.26.4公开源核对，不运行API inventory。source模块hash只涵盖公开源文件，未读canonical Secret或其hash。

## 实际观测与验证

| Command / check | Result | Evidence |
|---|---|---|
| installed broker git.fetch.main：sandbox首次TRANSPORT_ERROR；同typed host retry | PASS host；sandbox BLOCKED_EXTERNAL | external preflight；origin/main精确96ba |
| installed broker gitea.issue.list open | PASS，6个open，无同能力票 | deduplication及external readback |
| 327/333/336/340/342/343 issue.read + comments.read | PASS，各0评论，范围不同 | external issue/comments receipts；deduplication |
| 337/339 fresh issue.read | PASS closed/completed | deduplication；不把source/install层当access |
| public installed catalog/receipt read | PASS observation：38ops/helper=null/pin=c9b5 | installed-catalog；完整byte重新验收NOT RUN |
| Context7 resolve/query→official tag/public module hash | PASS source research | api-source-evidence；Context7 main不是1.26.4证明 |
| #344 broker issue.create entry triage/needs-triage | PASS，actual344 | external issue-create.json |
| git worktree add + claim-worktree | PASS host retry | exact WT/owner；初次sandbox lock denial未写合同 |
| 四角色resolver/required-docs/check-change-documents | PASS（实际命令完成） | resolver四角色；required_docs四角色；changes=158/pass=2/gap=0 |
| Classification parser/route与真实投影/verify | PASS parser/route/draft/readback | security/complex，verify result=projected；lifecycle=spec-drafting，未approved |
| git diff --check/exact scope/claim/clean candidate | PENDING（提交前后记录） | external local-check/handoff |

提交前后最终检查保存在本轮external receipt，未执行层保持NOT RUN；文档本地commit head/tree存仓外handoff避免自指SHA。

## AC结果（仅治理文档交付）

| AC | 本轮结论 | 限制 |
|---|---|---|
| AC-1 | PASS preparation，final gate外存 | 唯一Issue/tuple/claim已实证，parser route、6AC/4roles、dep与claim/scope均PASS |
| AC-2 | PASS document design | 固定GET/human/输出/Secret规范已写；实际auth/list NOT RUN |
| AC-3 | PASS document design | Q-01…Q-12有界矩阵已写；runtime执行NOT RUN |
| AC-4 | PASS design，scope final gate外存 | Mac-only/no-sudo/三恢复已写，scope/diff最终9文件scope/claim/manifest已PASS；staged diff及提交后检查外存 |
| AC-5 | PASS preparation boundary | T01完成STOP，不代表G1 approved/applied或runtime |
| AC-6 | PASS dependency review | deps[337,339]与342/343 evidence独立，无改他人依赖/AC |

## 未运行与GAP

G1 approval/apply、runtime/source tool/CLI/manifests/AGENTS/global skills、push/PR/requiredCI/merge、安装/root/sudo/helper/grant、真实Basic输入/PAT/Secret页面/list API/DB、canonical内容/hash、签发/撤销/轮换/发布PAT、password/UID5 flag/ACL/保护、服务/VM/部署/UAT/后台监控均NOT RUN/0。本票仍open/contract-drafting，未approved、未启动Loop、未完成/归档。

operator_UID/login、安全transport、future source/install/read Issue、新source/installed pin、read-window均null/GAP。CURRENT未取得，旧PAT来源与canonical ownership NOT VERIFIED，HSDB三项HTTP_401 ACCESS_GAP未解除。

#342/#343文档发表仍各自合同/owner负责；#327/#336后续能力缺口不借用，PAUSED monitor未恢复。最终源PR CI只是后续治理源证据，不是installed或CURRENT/live/UAT PASS。

## 2026-10-06 人类补充的仓库归属边界

人类直接补充：“当前项目具体部署的问题，不要在 aisoft 平台创建。具体项目的推进在本项目里处理。”本票据此仅保留真实**共享平台能力**：共享manager与固定受管agent的CURRENT清单工具、版本/身份/分页/Secret剔除协议及平台治理例外；工具源规范/代码和共享用户安装合同属于`admin/aisoft-platform`。首个受控用例为UID3/UID5，允许范围仍固定两者，不借“共享”扩大为任意账户读取。

HSDB是该能力消费方。HSDB一次性现场read请求、hsdb-agent凭据/flag恢复与adoption、项目本地部署、环境/配置、迁移/备份/恢复、应用健康检查、业务修复、UAT和公司试运行均由`admin/HSDB`的对应既有聊天及独立项目合同追踪；不在AISoftPlatform新建或承接，不以平台completed取代HSDB验收。共享manager-mutation影响所有平台消费者的恢复另用平台security合同，不能与HSDB agent恢复合票。

本轮保留#344/owner/claim及原授权，既有#342/#343仅exact证据输入，不自行迁移/关闭/接管。未来若仅剩HSDB一次性现场处置而没有共享工具/协议/治理delta，停止该混入范围并交根拆分，不用平台票容纳项目推进。后继项目票号/owner/窗口均null；本轮不创建项目票，不使用未验收跨仓broker能力来投影项目状态。

## 2026-10-06 最终本地结构核验

`local-contract-check.json`实际PASS：classification parser/route=security/complex/add、manual/routine=false；read-only `load_contract(allowed_lifecycle=spec-drafting)`获得6AC、4roles、deps[337,339]；默认`approved`启动门真实拒绝（当前spec-drafting）；Ticket graph T01 done、T02/T03 blocked；claim本owner且last_push_head=null；精确9文件与公开evidence manifest哈希一致。该只读draft校验不是批准或Loop执行。

本轮既有shell/runtime零修改，所以不重跑smoke、bash -n、ShellCheck或runtime test suites；这些为NOT RUN，未来源实现修改shell时必须按AGENTS真实运行。staged diff --check、最终document gate、clean/head/tree与primary/其它owner未变读回在仓外final-checks/handoff存实际结果，不把未提交验证预填为PASS。
