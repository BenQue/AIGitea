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
status: approved
branch: change/286-dependency-references
created: 2026-10-02
updated: 2026-10-03
---

# #286 · 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | G01：只应用已批准治理合同，独立提交后停止 | - | completed |
| T02 | 旧本仓兼容 + qualified parser + broker bounded read 的完整读取路径 | T01 | completed |
| T03 | Controller 与 routine 同规则依赖等待、终态解锁和展示 | T02 | completed |
| T04 | 两 provider 示例、全部 gates 与唯一最终 PR 候选 | T03 | completed |

此表是已批准候选 G01→T01→T02→T03 的合法 Txx 编号映射；依次对应本表 T01→T02→T03→T04，
切片边界没有改变。T01 必须是纯治理合同步骤；完成后 fresh run 重新读取合同再启动 T02。
不得在当前治理步骤 dispatch runtime implement；无需再申请合同确认。

## Expected touch points

- T01：README.md、03-Issue-Spec-Plan与单闸门开发流程.md、04-Agent编排与定时任务.md、
  skill-for-codex/references/private-gitea-access.md、codex/skills/issue-session-flow/SKILL.md、
  skill-for-claude/issue-session-flow/SKILL.md、templates/docs/changes/_template/summary.md，
  codex/config/change-template-sync.json 的模板 digest、本票映射 summary/spec/plan/verification。
- T02：codex/runtime/aisoft_loop/contract.py 与依赖身份/resolver、aisoft_host_access 的
  contract/broker/CLI、codex/config/host-access-broker.json、对应 tests；必要 adapter 仅用于
  manifest-bound typed dependency read，不新增任意跨仓 API client。
- T03：loop controller/gitea/CLI/状态与 PR body、routine dependency gate、对应 tests。
- T04：上述范围内测试、skill/模板同步及本票 evidence；不顺手修改其它 Issue 的合同或 runtime。

## 数据库迁移

无。旧整数依赖保留语义；新增 qualified scalar 是显式 opt-in，不做历史文档批量迁移。

## 测试与验收映射

| Acceptance criterion | Ticket | Verification command or review |
|---|---|---|
| AC-1 | T02 | contract/Controller 原测试 + 新 qualified contract 测试 |
| AC-2 | T03 | 源仓同号终态、目标仓 open/terminal 的 collision fixture；核实际请求目标 |
| AC-3 | T02 | dependency parser 与 broker denial 测试，非法边/格式的 request count=0 |
| AC-4 | T02/T03 | 404/403/transport/invalid JSON/PR/identity failure fixture；merge POST=0 |
| AC-5 | T02/T03 | Controller/routine 共用 fixture；Mac/VM adapter 与凭据路由零 fallback 断言 |
| AC-6 | T03 | 阻塞→解锁→重启轮询；provider/PR 创建次数与 state/PR body qualified identity |
| AC-7 | T01/T04 | resolve-documents/load_contract/check-change-documents、双 provider 文档对照、全量 runtime、smoke |

基线命令：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest
codex/runtime/tests/test_contract.py codex/runtime/tests/test_controller.py -q`。
全量：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s
codex/runtime/tests -p 'test_*.py'`；`bash codex/tests/smoke.sh`。shell 变动再跑 bash -n 与可用 ShellCheck。
具体新增测试名称可在实施中确定，不能删覆盖或弱化验收。最后执行
`bash codex/tools/apply-classification-labels.sh --repo <worktree> --project aisoft-platform --verify 286`，
两维 projected 才能进入最终 PR 候选。该 readback 不是启动批准本身。

## 部署与回滚

无部署动作。source 合同与实现不包含安装/credential/ACL/live apply。source 人工 revert；
旧版本面对新增格式必须 fail closed。verification 保存改动前复现及真实执行记录。

## 集成约束

总调度 2026-10-02：#286 排在 #289 后集成（优先级 5）。#289 的真实 merge 到达后，由
#286 owner 自己 fresh-fetch/rebase，复核 dependency gates、文档与终态全部验证。该排序
不是产品依赖，不改 depends_on；准备可以先进行，不把未 ready 的其它项当可合并。

## 交付与停止点

T01 文档合同校验与独立全量 runtime 基线已通过，完整 smoke 保留 registry fixture FAIL；
该缺口未被豁免，最终 PR 候选前必须通过完整 smoke。T01 本地纯治理合同 commit 后返回
GOVERNANCE_CONTRACT_APPLIED_FRESH_RUN_REQUIRED；
下一 fresh run 可以自主 T02→T04。最终 PR 前停 AWAITING_PR_CONFIRMATION，再请求绑定
#286/change/286-dependency-references/manual 的提交确认。required CI 通过后 READY_FOR_REVIEW，
人合并；merge 后才做终态与清理归档。当前不得 push、创建 PR 或 archive 未解决的 Issue。


## T04 当前收据

T02/T03 已 completed；T04 的双 provider/source 文档同步、双轴审查修复、998 runtime、
broker shell、bash -n/ShellCheck、document/digest、classification readback 已通过。
本轮已无冲突整合 #320 的 origin/main；LC_ALL=C 下完整 smoke PASS，包含 998 tests。
原 C.UTF-8/Bash 3.2 registry fixture FAIL 保留；未改该断言或全局 locale。

#289 的 PR #325 最新读回 open、merged=false；merge 后串行整合尚未执行，T04 保持 pending。
完整执行收据见 evidence/t04-resume-receipt.json。没有最终 PR 提交确认，不 push、不建 PR、
不归档。#289 真正合并后，由本 owner 继续 fresh-fetch/rebase 及剩余闸门，不重复启动确认。


## 人类授权的提前准备例外与最新 T04 收据

用户对“提前将未发布 change/286-dependency-references rebase 到 65268ee5，仅做独立验证，
最终组合验收仍等 #289 合并”的 exact 请求回复“按你的建议继续”。仅覆盖提前本地整合的
准备顺序；保留 #289 实际 merge 后最终组合验收、完整 smoke 硬门和最终 PR 人工确认。
本轮无冲突 rebase、6 个 patch 不变；1012 runtime 与 20 依赖测试 PASS。

65268ee5 基线新增的 #308 installed-drift fixture 在本票未合并分支失败：8 类安装字节
检查 PASS，但 source/main 差异使 aggregate exit 1，而正常 fixture 仍期待 0。
完整 smoke FAIL，未改上游检查或绕过。PR325 仍未 merge；T04 pending。
真实结果与直接授权见 evidence/t04-human-authorized-rebase-receipt.json。


## #289 真 merge 后最终整合与候选

PR325 merged=true，exact merge 16beee09aefe89b5bc80a31544c59d456190ea32 已经 fresh-fetch
并证实位于 origin/main。本 owner 无冲突 rebase；7 个 patch 相同。主线已包含上游漂移
fixture 的隔离 source baseline 修复，本票未改 checker 或删除断言。

完整 smoke PASS（1042 tests / 104.165s）；双依赖+required_docs targeted 34 tests PASS；
Standards/Spec 增量复核均 0 项；文档、模板 digest、真实 approved loader、分类与终态
只读 dry-run 均通过。T04 completed，进入 AWAITING_PR_CONFIRMATION。
本地日志与 SHA 绑定见 evidence/t04-post289-integration-receipt.json。

唯一剩余确认点是 exact #286/change/286-dependency-references/manual 提交唯一最终 PR。
未执行 push/PR/CI/manual merge/真实安装/live/部署/终态 apply/归档；不将候选等同 merge。
