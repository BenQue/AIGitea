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
status: pending
---

# #327 分层证据与 T05 独立治理验收

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
