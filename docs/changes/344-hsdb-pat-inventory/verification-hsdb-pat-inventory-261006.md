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

# #344 · T01历史证据与G1候选Verification

下列T01表格和原结构核验是原owner准备时的历史证据，保留原字节含义；不表示接续会话重新运行远程读取、分类投影或现场验证。G1接续结果分列在文末。

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

## 正式接续与G1证据分层

- 原owner `01a10ebe-7d29-73d0-9151-51fd09f71b49` HANDOFF_STOP；current owner `01a10ecc-1a09-78b0-8e41-2b15de72df43` 已通过正式claim-worktree --takeover接管，claim读回一致；原聊天已actual archive。
- 仓外`issue-344-reception/HANDOFF_ACCEPTED-344.json`实证：交接包hash、9文件范围/HEAD字节、patch/bundle/card hashes、old/new claim核验PASS；original HEAD=`09084e19a8b1a3bb018f70d80e1a3b1cc3611a88`、tree=`fd3b732c5f490c49aec6aa8e472ab17a9d59ffae`、clean保持。该接收不是G1批准。
- G1六路径拟议文本、patch与文件manifest在本会话仓外审阅包保存；四角色、reference和skill候选必须独立核验，实际运行结果只记仓外checks.json，不能用拟议文本预填应用PASS。
- G1人类具体确认、repo apply、local commit/revert、Issue正文/状态/labels、runtime、push/PR/CI/merge、安装/真实read/凭据或账号/服务/部署仍NOT RUN。Q-01…Q-12只是后继设计，未执行；PAUSED监控继续保持。
- G1执行后才追加真实命令与结果回执；本候选不提前宣称T02 done或Issue completed。旧五个公开JSON作为T01历史快照保留，不因G1文档修改更新为批准、installed或现场结果。

## G1实际完成与T03 fresh读回（2026-10-06）

上文T01/G1候选中的未批准/NOT RUN只描述当时阶段，以下为接续实际结果；五个evidence JSON保持历史字节。

- 人类exact G1批准绑定六路径patch SHA256=`aceaf2622156ea30060c482f7020f187bb40b519c21f9bdb0b4586e76e8ff24b`。执行回执`G1-EXECUTED-STOP-344.json/.md`：apply、resolver/required-docs/document gate、6AC/Q矩阵/deps/claim/范围验证PASS；一个原子commit=`dc66b448e231edc7f8a3438fbba20152547ea101`，parent=`09084e19a8b1a3bb018f70d80e1a3b1cc3611a88`，tree=`a876ae91d91dc77d07e3603e4d37b983ecb5f080`，六文件149 insertions/9 deletions，clean后STOP。
- T03固定installed broker `git.fetch.main`实际PASS，current manifest main=`11628709e659dac48f5cb66bade81f1617974546`。`gitea.issue.read` #344/#337/#339、#344 comments、main protection read实际PASS；#344 open且type/security、complexity/complex；deps两项closed/completed。live #344 lifecycle仍spec-drafting，与新local approved投影区分。
- `gitea.pulls.read --state all`两次实际exit0；每次schema=`aisoft.broker.pull-collection/v1`、scan_count=2、count=server_total=165、limit=50、terminal_empty_pages=[5,5]，stdout SHA256=`0e2795d377ac021ff9493011430304071c0179017eee00ab0e305267cb22c3c0`。165个number唯一，两次完整字节一致，按#344 head namespace/独立Closes行/semantic docs路径查找无同票PR。完整清单只含仓库PR公共metadata，不是PAT清单。
- `git.fetch.change --branch change/344-hsdb-pat-inventory`两次实际exit0/PASS，remote_known=true/head=null。已安装generic `_remote_change_heads`固定枚举`refs/heads/change/344`与`refs/heads/change/344-*`，`_change_tip`拒绝其它slug/重复ref，满足本票普通namespace检查；不声称#336专用#333 namespace receipt适用于#344。
- actual `qualified_broker_environment()` PASS：固定wrapper SHA和7项source/installed dispatch/FF字节、loaded module与本owner session验证。#327 Mac全安装/restore/reinstall/idempotence回执先前已独立核验；本轮资格核验只证明现有普通路径，不执行安装/root/sudo。main protection=`CI / verify (pull_request)`且block_on_outdated_branch=true、main push disabled、人类admin唯一merge。
- 原dc66 HEAD调用`GitRepository.scope`真实拒绝`mapped summary lifecycle differs`。T03仅补既有批准状态和原11路径exact scope，无扩大产品/安全授权；下游qualified整合及验证结果在仓外最终回执记录，未执行前不预填PASS。

实际读取命令和stdout/stderr保存于本会话`t03-344/read_current.py`、`read-current-report.json`和逐操作文件；`preflight.json`保存完整集合哈希/计数、资格与namespace结果。源工具Q-01…Q-12、runtime、push/PR/CI/merge、安装、真实PAT读取与所有安全写入继续NOT RUN，PAUSED监控未恢复。

T03本地事实投影后实际执行：`git diff --check`、`python3 -m aisoft_loop.cli resolve-documents 344 --repo <owned-WT>`、`resolve-required-documents`、`check-change-documents`全部exit0，158 changes/pass2/gap0；`bash .../apply-classification-labels.sh --repo <owned-WT> --verify 344`实际read-back=`projected`，type/security与complexity/complex。`load_contract(repo, live_issue, allowed_lifecycle=('spec-drafting',))`只读解析6AC/四角色成功；默认approved Loop门仍因live spec-drafting拒绝，未伪造live启动。原6AC、12个Q设计行、deps、reference/skill和五个JSON字节核验PASS。仓外校验脚本初次参数顺序错误已修正，未修改合同行为。
