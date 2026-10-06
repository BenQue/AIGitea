---
issue: 340
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/340
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on: []
reason: 新增固定目标只读接口及跨 VM 安全边界，属于平台共享核心与治理变更
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-appserver-preflight-read-261006.md
  spec: spec-appserver-preflight-read-261006.md
  plan: plan-appserver-preflight-read-261006.md
  verification: verification-appserver-preflight-read-261006.md
override_reason: ''
status: approved
branch: change/340-appserver-preflight-read
pr_url:
created: 2026-10-06
updated: 2026-10-06
---

# #340 固定目标只读预检：已批准合同与 fresh source 工作

状态：SOURCE_LOCAL_COMPLETE / PR_SUBMISSION_CONFIRMED（Mac 交互路径；尚未 push/PR）。本会话实际本人已确认四份合同、exact tuple 和 manual policy；
T01 在 adbe53252f71474afffdd886ca7509cc75ab0842 应用治理合同并完成 STOP，当前已 fresh 重新读取。
T02–T05 的白名单 source/local 工作已完成；源码冻结点为
83fdd12dc93b79442aae9c0763c7e92e221344d8，完整 smoke 1147 项通过。
T05 只追加本 Issue 证据与交接文档；最终本地 HEAD 见提交后回执。
初次 live 写入曾被自动审批拒绝；本人本轮明确批准后，typed classification/approved 投影已执行，
独立读回为 type/platform、complexity/complex、approved，原 triage/needs-triage 保留；verifier=projected。
本人批准的 exact main 96ba8a17baad8e9854d4e8d0397d4162b8067b09 已 local rebase 整合，
rebase 后 HEAD=0797969955b454a660bedf34858670e2ed7b3c35；九个 frozen source/fixture SHA256 未变。
原 HEAD/T01 由 refs/aisoft/recovery/340/pre-main-integration 保留；六 commit range-diff 全为一致。
完整远端同票 namespace 已补证 PASS：2026-10-06 13:33 JST，23 个现存分支、2 条已删除记录、0 open PR、162 closed PR 全分页无匹配。
本人已确认同一 branch/manual 的唯一最终 PR 提交、必要 FF push 与合同内 CI 修复；真实安装和现场层仍未授权。
[完整 namespace 与最终 PR 授权回执](evidence/final-pr-namespace-261006.json)保留逐页脱敏元数据。

## 问题/需求总结

唯一 Issue：[admin/aisoft-platform #340](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/340)。
来源消费者为 admin/LocalWMS #333，其 owner/session 为 01a10bfa-fa27-7181-beb8-77c72d47ff21。
它继续 systemd-native/v1；本 Issue 补齐指定 AppServer 的只读预检通道。

合同准备阶段（T01 前）的 fresh installed typed broker 读取 Issue：OPEN，content_version=0，
仅 triage/needs-triage，comments=0；独立 comments.read 返回 []。
合同准备时 source 与本机 installed host-access-broker.json SHA256 均为
509bdffb34494cbf82ef016d96e519c6bc3a17034a68ea052a516121aca4a8b9，
当时均含 38 个操作、固定 mac_host.orbstack_machine=gitea-ci，没有目标预检接口。
当前 source 增至 39 个操作，installed 未修改；新增接口只提供安全拒绝与隔离 fixture，
真实 VM no-start primitive、native Docker read 仍 GAP，目标执行次数为零。
这是本次 manifest 的精确观测，不表示整个安装面逐字节一致或 AppServer 已可读。

## 基线与归属

| 项目 | 本次事实 |
|---|---|
| owner/session | 01a10e8e-9128-7fa2-97a8-6493ee84be08，local |
| branch | change/340-appserver-preflight-read |
| worktree | /private/tmp/issue-340-appserver-preflight-read |
| semantic directory | docs/changes/340-appserver-preflight-read/ |
| T01 前 fresh baseline / HEAD | c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 |
| baseline 来源 | installed git.fetch.main 在 host 成功，随后本地读取 origin/main |
| remote | origin，http://gitea-ci.orb.local:3000/admin/aisoft-platform.git，fetch/push URL 一致 |
| 本地归属 | 已创建单一 tuple 并成功 claim；last_push_head=null |
| 调度台账 | issue-sweep.json 中 #340 唯一 owner 是本会话；未修改调度台账或恢复 heartbeat |
| main 保护 | push=false、force=false、merge whitelist=[admin]；required CI=CI / verify (pull_request) |
| repository policy | public-platform；change_control 未声明，按 production；routine_auto_merge_enabled=false；manual |

本地完整 worktree/ref、Git history/docs 和调度台账未发现第二个 #340 tuple/owner。
准备/fresh T02 的 installed gitea.pulls.read(state=all) 只返回最新 50 条，
其中无 #340；该有界读取不是全历史/全分页完整性证明。#341 已合入上述 fresh main。
候选 exact branch 的 git.fetch.change 在 sandbox 为 TRANSPORT_ERROR，在 host 为
HOST_COMMAND_FAILED；不能把该错误解释成远端无分支。该历史 GAP 后由本人明确批准的一次性已登录浏览器读取补齐：
branches 两页、closed PR 九页和空 open 结果全部核对，change/340 与 change/340-* 无匹配。
继续前 fresh 核对已有证据；任何实际 owner/同票 tuple 冲突立即 STOP，不能新造别的 slug、
接管或为此修改本 Issue 以外的 broker。尚未证明的远端唯一性不得写成 PASS。

## 初步方案与建议

增加一个 non-mutating typed operation：application.target.preflight.read。
caller 只能提供 --project localwms 和 --target localwms-local-test；
strict manifest 唯一派生大小写精确 AppServer、固定 operator/helper、路径、字段及 limits。
旧 gitea-ci VM/profile 操作、Gitea identity/ACL/credential route 和项目集合保持原语义。

最小实现由现有 broker、一个固定目标预检模块、一个固定一次性只读 helper 构成。
不新增常驻服务、helper 链、通用 shell/SSH/sudo 入口或新审批状态机。
helper/operator 不存在、权限不足、目标停止或无法证明不会自动启动 VM，都返回明确 BLOCKED/GAP。

固定字段、路径、限制、兼容和验收的完整合同见
[spec](spec-appserver-preflight-read-261006.md)，票据与允许 touch points 见
[plan](plan-appserver-preflight-read-261006.md)，事实与未执行项见
[verification](verification-appserver-preflight-read-261006.md)。

## 风险

- 当前 orb run/exec help 没有 --no-start 参数，官方文档也未给出“不启动 VM”的保证。
  running 预读不能消除检查后停机的竞态；源实现必须证明执行 primitive 不会自启，
  否则拒绝 target execution，不能用停止后再停回去掩盖 mutation。
- 推荐固定独立 operator=aisoft-preflight，禁止 root/sudo/docker group 和身份 fallback。
  这是 source binding 候选，现存账户、权限和 helper 可用性尚未验证；不在启动批准内创建。
- npm --version 可能读取配置/产生缓存；helper 优先只读取固定 npm package.json 的 version
  白名单字段。固定 binary 版本调用必须先验证可信 owner/mode/路径与受限环境。
- Docker socket 权限可隐含写能力；只读操作合同不等于凭 OS 用户强制 read-only。
  无现存获准访问就 BLOCKED，不加入 docker group。PG 实例/角色默认 BLOCKED，
  没有已获准非 Secret 读取通路时禁止尝试连接、读取 .pgpass 或借 postgres/root 身份。
- filesystem atime、系统 audit 等附带行为和完整保留对象 before/after 尚未验证；
  “helper 不发起业务/主机配置写操作”不能升级成“整台 VM 全对象零变化”。

## AI 判级

~~~yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增固定目标只读接口及跨 VM 安全边界，属于平台共享核心与治理变更
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
~~~

### 判级证据

- AGENTS.md：新功能、外部契约、安全、共享核心、平台治理强制 complex。
- 03 §1：未声明 change_control 按 production，因此四角色合同需齐备。
- Issue AC4–AC6 涉及安装/live 和一次性真实观察，verification 必须声明。
- canonical governance manifest 与 fresh protection：平台固定 manual，不能 routine-auto。
- 判级经本轮 existing typed broker 实际投影并独立 verify=projected；不等于允许 PR 或部署。

### 缺失的 acceptance criteria 或决策

没有待人选择的产品方案；安全默认是 fail closed。
远端 namespace 已完整核对 PASS；no-autostart transport、operator/helper 权限仍是尚待取得的技术证据，
不是假定已通过的启动条件。无已知 source 实现硬依赖，depends_on=[]；
没有把 #327/#336 或消费者 LocalWMS #333 挂成 AISoftPlatform 产品 hard dependency。
source 工作不得因未来 operator 尚未授权而停止合同分析；现场调用仍须逐项真实阻断。

## 开发启动批准与执行边界

批准对象：仅本 Issue、上述 exact tuple、owner、四份 2026-10-06 合同与 manual policy。
原完整确认卡保留在本会话 visualization 目录；本人确认原文与批准前四文件/卡 SHA256
见 [T01 approval receipt](evidence/t01-approval-readback.json)，全部 hash 核对匹配。

已批准范围：

1. T01 独立、仅修改 06 中本接口治理合同与本 Issue 文档，形成本地原子 commit 后 STOP。
2. 后续 fresh run 重新读取 AGENTS/skills/已应用合同后，沿同一 owner/tuple 完成 T02–T05
   的白名单源码、隔离 fixture、必要本地测试、范围内修复和原子 commit。
3. 只使用 existing CI 的验证要求，保留 Gitea ACL、凭据、main 保护和两个 provider。
4. 验证及真实 classification/base/namespace 闸门均满足后，才停在 AWAITING_PR_CONFIRMATION；唯一最终 PR 的 push/提交另确认，
   required CI 全绿后 READY_FOR_REVIEW，manual 合并由本人进行。

允许源码路径、每条既有依据及禁止扩大范围详见 spec §允许修改范围。
T01 的治理 STOP 与 fresh run 是执行隔离要求，不增加同范围产品确认；
不得在同一 implementation run 先改治理再继续实现 runtime。

AC1–AC3 须通过拒绝先于 target execution、停止/竞态/no-start、Secret sentinel、
资源超限/超时/完整性和旧操作回归。AC4–AC6 另分 source、本地、CI、installed、live：
安装、operator/权限变更、fresh live 以及部署均未执行，未授权层保持 NOT RUN，
source 合并不能解除 LocalWMS #333 的现场前置或宣称六项整体 PASS。

回滚：未 push 的 source 用本 owner 的追加 revert commit 恢复，保留 claim 与证据；
无目标写入所以没有本轮主机回滚。未来安装必须在单独卡内绑定 exact merged SHA、
文件/权限清单、真实 snapshot restore 与 installed bytes/readback，不以 source revert 代替。

本会话实际本人确认原文（2026-10-06）：

> 确认 AISoftPlatform #340（change/340-appserver-preflight-read，manual）的四份
> appserver-preflight-read-261006 合同，批准本会话 owner 完成 T01 治理合同本地提交后 STOP，
> 后续 fresh run 重新读取后继续合同白名单内的 source 实现、本地 fixture/测试、修复和 commit。
> 不批准 push/PR、merge、正式安装、operator/权限变更、Secret/DB/服务/容器写入或部署；
> 唯一最终 PR 另确认。

T01 run 已止于本地治理提交。当前 fresh run 已重新读取合同/归属，继续原批准源码白名单；
本轮另批的 live 分类/approved 与本地 rebase 已完成，使用真实读回，未提供 synthetic labels。
当前已完成 source/local、标签/rebase 和完整 namespace 补证；未运行或伪造 Controller candidate。
本次实际本人已另确认唯一最终 manual PR，见 evidence/final-pr-namespace-261006.json 的逐字授权。
采用 Mac 交互路径，fresh 验证候选后由 installed typed broker 推送同一分支并创建唯一最终 PR；
实际 PR 创建后只在 summary 自动回填 pr_url/status 并形成一份追加本地 commit，随后核对新 head 的 required CI。
required CI 全绿后 STOP 于 READY_FOR_REVIEW；人工 merge、正式安装、权限、Secret/DB/服务/容器写入和部署仍未授权。
