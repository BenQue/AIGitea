---
issue: 239
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/239
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - ci-change
depends_on:
  - 237
status: approved
branch: change/239-param-company-delivery
created: 2026-09-03
updated: 2026-09-03
---

# Implementation plan · company-delivery runtime 参数化

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 基线观测入 verification（grep 计数、smoke 基线、#75 state）+ sync timer 参数化：`contract.py` R-01～R-06、`collector.py` R-07、inventory schema R-11、测试 fixture 去项目名 + R-03/R-06/R-07 正反向测试；`python3 -m unittest tests.test_company_delivery` 全绿 | - | done |
| T02 | compatibility matrix 参数化：`bundle.py` R-08、`cli.py` R-09、`VERSION` R-10、handoff/compatibility schema R-12/R-13、templates R-14～R-16、R-04/R-08/R-09 测试与「runtime 包零项目名」断言、版本断言 `1.3.0`；单测全绿 | T01 | done |
| T03 | 文档与脚本合同：README/runbook R-17、integration 脚本 R-18（`--compatibility-matrix` 参数 + `1.3.0` 身份钉）、harness 守卫；`bash codex/tests/smoke.sh` 全绿；integration `--execute` 记 NOT RUN | T02 | done |
| T04 | verification 定稿（AC-1/3/4/5/6 + AC-2 中间状态）；`check-change-documents` PASS；判级投影 `apply-classification-labels.sh 239` → `--apply` → `--verify 239` = `projected` | T03 | done |
| T05 | **软依赖 NewEmaint #75 closed**（broker `gitea.issue.read --project newemaint --number 75` 读回 `state: closed`）：`git rm company-delivery/compatibility/newemaint-company-pilot-v1.json`；`smoke.sh` 守卫扩展到整个 `company-delivery/` + 反向证明；verification AC-2 回填；smoke 全绿 | T04 + #75 | blocked（#75 open） |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。每个 ticket 都应可由 `$implement #N Txx` 独立执行和验证。
T01→T02→T03→T04 串行（每张 ticket 单独 commit）。**T05 之前停下报告调度会话**（`local_18321282-0f38-48ea-8e6c-ae3d257efe1b`）：
#75 已 closed 则继续 T05 后进入确认点 2；#75 仍 open 则由调度会话决定是等待、还是把 T05 拆成衍生 Issue 后以
T01–T04 进入确认点 2。不把删除强行做进同一个 PR。

## Expected touch points

- T01：`codex/runtime/aisoft_company_delivery/contract.py`、`collector.py`；`company-delivery/schema/inventory-v{1,2,3}.schema.json`；
  `codex/runtime/tests/test_company_delivery.py`；`docs/changes/239-param-company-delivery/verification-*.md`（基线节）。
- T02：`codex/runtime/aisoft_company_delivery/bundle.py`、`cli.py`；`company-delivery/VERSION`；
  `company-delivery/schema/handoff-v1.schema.json`、新建 `schema/compatibility-v1.schema.json`；
  `company-delivery/templates/handoff-manifest.example.json`、新建 `templates/compatibility-matrix.example.json`、
  `templates/gitea-transition.example.json`、`inventory.example.json`、`evidence.*.example.json`；测试文件。
- T03：`company-delivery/README.md`、`runbook.md`；`codex/tests/integration/test-company-delivery-real-release.sh`；
  `codex/tests/test-company-delivery-real-release-harness.sh`（新增一条 `--compatibility-matrix` 静态守卫）。
- T04：verification、summary `status`。
- T05：`company-delivery/compatibility/newemaint-company-pilot-v1.json`（删除）、`codex/tests/smoke.sh`、verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `grep -rci newemaint codex/runtime/aisoft_company_delivery/`（每文件 0）；`grep -n COMPATIBILITY_PATH codex/runtime/aisoft_company_delivery/*.py`（空）；`PYTHONPATH=codex/runtime python3 -m unittest tests.test_company_delivery -k timer -k matrix -k handoff`（新增用例逐条列入 verification） |
| AC-2 | T05：`test ! -e company-delivery/compatibility/newemaint-company-pilot-v1.json`；`grep -rci NewEmaint company-delivery/ \| grep -v ':0$'`（空）；守卫反向证明（临时副本 `ROOT=<tmp>` 单独执行守卫块 rc=1；真实树 rc=0）。T05 前：同一命令记录中间计数 |
| AC-3 | `cat company-delivery/VERSION`；`python3 -c 'from aisoft_company_delivery.contract import OPERATOR_VERSION; print(OPERATOR_VERSION)'`；bundle 测试 `archive_name` 前缀断言；legacy handoff 单测 |
| AC-4 | `bash codex/tests/smoke.sh` rc=0；`grep -ci newemaint codex/runtime/tests/test_company_delivery.py company-delivery/templates/compatibility-matrix.example.json`；`bash -n` + `shellcheck -S warning codex/tests/smoke.sh codex/tests/integration/test-company-delivery-real-release.sh`；`bash codex/tests/test-company-delivery-real-release-harness.sh`；integration 默认输出含 `NOT RUN:` |
| AC-5 | verification 「平台侧读取路径」小节 + broker `gitea.issue.read --project newemaint --number 75` 读回 |
| AC-6 | `git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/config codex/tools AGENTS.md skill-for-codex skill-for-claude codex/skills codex/runtime/aisoft_loop codex/runtime/aisoft_release`（空）；`git diff --stat origin/main...HEAD` 全部为平台仓路径 |

## 部署与回滚

无部署影响；回滚 = revert 唯一 PR。声明 `verification` 是因为 grep 计数、守卫反向证明、#75 state 读回与
integration NOT RUN 属一次性证据，不是因为部署。
