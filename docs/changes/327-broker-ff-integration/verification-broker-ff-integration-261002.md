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
updated: 2026-10-06
status: pending
---

# #327 分层证据与 T05 独立治理验收

## 2026-10-06 T03 最新：生命周期修复通过；新 main 整合待本人执行

以下仅更新本轮已实际观察到的层次；下文历史 FAIL/GAP/NOT RUN 与保全对象均保留。

| Check | Result | Evidence / limit |
|---|---|---|
| 实际首次普通FF / PR #346初始head | PASS | 本人恢复回执与实际guard已核，remote/owner.last_push=`f97d0d88a99373711a22c44b72d46976cd290638`；R0仍known absent，未重pin |
| 初始required CI | PASS（初始head） | typed `gitea.commit.status.read`：exact `CI / verify (pull_request)` success，run1801/job2007；不覆盖后继head/new base |
| fresh PR/main/protection | PASS（读取） | 唯一PR346 open/notmerged，head仍f97；main/base=`000a3f73cd7069f4aef0a202b1a19555014fd887`；main禁止push/force、manual/admin与required context/outdated gate保持 |
| 实际回填提交scope预检 | FAIL（旧模块） | local `019cabf9bac4e456fefcf397ed503f086250882a`仅四mapped docs；既有回填器 summary→pr-open，旧最小Git只接approved，未执行该后继发表 |
| 原批准模块/测试内生命周期修复 | PASS（source/local） | summary approved或pr-open；开放PR要求唯一exact Issue/同仓正数PR URL；spec仍唯一approved；先数所有原始键含空值，再验证值，拒绝合法+错误/空/畸形重复项 |
| 实际回填器→scope/history→guarded bare FF；16负向cases | PASS（fixture） | `/usr/bin/python3` Git核心20 tests OK；最初fixture缺映射/created/required_docs的失败日志保留，修正真实fixture后通过 |
| 全runtime | PASS（Homebrew source/local） | 1148 tests OK，167.330s；run wrapper before/after两个改动源码SHA相同，stable=true；测试日志与hash在原owner外部E |
| 系统Python3.9全仓误用回归 | FAIL（保留） | 1011 tests，6 errors/1 failure：全仓既有其他模块的联合类型/tar filter/bytecode fixture兼容性；不把Git核心3.9 PASS提升成全仓3.9 PASS，也不扩大本票修复 |
| 默认 `bash codex/tests/smoke.sh` | FAIL（BASE_STALE） | sourceguard发现behind origin/main 10 commits，5.6s停止，runtime NOT REACHED；源码before/after稳定；不隐藏/跳过门，不把独立runtime PASS记成smoke PASS |
| 修复两轴审阅 | PASS（增量） | Spec hard=0/scope creep=0，Standards hard=0/new smell=0；原重复字段P2报告保留并闭合 |
| 新main只读三方tree预演 | PASS（preview only） | 临时ODB计算，无worktree/index/ref写；实际后继固定H/tree绑定在外部入口；不当作实际整合 |
| 人工本地main入口 | PASS（6真实Gitfixture） | 成功、main漂移、dirty、owner漂移、冲突、commit落地后lostreply：actualH/parents/tree有限读回、CREATED_OBSERVED_AFTER_ERROR且仍STOP；无重试/回退；原模板P2及fixture故障保留 |
| 实际新main本地整合 / 同一PR后继发表 / final head-base CI | NOT RUN | 先本人按冻结H/M/tree保存checkpoint bundle并本地two-parent commit/STOP；fresh owner重跑全部默认门后才准备同PR普通FF；旧发表入口已停用 |
| manual merge / 新broker安装 / live / 部署 | NOT RUN | source/local/initial CI不赋予安装或部署授权，T03仍in-progress |

外部证据目录：`/Users/benque/.codex/visualizations/2026/10/02/01a0fcec-eb78-7790-a36a-daea917f43d2/issue-327-convergence-20261005/t02-minimal-git-fresh-20261006-5r33dgqe/`。本次局部修复不修改AGENTS/治理合同/权限/Secret；既有stash `4888c0345a90ab76560f33172dd9923f79c3a988`与其bundle、parked源码及原owner台账均保留。最终commit SHA在外部回执记录，避免文档自引用。

## 基线与范围

- 时间：2026-10-02（Asia/Shanghai）；详细时间戳见 `/private/tmp/aisoft-327-contract-evidence/baseline.json`。
- Commit SHA / fresh `origin/main`：`65268ee5f1e622c486fd9e354dd35e20a2900f91`。
- 共享main checkout当时HEAD=`5c2cd726c9aeaee9d17541d8feb049e33881bbac`，本owner未移动；从fresh tracking ref建独立worktree。
- worktree：`/private/tmp/issue-327-broker-ff-integration`；claim owner=`01a0fcec-eb78-7790-a36a-daea917f43d2`；last_push_head=null。
- Issue open，准备阶段及 T01 前 fresh 读取均仅 triage/needs-triage，comments 空；负责人在本聊天直接确认合同并仅启动独立 T01，本轮没有 runtime 执行授权。
- 合同准备证明 fresh 只读事实和隔离归属；T01 commit `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 已完成映射治理应用与文档验证，不证明新 FF runtime/PR/安装/live。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| installed broker `gitea.issue.read` / `gitea.issue.comments.read` #327 | PASS | evidence/issue.json、comments.json；sandbox最初TRANSPORT_ERROR，经同一typed host execution重试通过 |
| `git worktree list` / exact local branch/docs检查 | PASS | 建立前没有#327 worktree/local branch/docs；其他owner未操作 |
| `claim-worktree` exact tuple | PASS | claim receipt，owner与branch一致，未接管他人 |
| installed typed `git.fetch.main`（本人worktree） | PASS | main-fetch.json；fresh main如上，未移动共享main HEAD |
| `gitea.pulls.read --state open` | PASS | open-pulls.json，共2条，<50分页上限；PR325/323，未见#327 open PR |
| 远端#327 ref精确存在/不存在 | GAP | 现行typed surface没有独立ref枚举operation；本次未用失败fetch推断absent，发表前必须查重 |
| `gitea.protection.read` | PASS | protection.json：push=false、force=false、merge whitelist=[admin]、required CI=[CI / verify (pull_request)]、outdated blocking=true |
| fresh main源码/Mac installed broker.py bytes | PASS | baseline.json，SHA256均为2c1b05977437f16b461c8db0d41a2ad6947d9df5a929bcc3eaeadd332030da7f；三项互锁仍在 |
| gitea-ci installed完整bytes/mode/owner fresh | GAP | 未经额外typed读面取得；历史两机一致输入不能当本次全组件fresh证明 |
| #319事件审计 | PASS（事件读取） | `/private/tmp/aisoft-319-publish-audit/audit.json`，old cc34b550…不是new 9fbdb835…祖先；历史policy FAIL_NON_FAST_FORWARD；本次未重放写入 |
| #289候选保全与人工更新卡 | PASS（文件读取） | main-287-integration.json、candidate-preservation.json、PR-325-manual-update-card.md；35/1006/smoke是历史候选值，非#327通过 |
| Gitea本人New File/Upload File自举入口 | PASS（仅入口） | ui-bootstrap-readonly.json；新branch/PR选项可用，main direct disabled；未填字段/提交，已关闭核查tab |
| 四份新合同resolver/check | PASS | resolver精确返回四basename；check-change-documents：changes=148、pass=2、gap=0；draft-structure.json复核双份判级一致、8条AC、T01→T02→T03；这是文档结构检查，非Loop approved |
| triage/分类live投影 | GAP | `apply-classification-labels.sh --verify 327` 返回projection-missing、applied=false；type/platform与complexity/complex均未投影；category建议enhancement、state ready-for-agent |
| T01 映射治理应用与本地原子提交 | PASS（原 T01 commit 061b0f3ec59869fe379d70b7d2f0455df4b8708a） | 14 个映射治理文件 + 4 个语义文档；exact commit/parent/clean tree 与 STOP 见外部 T01 receipt，不在文件中自引用 SHA |
| runtime T02/T03 | NOT RUN | T01 后 fresh 只读发现缺口；新具体合同已直接确认，本次仅独立 T04 治理；后续 fresh T02 尚未运行 |
| bare-remote FF/guard/race与完整smoke | NOT RUN | 没有实现，禁止用历史测试当新能力PASS |
| 唯一PR发表、新headCI、manual merge | NOT RUN | 未最终PR批准，pr_url为空 |
| 两机安装、realFF、rollback、原owner采用 | NOT RUN | source尚未实现/合并；需各exact安装批准；未宣称#289已解锁 |

## Acceptance criteria 结果

| AC | 结论 | 当前证据 / 后续闭合方式 |
|---|---|---|
| AC-1 | PARTIAL | 四角色/T01/STOP、fresh T02 gap proof、具体补充批准与 T04 独立治理可核；后续 fresh T02 未执行，live 投影 GAP |
| AC-2 | NOT RUN | spec已定义正向路径；新实现/bare remote证据未产生 |
| AC-3 | NOT RUN | strictR竞态方案和fixture场景已写，不能以普通FF推导race通过 |
| AC-4 | NOT RUN | 负向矩阵已写，未实现/执行 |
| AC-5 | NOT RUN | 回执/freshness/全量smoke待实现 |
| AC-6 | PARTIAL | UI入口已观察；tree/mode/uniquePR/newCI/humanmerge未执行 |
| AC-7 | NOT RUN | 两机exact批准/安装/真实FF/no-op/rollback均未执行 |
| AC-8 | PARTIAL | fresh保护/身份边界已读；未来新实现保持及原owner采用待实证 |
| AC-9 | NOT RUN | authority/default-disabled/strict schema/真实 peer/隔离/records/重算/I02 已有批准 source 合同，但实现/真实注册启停rollback仍未执行；不能把文档或 mock 当真实可信根 |

## T01 批准与验证记录

- 授权来源：本聊天负责人直接“确认”，绑定 #327 / `change/327-broker-ff-integration` / manual；记录时间 2026-10-02T22:28:43+08:00。只启动独立 T01，验证和本地 commit 后立即 STOP。
- 治理前态/授权/清单保全：`/private/tmp/aisoft-327-contract-evidence/t01-before-governance.json`、`t01-approval.json`、`t01-governance-paths.json`。本提交 SHA/parent/全路径与 STOP 由外部 `t01-stop-receipt.json` 读回。
- 文档门：提交前重新执行 resolver、全仓 semantic document check、四角色状态/双份判级/8 AC/Ticket graph、精确 18 文件范围、runtime/install/config 与 HEAD 字节相等，以及 `git diff --check`。上述文档/范围检查 PASS，详细输出与所有文件 SHA256 见外部 `t01-validation.json`；不能把文档检查当 runtime 测试。
- 无 shell/Python/runtime/installer/manifest 实现改动；bare-remote、unit tests、完整 smoke、远端写入与 installed 验收均 NOT RUN。
- T01 本轮 STOP；当时计划后续 fresh run 从 T02 继续，并重读新治理、Issue/评论、spec/plan、批准和 installed 能力；该次原范围未新增合同确认点。后来 fresh T02 发现的具体可信根扩展另见下一节，不能继承此句批准。

## T02 fresh 分析与 T04 补充准备（此前草案 ac172e5）

- fresh T02 的 T01 治理 14 hash、Issue/comments、main 与保护已核对。HEAD 为原 T01；main=`65268ee5f1e622c486fd9e354dd35e20a2900f91`。Mac source/installed broker 同 hash，仍旧 leased code；VM 完整 bytes 未执行。
- 隔离 fixture 真实复核 current Controller：`#327 T02` subject + declared path 能通过现有 complex gate，虽文件不在 #327 exact scope；同一 object 可被不同 Issue ref 指向。这是**现有门的 GAP**，不证明真实外 Issue 创作或 live 攻击、不证明新门通过。见 `/private/tmp/aisoft-327-contract-evidence/t02-provenance-gap-proof.json`。
- 授权来源是本聊天 human literal“按建议继续”，只选择 A 路线并准备具体可信根合同。其他聊天提供的批准台账不代替人批准新权限/文件/运行接口；不虚构本聊天消息 ID。
- 本次只修改 summary/spec/plan/verification 四份草案。T01 已批准的 governing 14 文件、runtime/config/installer/service 全部与原 T01 保持相同；无新身份/Secret、root state、socket、服务或 live mutation。
- 补充完整写入 spec：固定 authority、trusted-critical/root 与非 root provider/真实 OS 隔离、peer 不等于程序、人类业务批准到 protected grant 的独立登记、逐对象/完整 scope/内容目的、两项 typed 操作、default-disabled、exact source 扩展、I02 card 与新增 AC-9。新具体合同待审阅，T04 pending；本次不标 approved 或 T04 completed。
- 文档/范围门：PASS。实跑 resolver、semantic document check、四角色状态与双份判级、9 AC/graph/22项新增映射、exact 四文件 diff 和 `git diff --check`；其余 1198 个 tracked 文件 bytes/Git modes 保持，其中14个 governing 文件还逐项核对原 T01 receipt 的 SHA256。结果保存为外部 `t04-proposal-validation.json`；这不是 runtime 测试。
- 具体确认须绑定本次提案 commit/spec+plan hash、#327 / branch / manual；确认之后才执行独立 T04 治理文本应用/local commit/STOP，再后续 fresh T02。不因路线选择跳过新增合同确认，也不新增 A/B 路线问题。

## T04 具体确认与独立治理应用（本次）

- 负责人在本聊天直接“确认”，批准前次审阅卡绑定的 #327 / exact branch / manual / draft commit `ac172e515a47357d24ff268473af6bbee5c13fe1` 与原 spec/plan SHA256；原批准 hash 保存在外部 `t04-application-approval.json`。记录时间只表示本地登记时间，不伪造消息 ID 或人类消息时间。
- fresh canonical broker 只读：Issue open、正文与前次相同、comments=[]；live 仍只有 triage/needs-triage。未写 live 标签、评论或 approved，不把本地文档状态当投影/protected grant。
- 本次只应用原14个 exact治理文本（含 AGENTS、双方源技能及共享 tracker）和四角色，落实 authority/protected grant/实际受控执行/非 root OS 隔离、两项受限接口、broker独立重算、default-disabled、I01/I02及STOP。source合同 approved，T01/T04 completed、T02/T03 pending；本提交不实现新 runtime/config/service 或创建 protected grant。
- 提交前检查 PASS：resolver精确四basename；semantic document check（changes=148、pass=2、gap=0）；四角色/双份判级、9 AC、graph/22项source映射、批准技术条款保持、双方共享文本一致和 `git diff --check`。exact18文件为14治理+4角色，其余1184个tracked文件bytes/Git modes保持；无新增runtime/config/service文件。结果保存外部 `t04-application-validation.json`，来自本次实跑，不继承草案 PASS。
- 本地原子commit后仅做 exact parent/paths/clean/owner/last_push/main 读回，保存外部 `t04-stop-receipt.json`，然后 STOP。治理不为运行时自授同轮权限；后续 fresh run 重新读取本提交治理、Issue/有效评论、spec/plan、批准、installed/capability/live gates 才评估 T02。
- 新 unit/smoke/FF/OS权限/root custody/installed/I01/I02/remote写/唯一PR/merge/部署均 NOT RUN。本次无脚本变更，不把语法/完整smoke写为 PASS，不安装全局源技能；source/installed 差异单独保留。

## 前后证据与安装回滚模板

每台主机独立记录：批准的人/消息/目标/版本source SHA；installed roots；文件before/after SHA256、mode、owner；缺失前态；source/installed比较；typedFF H/R0/R/M；remote写前后读回；requiredCI/main保护；no-op与失败rollback；完整旧态恢复读回。不记录token/path contents/auth headers。

本地bare-remote回归不能代替真实安装FF；真实已有Issue若需采用，由其owner带自身批准/原remote tip完成，不由#327代操作。缺真实可用目标时记录GAP并等待exact验收安排，不默默创建live canary。

## 遗留风险与未完成项

原 T01 已完成并停止；本次具体补充已直接确认并独立应用 T04 治理，验证/local commit 后 STOP，非 runtime 或 Issue 完成；没有 runtime、push、PR、live 标签、install、credential、protection apply 或 deploy。AC-7/AC-9 在 source 合并后仍须真实闭合；自动closed不当completed。不用已知历史PASS消除当前GAP。


## 2026-10-03 fresh T02 本地 source 实施记录（未完成、未提交）

本节覆盖前文“后续 fresh T02 尚未运行”的历史状态，不覆盖 T01/T04 原验证边界。负责人本聊天直接“继续 T02”；fresh receipt 时间 `2026-10-03T00:22:16.864516+08:00`，HEAD 为 T04 `c58a864329b83c2d81fb5aa01e5871d1b178b77b`。fresh canonical main `16beee09aefe89b5bc80a31544c59d456190ea32`；Issue open/comments 空/live 仍仅 triage/needs-triage；installed Mac broker 仍旧 bytes，VM 全组件仍 NOT RUN。

### 已实现的本地 source / fixture

- default-disabled policy；strict grant/record/operator card/typed request；固定 Unix socket、真实 peer 读取、root-only store 与 prefix/锁/原子持久化机制。
- hash-verified 私有 Git 对象导入、完整 first-parent/DAG/tree/delta 重算、固定 ordinary FF/pre-push 公告检查与真实临时 bare-remote 竞态 fixture；broker 两项新 typed 操作和 push 转交固定 client，旧 leased push 实现已移除。
- verifier 每次使用新建 root-owned 只读输入副本；materialization 对重复 blob 的每条路径都计费，展开前有总量上限。integration 保留旧 Issue 文件的 ticket 来源，不用 merge ticket 重授权旧内容。
- owner 在 begin/export/publish 前检查，marker 读取有字节/regular/no-follow/duplicate 限制；推送进入 transport 后失败保留 possible H，journal/marker 失败保留已落地 H；没有自动重试。
- fixed installed launcher 与 inert systemd/launchd 描述仅为 source 文件，模式100644；未安装、创建 state/socket、注册 grant、启用或启动。

### 检查结果与未闭合项

| 检查 | 结论 | 本次实际证据 |
|---|---|---|
| grant/record/schema、真实 peer 与实际非 root root-store 拒绝、Git/bare-race、owner 定向 | PASS（source/local） | `/private/tmp/aisoft-327-contract-evidence/t02-current-core-tests.log`；最终数量由最新测试回执读回，不能继承旧日志数量 |
| 两个新改 launcher 的 bash -n / ShellCheck | PASS | `t02-shellcheck.log` 为空且 exit=0；实际命令见 source receipt |
| 首次全量 runtime discover | FAIL | `t02-all-runtime-tests.log`：1043 tests，9 failures/9 errors；旧 leased/rebase 正向预期已被新 source 拒绝，CLI 增 ticket 需更新回归；两处裸模块互导已随后修正；不可把定向绿灯升为全量 PASS |
| 默认 locale 完整 smoke | FAIL（source staleness gate） | `t02-default-locale-smoke.log`：source 比 origin/main 落后48 commits；未执行提示中的 rebase/force/installer bypass，未宣称后续 smoke 已运行 |
| 14 个 T04 governing 文本 | 原样保留 | source receipt 逐项 hash 比较；本 runtime run 不修改正在遵循的治理 |
| source 新工具链完整闭包 | GAP | 当前 loaded-module pin 集不能证明 interpreter/native loader/Git transport/helper/late-import closure；`require_toolchain_closure` 无条件拒绝。prepare/apply、approve、approve-pr、restore、service 构造和 typed dispatch 均在任何新增/恢复授权或 worker 前阻断；root-only revoke 与默认只读 check 保留 |
| Mac verifier 可写 scratch 总量边界 | GAP | 单文件 RLIMIT 不能防很多文件耗尽宿主磁盘；非空 temporary 明确 `SCRATCH_QUOTA_GAP`。Linux bounded tmpfs 仅 source 规则，真实 namespace/root/drop/isolation 仍 NOT RUN |
| Controller / provider / verifier / progress 接线、唯一 PR/docs gate、显式 remote adoption、安装与漂移映射、完整回归 | 未完成 | 不把当前 source skeleton 当 T02 completed；SDK provider 仍 capability GAP，不启用任何 provider |
| root/OS sandbox/installed/I01/I02/远端写/唯一 PR/CI/merge/deploy | NOT RUN | 无此阶段授权或执行；没有把 mock、普通用户 fixture 或局部 bare 测试升级为主机实证 |

### 安全决策卡（只供审阅，不改变 approved spec）

依据当前 `AGENTS.md`：Development Loop“遇到……安全决策……必须停止并升级给人”。本卡只针对真实缺口；普通代码选择及此前已授权的 T02 不重新确认。已批准 spec 要求完整固定工具链/库 pin 和防资源放大，但没有决定 Mac 可写 scratch 的容量/inode/lifecycle/恢复机制。若新增受管卷、disk image、挂载/卸载或 privileged resource helper，不能把它当现有 sandbox 的普通参数，必须先冻结新增 OS tool/resource 与 rollback 合同；本 run 不引入这些权限。

共同必须补齐的工具链条件：固定 launcher/interpreter/stdlib/native loader/library/Git transport/helper/后续导入模块的完整依赖清单；每项 exact path/hash/mode/owner、OS 别名和缓存处理、发现/重验算法、未知依赖 fail closed；安装 provenance/drift/升级恢复映射；独立 per-host 正反向实证。不能用“当前已加载模块”或 root 所有权代替完整 closure。新机制仍 default-disabled，不能借本地 PASS 为 installed 授权。

Mac 两个具体范围选择：

- **A（建议）：补齐可写 scratch 的受控资源合同。** 下一步只在本 Issue 四角色准备可审阅的具体补充：固定总容量且禁止扩容、数量/生命周期边界、exact OS 工具与 root 执行参数、非 root 可写与只读输入分离、跨 generation 清理/崩溃恢复、磁盘满及卸载失败的 fail-closed 行为、before/after 与 rollback 清单。具体 OS 机制未选定前不写 runtime 或执行命令；批准后按独立治理应用/STOP/fresh runtime 顺序继续。该选择不授权实际安装、卷创建、mount、服务、账号或凭据动作。
- **B：Mac required verifier 只读执行，任何需要 scratch 的任务明确不支持。** 不新增 privileged volume/mount 权限，但需明确修改 Mac 支持合同及 acceptance matrix；不能把大量需要 build/temp 的项目写成可用。工具链 closure 同样必须补齐，双机 AC 仍未完成。

本卡不是新的 approved grant，不改变 R0、ticket graph、source policy 或安装权限。未收到范围选择前，不继续引入可写 Mac 资源机制；不把无条件 capability gate 删除来获得测试绿灯。当前所有 source 改动留在原 owner worktree 未提交，T02 in-progress，T03 pending。

## 2026-10-03 T05 安全草案准备（此前，非治理应用/非实施）

本节记录此前草案阶段；当前具体批准/独立应用见后节，前文T01/T04/初始T02数字均为对应历史证据。负责人直接“按建议执行”选择A，授权四角色具体draft。本轮新机制待具体确认；front matter summary/spec/plan为spec-drafting，verification pending；T01/T04 completed，T05 pending，T02 in-progress WIP且blocked by T05，T03 pending。不把路线选择登记为protected批准。

- 新鲜只读 #327：open、仅triage/needs-triage、comments=[]，见外部 `t05-draft-fresh-issue.json` / `t05-draft-fresh-comments.json`。未写标签/评论/ref/PR。
- 本轮只更改四个mapped语义文档。14个T04 governing与既有18项runtime/source WIP逐项byte/mode保持；其他tracked/untracked对象保全，before manifest见 `t05-draft-before-receipt.json`。未提交现有source、未改共享checkout。新9个source文件只是映射，不创建。
- 草案固定64 MiB scratch、256 MiB rootGit、owned-template/device/lease生命周期、全局并发/保留/input bounds、busy/crash quarantine和Mac noexec支持范围；完整Python前置nativebootstrap/目录+native+cache+alias+lateimport closure、v2私有绑定、default-disabled registry和publish durable pending。
- 工具文档：Context7无适配hdiutil库；只读Apple随OS手册与Apple一手网页，未运行hdiutil/mount/diskutil/root命令。本机sw_vers观察27.0.1/build26A434仅candidate，不算accepted matrix。手册hash/具体proposal校验receipt另存在外部evidence。
- 本轮文档resolver/semantic/exact四文件/AC11/graph/保全/diff检查的实跑结果见 `t05-proposal-validation.json`；检查完成后写确切结果，不继承旧PASS。code-review双轴只读审阅冻结草案；不把review当root安全测试。

| 新验收项 | 本轮结论 | 下一闭合阶段 |
|---|---|---|
| AC-10 完整closure/nativebootstrap/v2/OSalias/cache/late-import | NOT RUN | 草案待确认→T05→freshT02 source/build/negative→各主机I02真实pre-import/完整inventory/漂移/rollback |
| AC-11 bounded scratch/rootGit/ownlease/ENOSPC/tinyfiles/崩溃恢复 | NOT RUN | source fixture不能证明真实mount/UID；未来exactI02实际正反向及before/afterreadback |
| 模板create/attach/mount/detach/恢复；rootbootstrap/registry/服务/grant | NOT RUN | 本轮无具体主机执行授权；I01仅惰性文件，I02独立卡 |
| 全量runtime/smoke | 本轮未重跑；旧FAIL保留 | 原89targeted PASS与首次1043 FAIL、staleness smoke FAIL仅历史；freshT02完成源码后再实跑 |
| T05治理应用/新9source/remote/PR/install/merge/deploy | NOT RUN | 本轮四角色草案，不算governance完成、T02完成或Issue完成 |

审批卡须绑定新spec/plan内容hash、exact Issue/branch/manual/draftcommit（如有），确认仅启动独立T05应用原14治理文本+四角色/验证/localcommit/STOP。新grant/服务/卷/安装/启用不能从此次确认继承。真实安装与root能力未闭合继续open/保全，不cleanup/归档、不报#289解锁。

### 草案双轴审阅修正（此前）

Spec轴初审四项：CONTEXT输入未明确总预算/回收、I01/I02 realFF阶段依赖、治理计数歧义、incoming descriptor未给exact位置。均已在本轮草案修正：所有CONTEXT/temp/复制重叠计费、全局单副本/entry深度上限/受保护清单回收/失败quarantine；I01只文件验收、完整FF/运行rollback移I02；14+4=18；incoming常量路径/FD/mode/初次native staged preflight。Standards轴初审一项同一计数歧义，亦修正。修订固定snapshot/hash与最终只读复核见外部review receipt；这些修正不执行任何主机权限动作或source。

## 2026-10-03 T05 具体批准与独立治理应用（当前）

负责人本聊天直接“批准”，绑定已展示审阅卡的#327/exactbranch/manual及原spec/plan SHA256；批准登记时间仅本地receipt时间，不伪造human消息ID/时间。原批准内容/hash、治理前态与18项source WIP保全见 `t05-application-approval.json` / `t05-before-governance/`。当前本节覆盖此前“草案待确认”，历史事实仍保留。

- fresh canonical只读Issue open、正文与草案时一致、comments=[]，live仍triage/needs-triage；未写标签/评论/remote/PR。
- 本次仅原14治理文件的#327活段落和四角色（共18文件），同步完整pre-Python closure/bootstrap、fixed scratch/rootGit/CONTEXT预算/own-lease/quarantine、privatev2/public不扩、pendingpublish、I01文件/I02运行与source-installed/STOP。无runtime/config/service/installer/新9source改动；既有source WIP原样不混commit。
- summary/spec/plan approved；T01/T04/T05 completed，T02 in-progress、T03 pending。T05只指治理步骤，不将新增机制、root/OS隔离/主机或Issue写completed。
- 本次实跑resolver/semantic、11AC/graph/技术条款保持、exact18范围、双方共享合同一致、所有非范围bytes/mode与 `git diff --check`；结果保存 `t05-application-validation.json`。检查确认后本地独立commit，exactparent/paths/sourceWIP/owner/sharedmain/lastpush与STOP读回保存 `t05-stop-receipt.json`，不在本提交自引用hash。
- 无脚本变更，不重跑runtime/smoke并虚构PASS；旧89定向PASS、首次全量FAIL和staleness smokeFAIL保留。新bootstrap/模板create/mount/registry/grant/service/I01/I02/FF实证、远端/唯一PR/CI/merge/deploy均NOT RUN。
- commit后STOP，后续fresh run重读完整治理、Issue/comments、具体批准和source/installed能力再T02；不凭本run新治理自授同轮runtime权限。


## Fresh T02（T05 STOP 后；2026-10-03 source WIP）

本段只记源码进展，不改冻结 spec/plan、治理或安装合同。fresh run 已读回 T05
`bba5ea1790d4f8508746acb9a59ec99d39fbd4ab`、批准/STOP、14 governing + 四角色、
原18项source保全、owner/session/branch/index。Issue/comments/protection 经既有只读typed
broker读回，Issue仍open/triage-needs-triage且comments为空；不投影批准标签。

新增9项已批准source均保持100644：两个disabled/null registry、toolchain/scratch与相应
单元测试、native bootstrap、nonroot build脚本和bootstrap shell测试。grant/record/operator
切换v2私有descriptor/profile绑定；v1账本payload只读保留，不能成为active授权。
服务及privileged launcher改用fixed native entry，critical broker wrapper在任何source
Python导入前转fixed native入口；必要shell为`/bin/bash -p`，无caller PATH/BASH_ENV启动入口。

native源码目前只有bounded strict JSON/SHA-256/root-FD custody/inventory/固定角色负向入口；
完整Mach-O/ELF/native dynamic/shared-cache metadata、held-FD descriptor/resource/card调度与
canonical interpreter dispatch尚未完成。native和Pythonclosure gate继续拒绝，无通过字段或fixture
开关。build receipt明确SOURCE_ONLY/dependency closure GAP/SDK freeze NOT RUN，不充I01安装凭据。

resource纯schema/预算/租约/prefix/device/kernel projection已补，Mac create/attach框架未接到
authority。真实descendant跟踪、seal/retained-object闭包、Linux bounded tmpfs、protected resource
book和generation/verifier接线未完成；record builder只接受v2与exact lease digest，真实lease seal
缺失时明确RESOURCE_CAPABILITY_GAP，绝不填placeholder。detach在跟踪缺失时先持久quarantine，
保留lease/proof/预算并阻断新generation，不用caller Boolean证明后代退出。
Apple SDK及Apple XNU `bsd/sys/event.h`表明NOTE_TRACK/NOTE_TRACKERR/NOTE_CHILD自10.5不再支持，
不能把kqueue parent/process-group退出当全后代证明；未引入新EndpointSecurity授权。

publish加入protected durable attempt/state与restart/reentry只poll语义。attempt绑定exact record/H/
generation；generation和publication互斥；job与transport前重新核对sealed record和active grant；
实际transport开始/返回与operator revoke串行。断线/重启保留H/phase/possible_write，不能自动再推。
以上为source实现/fixture证据，当前closure gate使live transport始终不可达。

| Check | Result | Evidence / boundary |
|---|---|---|
| fresh T05 approval/STOP/source/governing/owner readback | PASS | 外部`t02-after-t05-fresh-receipt.json` |
| targeted change_evidence/toolchain/scratch/authority/main_integration/worktree_owner + CLI typed fields | PASS | 109tests；`t02-after-t05-targeted-repaired.log`；全部source/nonroot/pure或本地bare fixtures，不是root证明 |
| native SHA-256 million-byte/vector/strict JSON duplicate/NUL/overflow/role negatives；两个source build逐byte一致；startup拒绝 | PASS | `t02-after-t05-native-repaired.log`；真实nonroot；未装或运行root角色 |
| 4 changed shell `bash -n` + ShellCheck | PASS | source静态检查；不推导installed mode/exec能力 |
| all runtime discover | FAIL | 最新完整run1065tests，8failures/9errors；`t02-after-t05-all-runtime.log`；旧leased-push期待与新authority拒绝边界冲突，CLI缺ticket=None expectation后来定向修正；修后未再跑完整集，不推导全量PASS |
| required default `bash codex/tests/smoke.sh` | FAIL | `t02-after-t05-smoke.log`；source guard：architecture/install checkout behind origin/main68commits；未移除guard、自动rebase/merge或安装 |
| parallel Spec/Standards review of fixed WIP | repair recheck PASS (limited scope) | 初次snapshot receipt `0d005fce72217d35dfac4b1ba7717570a435bce327454547638b51b9c53844eb`；record race/revoke serialization、durable quarantine、fixed shell startup、NUL strict JSON已修 |
| native dependency/dispatch、actual tracking、resource+Loop+installer/drift接线 | GAP / pending | 已批准范围内仍未完成的source，不称外部安装阻塞，也不把schema/拒绝测试当实现闭合 |
| I01/I02/root incoming/grant/UID/socket/service/镜像创建或挂载/PAT/provider/live remote/PR/merge/deploy | NOT RUN | 本次只有source/nonroot fixtures与只读事实 |

T02仍in-progress，T03/firstPR/I01/I02均未启动；本次源码WIP未提交。HEAD仍为T05，index为空，
零remote写。冻结spec/plan和14 governing保持T05字节；共享checkout未操作。后续在同一批准source
范围内补齐native依赖/调度与真实OS跟踪/资源生命周期，再接Loop/install/drift并迁移旧leased-push
测试；保留当前FAIL/GAP，不以减少硬门或fixture root PASS完成T02。


### 本次修复复核读回

Spec 与 Standards分别只读复核固定 repaired snapshot（29路径，receipt SHA256
`0ee0f8ffc8c9be9e6dd7b120b44c341239c2ad75f3ebe8b45ce758afa8c04237`）。两个轴均确认上述
已发现项的修复闭合、限定范围剩余新增硬项0；并明确不是T02完成验收。未重跑或声称root/remote
验收，仍保留all-runtime/smoke FAIL和native/tracking/resource/Loop等GAP。

末次installed校验明确按同一对象比较：`/usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py`
仍为fresh起始hash `2c1b05977437f16b461c8db0d41a2ad6947d9df5a929bcc3eaeadd332030da7f`、root0644。
另一个对象launcher `/usr/local/libexec/aisoft/host-access-broker` 为
`88c663af3a3e3b710cc271e7ff671e279d38fc357657330682a338d6ba3f4135`、root0755；两个不同对象的
hash差异不是installed漂移证明。早前误混比较已更正。fixed native endpoint依然不存在。


### Fresh T02 后续源码进展：Loop/client、native metadata 与受保护资源账本

本节覆盖前节对“metadata尚未实现”“protected resource book未实现”的旧进度描述；
保留当时测试结果为历史。T02仍in-progress，完整closure/dispatch、真实tracking、资源生命周期与
Loop/provider/PR/installer/drift端到端仍未闭合。本节仅source/nonroot及纯fixture；无root或安装执行。

- Loop `LocalGit` 的push改走fixed VerificationClient typed request；project必须绑定，移除普通Git push。
  publication projection只接受exact字段；pending/失败保留H、attempt、possible_write与nullable读回，
  客户端读回null不会覆盖证据错误或伪造零写。对应67项定向测试通过，两轴冻结scope复核新增硬项0。
- native clock改为monotonic；16字段closure语义图、alias字节、role、public四keypolicy、resource/OS/
  canonical toolchain digest先行校验；16384 aggregate计入cache backing与三个role imports。
  Linux实际procfs full-identity UID-map preflight源码不声称唯一initial namespace证明；实际Linux/root NOT RUN。
- C与Python都有有界ELF64 metadata解析，保留RPATH/RUNPATH原始语义，拒绝动态表/字符串越界、
  u64溢出、LOAD/BSS重叠、未知audit/filter/delegate。Mac补thin64、fat32/fat64、唯一CPU slice、
  fat/thin subtype一致、MH_BUNDLE/dyld ID、linked/rpath/UUID、segment/section/linkedit等结构。
  未知或加密delegate拒绝；只观测文件metadata，不完成kernel page/ABI/resolution/cache/dynamic证明。
- Python incoming reader固定三个名字；root0700父目录、root0600 regular/nlink1/no-follow、8MiB或卡1MiB，
  FD前后stamp、同名entry和目录身份重验。private `--apply` operator卡只从固定incoming读取，不读stdin。
  尚未完成首次注册native held-FD proof交接，不能以Pythonreader替代pre-import gate。
- `ProtectedResources`将严格单步resource event追加到既有protected ledger，持锁拒绝stale snapshot、
  prefix重置或profile重绑定，不增第二个可覆盖的book。纯内存store测试不证明root custody、真实quota或seal。
- Mac backend补observer缺失的allocation前闸门：constructor完整closure gate、attach在reserve前、run在exec前
  均拒绝未实现的observer；detach仍先durable quarantine并保留预算。未实现observer/模板/kernel接线时不分配，
  不以leader或process group退出替代全后代证明。Linux backend与actual tracking/seal/retention仍pending。

| Check | Current recorded result | Exact scope / evidence |
|---|---|---|
| Loop/client定向 | PASS | 67项；`t02-loop-client-tests.log`；scope receipt `7113ac0b30dfa805d5536440efd35ac91b4b655e4a1763ff47fa93a530410d08` |
| incoming/protected resource/toolchain/controller/scratch定向 | PASS（对应冻结scope） | 103项；`t02-protected-resource-source-tests.log`；receipt `cfa1a92018f5ea56a1d0bf37b9be45f0b397664c5a83bda9da2dd0c467ea4dcb` |
| Mach-O C native FD/parser/build与Python定向 | PASS（解析scope） | `t02-native-macho-source-final.log`与exit0 receipt；Python23项/exit0 `t02-macho-targeted-final.log`；无loader执行或root验收 |
| Mach-O冻结两轴复核 | 新增硬项0/0，无新增实质smell | 4文件receipt `c2a5077afe7a04f527bc3c578fab62f552958c634bf1c1da5a012d40abf1c9eb`；不能投影T02完成 |
| 全量runtime（Mach-O后、observer entry-order新增前） | FAIL | 1098项，7failures/9errors，92.150s；`t02-macho-all-runtime.log`；输入receipt `24d637fe5c9bea95cbc69c5abf8dd0a16074a27437e3395e3426a9e6013492fe`，source inputs运行中保持（progress文档除外） |
| Mac observer allocation前拒绝定向 | PASS（纯entry-order/lifecycle） | 10项scratch测试；无root/backend constructor或mount执行；此新增后未重跑全量 |
| required default smoke（最新） | FAIL | `t02-native-macho-smoke.log`/exit1；architecture/install source guard读回behind origin/main87commits，覆盖此前68差距读回；无merge/rebase/guard移除 |
| changed shell bash-n/ShellCheck与diff whitespace | PASS | source静态；不证明installed executable mode或能力 |
| governing/冻结summary-spec-plan/index/shared checkout | PASS（只读） | `t02-macho-frozen-contract-check.json`；17文件与T05逐byte一致，HEAD仍bba5ea1790d4f8508746acb9a59ec99d39fbd4ab，index empty，共享HEAD5c2cd726c9aeaee9d17541d8feb049e33881bbac |
| 完整native graph/cache/dynamic/held-FD/dispatch、真实resource/tracking与完整Loop/provider/PR/install/drift | GAP / pending | 已批准source仍需实现，不能用拒绝或schema测试代替闭合 |
| I01/I02/root/installed/live/remote mutation/PR/merge/deploy | NOT RUN | 无新增主机执行授权或行为；WIP未提交 |

全量失败仍是旧leased-push/ownership/rebase/任意merge预期与新authority custody拒绝边界的冲突；
后续须保持对应真实DAG、ownership、race、manifest以及publication硬门，完成可信执行链和合法回归迁移。
不得只把旧预期改成CUSTODY_GAP、删测试或放开root fixture来制造PASS。


### Native frozen-link解析修复与重复失败升级停点

新增`native_link_targets`仅为纯解析函数，未接入native/authority或授予exec。
冻结execution root/inventory/search顺序、ELF RPATH与RUNPATH分离、Mac path tokens、alias与
linked manifest逐项对齐均有拒绝边界和monotonic deadline；仍需递归execution context、
accepted loader/kernel ABI、cache/dynamic/build manifest、native pre-import与held-FD完整接线。

两轴初审均发现P2：alias前的词法normpath可能将目录alias之后的`..`绑定为不同库。
第一修复仍在PurePosixPath前遗漏alias raw `.`/末尾斜线的目录语义；最终修复在任何Path构造前
检查原文，未证明的dot/dotdot/trailing-slash直接GAP。负例含目录alias+`..`、不存在中间目录+`..`、
alias target三种raw dot/trailing组合。最终28tests实跑exit0；两轴限定复核hard0/0、smell0，
receipt `8ffc644916f8e4b1206364bcf46b2c599f0f24f9c25cf5ab4530e2e3d9871257`。
这些PASS仅pure source；未把strict拒绝、module parser或loaded-module列表当完整closure。

两次完整runtime日志1096与1098tests的failure/error method+subtest逐项相同（7failures/9errors，
13个method/16case）。依据本worktree AGENTS.md:15“遇到……重复失败时必须停止并升级给人”，
本次修复/复核和保全后停在repeat-failure escalation；T02仍in-progress，未标完成。
外部`/private/tmp/aisoft-327-contract-evidence/t02-repeat-failure-recovery-card.md`绑定exact
Issue/branch/owner/HEAD和失败映射：建议A先完成已批准可信执行链，再逐项保留DAG/ownership/
race/manifest/publication硬门迁移旧leased-push回归；B先只读核对canonical-main差距并准备整合卡。
不改测试预期为统一CUSTODY_GAP、不删skip硬门、不自动rebase/merge或凭此启动I01/I02。
最后修复后只重跑相关定向门；不继续重跑未修复的完整集来消耗或制造PASS。
source WIP保全，HEAD/index/owner/共享checkout与冻结合同保持，零remote/安装/主机写。


### 恢复卡 A 后的 native card、link 与 cache source 进展

用户于本轮直接选择“按你的建议执行”，已按 exact Issue #327 / branch
`change/327-broker-ff-integration` 记录恢复卡 A；本节覆盖前节 repeat-failure 停点的当前状态。
原批准 source 范围继续执行，T02 仍 in-progress。恢复 receipt 为
`/private/tmp/aisoft-327-contract-evidence/t02-recovery-a-resume.json`，绑定恢复卡 SHA256
`9cdaba89a12b0bd3163d66aca1f84b246eaf917944b5dd7adce9e72ad23e4c6f`；无新增 root/installed/live/remote 权限。

- native 固定 `--apply` 卡预检绑定 v2、operation、toolchain/resource/policy/profile 摘要；卡、policy、
  descriptor 持有 FD 穿越有界 closure walk，并重验 held object 与 fixed 同名 entry。
  卡完整 grant 校验仍由后续 pinned operator 承担；首次登记的同 FD dispatch 尚未完成。
- C 解析接入冻结目录、first candidate、Mach-O tokens、ELF RPATH/RUNPATH 和 exact linked set；
  未登记 loader 默认目录直接 GAP。C/Python schema 同步拒绝 raw alias dot/empty/trailing components。
  两轴发现并修复 P2：Mach-O 中间位置误展开 ELF ORIGIN。负例登记原错误目标/目录/edge；
  临时 source copy 去掉格式限制后 fixture53/exit1，当前修正版通过。冻结修复复核 hard0/0，
  receipt `386fc756730caa0429f5f5b5cc0f747bafba78a758f54470b4d401299766ed14`。
- native pin hash 与 ELF/Mach-O/cache 表观察改为同一 FD，随后核同名 binding；实际重复 streaming hash
  也计入 64 GiB 总界。dyld cache 的 UUID、image-text UUID、mapping 与 24/56 字节 subcache 表从
  held bytes 读取，不 hash logical name 冒充字节证明。固定子路径、完整 declared backing set、UUID、
  region/VM offset、text 所属 RX mapping 和重叠拒绝已有 C/Python source fixtures。
  cache reader compact metadata，单独对 cache pool 的内存留存和最坏 parse peak 设界；
  这不替代 protected 文件/卷的真实额度账本；symbol-only/未知格式仍能力 GAP。
  格式参考 [Apple dyld cache header](https://raw.githubusercontent.com/apple-oss-distributions/dyld/main/include/mach-o/dyld_cache_format.h)
  与 [Apple cache reader](https://github.com/apple-oss-distributions/dyld/blob/main/other-tools/dsc_extractor.cpp)，
  文档不能代替 OS/cache/root 实证。

| Check | Recorded result | Evidence boundary |
|---|---|---|
| native card/link/cache/set 的 nonroot FD fixtures 与两次 build | PASS | `native-cache-set-source.log` / exit0；artifact 字节相同，非 root 安装或执行验收 |
| toolchain/cache Python 定向 | PASS | `native-cache-set-python.log`：39 tests / OK；raw temporary FD + pure binding，非 actual active cache |
| changed shell bash-n / ShellCheck / diff | PASS | `native-cache-set-exits.json`；source static scope |
| required smoke（恢复后） | FAIL | `native-card-smoke.log` / exit1；source guard behind tracking origin/main87 commits，无 rebase/merge/guard bypass |
| card/link/byte-cache 两轴冻结复核 | 新增 hard0/0 | card receipt `74de4ff7c1c40740c935f4f2f6613631b697d66c0d499783a8d7d21a8164e8c2`；修复 link receipt 上述；byte-cache receipt `64a27346e437fe91e8bc1474e26a233f721116dac86c29cbc11b1750a0e5bae2` |
| 完整 backing-set 峰值修复复核 | PASS，双轴 hard 0 / 0 | fixed snapshot receipt `298ac086ef275c9add3a9fe07d0b85d12fdf3f0165c25c80882708c3c712cb56`；compact 双 arena 复制窗口与旧错误边界负例已复核闭合。不把此内存预检等同磁盘预算验收 |
| 完整 runtime | 未重跑，最新历史 FAIL 保留 | 旧重复失败尚未迁移；仅 source 定向修复，不重复未修复 full run |
| recursive cached Mach-O/native graph、dynamic/build、actual active cache/OS TCB、same-FD dispatch | GAP / pending | native 仍无 exec；authority complete-closure gate 未解除 |
| observer/resource 生命周期、Loop/provider/PR/generation 与 installer/drift E2E | GAP / pending | 既有已批准 source 尚需完成 |
| root/installed/I01/I02/service/template/mount/live/remote mutation/PR/merge/deploy | NOT RUN | 本轮 source WIP 未提交；没有使用 root 模拟验收 |

本节的 PASS 仅对对应 source/fixture scope，不投影 T02 完成或 installed/live。原17 governing 与冻结
summary/spec/plan 仍须保持 T05；共享 checkout、owner、HEAD 与 index 保持，不自动整合 main。


### 恢复卡 A：cached Mach-O、同 FD 递归图与主线整合停点

本节更新前节 cached Mach-O/native graph 尚未实现的进度，不改变完整 closure/dispatch 的 GAP。
本次仍限 source/nonroot/pure fixture，无 root、安装或现场验收。

- cached Mach-O 从实际 held cache/subcache FD 的 mapping 字节解析 header/load commands；
  `__LINKEDIT` 的原 fileoff 通过 segment VM 映射到实际 backing，拒绝未知 command、UUID/ID 不符、
  跨界与歧义 mapping。CacheUniverse 核对整个 descriptor 的 UUID/VM 与 aggregate 条目界。
  negative fixture 实际改写 backing 后再次核对 FD stamp；不以 cache 表中的 logical name 替代字节。
- closure preflight 先固定并 streaming hash 全部文件，再用同一组 PinnedFiles 做 native/cache 元数据
  与逐 root 的静态及 declared dynamic graph，最后复核 FD 和同名 path。一次 critical 内复用已验证 FD；
  不创建跨 critical 的 mtime 信任缓存，不解除最终 `TOOLCHAIN_CLOSURE_GAP`，仍无 Python exec。
- C/Python 递归图使用 source 与完整 inherited search context 作为 visited identity；每个 fixed execution
  root 独立展开，保留 ELF RPATH/RUNPATH 的传递差别、Mach-O token、late extension/interpreter context、
  declared dynamic/delegate 与 cycle 硬门。队列/状态/元数据合计有界，生产 reader 仅读同 held FD。
  pure Python recheck 不能替代 native custody、dynamic/build completeness 或实际 accepted loader/OS/cache。
- 两轴发现的 deadline 错误分类与 graph resident 内存漏计 P2 已修复：helper 的 timeout 保留 GAP；
  64 MiB graph 界计入常驻 pins/CacheUniverse/cache binding，且在分配前检查。
  最新 fixed 4-file snapshot SHA256 为
  `4a953abb5f1f879e5dac78218018428f6d2d52f3cef8a2d06207966307e7d77d`；
  Spec hard0、Standards hard0；Standards 保留 1 项非阻断 judgement smell（resident 公式重复）。

| Check | Latest result | Evidence boundary |
|---|---|---|
| native nonroot source fixtures 与重复 deterministic build | PASS | `native-held-memory-fixed.log` / exit0；fixture bytes/parser/graph/bounds，不是 root/active-cache/dispatch 验收 |
| Python toolchain graph/cache 定向 | PASS | `native-context-python.log`：47 tests / OK；pure/temporary FD scope |
| source-only context mutant | 负例有效 | `native-context-mutant-fixed.json`：source-only visited mutant 使 diamond context test 真失败；首次 import-error attempt 不作有效负例 |
| bash-n / ShellCheck / diff whitespace | PASS | fixed 4-file snapshot 的静态出口均 0 |
| 固定 snapshot 双轴复核 | hard0 / hard0 | 上述 receipt；非 T02 全量复核，1 judgement smell 保留 |
| required default smoke | FAIL | 最新 `native-held-graph-smoke.log` / exit1；source guard 读回 behind origin/main 87，恢复后多次同一阻塞，没有 bypass |
| 完整 runtime | 未重跑；历史 FAIL 保留 | 旧 13 methods/16 cases（7 failures/9 errors）尚待可信链完成后的合法回归迁移；不得统一改成拒绝/skip |
| fresh canonical main typed fetch | PASS（只读） | sandbox TRANSPORT_ERROR 后，同 typed `git.fetch.main` host 路径通过；main=`dc9aa468580f92a73dfa054c6f04ef5113f56694`，没有 remote write |
| 主线三方整合预览 | 1 内容冲突 | 只在临时 object dir/index；`broker.py` 冲突，8 个 WIP 路径与 upstream delta 重叠；实际 HEAD/index/worktree 未整合 |
| main 中 incoming governing | 7 个文件的 proposal，NOT APPLIED | 保留 #327 T05 合同；需具体同步审批、治理-only 步骤与 STOP/fresh run，恢复卡 A 不授权 main integration |
| 完整 native closure/dynamic/build/ABI/cache proof/同 FD dispatch，observer/resources/Loop/install-drift | GAP / pending | T02 仍 in-progress、32 个 source WIP 未提交 |
| root/installed/I01/I02/Secret/service/image/mount/remote mutation/PR/merge/deploy | NOT RUN | 无新增现场或外部执行授权 |

重复 smoke source guard 阻塞已升级到具体的 canonical-main 整合卡准备。本轮只做只读 preview、
source WIP 保全和证据更新；原17冻结治理/summary/spec/plan、owner、HEAD 与空 index 保持。
后续治理 proposal 或本地 main integration 必须绑定 exact source/main/patch/owner 卡确认，
治理-only 应用后 STOP，fresh run 重读后才能 runtime；不能凭 A 自动 rebase/merge。


### T06 实际 STOP 后的 fresh T02/R01 与固定解释器兼容停点

本节覆盖上一节“主线尚未整合”的当前状态。负责人已直接批准 exact T06/R01 卡
`a53a215d223381e131600414b9c1677d1689db408971a22af923322fdc6ca4e1`；T06 实际治理提交
`ad305ac30f4b6bb004934ba3c5d921acd28dc162` 后已 STOP。当前是随后 fresh run，已重读合同、
批准、Issue/comments、main/source/owner/installed；未等待其它聊天或代操作其 worktree。

- canonical typed main fetch 经 host 路径成功，pin 仍为
  `dc9aa468580f92a73dfa054c6f04ef5113f56694`。live Issue open、comments0、仅 needs-triage；
  本地具体 source 批准不当作 live approved label 或 protected grant，投影 GAP 保留。
- 原32 WIP 按 bytes/mode 保全、park 后，实际纯 main checkpoint 为
  `4cb627d9525611bff34387830978ba5c5785863e`；parent 顺序为 T06 commit、上述 canonical main，
  tree 为 `222feec17b625aa0c14b5fcf366f6057057454a1`，恰等于获批 preview。随后恢复未提交 WIP，
  唯一 broker 调度手修恰等于获批候选，未混入 checkpoint；未 rebase/force/改写旧历史。
- 首次整合检查因 main 中其它 Issue 的 evidence.patch 六个单空格 context 行退出，已 abort 并
  恢复原32 WIP。保留 canonical patch bytes 后，本 Issue delta 对 main 的 whitespace 门通过，
  第二次实际整合成功；未修改其它 Issue 证据来制造 PASS。
- 已在原 scope 内更新 `test-host-access-broker.sh`：operation 38→40，并校验 begin/verify
  exact shape；Keychain 静态扫描仅豁免固定文件的完整 inventory deny-list 行。
  同行命令注入、其它文件命令、新增 secret path、deny-line drift 均真实拒绝；toolchain unit
  增加 Keychains 路径拒绝向量。当前33 WIP 未提交，17治理文件保持 T06 bytes。

| Check | 本轮实际结果 | 证据及边界 |
|---|---|---|
| main 后7组 source 定向 | PASS，203项 | `t02-r01-fresh/targeted-after-main.json`；pure/普通用户/临时 FD，非 root 或全量 |
| Keychain 修复后 toolchain | PASS，47项 | `toolchain-after-keychain-fix.log`；与上行有重叠，不累计为250项 |
| 改动 shell 的 bash-n / ShellCheck / diff | PASS | `keychain-gate-vectors.json`，5个静态正负向量；未执行 Keychain 或凭据读取 |
| required default smoke | FAIL，exit1 | `smoke-keychain-fixed.log`；原 source guard 差距解除，停于 fixed broker fixture:131；固定 Python3.9 导入 dependencies alias 失败 |
| actual native source fixture | FAIL，exit1 | `native-after-main.log`；同一 dependencies alias 导入失败，未替换固定解释器或删除门 |
| 完整 runtime | 本轮 NOT RUN；历史 FAIL 保留 | 原13 methods/16cases尚未完成可信链后的合法迁移，不重复未修复全量集 |
| 完整 closure/dispatch/resources/observer/Loop/install-drift | GAP / pending | T02仍in-progress，T03 pending；不能把 fail-closed/schema/parser 测试当能力闭合 |
| root/installed/grant/Secret/service/image/mount/remote mutation/PR/merge/deploy | NOT RUN | owner、共享 checkout 与 installed 受管文件保持；无新增执行许可 |

固定 `/usr/bin/python3` 实际为3.9.6。canonical main #286 的模块级
`Dependency = int | str` 不能在其下加载；隔离候选先恢复此 alias 后，完整 broker 导入还触发既有
`profiles.py` 的模块级 Callable/PathLike union alias。后者来自原 profile runtime；旧 wrapper
使用 PATH Python，而本 Issue 固定解释器入口要求其兼容。两个原文件均不在旧 #327 exact scope，
actual checkout 保持原 bytes，未应用未经确认的修复。

只读 T07 提案仅新增这两个 exact 文件的四行等价 `typing.Union` import/alias，先应用
mapped summary/spec/plan 的独立治理合同/localcommit/STOP，后续 fresh T02 才允许 source 修复。
proposal、before/candidate/patch、两项已授权测试增量与负向 vectors 的 hash 绑定在
`t02-r01-fresh/t07-compatibility-contract-proposal/receipt.json`；当前未批准、未应用。

隔离双文件候选在相同固定3.9下通过65项 toolchain/profile units、broker未知 operation 的
exit20/REQUEST_DENIED、完整 nonroot native source fixture。actual checkout 同65项在3.14通过；
上述 candidate PASS 不覆盖 actual fixed3.9/native/smoke FAIL，也不证明完整 native dispatch。
首次扩展 unit harness 指定 `/private/tmp` 使文件实际继承 wheel group，与调用用户组不同，
两份源代码均真实拒绝，1failure/4errors日志保留；最终只改用现有用户临时目录的真实匹配 UID/GID，
未改代码/测试/UID或 chown 来通过。其它不完整临时 copy/import attempt 也保留，不作有效 PASS。

依据 AGENTS 的 scope 扩张与外部阻塞边界，本轮在保全与具体兼容提案完成后停下 runtime 实施，
等待这项新范围的具体确认；原 T02 启动批准与已完成 T06/R01 均无需重复确认。

### T07 实际完成后的 fresh T02：固定3.9恢复与 source loader 修复

上节是确认前的历史停点，保留原 FAIL/候选证据。本聊天随后直接“确认”精确 T07 卡；
三份治理合同独立提交 `9ea1e90f0fe129181600851e2a701bceeca6b026` 并 STOP，
后续 fresh run 重读批准、17 governing、source/owner/index、live Issue/comments、
canonical main 与两项 managed installed bytes。原 main pin
`dc9aa468580f92a73dfa054c6f04ef5113f56694` 保持，live 仅 `triage/needs-triage`、comments 空，
本地具体批准仍不作为 live approved projection 或 protected grant。

四行 `typing.Union` 修复已实际应用，after bytes 与批准的两个候选 hash 完全一致，
并独立提交 `1849735a510299b183b00edebea9a6e7e999de0b`（parent 为上述 T07 commit），
仅 `dependencies.py` / `profiles.py` 各2行替换。提交时原33 WIP、17 governing、owner 均保持，index 空。
实际提交、before/after、验证和保全记录在
`/private/tmp/aisoft-327-contract-evidence/t02-after-t07-fresh/python39-source-commit-receipt.json`。

随后在原 T02 的两个 exact 文件范围修复 source import seam：
`toolchain.py` 的 loader 执行同一次接受并核验 size/hash 的源码字节，
不让 `SourceFileLoader` 再读路径或时间戳有效的 pyc；按固定 role 限制 registered imports，
pyc 与尚未具备 held-object 能力的 native extension 在读取/加载前拒绝。
`test_toolchain.py` 加五项有意义的负向/实际字节替换测试，main guard 在全部类之后。
原 loader 的同一攻击样例真实执行了替换字节，red 为3 FAIL/1 ERROR；候选与实际 source 均转绿。
这是 pinned-reader unit seam，不能证明 root custody 或完整 bootstrap/loader 能力。

| 本 fresh turn 实跑 | 结果 | 边界 |
|---|---|---|
| actual fixed `/usr/bin/python3 -I -S -B` 导入、65项相关 unit、unknown `shell.run` | PASS；deny exit20/REQUEST_DENIED | 四行实际 checkout；未读取 credential |
| source loader 修复后的 fixed3.9 相关 unit | 70 tests PASS | 52项 toolchain +18项 profile；不和下面重叠项累加 |
| 七组 source 定向回归 | 208 tests PASS | toolchain52/main-integration17/change-evidence23/authority25/controller48/owner33/scratch10 |
| 真正临时 bare remote 的普通FF/竞态/DAG/tree/ref | 17 tests PASS | 包含在208项；仅本服务测试临时 remote，无 live target |
| loader 候选 discover/direct 两入口 | 各52 tests PASS | 隔离副本；actual source after hash 已核对，不替代 root 验收 |
| 四行后的 nonroot native source fixture | PASS | 编译两次字节一致；actual UID501，不模拟root，不证明完整闭包 |
| default smoke，sandbox 路径 | FAIL | 已越过旧3.9导入故障，后被 local socket bind 权限拒绝；原日志保留 |
| 原命令 default smoke，host 路径 | FAIL：runtime 1242 tests，7 failures/9 errors | 仍是既有13方法/16cases旧发布语义；没有统一改成 CUSTODY_GAP、删除或skip硬门 |
| 完整 native closure/dispatch、observer/resources、其余可信链和旧回归迁移 | GAP / pending | 不把上述 unit/fixture PASS 投影为 T02 完成 |
| root/installed grant/service/socket/镜像/签名/权限/remote mutation/PR/merge/deploy | NOT RUN | 没有从本轮确认继承这些权限 |

全部日志与逐文件 hash 位于上述 `t02-after-t07-fresh/`。两轴 review 的 loader slice
hard0 / hard0；Spec 轴发现 main guard 位置 smell，已修正并复核为0，非全 T02 review。
新 loader 两项 WIP 与本 verification 进度是本轮 source 增量；其余原 WIP、17治理合同保持。

Mac observer 的后续安全边界尚待裁决：本机 product version 实读27.0.1；现有 SDK 与 Apple XNU
源码都明确 `NOTE_TRACK/NOTE_TRACKERR/NOTE_CHILD` 自10.5起不支持，常量存在不表示完整跟踪能力。
SDK 的 `es_new_descendants_client` 仅27+、需要 endpoint-security.client entitlement，
只可观察自身后代，且不要求root/TCC；没有实际创建 ES client 或查询/改变签名/TCC/审计策略。
不能用 kqueue/PID轮询或不明签名代替完整 descendant 证明；完整闭包与 observer gate 仍关闭。
T02保持in-progress、T03 pending；新后端或其签名/OS权限只能先明确受控合同及未来独立 I02 卡。


### T08已完成后的fresh T02：provenance绑定、OS只读纠错与实际停点

本聊天直接“确认批准”T08 exact卡。T08仅三治理合同实际于
`c9a9154436a8ae3ea277d176389f9854833a74b5`（parent
`1849735a510299b183b00edebea9a6e7e999de0b`）独立提交，随后STOP。
本fresh run按原批准重读owner/17治理/33 WIP/index/installed，最初main tracking仍
`dc9aa468580f92a73dfa054c6f04ef5113f56694`。typed Issue/comments只读body hash
保持，Issue open、comments0、仅triage/needs-triage；live approved/classification仍GAP。

既定source范围内新增量实际落到4个原WIP文件：toolchain.py/test_toolchain.py、
verification-bootstrap.c/test-verification-bootstrap.sh。Python/C要求build receipt、
dependency manifest、OS matrix三digest各绑定唯一、独立、非空且≤8MiB的trust数据pin；
native hash后保留实际FD并复核稳定性。仅完成绑定前置，不验证冻结文档语义或完整闭包，
SOURCE_ONLY不升级为accepted；原native closure/dispatch无条件GAP仍保留。
七项Python安全测试与12项native pure JSON vectors没有替换原拒绝guard或模拟root UID。

另在同一toolchain/test_toolchain纠正固定SystemVersion.plist读取的精确mode期望：
实际只读观察为regular/root UID0/nlink1/mode0444/size604，旧源码默认0644因而拒绝。
只显式指定0444，原root/parent/no-follow/nlink/大小/漂移检查不变；新增三OS-data seam
测试保留异常build与custody拒绝。实际UID501读取OS tuple为27.0.0/arm64/26A434，
仍只作observation，不是accepted OS matrix或完整root/kernel闭包证明。

| 本fresh run实际执行 | 真实结果与适用快照 |
|---|---|
| provenance后的固定Python3.9 unit | 77 PASS：toolchain59+profile18，包含纯模型，非root能力证明 |
| provenance后的native source fixture | UID501/unsigned/repeat build PASS；新增12 vectors，完整dispatch仍GAP |
| 改动shell的bash-n/可用ShellCheck | PASS；固定native fixture脚本；无host安装 |
| provenance后默认host smoke | FAIL：runtime1254 tests，7 failures/9 errors；OS mode纠错前快照 |
| OS mode纠错后固定Python3.9 unit | 80 PASS：toolchain62+profile18；不与77或native相加 |
| 最新默认host smoke | FAIL exit1：source guard发现origin/main推进3提交，runtime discover未到达；不得引用1254为此快照的全量结果 |
| native完整冻结语义/同FD执行对象绑定/observer/资源/其余可信链/旧回归迁移 | GAP/pending，T02未完成，T03 pending |
| kernel ES、签名/资格、root registry/state/service/socket/镜像、installed/remote/PR/merge/deploy | NOT RUN |

两份source增量均两轴hard0/smell0，partial为明确披露的能力GAP；审阅只读，未放宽执行门。
首次OS候选green因独立fixture漏复制config出现1error，原日志保留；补齐fixture后62 PASS，
actual owned source再实跑80 PASS。不存在删test/skip/统一CUSTODY_GAP制造通过。

期间本地tracking ref被观察到变为
`e2edb3e08194624a6647212571c6cc866298575b`（#334/#335，新增3提交），
本owner未执行fetch/merge/rebase/reset/改变获准pin；实际HEAD仍C9，branch ahead9/behind3。
不遵循installer诊断输出的追main/rebase建议；当前staleness失败与Mac安全证明待裁决并列保留。
SDK未发现fexecve/execveat声明，UID501的/dev/fd exec探针实际EACCES；这不证明所有技术均不可能。
canonical interpreter与held FD的kernel exec核对方案仅为待审security proposal；
不能在AGENTS:15安全决策明确前自行把事后身份核对当同FD执行，T09候选三合同未应用。

当前owner worktree治理17文件/owner/index/installed两文件保持；共享checkout已从原5c2移动到
上述e2edb3e且clean，这是本轮只读观察的外部基线变化，本owner没有对共享checkout执行写入。
4 source增量与本节证据外，
其余28 WIP原字节/mode保持。全部before/candidate/after hashes、red/green、smoke及备份在
`/private/tmp/aisoft-327-contract-evidence/t02-after-t08-fresh/`，完整原33 tar/governing17 tar/C9 bundle
已保全。无本次source commit、远端写、host enable或新批准记录。停止后续runtime推进，保留可恢复WIP。


## 2026-10-05 本人接受收缩后的治理与保全（当前，取代旧运行前置）

本人的一次定向续办明确接受最小 Git 收缩；不是 T10 批准重放。上文为原始分层历史证据，FAIL/GAP/NOT RUN 字节正文保留；root authority、R02 qualified program、ES/kernel/signing、完整 OS/解释器闭包及 scratch/resource/AC-9～11 改为明确延期，未交付、未验收，不改成 PASS。原 AC-7 两机 installed/authority 验收也延期，source 与 installed 不混淆。spec/plan/summary 的当前段落为本次范围事实源。

- before HEAD `f8750441f3dce96f3b9a24a134f877ad1cf6aa35`、tree `8f6935ca1b59f13ea2c0f36b4530b18eee75c3a9`；fresh canonical main `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853` 尚未整合。
- 恢复证据根 `/Users/benque/.codex/visualizations/2026/10/02/01a0fcec-eb78-7790-a36a-daea917f43d2/issue-327-convergence-20261005`；`preservation.json` 绑定 HEAD bundle、refs objects pack/raw refs、raw index、33 WIP tar、17 治理 tar 和 5,721 个原证据条目的完整 archive/hash/mode/uid/gid。tar 每 member、独立 bare HEAD/parents/tree/ref targets 与复制 index entries 已真实 PASS；没有恢复 writer/删除/reset 原文件或 refs。
- fresh `capability-readback.json`：repo role `aisoft-platform-agent` non-admin pull/push，manifest-fixed origin/helper 存在；main 禁直推/force，仅本人 admin merge，required `CI / verify (pull_request)`。installed broker 模块 SHA256 `c865bd757a6213673d55e39dc64be46dfb02022e9baf76065f95849cb9a78260`；仍 lease-force/blanket merge deny，begin/verify/bootstrap 缺失。旧 T10 的 installed 字节仅是当时事实，不能冒充今日状态。
- 本次 `git.fetch.change` 为 HOST_COMMAND_FAILED；exact #327 ref、R0/R 仍 GAP，不推断 absent。只读 host transport/main fetch PASS，不表示发布能力 PASS。first manual Git transport 的既有 helper/ACL 是可用入口，guard/ordinary FF/真实发表仍须 T02/T03 与最终第二确认实证。
- full-ref identity 实际 FAIL：观察到 unrelated #339 branch 前进及 codex turn-diffs namespace 变化；actor attribution GAP。owned #327 branch/main/tracking 与 raw index/source 当时保持，未触碰/恢复/prune 这些外部 refs；原 T10 full-ref FAIL 也保留。不宣称全部共享 Git metadata 不变。
- 本轮只收缩原 14 活治理消费者＋四 mapped docs。verification 本来未提交的历史证据正文完整保留并随治理提交；32 个源码 WIP 仍原 bytes/mode/uid/gid，未运行 runtime/bare-remote Git feature tests/default smoke/Controller/provider/OS/root/签名/安装/服务/Secret/远端写/PR/merge/deploy，均 NOT RUN。
- 文档/graph/staged/parent/tree 的实际执行与最终治理 G 在本证据根 `governance-stop.json` 记录；只有实际成功才报告 PASS。T02 保持 in-progress，T03 pending，本輪治理成功后 STOP。下一具体本人操作为 `human-first-main-integration.md` 中只本地的标准 Git 整合；不再等待未交付 R02。

当前 AC-1 仅本轮治理/保全子项可验；AC-2～6/8 最小 Git/source/CI/首次发布尚未完成；AC-7/9～11 DEFERRED 并保留原 GAP/NOT RUN。最新 smoke 仍 staleness guard 失败、runtime NOT REACHED；旧 1254 tests/7 FAIL/9 ERROR 原样保留。延期不是 skip 原 required 门或测试通过，source/local/CI 仍不能证明 installed/live。


## 2026-10-06 人工 main 整合预检停止与 README 对齐候选

- 实际 HEAD 仍为 4f7d2c29122a559c640c8d46837bd9df37a101b7，branch/owner 不变；本人 fetch main 为 c9b5ef4e74592cbc68d6bdc6219568a1d51b6853。原 32 源码 WIP 已 park 于不可变 stash 4888c0345a90ab76560f33172dd9923f79c3a988，其第一 parent 为治理 HEAD；bundle heads/verify 实际 PASS。stash 的 32 文件 bytes 与执行位已逐项匹配原保全记录，stash index 对应原治理 HEAD。原 tar 的完整 mode/uid/gid 仍为恢复事实源。
- 原 merge-tree --write-tree 预检在 set -e 下以 1 停止，stdout 被收进变量，未显示冲突原因。实际 merge/整合 commit 尚未运行：HEAD 未变、index/工作区 clean、无 MERGE_HEAD/unmerged；clean 只表示 WIP 已 park。
- 独立临时 object directory 中对原 G/M 连续两次复现，均 exit 1、stdout SHA256 相同。仅 README.md 的两个段落冲突：旧六仓与 main #337 恢复 HSDB 后七仓的说明、本票 #327 收缩说明。诊断期间原 index/refs/owner/worktree 未变。诊断与候选位于本 owner evidence 的 diagnostic-human-preflight-20261006-2pwsjf8z/，未修改原执行文件或旧治理 STOP receipt。
- 未应用的 README 候选保留完整 main README，并把原 #327 收缩段正文移到独立第 8 章；包含七仓/HSDB source、private/manual/required CI/安装与 adoption 边界。第一版原位置候选的文本预检仍冲突，已保留其失败输出。编号修正前的第 7 章保留候选对共同基线与 main 的 git merge-file -p 文本预检 exit 0，输出等于该历史候选；本轮第 8 章候选亦实际文本预检 exit 0，stdout SHA256 为 ee66d6cb9d4f5dbc98b0059a336300affcdfe2cedce1c552cc743cc347466757，等于本轮 README bytes，输出保留于 alignment-current-README.text-preflight.stdout。两次结果各自只证明其文本候选，不证明完整 main 整合、runtime/CI/安装/发表。
- 原冲突停止要求保持。候选仅 README.md 与本 verification 的真实事实回填，等待本人确认后才独立本地线性文档 commit/STOP；之后重试限定无冲突 main 整合。原 stash/bundle 保留，不重复首次 stash、不重 pin R0/R；所有旧 FAIL/GAP/NOT RUN 保留。

授权回填（2026-10-06）：本人在本 owner 会话对“只对齐 README、回填 verification，并本地线性提交后 STOP”明确回复“确认”。本次只落实这两份文档；既有 stash/bundle 与延期边界保留。后续本人标准 Git 的 main 整合、runtime/CI/发表/安装仍 NOT RUN。

两文档 checkpoint 的链接边界：完整 main README 中引用的 #337 verification 在 exact M c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 中存在，当前治理 G 工作树尚未带入该文件。本次只对齐两份文档，不复制第三文件；此相对链接在本地对齐 checkpoint 暂记 GAP，待本人整合 M 后核对闭合。#327 resolver/graph 文档检查不代表 README 全部相对链接已闭合。

## 2026-10-06 人工整合完成后的 fresh T02（计数补充前历史）

本节覆盖前文的旧“整合/runtime 尚未运行”状态，保留原 FAIL/GAP/NOT RUN 的时间和证据。本 owner 收到本人实际整合回执并核实 HEAD `3052a8a0d47a8c7333f06e073ca5a4ecc1047a90`，parents 精确 `[1078e4aead52020b49a91cc97b118245f7d972f1,96ba8a17baad8e9854d4e8d0397d4162b8067b09]`，tree `0c5243d46a4a53006b7e50ff4acc9cc6e5b7e2a9`。后续定向续办已授权 fresh T02 到下一真实人工确认/操作点；原 owner/branch/worktree/manual 保持，没有 Agent 实际 merge/rebase/cherry-pick/reset 或真实远端写入。

本轮证据根：`/Users/benque/.codex/visualizations/2026/10/02/01a0fcec-eb78-7790-a36a-daea917f43d2/issue-327-convergence-20261005/t02-minimal-git-fresh-20261006-5r33dgqe/`。`baseline.json`、`source32-reuse-deferred-map.json`、全部原 blob/补丁与 `parked-source32.tar` 可恢复；32 原源码 bytes/mode/uid/gid 全部核对 PASS，9 直接 Git WIP 复用、23 authority/ES/closure/scratch 等延期。stash `4888c0345a90ab76560f33172dd9923f79c3a988` 与原 bundle 保留，没有 pop/drop/clear 或重 pin。原 tar SHA256 `94f0044226f9a8c4c816024584d9cc322dad88bdec1a1ada105887b6fdeafee7`；首次 tar 的 uid/gid 元数据不匹配失败也另存，第二 tar 按原 metadata 核实，不覆盖失败证据。

| 实际检查 | 结果 | 同证据根文件 / 边界 |
|---|---|---|
| fresh installed broker Issue/comments/onboarding 与 fetch main | PASS（只读） | live Issue open、comments 空、仅 triage/needs-triage；main M 仍 `96ba8a17...`；main 禁直推/force、required `CI / verify (pull_request)`、routine disabled |
| installed `git.fetch.change` | GAP / HOST_COMMAND_FAILED | `installed-readback.json`；R0/R 未取得成功读回，未推断 absent |
| 原 32 源码和 stash/bundle 恢复保全 | PASS | mapping/tar/原 patches，原 bundle SHA256 `8ff92fec2b6936218f8d85baa59acf7fbb1550fd07b01ba15163d6a816b62677` |
| actual H0 relevant DAG/tree/逐 commit scope | PASS_LOCAL_HISTORY_ONLY | `actual-h0-complete-relevant-history.json`；14 commit；R0/R unknown，不当真实发布资格 |
| 首轮 107 项 targeted Git/owner/Controller/broker | PASS | `git-owner-controller-broker-repaired.log`；真实临时 bare remote 与实际 guard/普通 push |
| 双轴 hard 修正后的 96 项 targeted | PASS | `git-hard-review-regression.log`；R0 absent 抢占重试、pending candidate 失败重试、actual/possible 回执/no-op/main 前进 |
| 固定源码 full runtime discover（严格 `-t codex/runtime`） | PASS，1140 tests | `runtime-discover-stable-source.log/json`；Python3.14.4；before/after 源码 hash 一致 |
| `/usr/bin/python3` 核心回归 | PASS，94 tests | `minimum-git-python39-stable.log`；Python3.9.6；不外推全部 runtime 在 3.9 通过 |
| 已修改 shell 的 bash-n/ShellCheck | PASS | `shell-static.log`；未执行 host 安装 |
| 默认 `bash codex/tests/smoke.sh` | FAIL，runtime NOT REACHED | `smoke-default.log`；level/install-vm 实际 modules=34，旧测试预期=33；不 skip/改变来源闸门 |
| Spec/Standards 双轴增量 review | hard=0 / hard=0 | 此前三项 P2 已闭合；Standards 仍有一项 nonblocking possible Duplicated Code；review 不代替测试/最终 commit 审查 |
| source commit、T03 exact publish candidate/guard command | NOT RUN / PENDING | 待范围内全部门完成后本地原子 commit；current HEAD 仍 H0 |
| 真实首次普通 FF、唯一 PR、新 head/base CI、本人 merge | NOT RUN | 第二确认尚未到达；没有 push/PR |
| installed 新模块、两机 FF/root/OS/启用/服务/部署 | GAP / NOT RUN / DEFERRED | 旧 installed broker SHA256 `c865bd757a6213673d55e39dc64be46dfb02022e9baf76065f95849cb9a78260`、新模块 absent；源映射测试不代表实际安装 |

最小源码已实现：committed mapped scope、完整 relevant 第一父 DAG、独立真实 merge-tree、逐 commit delta、R0 不重 pin、fresh M/R、单 SHA/单 ref ordinary FF、固定 pre-push 的实际 advertised old-id 和执行回执、server 后窗口、truthful no-op/actual/possible H 与 Controller 重试保全。测试中的 Git merge/rebase/remote writes 仅发生在临时 fixture 仓库。中文目录属性扫描使用 NUL 路径；标准 worktreeConfig 的 active 配置同样核验；`fsck --strict --no-references` 只关闭无关整个 ref-db consistency，仍验证对象/hash/连通性/缺 blob，精确分支/main 在 route/guard 单独核对。实际共享 `refs/.DS_Store` 失败、worktreeConfig 初次过拒绝与所有修正前日志保留，未删除共享 metadata。

首次 full runtime 为 1137 tests / 1 FAIL / 9 ERROR，保留 `runtime-discover-default.log`：运行中源码修正触发 guard hash 漂移；另有 tracker 两 consumer 的不同相对链接与旧 byte equality 不一致。修正为先核两个链接真实目标一致、存在，再保持其余 bytes 比较；固定源码后全量重跑如上。原 1254 tests / 7 FAIL / 9 ERROR 与旧 staleness guard FAIL 继续保留，新的 PASS 只对应本节固定 source。

当前真正人工断点仅为 **范围补充**：默认 smoke 的 `codex/tests/test-installer-source-guard.sh` 不在 current exact 23 路径；一行 `expected_runtime_modules +2`→`+3` 补丁已保存为 `source-guard-fixture-count.patch`，已请求本人批准新增该 exact 测试文件。未应用或修改 `codex/lib/install-source-guard.sh`，不降低其 provenance/staleness/写入前门，不把默认 smoke 报成 PASS。T02 in-progress、T03 pending、verification pending；当前源码和证据保全等待补充，不重复已完成人工 main 整合，也未请求发表/安装批准。

## 2026-10-06 来源计数补充后最终 source/local 验证（当前）

本人直接“确认”已绑定仅 test-installer-source-guard.sh 预期 +2→+3；补充凭据为同证据根 count-fixture-human-approval.json。24 允许路径、22 实际变更；不修改 codex/lib/install-source-guard.sh 或本轮治理消费者。

当前结果（完成全门后回填）：本人已确认来源数量 +2→+3；24 允许路径、22 实际变更。新受管映射及 installer fingerprints 已同步；默认门不 skip/不放宽 source guard。tracker 比较先核两个 consumer 的真实 #327 spec target，再严格比较其余 bytes；不改治理消费者。

增量双轴审阅修闭合：旧/mixed installed broker 在启动写入口前以固定 wrapper SHA 和相关 dispatch/FF 受管文件核对拒绝；仅 cooperative version binding，不声称 OS/root closure。净化环境保留经过格式校验的 owner session。LocalGit 与 typed runner 对 malformed/partial/bad-encoding/timeout 回执保留 bounded 候选 H 与 possible_write/UNKNOWN，不保留未知字段；未读回前不能盲重推。

原错误持续留档：smoke 旧 count 失败；count 修正后的 installer mapping stale；sandbox localhost bind PermissionError；host runtime 1140 PASS 后旧 tracker cmp 失败；qualified v1/v2 为等待晚到审阅修正受控终止，exit -15、stable true，非 PASS。最终固定 source 的原样默认 smoke 和 Python3.9 核心结果单列；不从历史 PASS 推断当前 full gate。

T03 当前准备 source candidate 与只读 R0/R entry；旧 installed broker 未更新、新模块 absent、R0/R 缺成功 exact ref 读回。唯一 open-PR 读回为 0（open 完整页）；all-history 50 条是 first-page-only GAP，不能证明全部闭合 PR 不存在。不给 #336 新硬依赖。下一真正人操作只是一条固定 SHA/read-only standard Git 精确 ref 读回，零 fetch/push/owner 写；其回执不是发表授权。得到 R0/R 后才形成 exact-R/H guard/publisher 与唯一最终 PR 第二确认。

| 最终固定 source 实跑 | 结果与边界 | 同证据根 |
|---|---|---|
| 原样 bash codex/tests/smoke.sh（host 隔离 fixture） | PASS exit0；full runtime 1146 tests，strict -t；源码 before/after hash 一致 | smoke-default-qualified-v3.log/json |
| /usr/bin/python3 核心回归 | PASS，98 tests，Python3.9.6；不外推完整 runtime 在3.9通过 | minimum-git-python39-qualified-v3.log |
| mixed dispatch / partial、invalid JSON、timeout、UnicodeError | PASS；19项 dispatch 回归及坏编码 seam；实际安装与真实远端写 NOT RUN | dispatch-publication-regression.log、unicode-publication-regression.log |
| 7 修改 shell 的 bash-n/ShellCheck | PASS | shell-static-qualified-v3.log/json |
| 受管 source mapping | PASS；source相对main未合并仍GAP，非installed验收 | source-mapping-qualified-v3.json |
| source 本地原子 commit/最终 H/history/双轴 review | 按原授权完成本地；exact结果在外部候选回执，未在文档自引用H | source-candidate.json、final-review-spec.txt、final-review-standards.txt |
| T03 只读 exact ref入口 | 已准备；R0/R成功读回GAP，guard发行参数尚不能绑定R | human-next-step.md、human-read-exact-ref.sh |
| remote发表/唯一PR/新head+base requiredCI/manualmerge/实际安装 | NOT RUN；第二确认尚未到达 | 历史失败、保护和延期边界保持 |

T02仅当前source/local范围完成，T03in-progress；不把 source test/fixture 安装/普通Git模型 PASS 提升为真实 installed/live/发表。原 owner、immutable stash/bundle 与23延期源码完整保全；没有 Agent 实际 main merge/rebase/reset、远端push/API写或新安装。

## 2026-10-06 T03 实际首次 ordinary FF 与 PR #346（最新）

本人在根 owner 会话明确批准 #327 / change/327-broker-ff-integration / manual，以首次 H=`f97d0d88a99373711a22c44b72d46976cd290638` 执行本人 ordinary FF、owner审计和唯一 PR。批准原文及 hash 保存在本 owner 外部 `human-final-pr-approval.json`；范围内操作修复沿用原批准，派生记录不声称新增人工回复。此前“未批准/未发表/PR NOT RUN”段落均为历史快照。

证据目录：`/Users/benque/.codex/visualizations/2026/10/02/01a0fcec-eb78-7790-a36a-daea917f43d2/issue-327-convergence-20261005/t02-minimal-git-fresh-20261006-5r33dgqe`。

| 检查 | Result | 证据 / 边界 |
|---|---|---|
| exact ref 初次本人只读 | PASS | human-exact-ref-read-1791260161286000000.json：R known=true/null、M固定；不是发表批准 |
| 首次尝试 | FAIL GUARD_NOT_EXECUTED | human-first-publication-1791261663898846000.json：guard未执行，possible_write=true保留；R0已pin known absent，lastpush未写；不盲重推 |
| 本人诊断 | PASS 读回 / FAIL dry-run | human-publication-diagnostic-1791261870413998000.json：前后R已知null/M固定；AUTHENTICATION_UNAVAILABLE/PYTHON_RUNTIME_IMPORT_FAILURE，不推断账号或权限需修改 |
| helper根因与最小操作修正 | PASS_LOCAL_ONLY | installed CLI 在系统3.9的 Dependency=int或str导入TypeError已复现，现有Homebrew3.14importPASS；helper-only固定PATH合成Git private protocol fixture PASS，未读真实credential/访问网络，未修改installed或source |
| 恢复入口 bare矩阵 | PASS 10 | recovery-publication-real-fixtures.json；创建、缺确认、占用、两竞态、写后main/owner漂移、dry-run失败、helperbinary漂移、无效R0；负例保全/零写，限定临时bare层 |
| 恢复两轴审阅 | PASS hard0/0 | recovery-review-spec-final.txt、recovery-review-standards-final.txt；原symlink P2修复后重验；Standards1个非阻断重复检查建议 |
| 本人实际 dry-run + ordinary FF | PASS_ACTUAL | human-publication-recovery-1791262255723614000.json：dry-run guard PASS；实际单ref exact H、guard_executed=true、write_status=PUBLISHED、actual remote=H/actual M固定 |
| 实际固定guard | PASS | recovery-publication-guard/receipt.json：nonce/hash/input绑定PASS、old-id全零；program SHA256=c8dc785df0496acb48982ceb06068ae65f63d030d8a1acb534a243681630fcf7；hook SHA256=acb665abff5ac97e21807741bc58495ef1876ae0f44f4ebdafa98b00b97ff8f0 |
| owner审计与 typed Git只读 | PASS | R0 known=true/null未重pin；last_push_head=首次H；typed fetch.change/main PASS并读取tracking H/M；actual-publication-validated.json |
| 唯一最终 PR | PASS_CREATED | [PR #346](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/346)，typed broker唯一active门；head=首次H/base=M/open/mergeable，actual-final-pr.json；App attach_artifact对该Gitea URL不支持，PR本身已存在 |
| required CI | PENDING_INITIAL_HEAD | CI / verify (pull_request)，run1801/job2007 queued；PR346-status-first.stdout、PR346-actions-first.stdout；不写成PASS |
| 四mapped docs回填 / final head | IN_PROGRESS | 本次只更新文档事实/PR URL，不改runtime；source全门1146/98/7shell保持原固定H层。文档提交更新同一PR后，final head/base/CI另以外部fresh回执验证，不用initial-H CI覆盖新head |
| manual merge / cleanup / installed/live | NOT RUN | 本人manualmerge后按确定性流程收尾；新runtime安装/采用、OS/root/authority/23延期源码未交付，不能称已解锁其他owner |

T03继续in-progress，verification pending，summary pr-open。原immutable stash/bundle、32源码保全、原FAIL/GAP/NOT RUN以及possible-write回执都保留。本次真实发表证明此本人固定入口/Git路径，不证明旧installed broker已支持新FF、root custody或同UID隔离；没有Agent direct push/API、main rewrite、force或安装。
