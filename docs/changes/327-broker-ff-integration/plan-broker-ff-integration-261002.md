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
status: approved
---

# #327 最小 Git 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 历史：独立原治理应用/commit/STOP | - | completed |
| T04 | 历史：可信根合同治理应用；相关能力现已明确延期，不表示验收 | T01 | completed |
| T05 | 历史：资源/工具链合同治理应用；能力延期，旧失败保留 | T04 | completed |
| T06 | 历史：canonical main 治理同步，随后 R01 checkpoint 保留 | T05 | completed |
| T07 | 历史：固定 Python3.9 兼容治理与后续已提交四行保持 | T06 | completed |
| T08 | 历史：Mac observer/签名治理；能力延期未验收 | T07 | completed |
| T09 | 历史：Mac interpreter 绑定治理；能力延期未验收 | T08 | completed |
| T10 | 历史：七文档治理 commit f8750441 后 STOP；旧 M 未整合 | T09 | completed |
| T02 | 最小 FF/DAG/tree/strict-R/owner/Controller/受管映射完成；原样默认 smoke（runtime 1146）、Python3.9 核心 98 与 shell/source mapping PASS；固定最终本地候选见外部回执 | T10 | completed |
| T03 | 原exact提交批准保留；本人首次FF/PR346初始CI、本地新main two-parent整合PASS；原样默认smoke/runtime1181、Python3.9核心100、两轴hard=0与更新入口8barefixture PASS；本地事实回填后同一PR普通FF/final CI/manual merge与收尾待完成，旧FAIL保留 | T02 | in-progress |

## 本轮与最短后续

本轮 exact 18 文档由 spec 列出；不混源码/config/installer/CI。verification 原 WIP 历史证据纳入文档，32 源码 WIP bytes/mode/uid/gid 保持。文档 resolver/semantic/graph、链接/范围/历史保全、staged tree/单 parent 与恢复校验真实通过后本地原子 commit 并 STOP；不新增 T11 或再问同一收缩批准。

1. 本人按 `human-first-main-integration.md` 在原 worktree 校验治理 G 与 fresh M，临时 park 32 WIP，保存不可变 stash SHA/bundle，标准 `--no-ff --no-commit` main merge；无冲突后仅本人 commit `[G,M]`。冲突 abort/保留恢复证据，不 pop/drop/reset/自动解决。无需 R02/authority/OS 能力，无远端写。
2. 下一 fresh T02 重读实际治理与新批准/Issue/source/installed，按 stash SHA 恢复和复用最小 Git 相关 WIP。main #337 的既有 config/test 变化保留；延期代码/测试以精确保全映射 park，不删除/skip 原 required 门。source 与旧 unsigned/mock/root/OS 证据分层，不用 clean checkpoint 充当修复。
3. 完成 spec 精确最小 runtime/测试/安装映射；运行真实 bare remote 正反向/两窗口竞态、owner/Controller/Git 回归、全 runtime discover、默认 smoke；shell 改动须 bash-n/ShellCheck。source guard 失败或 runtime 未到达如实写，不制造 PASS。
4. T03 形成一次可执行的本人首次发表命令，绑定 exact R0/R/M/H、fixed guard hash/argv、blob/mode/tree/恢复与唯一 PR；完成最小代码后才进入最终第二确认。本轮未批准 push/PR。确认后本人用现有 manifest-bound helper、固定 guard、exact SHA 单 ref ordinary FF；AI 只 broker 读回/准备，不代绕行。新 head/base required CI `CI / verify (pull_request)` 全绿后本人 manual merge。
5. 当前 source 范围完成后 deterministic 文档/终态/可恢复收尾；延期与 installed GAP 留档，不因 AC-9～11 等延期再建立 source-first 闭环，不抛弃保全 WIP。安装必须 source merge 后另获授权。

## AC 与验证

| AC | 阶段/检查 |
|---|---|
| AC-1 | 本轮文档/授权/owner/保全；future fresh 重读 |
| AC-2～4 | T02 实际临时 bare remote、main integration DAG/tree、ordinary FF、exact R races 与全部负向/provider deny |
| AC-5 | T02 全 runtime discover/default smoke/static，truthful marker/readback/main-advanced/no-op |
| AC-6、AC-8 | T03 本人首次 Git 发表/唯一 PR、新 head/base required CI/本人 merge/恢复；main/身份/owner 不变 |
| AC-7、AC-9～11 | DEFERRED / GAP / NOT RUN；原安装/root/closure/scratch/observer失败原样保留，不纳入当前 source PR 前置或宣称通过 |

无 schema/数据迁移、root/Secret/账号/全局安装/服务/部署或 provider 启用。source helper 映射不等于 installed；read-only transport 与 push ACL 不等于真实新 broker FF。缺实际能力给出一项标准 Git 人工操作或具体 GAP，不建设另一层执行系统。

## 2026-10-06 fresh T02 计数补充前断点（历史）

本人标准 Git main 整合已完成，无需再次执行旧人工卡。fixed-source runtime 1140 项、Python3.9 核心 94 项、bash-n/ShellCheck 与 actual H0 的 14 relevant commit DAG/tree/scope 均 PASS。默认 smoke 在 `test-installer-source-guard.sh` 旧数量断言停止（实际 34、预期 33）；原完整闸门保留，runtime 在该次 smoke 内 NOT REACHED，单独 runtime PASS 不覆盖 smoke FAIL。该 exact 测试文件的一行 `+2`→`+3` 补丁待本人范围补充，尚未修改或提交。

获得补充后只应用已准备的一行 fixture 映射，重跑默认 smoke 和文档/范围/保全门；全部通过后做原 owner 本地单 parent 原子 commit 与最终双轴复核，再续 T03。首次真实远端 exact ref 成功读回、发表命令与唯一最终 PR 第二确认另按既定路径准备；当前不执行 push/PR/安装。

## 2026-10-06 最终 source/local 进度

计数补充已由本人直接确认，仅 +2→+3；未改 source guard。默认 smoke 的后续 mapping stale、sandbox localhost 权限、旧 tracker cmp 与晚到审阅前受控终止全部留档。最小接线增量修复已获两轴 hard=0；固定源码全门通过，按原授权仅本地单 parent 原子 source commit。最终 SHA/tree、完整 relevant history 和正式 fixed-head 双轴结果以外部 source candidate receipt 为准。

T03 保持 in-progress；下一真实人工操作为已绑定 H/M/owner/stash/bundle/程序 hash 的只读 exact ref/main 读回。该入口只执行标准 Git ls-remote，无 fetch/push/owner 写，不构成发表批准。取得成功 R0/R 后才形成 exact-R/H publisher 和唯一最终 PR 第二确认；当前 source 不安装、不发表。

## 2026-10-06 T03 首次发表与唯一 PR（最新）

上述只读入口断点为历史。本人随后已明确批准 #327 / change/327-broker-ff-integration / manual 与 exact 首次 H，并实际完成单 ref ordinary FF。原 helper 在系统 Python3.9 导入 installed `Dependency = int | str` 失败；原 GUARD_NOT_EXECUTED/possible-write 回执保留。恢复仅为同一个 manifest helper 固定现有 Homebrew Python PATH，真实 dry-run guard PASS 后再发表，不改 Secret/身份/权限、不安装。R0 已 pin known absent，恢复未重 pin；actual remote/owner.last_push=H。外部恢复入口 10 个真实 bare case 与 helper 运行时合成协议 fixture PASS，两轴 hard=0。

唯一 [PR #346](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/346) 由 typed broker 创建，initial head=`f97d0d88a99373711a22c44b72d46976cd290638`、base=`96ba8a17baad8e9854d4e8d0397d4162b8067b09`；required CI run1801/job2007 当前 queued。四 mapped docs 只回填实际事实和 PR；同一确认允许合同内 CI 修复及回填，不新增 PR/确认点。更新后核 final exact head/base/required CI 到 READY_FOR_REVIEW，再由本人 manual merge；T03 不提前 completed。原 source 全门与延期/安装边界保持。

## 2026-10-06 T03 PR 生命周期修复与 main 前进（最新）

上段 queued 为创建断点，后续 actual initial CI 已 success。PR 回填 local commit `019cabf9bac4e456fefcf397ed503f086250882a` 保留为首次H的单parent后继；scope 的 approved-only 与既有回填器 pr-open 冲突已在原模块/测试范围修复。summary开放PR须唯一exact Issue/同仓PR URL，spec仍唯一approved；实际回填与bare FF正向、16负向、核心20/全runtime1148及两轴hard=0通过，旧失败保留。

fresh main与PR实际base已到 `000a3f73cd7069f4aef0a202b1a19555014fd887`，默认smoke sourceguard behind10 FAIL，runtime未到达；暂停旧发表入口。原owner本地线性修复提交后，由本人按新固定H/M/三方tree入口做本地two-parent main整合并STOP（checkpoint bundle保全、无owner/remote写）。入口6真实Gitfixture通过，含commit落地后lostreply有限读回；实际整合尚未执行。fresh owner重读并重跑完整默认smoke/历史/文档门后再为同一PR准备普通FF与final head/base CI。原exact Issue/branch/manual确认内的修复与回填不重复询问；PR manual merge、安装/部署仍独立，未提前ready或completed。

## 2026-10-06 T03 实际新main整合与完整验证（最新）

上述整合前断点保留。本人已形成 `6e901201b54a281b235345835c61aad69ae3733f` 的exact `[e102a1689c736da35de2caa06c7e7208329ec65b,000a3f73cd7069f4aef0a202b1a19555014fd887]`，三方tree/完整relevant18/clean/原owner与两bundle PASS；本地入口最终8fixture包括真实旧typed fetch回执与新字段、remote漂移拒绝，actual owner/remote write均NOT RUN。

原样完整默认smoke现PASS，430.52s、full runtime1181 tests、before/after所有被核源码hash相同；Python3.9核心100项PASS。旧smokebehind10FAIL、系统3.9全仓误用FAIL、错误core测试名称调用FAIL均在外部原日志保留。新main已有接线和后继更新入口增量两轴hard=0，8真实bare更新fixture（含默认smoke失败、源码摘要漂移、整合回执漂移拒绝）PASS。

只将当前事实回填summary/plan/verification，本地单parent接在测试head后，代码/配置/脚本/原approved spec不再改。固定最终H、测试源码blob与smoke回执、actual整合回执、完整DAG、R0/R/M、guard/owner保全后，给本人一条普通FF更新同一PR346命令；沿原批准不重复确认。fresh元数据只有一个active PR346，remote仍首次f97、base000a3；后继实际发表/final CI/manual merge/安装均NOT RUN，T03继续in-progress。
