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
updated: 2026-10-02
status: pending
---

# #327 合同准备、T01 治理、T02 缺口与 T04 补充草案验收

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
| runtime T02/T03 | NOT RUN | T01 后已 fresh 只读重读；发现可信根缺口，无 runtime 实施；新具体合同确认/T04应用/STOP/fresh前置尚未闭合 |
| bare-remote FF/guard/race与完整smoke | NOT RUN | 没有实现，禁止用历史测试当新能力PASS |
| 唯一PR发表、新headCI、manual merge | NOT RUN | 未最终PR批准，pr_url为空 |
| 两机安装、realFF、rollback、原owner采用 | NOT RUN | source尚未实现/合并；需各exact安装批准；未宣称#289已解锁 |

## Acceptance criteria 结果

| AC | 结论 | 当前证据 / 后续闭合方式 |
|---|---|---|
| AC-1 | PARTIAL | 原四角色/T01/STOP 与 fresh T02 read 可核；本次新四角色为补充草案，新增具体合同/T04 未批准或应用；live 投影 GAP |
| AC-2 | NOT RUN | spec已定义正向路径；新实现/bare remote证据未产生 |
| AC-3 | NOT RUN | strictR竞态方案和fixture场景已写，不能以普通FF推导race通过 |
| AC-4 | NOT RUN | 负向矩阵已写，未实现/执行 |
| AC-5 | NOT RUN | 回执/freshness/全量smoke待实现 |
| AC-6 | PARTIAL | UI入口已观察；tree/mode/uniquePR/newCI/humanmerge未执行 |
| AC-7 | NOT RUN | 两机exact批准/安装/真实FF/no-op/rollback均未执行 |
| AC-8 | PARTIAL | fresh保护/身份边界已读；未来新实现保持及原owner采用待实证 |
| AC-9 | NOT RUN | authority/default-disabled/strict schema/真实 peer/隔离/records/重算/I02 完整注册启停rollback均只是提案；不能把文档或 mock 当真实可信根 |

## T01 批准与验证记录

- 授权来源：本聊天负责人直接“确认”，绑定 #327 / `change/327-broker-ff-integration` / manual；记录时间 2026-10-02T22:28:43+08:00。只启动独立 T01，验证和本地 commit 后立即 STOP。
- 治理前态/授权/清单保全：`/private/tmp/aisoft-327-contract-evidence/t01-before-governance.json`、`t01-approval.json`、`t01-governance-paths.json`。本提交 SHA/parent/全路径与 STOP 由外部 `t01-stop-receipt.json` 读回。
- 文档门：提交前重新执行 resolver、全仓 semantic document check、四角色状态/双份判级/8 AC/Ticket graph、精确 18 文件范围、runtime/install/config 与 HEAD 字节相等，以及 `git diff --check`。上述文档/范围检查 PASS，详细输出与所有文件 SHA256 见外部 `t01-validation.json`；不能把文档检查当 runtime 测试。
- 无 shell/Python/runtime/installer/manifest 实现改动；bare-remote、unit tests、完整 smoke、远端写入与 installed 验收均 NOT RUN。
- T01 本轮 STOP；当时计划后续 fresh run 从 T02 继续，并重读新治理、Issue/评论、spec/plan、批准和 installed 能力；该次原范围未新增合同确认点。后来 fresh T02 发现的具体可信根扩展另见下一节，不能继承此句批准。

## T02 fresh 分析与 T04 补充准备（本次）

- fresh T02 的 T01 治理 14 hash、Issue/comments、main 与保护已核对。HEAD 为原 T01；main=`65268ee5f1e622c486fd9e354dd35e20a2900f91`。Mac source/installed broker 同 hash，仍旧 leased code；VM 完整 bytes 未执行。
- 隔离 fixture 真实复核 current Controller：`#327 T02` subject + declared path 能通过现有 complex gate，虽文件不在 #327 exact scope；同一 object 可被不同 Issue ref 指向。这是**现有门的 GAP**，不证明真实外 Issue 创作或 live 攻击、不证明新门通过。见 `/private/tmp/aisoft-327-contract-evidence/t02-provenance-gap-proof.json`。
- 授权来源是本聊天 human literal“按建议继续”，只选择 A 路线并准备具体可信根合同。其他聊天提供的批准台账不代替人批准新权限/文件/运行接口；不虚构本聊天消息 ID。
- 本次只修改 summary/spec/plan/verification 四份草案。T01 已批准的 governing 14 文件、runtime/config/installer/service 全部与原 T01 保持相同；无新身份/Secret、root state、socket、服务或 live mutation。
- 补充完整写入 spec：固定 authority、trusted-critical/root 与非 root provider/真实 OS 隔离、peer 不等于程序、人类业务批准到 protected grant 的独立登记、逐对象/完整 scope/内容目的、两项 typed 操作、default-disabled、exact source 扩展、I02 card 与新增 AC-9。新具体合同待审阅，T04 pending；本次不标 approved 或 T04 completed。
- 文档/范围门：PASS。实跑 resolver、semantic document check、四角色状态与双份判级、9 AC/graph/22项新增映射、exact 四文件 diff 和 `git diff --check`；其余 1198 个 tracked 文件 bytes/Git modes 保持，其中14个 governing 文件还逐项核对原 T01 receipt 的 SHA256。结果保存为外部 `t04-proposal-validation.json`；这不是 runtime 测试。
- 具体确认须绑定本次提案 commit/spec+plan hash、#327 / branch / manual；确认之后才执行独立 T04 治理文本应用/local commit/STOP，再后续 fresh T02。不因路线选择跳过新增合同确认，也不新增 A/B 路线问题。

## 前后证据与安装回滚模板

每台主机独立记录：批准的人/消息/目标/版本source SHA；installed roots；文件before/after SHA256、mode、owner；缺失前态；source/installed比较；typedFF H/R0/R/M；remote写前后读回；requiredCI/main保护；no-op与失败rollback；完整旧态恢复读回。不记录token/path contents/auth headers。

本地bare-remote回归不能代替真实安装FF；真实已有Issue若需采用，由其owner带自身批准/原remote tip完成，不由#327代操作。缺真实可用目标时记录GAP并等待exact验收安排，不默默创建live canary。

## 遗留风险与未完成项

原 T01 已完成并停止；本次只是可信根补充草案准备，非 T04 应用、runtime 或 Issue 完成。等待本份新增具体合同确认；没有 runtime、push、PR、live 标签、install、credential、protection apply 或 deploy。AC-7/AC-9 在 source 合并后仍须真实闭合；自动closed不当completed。不用已知历史PASS消除当前GAP。
