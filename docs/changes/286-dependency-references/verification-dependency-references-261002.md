---
issue: 286
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/286
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - authorization
  - platform-governance
depends_on: []
status: pending
branch: change/286-dependency-references
created: 2026-10-02
updated: 2026-10-03
---

# #286 · 验证记录

## 基线与范围

- origin/main 与初始 worktree：5c2cd726c9aeaee9d17541d8feb049e33881bbac。
- 环境：Mac 本地隔离 worktree /private/tmp/issue-286-dependency-references。
- session：01a0fc7c-1670-75b2-a61b-f47e62fc856c，claim-worktree=created，未 push。
- 记录一次性改动前证据、T01 治理合同校验及后续 AC-1–AC-7 的真实执行结果。
- 当前 T01 只改文档。不得把原代码误判复现或基线测试 PASS 当成修复 PASS。

## 改动前一次性证据

`parse_front_matter → _dependencies → Controller._unsatisfied_dependencies` 的原代码路径，
依赖客户端使用离线 stub。裸列表项 284 → (284,)；owner/repo#N 与 URL → ContractError。
作者意图外仓 #284 open，但 stub 本仓 #284 closed+completed → current_repo_requests=[284]，
waiting=()，gate_considered_satisfied=true。误判复现 PASS；这是合成场景，不断言真实外仓当前状态。

broker project=aisoft-platform 实际读回 #286 open、needs-analysis，唯一评论是旧部署后再派单。
用户本聊天随后回复“确认”，按推荐 A 和先治理合同后 fresh run 启动；旧调度前置被覆盖，
不推断 NewEMaint #80 实际部署成功。git.fetch.main PASS；初次 gitea.pulls.read(open)=[]。
共享 main 干净，未切分支、rebase 或 commit；T01 不写任何 runtime、shell 或 executable manifest。

## T01 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 原始 parse/Controller stub 复现 | PASS | 本仓同号终态造成外仓意图误判，改动前事实 |
| contract/Controller unittest 基线 | PASS | 67 tests，6.128s，OK；未改 runtime |
| 初稿 resolve-documents 286 / Classification.route | PASS | unresolved/summary-only，当前确认后已升级 complex |
| 初稿 check-change-documents | PASS | 145 changes，gap=0；不是 runtime 修复证据 |
| T01 正式映射合同、load_contract/frontier | PASS | 7 AC、4-role exact mapping、T01 frontier；从 broker 读回实际 approved #286 payload 再 load_contract PASS |
| T01 文档检查 | PASS | check-change-documents：145 changes、gap=0；git diff --check PASS |
| T01 模板 digest | PASS | verify-digest = sha256:2a668ff97054d0ac72b8b63d176460508d4f5e5cc3c00e5841f11b852a2b18c7 |
| T01 分类投影与独立读回 | PASS | --apply 286 updated；--verify 286 result=projected，type=platform、complexity=complex；lifecycle set approved 后 live loader PASS |
| T01 smoke（sandbox） | BLOCKED | exit 1；test fixture bind(127.0.0.1,0) PermissionError，/private/tmp/issue-286-g01-smoke.log |
| T01 smoke（同一命令，受控 host） | FAIL | exit 1；现有 registry-preflight：停掉 registry 后期望 exit 1，实际 0 |
| registry-preflight 单独复跑 | FAIL | exit 1；同样错误，/private/tmp/issue-286-registry-retry.log |
| 独立全量 runtime 基线 | PASS | exit 0；978 tests，88.769s，OK；/private/tmp/issue-286-g01-runtime.log；不代表新增功能修复验收 |
| 本票新增 runtime 修复验收 | NOT RUN | T02–T04 未开始；上述 978 tests 仅为原 runtime 基线 |
| PR CI / installed/live / 部署 | NOT RUN | 本轮无该授权或对象 |

## T01 Acceptance criteria 快照

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 旧行为基线 67 tests PASS，新增格式尚未实现 |
| AC-2 | NOT RUN | 只复现原缺陷，未验证修复后的正确目标仓 |
| AC-3 | NOT RUN | 新 parser/显式权限边尚未实现 |
| AC-4 | NOT RUN | 新 broker/Controller failure fixtures 尚未执行 |
| AC-5 | NOT RUN | 统一 resolver 与双 host adapter 尚未实施 |
| AC-6 | NOT RUN | 跨仓轮询与展示尚未实施 |
| AC-7 | PARTIAL | T01 合同文档；runtime/full gates 的修复验收留给 T04 |

## 遗留风险与未完成项

T01 后必须停止并 fresh run 重读。installed broker 仍为旧 schema，不接受新增 qualified
依赖，不能据文档声称已上线。真正跨仓读取需要后续独立安装授权；本票 source 不扩 ACL。
裸数字误填意图无法机器识别，保持旧兼容并明确只表示本仓。#289 文件 owner 边界保持。

## 模板采纳清单（未写下游）

change-template-sync --refresh-digest --today 2026-10-02 --porcelain 返回 3：digest 已刷新，
退出 3 表示存在 holder 需动作，不是刷新失败。LocalWMS、NewEMaint、SFMDigitalBoard 的
summary.md 副本 stale；myapp 与 smoke-test 无本地 checkout，unverified。
本票未改下游副本，未替它们创建 Issue/PR；source 合同标明 runtime pending。

## 调度收据

总调度要求 #286 在 #289 后集成；本会话在 #289 实际 merge 后亲自整合/全套验证。
depends_on 保持 []，排序不是新产品依赖。已批准 A 保留；G01 步骤后停止，由 fresh turn 续办。

## 当前 smoke 阻塞

受控 host 的完整 smoke 未通过，止于 test-registry-preflight.sh 的停服负向断言；
单独复跑再次失败。原 preflight 和 fixture 与 origin/main 字节未变，不属于 #286 依赖合同。
一次直接 fixture 对照因 subprocess 解码错误中止，未形成有效 PASS/FAIL 对照；不据此推断根因。
不读 curl/user credential 配置、不改该脚本、不弱化断言、不停止真实 registry。
该缺口必须在最终 PR 候选前解决或由总调度安排独立处理；当前不声称完整 smoke PASS。

## G01 交接

T01（G01）治理合同文档与 digest 校验已完成，frontier 将进入 T02。独立全量 runtime
978 tests PASS；完整 smoke FAIL 的 registry fixture 缺口保留，不豁免最终提交硬门。
仅提交本票八个治理源文件与四份语义文档；没有 runtime、shell、host-access schema、
AGENTS.md、其它 worktree、下游副本或 installed/live 改动。当前步骤在该 commit 后停止，
下一 fresh run 重读合同和平台规则后可继续已批准 T02–T04，无需再次批准 A。


## T02–T04 前轮验证快照

已按 AGENTS 重读 G01 后合同；未修改本次遵循的 AGENTS.md。所有执行在 exact
/private/tmp/issue-286-dependency-references，未写其它 owner worktree。

| Check | Result | Evidence |
|---|---|---|
| 首批 parser/broker TDD | PASS | 7 tests；RED 4 个未接线 errors，接线后全绿 |
| 双闸门与重启 fixture | PASS | tests.test_dependencies 与 tests.test_dependency_integration 最终共 20 tests |
| 首轮完整 runtime | PASS | 994 tests，86.415s，/private/tmp/issue-286-runtime-implementation.log |
| 审查后完整 runtime | PASS | 998 tests，83.501s，/private/tmp/issue-286-runtime-final.log |
| 双轴 code-review | PASS after repair | Standards 1 项、Spec 2 项，全部修复并独立复核，见下节 |
| 文档 gate | PASS | 145 changes，gap=0；python -m aisoft_loop.cli check-change-documents |
| 模板 digest | PASS | sha256:5077fbbed13edcf878a91f38917c14228fc95f2bf5b605da891b8093d3148430 |
| live 分类独立读回 | PASS | --verify 286 result=projected，type=platform、complexity=complex；/private/tmp/issue-286-classification-final.jsonl |
| broker shell + 临时 installer fixture | PASS | bash codex/tests/test-host-access-broker.sh；/private/tmp/issue-286-host-access-shell.log |
| 修改 shell 的 bash -n / ShellCheck | PASS | codex/tests/test-host-access-broker.sh，无 shell runtime/installer 实际改动 |
| 中间完整 smoke | FAIL, repaired in scope | 新增 typed read 后旧 smoke 精确计数仍 36；已改 37 并补 exact operation/唯一 edge/零权限拒绝断言，独立 PASS |
| 最终完整 smoke | FAIL | exit 1；registry-preflight 停掉测试 registry 后期望 exit 1，实际 0；/private/tmp/issue-286-final-smoke-host.log |
| #289 后整合 | BLOCKED_EXTERNAL | 受控 typed read 最新 #289=open/approved；未假设合并或擅自写它的 worktree |
| PR CI / installed / live dependency GET / 部署 | NOT RUN | 未 push、未建 PR；真实安装、凭据、ACL、VM 服务及外仓读取不在本票授权内 |

| AC | 结论 | 本地 source 证据 |
|---|---|---|
| AC-1 | PASS | 原 contract/Controller 与 routine tests 全量回归；缺省/空/整数/数字 scalar 保留本仓语义 |
| AC-2 | PASS | Controller/routine 同 issue() fixture；本仓同号终态不满足外仓 open，目标 closed+completed 才通过 |
| AC-3 | PASS | malformed/self/canonical alias/unknown target/unauthorized edge；拒绝前无越界 GET/凭据读取 |
| AC-4 | PASS | PR/错仓错号/403/404/transport/JSON/oversize/redirect/错误 audit 权限类型失败关闭；routine merge POST=0 |
| AC-5 | PASS, fixture only | shared dependencies helper；manager-audit 唯一路由；Mac/VM cwd 固定 argv adapter，无 direct fallback；没有真实 VM 运行验收 |
| AC-6 | PASS | 等待→重复轮询→重启→解锁，provider/PR 均一次；state/comment/PRbody/receipt 保留 qualified reference；CI等待删依赖拒绝 |
| AC-7 | PARTIAL | 文档/providers/templates 与 998 runtime PASS；完整 smoke FAIL，#289 后整合门尚未满足 |

### Standards

初审 1 项 P2：manager-audit 身份未明确要求 is_admin=False。已使用
require_non_admin_exact=True，缺失/null/string/number/container 在目标 GET 前拒绝。
复核 0 项未解决问题，无需要单独报告的 Fowler smell。复核者跑 4 项针对性测试 PASS。

### Spec

初审 2 项 P1：awaiting_ci 可以删除旧依赖；源仓 canonical binding 校验晚于 GET，失败仍会 comment。
已在所有 continuation 核对持久化引用，首次 provider 前保存；源仓网络调用之前核 binding，
失败不发 comment；CLI 核 manifest 后用 canonical URL/owner/repo 构造 client。
独立复核 0 项未解决缺口，20 项依赖测试 PASS；无额外 scope creep。

两轴固定点为已批准 spec 基线 5c2cd726c9aeaee9d17541d8feb049e33881bbac，
初审 git diff <base>...HEAD（G01/T02/T03），增量复核 git diff HEAD（T04修复）。
审查结论不代替完整 smoke、CI 或 installed/live。

### 本轮边界与后续

模板 holder 清单仍是 LocalWMS/NewEMaint/SFMDigitalBoard stale，myapp/smoke-test unverified；
只刷新本票 source digest，未覆盖下游副本。source README/03/04/双 provider/private-access 与模板
同步为 source/local 已验证、installed/live NOT RUN。未改变 #289 required_docs/documents 终态算法。

T04 尚未 completed：完整 smoke 通过且 #289 实际 merge 后，本 owner 才能 fresh-fetch/rebase，
重跑两闸门、文档与终态 gates。完整本地候选准备妥当后再取得 #286/change/286-dependency-references/manual
的最终 PR 提交确认；当前不 push、建 PR、merge、安装或归档。


### 最终阻塞读回

完整 smoke 在本票 broker 精确计数修复后重新运行，重新到达与 G01 相同的 registry 停服
负向 fixture FAIL。test-registry-preflight.sh、fake-npm-registry.py、templates/project/ci/registry-preflight.sh
相对固定基线未修改；未绕过/弱化断言、未读用户 curl credential 配置、未停止真实 registry。
该既有缺口不在 #286 依赖合同内，不能通过本票顺手修复或写 PASS。完整 smoke 的最终
runtime discover 尚未到达；998 tests PASS 来自独立完整 discover，不混作 smoke PASS。

broker 返回的真实 approved #286 payload 再 load_contract PASS：7 AC、4 份映射文档、
exact branch、depends_on=[]，frontier=T04。分类独立读回 projected。T04 status 保持 pending，
不是 AWAITING_PR_CONFIRMATION 或已解决。只提交本地修复及收据；last_push_head=null。

当前稳定阻塞：完整 smoke 的既有 registry fixture FAIL；#289 仍 open，尚不能执行约定的
merge 后 owner 整合。后续 fresh run 在已批准 A 范围内继续，不重复启动确认；最终 PR 前
仍须 exact Issue/branch/manual 确认。PR CI、合并、installed/live、部署和归档均未运行。


## 继续执行：#320 整合与 locale 控制后的完整 smoke

本轮通过 broker git.fetch.main 读回 origin/main=11c0410d3878d5449fa61796f174ba3d2dd5e59c，
#320 已真实合并。owner 在本票干净、未 push worktree 无冲突 rebase，保留 #320 的首次/后续
push 各自 exact head 验证合同；未写共享 main 或其它 owner worktree。前后 4 个 commit 的
完整映射保存在 evidence/t04-resume-receipt.json，旧提交仅作前轮历史证据。

registry 诊断记录表明，原环境 LANG/LC_ALL/LC_CTYPE 均为 C.UTF-8；Bash 为 Mac 内置
3.2.57。原脚本 connect failure 提示中的 $REGISTRY 后中文标点被误读进变量名，出现
REGISTRY 的 unbound variable 错误，probe 实际退出 0。该诊断在隔离 fake registry 上执行，
未读用户 curl/credential 配置；日志 /private/tmp/issue-286-registry-diagnostic.log。

前序 #320 在同一初始基线的收据明确使用 LC_ALL=C PYTHONDONTWRITEBYTECODE=1。按同样的
单次命令环境，原封不动的 registry fixture 全部 PASS，再运行完整 smoke：

| Check | Result | Evidence |
|---|---|---|
| 原 registry fixture，LC_ALL=C | PASS | exit 0，绿—红—绿与其余负向断言全部保留；/private/tmp/issue-286-registry-c-locale.log |
| #320 owner-local rebase | PASS | origin/main 11c0410d3878d5449fa61796f174ba3d2dd5e59c，测试 source head 12dd967eb60253d7033c2c8ccb0c382b499bf1c6 |
| 完整 smoke，受控 host | PASS | LC_ALL=C PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh，exit 0；998 tests，97.111s，最后输出 Codex platform static smoke checks passed. |
| 文档与模板 digest | PASS in full smoke | 最新 146 changes；模板 digest 未变，source 与 #320 合同均保留 |
| registry source 未修改 | PASS | 对初始基线与当前 origin/main 的三文件 diff 均为空；checksum 见本轮 receipt |
| #289 PR #325 live readback | BLOCKED_EXTERNAL | open，merged=false，head 15b963a4f4dab52e4a161de0d8bab29ebc7d53c5，merge_commit_sha=null |
| #289 后 rebase/双闸门/文档终态验证 | NOT RUN | 合并尚未发生；不把当前 #320 基线的 PASS 写成此项通过 |
| push/本票 PR/CI/installed/live/deploy/archive | NOT RUN | last_push_head=null，仍无最终 PR 提交确认 |

完整 smoke 日志：/private/tmp/issue-286-resume-smoke-c-host.log；SHA-256 与 source commit
完整绑定见 evidence/t04-resume-receipt.json。这里只设置一次测试进程的 LC_ALL=C，未改
全局环境或 registry 脚本；没有降低/删除负向断言。原 locale 下的 FAIL 收据继续保留。

当前唯一剩余阻塞为已批准 plan 的 #289 merge 后串行整合条件。AC-1–AC-6 当前 source/local
已通过；AC-7 的本轮完整 gates 通过，但最终 #289 后集成未执行，因此整体仍 PARTIAL。
T04 pending，本票未解决，不归档。后续 fresh run 无需再确认启动；最终 PR 前仍须 exact
#286/change/286-dependency-references/manual 提交确认。


## 调度更新后的只读核对与提前整合拒绝

broker fresh-fetch 读回 origin/main=65268ee5f1e622c486fd9e354dd35e20a2900f91；
#308 PR326 已真实合并，主线同时包含 #287 的 architecture profile checksum source。
#289 PR325 仍 open、merged=false，head=15b963a4f4dab52e4a161de0d8bab29ebc7d53c5。
#327 未被添加为本票 depends_on 或人工 PR 更新的 hard 前置；不代写 #289/#319/#327。

最新主线对本票原已验证 base 11c0410 的差异未触及 aisoft_loop、aisoft_host_access、
host-access-broker.json 或 AGENTS.md。#308 的新 smoke 仅增加 source-only 漂移映射与隔离
fixture；只读查看其映射，aisoft_host_access/*.py 已覆盖 dependencies.py，无需为本票
新增模块扩 installer/checker 映射。该结论只是 source 对照，不是最新主线组合测试 PASS。

本 owner 请求 git rebase origin/main 时，自动审批拒绝，命令未执行。拒绝理由为本地
history rewrite 且 approved plan 明确要求 #289 PR325 实际合并后整合。没有通过 merge、
cherry-pick、临时组合检出或修改 broker 绕过；HEAD 保持 2b132c7ea40a0c89f103dd07a03b2d7e8a9d4b82，
未发布，last_push_head=null。拒绝收据与只读影响核对见 evidence/t04-dispatch-readonly-receipt.json。

此前完整 smoke PASS 仍只绑定 11c0410 base / 12dd967 tested source；不将其外推为
65268ee5 或 #289 merge 后组合验证。组合 rebase/full gates NOT RUN，T04 pending。
按既定顺序，待 #289 真正合并后再由 owner 整合；提前改写本票本地历史需要直接的人类
授权改变执行顺序，调度消息本身不替代该授权。无 force/lease、push、PR、安装、凭据或部署动作。


## 新的人类授权：提前整合 65268ee5 的独立验证

用户直接回复“按你的建议继续”，绑定此前提前 local rebase 的 exact 请求。授权仅使未发布
本票可先整合指定主线作独立验证；#289 merge 后最终组合验收仍保留。新请求已获自动审批
执行许可，无冲突完成 6 个提交 rebase，range-diff 全部 =；不是绕过前次拒绝。

| Check | Result | Evidence |
|---|---|---|
| 本地 rebase 与 patch 完整性 | PASS | base 65268ee5f1e622c486fd9e354dd35e20a2900f91；tested source 6fae040e92e1c8e8c494cd4260965f3ef7c3bb05；6 个 patch 相同 |
| 完整 smoke（LC_ALL=C） | FAIL | exit 1；止于 #308 test-installed-drift.sh，23 tests / 16 failures / 37.400s；尚未到 smoke runtime discover |
| 8 类安装副本字节检查 | PASS, fixture only | 失败 report 中 8 类 installer 均 PASS；并非真实 host 安装验收 |
| #308 fixture 根因 | GAP | installed mode 把 source 与 cached main 差异加入 aggregate；有效未合并分支返回 GAP/exit 1，而 test_all_eight_real_installer_fixtures_pass 与 check() 默认期待 exit 0 |
| 独立全量 runtime | PASS | 1012 tests，95.253s，exit 0；不混作完整 smoke PASS |
| 双依赖闸门针对性测试 | PASS | 20 tests，1.403s，exit 0 |
| source-only | PASS | 8 类 SOURCE 定义通过，main provenance GAP 保留；不替代完整 smoke 或真实 installed 验收 |
| 文档 gate | PASS | 148 changes，gap=0；check-change-documents/check-change-pr-url |
| approved loader / 分类 readback | PASS | 7 AC、4 真实映射文档、depends_on=[]；projected platform/complex |
| owner 与未发布状态 | PASS | exact session/branch；last_push_head=null，干净 rebase |
| #289 PR325 | BLOCKED_EXTERNAL | open，merged=false，head 15b963a4f4dab52e4a161de0d8bab29ebc7d53c5；merge_commit_sha=null |
| #289 后最终组合 | NOT RUN | 真实 merge 未发生 |
| push/PR/CI/真实 installed/live/deployment | NOT RUN | 无对应操作或最终 PR 提交确认 |

本票的 smoke.sh、check-installed-drift.sh/.py、test-installed-drift.sh 与其 fixture 相对
65268ee5 均未修改；checksum 保存于 receipt。本轮未修改 #308 检查算法/fixture，未
篡改 cached main、未绕过或删除断言。缓存 main 由其它会话推进至 #319 merge 70baa358，
本票仍绑定获授权 exact base 65268ee5，不以缓存 ref 的推进宣称本票已整合 #319。

所有命令、授权绑定、前后 commit 映射、日志 SHA-256、最小错误 report 投影与剩余门见
[evidence/t04-human-authorized-rebase-receipt.json](evidence/t04-human-authorized-rebase-receipt.json)。
T04 保持 pending：需 #308 fixture 对有效未合并分支的验收缺口被受控解决，并在 #289 真实
merge 后由本 owner 最终整合/验证。当前不能进入最终 PR 确认或声明 AC-7 全部 PASS。
