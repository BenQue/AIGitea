---
issue: 201
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/201
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - platform-governance
depends_on: []
status: approved
branch: change/201-verdaccio-liveness-probe
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan · registry 存活断言

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `templates/project/ci/registry-preflight.sh` 与 `codex/tests/test-registry-preflight.sh`，含替身 registry 的五条路径与负向验证；注册进 smoke 三处 | - | pending |
| T02 | `templates/project/ci/ci.yml` 增加前置步骤，context 三要素不变 | T01 | pending |
| T03 | `aisoft-project-check.sh` 的 `ci-registry-preflight` 回读与 `test-project-check.sh` 用例 | T02 | pending |
| T04 | `01` §5 与 `06` 踩坑集的文档落点，以及交接项写入 verification | T03 | pending |

## Expected touch points

- T01：`templates/project/ci/registry-preflight.sh`、`codex/tests/test-registry-preflight.sh`、
  `codex/tests/smoke.sh`。
- T02：`templates/project/ci/ci.yml`。
- T03：`codex/tools/aisoft-project-check.sh`、`codex/tests/test-project-check.sh`。
- T04：`01-基础设施-VM-Gitea-Runner.md`、`06-运维手册与踩坑集.md`、本 change 的 `verification`。

范围提示，不授权扩大 spec。**不触碰**：`codex/config/host-access-broker.json`、
`codex/runtime/aisoft_host_access/`、`codex/tests/test-host-access-broker.sh`、任何 installer、
`AGENTS.md`、任何应用仓文件。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-registry-preflight.sh` 的成功路径用例；diff review 确认全程 curl、无 npm、无 pm2 |
| AC-2 | 同上，三类失败路径各断言各自的结论文本 |
| AC-3 | 同上，断言退出码与 `AISOFT_REGISTRY_PREFLIGHT_FAIL` / `_OK` 标记 |
| AC-4 | diff review：`ci.yml` 的 `name:`、job key `verify`、`on:` 三处逐字未改 |
| AC-5 | `bash codex/tests/test-project-check.sh`；对本仓跑一次 `aisoft-project-check.sh` 看新行出现 |
| AC-6 | `bash codex/tests/smoke.sh` 全绿；grep 确认新测试在三处均已注册 |
| AC-7 | 手工执行的负向验证序列，输出照抄进 verification |
| AC-8 | 对 `http://gitea-ci.orb.local:4873/` 执行一次，输出照抄 |
| AC-9 / AC-10 | diff review 文档落点 |
| AC-11 | verification 的交接项一节，逐条 NOT RUN 并附命令与预期输出 |

## 部署与回滚

无部署。本次不安装任何东西到 Mac 或 VM，不新增 installer，不改 broker 操作表。

回滚：`git revert` 本次唯一 merge commit 即完全回滚。新增文件全部是平台侧参考实现与测试，
没有应用仓已经消费它们，因此 revert 无下游破坏。

`verification` 声明的含义是「这次变更欠一份验证记录」，不是「这次变更要部署」。
