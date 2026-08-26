---
issue: 207
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/207
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - ci
  - shared-core
depends_on: []
status: pending
branch: change/207-codex-primary-readiness
created: 2026-08-26
updated: 2026-08-26
---

# Codex 主处理就绪验证记录

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `ac6441d510918c1fc99a302860176e8d7071c380`
- 环境: macOS 本地隔离 worktree；Gitea 只读状态通过受控 broker 读取
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 `bash codex/tests/smoke.sh` | PASS | 543 tests；exit 0 |
| 改动前 development complex frontier 复现 | FAIL（预期的基线缺陷） | 无 plan 的 complex contract 抛出 `complex contract must resolve exactly one plan document` |
| 改动前 live protection read-back | GAP | required status check 未启用且 context 为空；详细响应不写入仓库 |
| `python3 -m unittest codex.runtime.tests.test_contract codex.runtime.tests.test_controller` | PASS | 63 tests；exit 0 |
| `bash codex/tests/test-codex-drift.sh` | PASS | Codex source/installed byte drift 正反例通过 |
| `bash codex/tests/test-platform-readiness.sh` | PASS | source/installed/live 三层 PASS/GAP/BLOCKED 投影通过 |
| `shellcheck`（本次新增/修改 shell） | PASS | exit 0 |
| `bash codex/tests/smoke.sh` | PASS | 546 tests；exit 0 |
| 真实 `aisoft-platform-readiness.sh` | GAP（预期） | source PASS；installed Codex/Claude DRIFT；live repo PASS；live protection GAP |
| skills/runtime 安装 | NOT RUN | 本 Issue 禁止自动安装 |
| live branch protection apply | NOT RUN | 需要合并后独立授权 |
| 部署 | NOT RUN | 本 Issue 无部署 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | development 无 plan 返回 `T01`；production 对照拒绝 |
| AC-2 | PASS | 63 项 contract/controller 定向测试及 546 项全量测试 |
| AC-3 | PASS | 双工具入口、03/04/08 与 analyzer/spec/loop adapter 已统一；全量 smoke 通过 |
| AC-4 | PASS | 新增 Codex 原生 `issue-session-flow`，列出默认自动推进区间与硬升级条件 |
| AC-5 | PASS | 两个新 shell test 通过；真实检查如实投影 DRIFT/GAP，未执行 mutation |
| AC-6 | 待填写 | 待填写 |
| AC-7 | PASS | 546 项 smoke tests 与 ShellCheck 均通过 |
| AC-8 | 待填写 | PR diff/唯一性尚待 T03；安装、live apply、部署保持 NOT RUN |

## 遗留风险与未完成项

- skills/runtime 安装、live branch protection apply 与部署均为 `NOT RUN`，不得宣称 live
  已与 source 同步。
- 真实 PR CI context 只能在 PR 创建后回填；在此之前 AC-6 保持未完成。
