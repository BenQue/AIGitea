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
reason: 改变受控发布与主线整合行为并覆盖历史治理合同，涉及共享 broker、Controller、安全与回滚
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-broker-ff-integration-261002.md
  spec: spec-broker-ff-integration-261002.md
  plan: plan-broker-ff-integration-261002.md
  verification: verification-broker-ff-integration-261002.md
override_reason: ''
pr_url: ''
---

# #327 保留历史的 main 整合与 FF 发布合同

## 审阅入口与当前授权

T05具体安全补充已由本聊天负责人直接“批准”，绑定此前审阅卡#327 / exact branch / manual及spec+plan SHA256；原批准字节与审阅卡hash保存在外部 `t05-application-approval.json`。此前“按建议执行”只准备草案，本次直接批准才授权独立治理应用。summary/spec/plan approved只指source合同，不作live标签或protected grant。

本轮只应用原14治理文件和四份mapped语义文档（18文件），验证/local原子commit后STOP。既有18项T02 source WIP、非范围tracked/untracked与共享checkout原样保全，不混runtime/config/service/新9source或安装。T01/T04历史批准与STOP不改写；T05完成后须后续fresh重读再继续T02，当前T02仍in-progress、T03 pending。

- [spec](spec-broker-ff-integration-261002.md)：已确认64 MiB scratch/256 MiB rootGit/lease/全CONTEXT预算、Python前置完整closure/bootstrap、v2/exact9source、AC-10/11。
- [plan](plan-broker-ff-integration-261002.md)：T01/T04/T05治理分别独立STOP，后续fresh T02/T03；I01文件/I02运行验收分层。
- [verification](verification-broker-ff-integration-261002.md)：真实文档检查及source保全；旧runtime全量/smoke FAIL保留，新增机制/主机/PR全部NOT RUN。
- owner `01a0fcec-eb78-7790-a36a-daea917f43d2`；branch `change/327-broker-ff-integration`；worktree `/private/tmp/issue-327-broker-ff-integration`；manual。
- 本次未安装、创建镜像/卷、mount、start/register grant/service、写远端、提交PR或联系其他聊天。B01/I01/I02依独立exact闸门。

## 问题/需求总结

现行 AGENTS 要求 Controller FF、禁止 force；broker 要求 fresh main 祖先且拒绝 merge commit，却内部使用 `--force-with-lease`。已发表分支落后时，rebase 会丢弃 original remote tip 的祖先关系；保留历史的 main merge 又遭拒绝。#319 已有实际非 FF 发布审计，#289 保全原远端与本地候选。

2026-10-02 fresh main=`65268ee5f1e622c486fd9e354dd35e20a2900f91`。Mac installed broker 与该 main 的 broker.py SHA256 同为 `2c1b05977437f16b461c8db0d41a2ad6947d9df5a929bcc3eaeadd332030da7f`，不是 Mac 该模块的安装漂移。VM 当前 bytes 未通过本次 typed surface 刷新，保留 GAP。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变受控发布与主线整合行为并覆盖历史治理合同，涉及共享 broker、Controller、安全与回滚
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- production / platform 仓库；强制 complex，固定 manual；routine opt-in 不可启用。
- redundancy：检索 host-access broker、Loop Controller、单 writer、06 #136 和 #298 AC-5/6；未发现保留 remote 历史并经无 force FF 的受控路径。
- prior rejection：本基线没有 `.out-of-scope/`；不推断历史上从未否决过。
- claim verification：源码三项互锁、Mac installed 字节相同、#319 事件记录支持；本次没有复现 live 写入。
- category 建议 `triage/enhancement`；state 建议 `triage/ready-for-agent`，仅表示合同准备就绪，不等于 `approved`。
- 问题已由 Issue 与派单固定；无需重新 grill 已决定的 slug、manual、禁止 force 或原 owner 权限。原 FF 技术方向已由负责人确认；原 T01 已完成；原可信根合同已直接确认并应用 T04；本份资源/工具链补充已直接批准，独立T05应用后STOP。
- fresh Issue 只有 `triage/needs-triage`，没有 type/complexity/lifecycle。此次不写 live 标签、不发布评论；只读 `--verify 327` 返回 `projection-missing`，投影是 GAP，不能声称 projected。后续按合同批准后的受控投影与读回复核。

## 影响范围与风险

精确清单见 spec §治理映射与 §runtime 映射。只修共享发布/整合边界及对应治理，保留 main 保护、required CI、exact tuple、唯一最终 PR、单 writer、每次 SHA 锚。

最小路线：owner 本地原子提交 → Controller 在合同内构造无冲突 main 整合 → broker 独立验证 provenance/tree/range → ordinary FF push。泛化 merge、历史重写、冲突自动解决、身份 fallback 均拒绝。

旧 broker 首推亦带 force-with-lease，本 Issue 首次发表必须由负责人本人 Gitea UI 将已验证文件发布到 exact change branch，并只创建一个 manual PR。UI 入口存在；实际 tree 等价、文件 mode 与新 head CI 全部 NOT RUN。Agent 不代 UI 提交，也不调用 direct Git/API 绕 broker。

## 依赖、终态与确认点

`depends_on: []`：#289/#319 为问题来源，不是本变更的硬前置。本变更也不是所有人工 PR 更新的硬前置。若 fresh main 已包含 #319，重新验收；未包含时默认 UTF-8 smoke 的失败应真实报告，不跨 Issue 修复。

合同/启动确认绑定 #327、exact branch、manual。T01 已独立完成；原可信根合同已确认，T04 已独立停止；本轮仅执行已批准T05独立治理/STOP，后续fresh T02。最终唯一 PR 提交另有确认。两机安装各需独立 exact 版本批准，#316 旧授权不继承。

源码合并不证明 installed/live；安装 AC 未闭合时本任务保持可用、不 cleanup/归档、不报 Issue 实际完成。`Closes #327` 自动关闭的处理见 spec §完成边界。

## 可信根补充的具体审阅范围

- default-disabled 的 root verification authority；root 只运行 trusted-critical 代码，provider/verifier 以登记非 root 身份及真实 OS 隔离运行。
- protected grant 与记录绑定批准内容、scope/目的、graph、R0、每次 head/objects/verifier；broker 独立重算。OS peer 只证明 UID，不证明程序或人；caller PASS 永不登记。
- 仅新增 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`，没有 public merge/approve；`git.push.change(branch)` 不变。
- source 精确扩展见 spec 新表；新 config 默认关闭/空绑定，service 描述 inert，installer 不 provision/enable。
- I02 每主机 exact 注册/启动/权限/真实验收/rollback 是合并后的独立授权，非本次路线准备许可；新增 AC-9，不继承 T01/#316/泛安装许可。

### 缺失的 acceptance criteria 或决策

原方向及 T04 可信根合同已确认；fresh T02 source WIP 发现 Mac scratch 聚合资源和完整工具链缺口，原A草案经审阅后，新增具体合同已直接批准；本轮仅T05治理/STOP。旧 approved 不授权新增机制，不作为 live 投影或 protected grant。所有真实安装、首次人工发表、回滚与新行为测试尚未运行。远端 #327 ref 是否存在的独立精确读回仍为 GAP，任何未来创建/发表前必须重新查重。


## T06 基线同步补充与当前 frontier

恢复卡 A 后的 source WIP 已增至32文件，T02仍in-progress；native/toolchain定向通过，完整能力仍GAP，
默认smoke被 main 落后87提交的 source guard 拦住，旧runtime失败保留。为继续准备 exact T06 补充，
见 [spec 的 T06 合同](spec-broker-ff-integration-261002.md#t06canonical-main-治理基线同步补充合同)
与 [plan](plan-broker-ff-integration-261002.md)。本补充只有负责人确认 external exact卡后才生效；
旧 approved、恢复卡 A 不授权该新增步骤。T01/T04/T05历史不改。

T05 → T06（已具体确认；7个main治理段落与mapped summary/spec/plan已独立应用，STOP）
→ fresh T02/R01（纯基线main checkpoint，再恢复32WIP）→ T03。原single writer/branch/manual、
AC与source touch points保留。无root/安装/Secret/remote mutation/PR/merge/deploy许可。


## T07 固定 Python3.9 兼容补充与当前 frontier

R01已完成纯 main checkpoint `4cb627d9525611bff34387830978ba5c5785863e`，原32WIP
恢复后增加1个已在scope中的shell fixture修改，当前33项仍未提交。17治理文件保持T06 bytes。
203项source定向通过；默认smoke/native现因main #286模块级类型别名在固定Python3.9下导入失败，
真实FAIL保留。两个文件的四行等价候选仅在隔离副本验证，actual source未应用、未获新增范围授权。

见mapped spec的T07 exact runtime新增与mapped plan的独立治理/STOP步骤；
旧approved和T06/R01不覆盖新增两个文件，须负责人具体确认external卡后执行。
T07（已具体确认；仅 mapped summary/spec/plan 的兼容 scope 已独立应用、提交并 STOP）
→ fresh T02（四行恢复固定Python3.9，继续原source合同）→ T03。
原single writer/branch/manual/AC及B01/I01/I02边界保持，无安装或远端写授权。

## T08 候选安全选择与当前 frontier

T07三合同提交/STOP及fresh T02四行source提交已实际完成，证据保存在mapped verification与external receipt。
source loader两文件增量已核验；208项定向unit/source回归PASS，默认host smoke仍1242 tests/7 FAIL/9 ERROR。
完整closure/资源/可信链仍GAP，T02未完成；本轮实际17治理文件保持。
Mac缺完整后代observer，SDK的kqueue跟踪不可用；拟采用仅自身后代的macOS27+ EndpointSecurity API。
required entitlement及冻结签名artifact是新增安全边界，不能从T07批准或本机版本事实继承权限。
具体约束、private profile v2、exact现有source文件、签名/OS/Root权限边界见mapped spec的T08候选；
无签名来源/accepted kernel证据即GAP，禁止全host observer与TCC/SIP/audit策略fallback。
T08（具体确认后三合同已独立应用、校验、localcommit并STOP；仅治理完成，非observer能力）
→ 独立三合同/校验/localcommit/STOP → fresh T02原source与新observer受控实现 → T03。
本卡不执行签名、申请entitlement、安装、ES client或host enable；真实外部能力保持未来独立exact卡。


## T09 待裁决的Mac执行证明

T08治理已于c9a9154436a8ae3ea277d176389f9854833a74b5独立完成并STOP；fresh T02已继续原source。
当前新增量只绑定三provenance digest到独立held pins，并修正OS只读数据的精确mode期望。
完整闭包/同FD调度/observer与installed能力仍GAP，T02保持in-progress，T03 pending。
Mac interpreter的canonical执行与held FD绑定证明尚需具体安全裁决；参见mapped spec的T09候选。
负责人可以保留严格门，也可具体审阅并决定是否接受该方案的interpreter/loader初始化窗口。
旧T08批准不自动授权后者；source/unsigned fixture与SDK声明均不作kernel验收。
T09（具体确认后三合同已独立应用、校验、localcommit并STOP；仅治理完成）
→ 独立三合同/校验/localcommit/STOP → fresh T02原scope → T03；B01/I01/I02仍独立。
