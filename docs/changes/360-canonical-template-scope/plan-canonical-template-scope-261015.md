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
status: contract-drafting
branch: change/360-canonical-template-scope
created: 2026-10-15
updated: 2026-10-15
---

# #360 实施与验收计划

本计划与 mapped spec 的 D-SCOPE360-1 卡绑定。T01 是已获直接批准的本轮分析工作；
T02–T05 仅是 A 方案候选实施顺序，目前全部未授权、NOT RUN。选 B 时先修订合同。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | fresh单票/owner/source分析、四份mapped docs、D-SCOPE360-1、文档检查与线性本地文档提交 | - | completed |
| T02 | A方案批准后独立应用最小治理合同，文档校验/local commit并STOP；为fresh runtime run提供规则 | T01 | pending |
| T03 | fresh重读T02后，shared canonical policy与reader/Controller/broker一致性端到端切片，真实Git正负fixture | T02 | pending |
| T04 | policy输入受管分发、版本匹配与drift切片；isolated installer/no-op/恢复fixture | T03 | pending |
| T05 | 全量回归/默认硬门、完整AC evidence、唯一manual最终PR候选；提交PR前停下等待第二确认 | T04 | pending |

T01 完成不使 T02 自动可执行；必须先记录 D-SCOPE360-1 裁定与 #360 实施批准。
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
- T04：`codex/install-host-access-broker.sh`、`codex/install-vm.sh`、
  `codex/tools/check-installed-drift.py`、`codex/tests/test-install-host-access-broker.sh`、
  `codex/tests/test-installer-source-guard.sh`、`codex/tests/fixtures/installed-drift/test-installed-drift.py`。
  只增加 sync manifest 的受管映射及必要 pin，保留写前来源闸门和其他 installer行为。
- T05：本票文档；范围内 CI repair 不扩 spec，不 skip required tests。

完整精确 allowlist 以 spec 的 `git_scope` 为准。这里缩写 basename 仅为可读性，
不得将 `codex/runtime/tests/`、`docs/changes/` 或其他目录作为通配授权。

## 测试与验收映射

以下均为批准后计划，**本轮未执行**。从本票 WT 运行，使用 `PYTHONDONTWRITEBYTECODE=1`；
fixtures 仅新临时库/本地 bare remote、假身份/provider，不使用任何业务目标或凭据。

| AC / Fixture | Ticket | Verification command or review |
|---|---|---|
| AC-1/2；F01/02/04–08 | T03 | `PYTHONPATH=codex/runtime python3 -B -m unittest tests.test_main_integration tests.test_host_access tests.test_controller`；新增真实 canonical/holder/alias/批准子集案例 |
| AC-3；F09/10 | T03 | 同上；逐提交 add/revert、合法/非法历史锚、symlink中间tree及既有DAG/objects负例 |
| AC-4；F03/11 | T03 | 同上；真实LocalGit整合、ordinary_push本地bare remote、R0/R/M/H/guard/possible-write断言 |
| AC-5；F12 | T03 | 三入口对相同fixture逐项比较结果/错误码及实际零网络写；不只mock scope |
| AC-5；F13 | T04 | `bash codex/tests/test-install-host-access-broker.sh`、`bash codex/tests/test-installer-source-guard.sh`、`bash codex/tests/test-installed-drift.sh`（isolated fixture roots） |
| AC-6 | T05 | `PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests`，随后 `bash codex/tests/smoke.sh` 默认路径；不设置skip制造PASS |
| AC-6 | T04/T05 | `bash -n codex/install-host-access-broker.sh codex/install-vm.sh codex/tests/test-install-host-access-broker.sh codex/tests/test-installer-source-guard.sh`；环境可用时同文件 `shellcheck`，不可用写NOT RUN |
| AC-6 | T01/T02/T05 | `PYTHONPATH=codex/runtime python3 -B -m aisoft_loop.cli resolve-required-documents 360 --repo .`、`check-change-documents --repo .`、`git diff --check` |
| AC-6/7 | T05/未来PR | 文档/claim/branch/exact H fresh核对；最终PR确认后读取 `CI / verify (pull_request)` exact head/base与merge-preview；本轮PR/CI NOT RUN |
| AC-7 | 后续独立授权 | source合并后Mac/VM实际入口/版本/快照恢复；再由HSDB原owner采用；本票不执行 |

默认 smoke 可能涉及现有更多 fixture/原生工具；失败应保留完整命令、SHA及原因。
缺工具/外部依赖必须报告 BLOCKED_EXTERNAL/GAP，不能安装依赖或改CI来绕过。
本轮仅调用文档命令与Git只读核对，不执行上述产品/Gitfixture/installer测试。

## 数据库迁移

无。不得读取、复制或变更 HSDB 真实库、样本、附件、历史结果或公司数据。

## 部署与回滚

source 变更自身没有应用部署；分发脚本候选不等于执行安装。
Mac/VM 真安装须 source merge 后独立授权；精确入口、重复安装、故意失败和完整快照恢复
在 spec D-SCOPE360-1 已列，当前 NOT RUN，不作为 source merge 的循环前置。
HSDB 采用由其原 owner 另行推进，不修改原 #15 refs、claim、固定H或WIP。

source 修复/回滚只追加受控本票commit或后续revert PR；禁止reset/force/删除历史。
治理应用失败只撤回本轮确知未提交增量，保留原HEAD与证据；并发owner/H/policy漂移立即停止。

## 本轮收尾与下一步

保存准确 claim、fresh main、source事实、文档检查、仅四文档提交和最终HEAD。
停在 `ANALYSIS_COMPLETE / NEEDS_HUMAN_DECISION`，一次提交 D-SCOPE360-1 供裁定与实施批准。
不请求重复启动/WT/每项检查批准，不请求最终PR，不写产品approved。
