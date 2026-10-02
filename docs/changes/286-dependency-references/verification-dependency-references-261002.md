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
updated: 2026-10-02
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

## 执行结果

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

## Acceptance criteria 结果

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
