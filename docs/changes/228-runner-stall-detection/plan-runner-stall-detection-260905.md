---
issue: 228
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/228
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - platform-governance
  - external-contract
  - ci-change
depends_on: []
status: approved
branch: change/228-runner-stall-detection
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan · #228

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `orbstack.runner.status` 七处同步落地，smoke 全绿 | - | pending |
| T02 | 用候选 manifest 直接调 CLI 验收，取空闲与执行中两组真实读数 | T01 | pending |
| T03 | `01` §4 的 as-built 与建议取值，`06` 的判定规则表与踩坑条目 | T02 | pending |
| T04 | verification 记录、交接项与 NOT RUN 项 | T03 | pending |

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/contract.py`（`EXPECTED_OPERATIONS`）、
  `codex/runtime/aisoft_host_access/broker.py`（dispatch 分支与实现）、
  `codex/config/host-access-broker.json`、`codex/runtime/tests/test_host_access.py`、
  `codex/tests/test-host-access-broker.sh`。
  `runner.py` 的 `GovernedHostRunner` 只覆盖 Issue/change/PR 生命周期，
  既有 `orbstack.vm.status` 与四个 `vm.profile.*` 都不在其中，本操作同样不进——
  这是**核对后确认无需改动**，不是漏改（`06` 踩坑 20 的第三处在此为空）。
- T03：`01-基础设施-VM-Gitea-Runner.md`、`06-运维手册与踩坑集.md`。
- T04：`docs/changes/228-runner-stall-detection/verification-runner-stall-detection-260905.md`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `codex/runtime/tests/test_host_access.py` 新增用例断言路由、参数集与返回字段；diff review |
| AC-2 | 单元测试断言返回结构里没有原始日志正文字段；diff review |
| AC-3 | `bash codex/tests/smoke.sh`；`test-host-access-broker.sh` 的 `operation_count == 34` |
| AC-4 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json ...` 真实调用 |
| AC-5 | 同上，分别在 runner 空闲与 CI 执行中各取一次读数，抄进 verification |
| AC-6 | diff review `01` §4 |
| AC-7 | diff review `06`；`smoke.sh` 既有 `标准故障包` 守卫仍绿 |
| AC-8 | verification 的交接项一节与 NOT RUN 行 |

## 部署与回滚

无部署。broker 新操作要在 Mac 与 gitea-ci VM **两台**执行
`sudo bash codex/install-host-access-broker.sh` 才在运行时生效，这是合并后的人工交接项，
不属于本次变更的部署验收。回滚为 revert 本 PR 后两台重装。
