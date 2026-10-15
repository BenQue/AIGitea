---
issue: 360
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/360
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
depends_on: []
status: approved
branch: change/360-canonical-template-scope
created: 2026-10-15
updated: 2026-10-16
---

# #360 实施与验收计划

本计划与 mapped spec 的 D-SCOPE360-1 卡绑定。T01 是已获直接批准的本轮分析工作；
用户已在本会话直接批准`ed03008a6cfbbfbf1826501ec6a482929f2d557e`最小整包，绑定本branch。
T02已提交并STOP。本轮由调度在STOP后发起fresh接续，已重读治理/映射文档、原批准、claim及HEAD，
按同一授权执行T03–T05；全历史内容锁延期，六个installer/drift源码修改继续排除。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | fresh单票/owner/source分析、四份mapped docs、D-SCOPE360-1、文档检查与线性本地文档提交 | - | completed |
| T02 | 整包批准后独立应用最小治理合同，文档校验/local commit并STOP；为fresh runtime run提供规则 | T01 | completed |
| T03 | fresh重读T02后，shared canonical policy与reader/Controller/broker一致性端到端切片，真实Git正负fixture | T02 | completed |
| T04 | 复用既有installer/drift机制验证模块分发覆盖与版本匹配；不改installer或增加policy分发文件 | T03 | completed |
| T05 | 全量回归/默认硬门与本地审阅材料已完成；正式最终PR候选因live分类投影缺失而阻断，不能提前请求发表第二确认 | T04 | blocked |

本轮T02依据用户直接整包批准执行；批准锚和正文记录见summary/spec，不能扩成发表或安装授权。
T02 仅治理应用后按合同 STOP；后续 fresh run 重读后才进入 T03，不要求每命令新确认。
同票单 branch/单 WT/单 writer；不另开 child Issue、source worktree 或并行 writer。

## Expected touch points

- T01：本目录四份文档；证据落本会话 artifact 目录，不提交外部授权/会话全量数据。
- T02：`03-Issue-Spec-Plan与单闸门开发流程.md`、`skill-for-codex/references/project-align.md`、本票文档。
  不改当前 AGENTS 或全局已安装 skills。
- T03：`codex/runtime/aisoft_main_integration.py`、`codex/runtime/aisoft_loop/controller.py`、
  `codex/runtime/aisoft_loop/cli.py`、`codex/runtime/aisoft_host_access/broker.py`；
  `codex/runtime/tests/test_main_integration.py`、`test_controller.py`、`test_host_access.py`。
  复用 `RepositoryContract.vendors_change_templates`；不改 governance/access manifest。
- T04：仅本票验证文档可写。只读复用`codex/install-host-access-broker.sh`、`codex/install-vm.sh`、
  `codex/tools/check-installed-drift.py`及既有fixture；它们已经覆盖拟改runtime包、shared模块和
  access/governance manifests。不修改这些源码，不增加sync manifest安装目标或新的installer pin。
- T05：本票文档；范围内 CI repair 不扩 spec，不 skip required tests。

完整精确 allowlist 以 spec 的 `git_scope` 为准。这里缩写 basename 仅为可读性，
不得将 `codex/runtime/tests/`、`docs/changes/` 或其他目录作为通配授权。

## 最小范围审阅结论

必要source变动仅为四个既有runtime文件及三份既有测试文件：reader修正分类，
CLI/Controller把已解析项目/holder接入，broker使用自己的同一绑定，fixtures证明允许/拒绝一致。
复用已有holder字段、committed approved scope、历史锚、owner/来源检查、标准main整合、
ordinary FF和required CI；不新增policy框架、manifest schema、operation或授权根。
installer和drift变更从候选范围撤出，因为已有复制和mapping已经涵盖全部拟改文件。
若后续实现证明仍需额外安装源码变更，先给出具体未覆盖文件/入口证据并修订合同，不预授整目录。

## 测试与验收映射

以下命令在本轮获批fresh接续执行，实际结果见verification的T03–T05记录；不以计划表代替PASS。
从本票WT运行，使用`PYTHONDONTWRITEBYTECODE=1`；
fixtures 仅新临时库/本地 bare remote、假身份/provider，不使用任何业务目标或凭据。

| AC / Fixture | Ticket | Verification command or review |
|---|---|---|
| AC-1/2；F01/02/04–08 | T03 | `PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_main_integration tests.test_host_access tests.test_controller`；新增真实 canonical/holder/alias/批准子集案例 |
| AC-3；F09/10 | T03 | 同上；逐提交 add/revert、合法/非法历史锚、symlink中间tree及既有DAG/objects负例 |
| AC-4；F03/11 | T03 | 同上；真实LocalGit整合、ordinary_push本地bare remote、R0/R/M/H/guard/possible-write断言 |
| AC-5；F12 | T03 | 三入口对相同fixture逐项比较结果/错误码及实际零网络写；不只mock scope |
| AC-5；F13 | T04 | 复用`bash codex/tests/test-install-host-access-broker.sh`、`bash codex/tests/test-installer-source-guard.sh`、`bash codex/tests/test-installed-drift.sh`（isolated fixture roots）；验证现有机制，无新增分发文件 |
| AC-6 | T05 | `PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests`，随后 `bash codex/tests/smoke.sh` 默认路径；不设置skip制造PASS |
| AC-6 | T05 | 最小包不改shell；沿用默认smoke所含检查。仅当后续另批shell改动时才增加相应`bash -n`/ShellCheck，不为本票预设installer源码变动 |
| AC-6 | T01/T02/T05 | `PYTHONPATH=codex/runtime python3 -B -m aisoft_loop.cli resolve-required-documents 360 --repo .`、`check-change-documents --repo .`、`git diff --check` |
| AC-6/7 | T05/未来PR | 文档/claim/branch/exact H fresh核对；最终PR确认后读取 `CI / verify (pull_request)` exact head/base与merge-preview；本轮PR/CI NOT RUN |
| AC-7 | 后续独立授权 | source合并后Mac/VM实际入口/版本/快照恢复；再由HSDB原owner采用；本票不执行 |

默认 smoke 可能涉及现有更多 fixture/原生工具；失败应保留完整命令、SHA及原因。
缺工具/外部依赖必须报告 BLOCKED_EXTERNAL/GAP，不能安装依赖或改CI来绕过。
T02仅调用文档命令；本轮fresh T03–T05执行表内合成fixture/回归及默认硬门，无真实安装/凭据/业务目标访问。

## 数据库迁移

无。不得读取、复制或变更 HSDB 真实库、样本、附件、历史结果或公司数据。

## 部署与回滚

source变更自身没有应用部署；本最小包不改分发脚本，也不执行安装。
Mac/VM 真安装须 source merge 后独立授权；精确入口、重复安装、故意失败和完整快照恢复
在 spec D-SCOPE360-1 已列，当前 NOT RUN，不作为 source merge 的循环前置。
HSDB 采用由其原 owner 另行推进，不修改原 #15 refs、claim、固定H或WIP。
平台工具分发不等于HSDB部署：PM2、库、服务、环境配置与UAT均留在HSDB。
只等待本能力的消费者步骤由其owner判断，HSDB其他已批准业务开发不因本票统一停等。

source 修复/回滚只追加受控本票commit或后续revert PR；禁止reset/force/删除历史。
治理应用失败只撤回本轮确知未提交增量，保留原HEAD与证据；并发owner/H/policy漂移立即停止。

## 本轮收尾与下一步

保存准确claim、fresh main、source/fixture事实、实际验证、scope内线性提交和最终HEAD。
T02的STOP已完成；本轮继续到完整本地候选，禁止再次把原T02停止点当作未批准实施。
最终PR仍需第二确认；source/local/CI/installed/HSDB采用继续分层记录。

收尾：两项只读合同审阅发现已修复并复查，完整runtime为1260 tests OK，默认smoke exit0，
既有分发/drift与文档门通过；准确命令、失败历史、source指纹和HEAD见verification及artifact。
T05仅剩真实分类投影硬门：`--verify 360`仍projection-missing，`--apply`被自动审批拒绝且未执行。
不重复索取实施批准；下一最小授权仅为#360补齐type/platform和complexity/complex，
读回projected后再形成正式manual最终PR第二确认。不换入口绕审批，不扩大到lifecycle或发表。
