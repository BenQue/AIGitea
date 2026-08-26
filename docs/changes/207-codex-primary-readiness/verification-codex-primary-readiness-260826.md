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
status: verified
branch: change/207-codex-primary-readiness
created: 2026-08-26
updated: 2026-08-26
---

# Codex 主处理就绪验证记录

## 基线与范围

- Commit SHA: `de85f1d581a4bba524e057e087a95305ff510458`（manifest 实施 head；本验证记录的收口 commit 随后追加）
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
| `bash codex/tests/smoke.sh`（T01/T02） | PASS | 546 tests；exit 0 |
| 真实 `aisoft-platform-readiness.sh` | GAP（预期） | source PASS；installed Codex/Claude DRIFT；live repo PASS；live protection GAP |
| PR #209 初始 head `ab3fccd` Actions | PASS | run #715，event=pull_request，job=verify，41s，conclusion=success |
| PR #209 初始 commit status | PASS | 唯一 context `CI / verify (pull_request)`，state=success |
| `python3 -m unittest codex.runtime.tests.test_gitea_governance` | PASS | 14 tests；真实 context 已钉入 manifest 回归 |
| manifest 更新后的首次 `bash codex/tests/smoke.sh` | FAIL | 547 tests 中 2 项 host-access protection 夹具仍声明空 context；未削弱校验 |
| 修复夹具后 `bash codex/tests/smoke.sh` | PASS | 547 tests；exit 0 |
| PR #209 实施 head `de85f1d` Actions | PASS | run #717，event=pull_request，job=verify，40s，conclusion=success |
| PR #209 实施 head commit status | PASS | 唯一 context `CI / verify (pull_request)`，state=success |
| skills/runtime 安装 | NOT RUN | 本 Issue 禁止自动安装 |
| live branch protection apply | NOT RUN | 需要合并后独立授权 |
| 部署 | NOT RUN | 本 Issue 无部署 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | development 无 plan 返回 `T01`；production 对照拒绝 |
| AC-2 | PASS | 63 项 contract/controller 定向测试及最终 547 项全量测试 |
| AC-3 | PASS | 双工具入口、03/04/08 与 analyzer/spec/loop adapter 已统一；全量 smoke 通过 |
| AC-4 | PASS | 新增 Codex 原生 `issue-session-flow`，列出默认自动推进区间与硬升级条件 |
| AC-5 | PASS | 两个新 shell test 通过；真实检查如实投影 DRIFT/GAP，未执行 mutation |
| AC-6 | PASS | 初始与 manifest 实施 head 均真实读回 `CI / verify (pull_request)=success`；manifest 与回归测试已锁定该值 |
| AC-7 | PASS | 最终 547 项 smoke tests 与 ShellCheck 均通过 |
| AC-8 | PASS | Gitea 读回仅 PR #209 开放且 head/branch/Issue 精确；安装、live apply、部署保持 NOT RUN |

## 遗留风险与未完成项

- skills/runtime 安装、live branch protection apply 与部署均为 `NOT RUN`，不得宣称 live
  已与 source 同步。
- 真实 PR CI context 只能在 PR 创建后回填；在此之前 AC-6 保持未完成。
