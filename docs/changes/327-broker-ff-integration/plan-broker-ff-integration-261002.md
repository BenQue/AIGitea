---
issue: 327
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/327
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
depends_on: []
branch: change/327-broker-ff-integration
created: 2026-10-02
updated: 2026-10-03
status: approved
---

# #327 实施计划与 fresh frontier

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立只修改spec映射治理合同的受控本地步骤；验证范围、原子commit后停止 | - | completed |
| T04 | 具体补充合同经直接确认；当时独立应用原14治理文本+四角色、验证/本地commit后STOP；runtime未实施 | T01 | completed |
| T05 | 已直接批准具体安全合同；仅原14治理文本+四角色，bootstrap/closure/resource/v2文本应用、验证/localcommit/STOP | T04 | completed |
| T06 | exact卡确认后仅同步7个main治理段落与mapped summary/spec/plan；验证/本地commit后STOP | T05 | completed |
| T07 | 具体确认后仅补充 mapped summary/spec/plan 的固定 Python3.9 兼容 scope；文档校验/本地原子commit/STOP | T06 | completed |
| T08 | 具体确认Mac observer安全与签名选择后仅三合同/校验/localcommit/STOP；不执行新source或host能力 | T07 | completed |
| T02 | T08后fresh重读；T07四行实际提交已完成；续原全closure/同FD、observer/resources、authority/FF、惰性安装漂移与旧回归迁移 | T08 | in-progress |
| T03 | 集成/全量/静态/文档验收、source与installed分层、人工firstPR/安装rollback卡，准备唯一manualPR候选 | T02 | pending |

本聊天负责人直接“批准”审阅卡绑定的具体安全合同；本轮仅独立T05治理应用、验证/localcommit后STOP。T01/T04历史完成保留，T05 completed仅指治理文本步骤，不指新增source/主机验收。T02 in-progress是已保全WIP；后续fresh重读新governing/批准/Issue/installed才继续，当前run不得进入runtime。

T01 原治理已于 `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 独立提交并停止。fresh T02 分析发现可信根缺口；没有 runtime/新接口变更。负责人“按建议继续”仅选择 A 路线准备，四角色草案 ac172e515a47357d24ff268473af6bbee5c13fe1 不算 T04；随后本聊天直接确认原可信根具体合同，独立治理应用完成 T04；这段不包含后来T05安全补充。

新增 T04 保留原 ticket ID/历史，置于 T02 之前。历史T04已获审阅卡 exact draft/spec/plan SHA256 的具体确认，当时在独立治理 run 执行 T04，只改原14治理文件+四角色，应用/验证/local commit 后 STOP。批准与提交后 SHA 分别保存在外部 receipt，避免本提交自引用。后续 fresh run 重读，live 分类/approved 投影、installed/capability 和 grant 状态均真实核对，T02 才能实施其新 source 范围。任何 runtime/config/service 不得混入 T04。

T02/T03 本地实施许可不授权 push/PR。人工 UI 发表 B01、合并后 I01 文件安装及 I02 authority 注册/启动验收均是 graph 外的独立受控阶段，不等待未合并代码先安装才能准备源码 PR。最终 PR 确认只问一次；其 protected 登记不作新的业务决定，CI repair 每次 exact H 重验而不逐 commit 问。
## Expected touch points

exact 清单由 spec 原治理/runtime 表与新可信根扩展表逐项定义。原T04可信根source表已确认；当前T05安全增补9项已直接确认，但只能后续fresh T02实施，本轮均不实施。T01/T04 已完成；T05已批准，仅原14治理表+四角色；fresh T02仅获确认的runtime/可信根及本次安全增补表；T03只更新四份证据和外部脱敏 B01/I01/I02 卡。新文件新增模式限100644；固定运行hook若由runtime临时生成必须隔离保护、不得变为额外可配置入口。

所有stage保持owner `01a0fcec-eb78-7790-a36a-daea917f43d2`；branch `change/327-broker-ff-integration`；worktree `/private/tmp/issue-327-broker-ff-integration`。commit包含 #327 与Txx；不接受他人代做整合/rebase。

## 数据库迁移

无数据库迁移。原protected grant/record source为v1；本T05已批准 `change-grant/v2` / `change-record/v2` / `change-operator/v2`并绑定closure/resource/lease。v1仅历史只读；无自动迁移、旧状态清空或R0升级。public默认policy仍v1四key；新registry默认disabled、hosts=null。owner/progress 只作兼容审计/引用，不升级成批准记录；缺可信证据必须 fail closed/adoption review。状态丢失、旧 root 或异常 remote 不重置 R0。

## 测试与验收映射

| AC | Ticket / 外部阶段 | Verification command or review |
|---|---|---|
| AC-1 | T01/T04/T05；T03 | `resolve-documents 327`、`check-change-documents`、判级只读plan/verify；T01 exactdiff+commit清单与STOP receipt；fresh-run重读hash |
| AC-2 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_main_integration.py -v`；真实临时bare remote正向DAG/tree/ref证据 |
| AC-3 | T02 | 同integration fixture：预读/传输公告两窗口注入race，包括R1祖先候选、首次ref存在抢占、删重建；拒绝前后ref/argv |
| AC-4 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_host_access.py -v`；`test_controller.py`、`test_worktree_owner.py`定向；pre-mutation remote保持与provider gate |
| AC-5 | T02/T03 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v`；`bash codex/tests/smoke.sh`；真实remote读回、receipt failure和freshness后漂移 |
| AC-6 | T03准备/B01执行 | bundle/patch/tree/blob/mode card；本人UI发表；broker fetch H/main/PR/status/actions；导出H在隔离目录重跑本地门；唯一humanPR/merge读回 |
| AC-7 | T03准备/I01文件/I02执行 | 两机exact批准：I01 installer/before-after owner-mode-hash/installer no-op/文件失败rollback；I02注册后realFF/publish no-op/reject/authority-resource rollback及前后ref/main保护 |
| AC-8 | T03/B01/I01 | `gitea.protection.read`、manifest byte diff、单writer scan、同Issue唯一PR读回；原owner采用receipt或保持NOT RUN |
| AC-9 | T04；T02/T03；I02 | 对 `test_change_evidence.py` / `test_verification_authority.py` / `test_verifier.py` / `test_state.py` / `test_contract.py` 分别执行 unittest discover；新文件存在后才运行；真实 peer、privilege/FS/exec/socket negative、grant/record/adoption/replay/restart/default-disabled + 两机 I02 受控实证 |
| AC-10 | T05；fresh T02/T03；I02 | 新文件实际存在后定向 `test_toolchain.py` / `test_change_evidence.py` / `test_verification_authority.py` discover及 `bash codex/tests/test-verification-bootstrap.sh`；完整pin/v2/late-import/alias/cache/OSdelegate；非root build、真实pre-Python拒绝与每主机I02，mock不报rootPASS |
| AC-11 | T05；fresh T02/T03；I02 | `test_scratch.py`定向discover与bare-remote组合；租约/预算/固定argv负向，未来I02实际ENOSPC/tinyfiles/own-device/busy/descendant/power-recovery/flags/noexec/保留/rollback |

每个定向unittest分别使用上行discover格式，只更换 -p 的exact文件名；新integration测试文件必须真实存在后才能执行。每次变动shell须运行对应 `bash -n`、可用ShellCheck及完整smoke。fixture只能本地临时remote；不创建live canary Issue/PR来伪装隔离测试。

完整smoke按默认host locale实际执行。若#319尚未入main而registry UTF-8 fixture FAIL，保存原失败、不修别人的6处Bash；LC_ALL=C可作诊断单独标注，不能替代默认结果PASS。future fresh main若已有修复，不继承旧FAIL或PASS，重读实跑。

## 可信根 source 分步验收

T02在T05完成/STOP/fresh重读后，同一ticket依赖推进：native bootstrap/完整closure与v2、default-disabled registry → bounded scratch/root对象暂存/lease与capability gate → strict schema/冻结政策与 scope → default-disabled fixed client/server/OS peer → protected operator grant 与受控 generation/非 root sandbox execution → per-commit/完整 delta 与限定 integration checkpoint → 独立 broker重算+protected PR授权+strict R ordinary FF → installer/drift/inert unit 和全量回归。任何阶段缺可信输入均 fail closed，不能先发布“暂用本地 PASS”的版本；不改既有 required gate 或让 fixture 开关进入 public runtime。

必须区分 unit/mock、真实普通用户 Unix socket/bare remote、真实 root custody 与 installed/live。无权限环境的 root/另UID/服务测试真实 NOT RUN/GAP，不能 monkeypatch UID 后写 PASS。两机 I02 之前 source merge 不表示功能启用，不自动创建授权记录。

I02 卡须完整列出实际 root runtime/interpreter/Git hash、registered existing UID/GID、隔离能力、socket/context/state/service 前态、grant/业务批准与 protected PR确认登记、停止/恢复对象、真实 FF/negative/restart/rollback 目标。source-only smoke 不代替这些项；不自动 provision credential/账户/SDK auth/profile/provider/timer。

## 风险与失败分支

- 非FF或未知remote/provenance：fail closed，不 rebase已发表历史、不force；不删除重建branch。
- 合并冲突/范围变化/不支持Git：NEEDS_HUMAN_DECISION，保全原候选；超出最小无冲突合同须明确裁决。
- 外部UI不能保留tree/mode：B01阻塞；不先装unmerged版本，不directGit/API，重新交负责人具体路径决定。
- 相同外部根因连续三次：BLOCKED_EXTERNAL；不空提交重试CI、不移除CI/action硬门。
- postpush readback不明：可能已落地，先只读取证再决策，不force恢复。
- main在publish后推进：保留已发表H，再整合/重验；不按旧CI通知merge。

## 发布、安装与回滚

B01先取得绑定#327/branch/manual的最终PR提交确认，使用spec人工UI卡；owner不代提交。H不同于L，exact新H验收、summary唯一URL回填与requiredCI均重新取证；manual合并只由人。

I01只在源码merge且fresh stable pin后，分别取得Mac/gitea-ci exact安装批准。只改安装卡列出的受管byte/mode/owner；不继承#316授权、不启用profile/service/provider、不涉及credential或应用部署。I01必须完整旧态保全、installer两次执行/no-op与故意文件安装失败rollback。新行为realFF/publish no-op/reject及authority/resource操作rollback移到I02注册/启动后受控验收；AC-7整体要求不减，避免I01必须先运行未注册服务的依赖环。

AC-7/AC-9/AC-10/AC-11 未闭合保持本 Issue 实际未完成与 chat 可用；见spec自动closed后的typedopen保留验收规则。AC全闭合后确定性terminal/document/cleanup/archive，无新增确认点。

## T05 exact治理与保全检查

本次直接批准绑定前次审阅卡spec/plan SHA256、draftcommit（如有）、#327/exact branch/manual；不是安装授权。T05限定原14治理表中的#327活段落，新增内容只为spec安全补充与source-installed/I02/STOP；不得混入已存在T02 WIP或新native/config。应用前保全source18项及所有非文档tracked/untrackedbytes/mode；应用后检查exact18文件（14治理+4角色）diff、双工具一致、resolver/semantic/AC11/graph、独立localcommit路径与STOP receipt。随后fresh run重新读完整governing/批准/Issue/comments/source/installed事实，才继续T02。

I02 card进一步冻结两模板创建和ownlease mount/detach、每hostOSbuild/closure/cache/alias/bootstrapartifact/role、真实quota/tinyfile/descendant/crash读回与rollback。I01不创建模板、不register/enable/start，不自动provision账户/toolchain/凭据。任何缺能力保留GAP。T03记录旧全量和smoke失败并完成修复后重跑；不为治理文本应用虚构新runtime测试或改main绕staleness。


## T06 执行与停止点

exact范围、main/source/owner pin、7治理路径、32WIP保全与回退见 mapped spec 的 T06补充及 external审阅卡。
本补充待负责人确认，旧 approved 与恢复卡 A 不授权它；T01/T04/T05历史、原AC和source范围保持。
T06只应用7个main治理段落与mapped summary/spec/plan；不得混入32WIP中的verification、runtime/config/service。
校验proposal bytes/hash、文档映射/graph、governing最小diff与source保全后，提交前仅投影plan的T06状态和summary的T06 frontier两行，纳入同一独立治理原子commit；commit成功立即STOP。commit失败恢复pending投影、保全WIP并升级，不认定T06完成。
下一fresh run重读合同/具体批准/Issue/comments/source/installed，T02/R01先纯main integration checkpoint，
再恢复未提交WIP并单独解决broker调度冲突；手工内容不混进checkpoint。保持两parent顺序、限定merge tree与历史，
新增冲突或scope漂移停止。原T02验证门和B01/I01/I02边界保持，完成实质修复后重跑完整runtime及默认smoke。


## T07 补充 frontier 与执行停点

本补充仅为待具体确认的 exact proposal；旧 approved 不授权新 runtime 文件。新增范围与两个文件的四行等价候选
仅见 mapped spec 的 T07 表及 external SHA256 卡，不覆盖 #286 其它变更。T06已完成/STOP，
R01实际纯 main checkpoint `4cb627d9525611bff34387830978ba5c5785863e` 保留；T02仍in-progress。

确认后 T07只应用 mapped summary/spec/plan 三份治理合同，保全33 source WIP；校验语义映射、
精确 diff、原14治理/source/owner/index 保全后，仅把 T07 graph row 和 summary T07 frontier line
投影完成，纳入同一本地原子commit，并立即STOP。失败保存证据并撤回本次文档增量，不能报T07完成。
随后fresh T02重读批准与上述事实，才在本spec限定的四行范围修改 dependencies.py 与 profiles.py；
固定Python3.9与native/相关unit/默认smoke按spec实跑，原其余source、全量回归和T03验收保持。
所有PR/安装/服务/远端写边界保持，外部候选PASS不覆盖actualcheckout当前FAIL。

## T08 候选受控治理步骤

仅在负责人具体确认卡的#327/exact branch/manual、before/candidate/完成投影SHA256后，
独立应用mapped summary/spec/plan三合同。保全卡列出的33 source WIP/owner/index与原14治理hash/mode，
checks为resolve-documents/check-change-documents/graph与exact diff；实际成功才把T08 row和summary frontier
投影为治理完成，独立localcommit后立即STOP。verification与runtime不混提交，不创建root对象或kernel client。
失败撤回exact三文档/本次index项并保存证据；不reset历史、不恢复旧lease或降低硬门。

后续fresh T02重读批准与新spec，仅在原exact source映射中实现macOS27+的kernel descendants observer，
private Mac profile v2、签名artifact/closure绑定和拒绝条件。无真实签名/OS能力时不激活，不调用更宽API。
先完成原native全闭包/同FD调度，再推进observer/资源/authority/完整内容/FF/惰性installer-drift与旧回归迁移；
不把source模型/unsigned build/fixture PASS当root或signed/installed能力。每shell改动保持完整默认smoke/static门。
未来I01/I02的签名来源/kernel/安装/权限必须独立exact卡；T08只批准治理和fresh source，不授权host改变。
