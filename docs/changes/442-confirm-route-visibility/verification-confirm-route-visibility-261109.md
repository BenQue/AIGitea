---
issue: 442
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/442
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
status: passed
branch: change/442-confirm-route-visibility
created: 2026-11-09
updated: 2026-11-09
---

# 验证记录：classify/resolve-route 显示 confirm 与 change_control

## 基线与范围

- Commit SHA：实现候选 `4ca698d4b2527f0a98ff69cf3e3e206141d6cec5`（之后只有本证据提交）
- 基线：`origin/main` = `064fadba`（#440 合并）
- 环境：Mac，源码 runtime；未重装任何 installer
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-5

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 先写测试、未改实现：`python3 -m unittest tests.test_route_policy tests.test_contract tests.test_classification`；`bash codex/tests/test-aisoft-entry.sh` | FAIL（预期） | `FAILED (failures=3, errors=1)`；entry `missing output:  · confirm 2` |
| 实现后同上 | PASS | `Ran 78 tests … OK`；`test-aisoft-entry: PASS`（发版后） |
| 反向证明：删掉 `contract._safe_scalar` 的 flow 列表提示分支，跑 `tests.test_contract.FlowListHintTests` | FAIL（预期） | `FAILED (failures=2)`；已还原 |
| 首次 smoke（HEAD `caa183d5`） | rc=3 | 模板 digest 漂移：summary 模板改动须同 PR `change-template-sync.sh --refresh-digest`；已刷新（`ff3e0b83`），spec `git_scope` 补 `codex/config/change-template-sync.json` |
| `bash codex/tests/smoke.sh`（HEAD `ff3e0b83`） | rc=0 | `Ran 816 tests … OK`；`Codex platform static smoke checks passed.` |
| `bash codex/tests/smoke.sh`（HEAD `4ca698d4`） | rc=0 | `Ran 816 tests … OK`；`Codex platform static smoke checks passed.` |
| `usage-bundle.sh --release 1.23.1 --compatibility patch`（R1 修复后从 `origin/main` 的 bundle.json 重发同号）与 `--verify` | PASS | `VERIFIED 1.23.1 sha256:eecd6c1111b0f3825a6b1cf91acf70754bf63edbe009b7edb44f6aa0f7eb7553` |
| `aisoft classify 442` | PASS | 路由行以 `· confirm 2` 结尾；文档预检 OK |
| `aisoft resolve-route 442 --provider claude --repo .` | PASS | `change_control: production`，`confirm: 2`，`differences: {}` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `test-aisoft-entry.sh` 钉 ` · confirm 2`；缺 `confirm` 的卡由 `test_contract.py` 既有「route keys」用例在合同校验处拒绝（R1 处置） |
| AC-2 | PASS | `test_cli_resolves_historical_summary_without_rewriting`：CLI 输出 `change_control: production`；阶段为 `development` 时输出 `development` 且 `confirm: 1` |
| AC-3 | PASS | `FlowListHintTests` 与 `test_flow_list_is_rejected_with_the_supported_spelling`；`[]` 仍接受、`&` 与 `{` 报错原文不变；反向证明见上表；审查方对两函数各 1,892 个输入比较 BASE/HEAD 接受范围一致 |
| AC-4 | PASS | summary 模板 HTML 注释写明逗号分隔；digest 已刷新；发布包 `VERIFIED 1.23.1`；smoke rc=0 |
| AC-5 | PASS | 见下节，R2 PASS |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex gpt-6-astra / high（hc 终端 `review-442`，Herdr 空间 `~` 标签页 `review-442` 可见，`--sandbox read-only --ask-for-approval never`） | `ff3e0b8397d1b3567d165d0192762a7537d9263b` | FAIL | 1 P2：`confirm ?` 兜底不可达（合同校验先拒绝缺键卡）。处置：展示层直接读 `route['confirm']`，spec D1 改写为由合同校验拒绝 |
| 2 | Claude | 同上，同一终端 | `4ca698d4b2527f0a98ff69cf3e3e206141d6cec5` | PASS | R1 fixed，新发现无；审查方在只读沙箱跑 23 项定向测试、发布包校验、digest 重算与 shellcheck，全量 smoke 由实现方实跑（上表） |

## 遗留风险与未完成项

- 下游项目的 vendored change 模板在本票之前就已过期（HSDB、NewEMaint、SFMDigitalBoard 四份，LocalWMS 的 summary），随各项目采用 1.23.1 同步；本票不改下游。
- 本机技能与 runtime 未重装；合并后由人按 issue-session-flow「平台仓重装读回」重装（`NOT RUN`）。
