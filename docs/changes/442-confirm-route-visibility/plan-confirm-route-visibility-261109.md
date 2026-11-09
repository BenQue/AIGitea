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
branch: change/442-confirm-route-visibility
created: 2026-11-09
updated: 2026-11-09
---

# 实施计划

## 全局约束与接口

- 只改输出与错误文本；解析器语法、路由规则与 `confirm` 语义不变。
- 不触碰治理文件（技能、AGENTS、路由表、使用合同正文），本批无治理 STOP 点。
- 停止条件：需要放开 YAML 语法、改路由规则或改技能正文时停下升级。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | runtime 与测试：classify 路由行 confirm、resolve-route change_control、两个解析器的 flow 列表提示、summary 模板提示 | - | pending |
| T02 | 发布包 1.23.1、全量 smoke、verification、审查证据索引行、Codex 交叉审查 | T01 | pending |

## T01：runtime 与测试

- **交付/范围**：spec D1–D3。先写失败测试：`test-aisoft-entry.sh` 路由行钉 `· confirm`；`test_route_policy` 断言
  `resolve_issue_route` 含 `change_control`；`test_contract`/`test_classification` 断言 `[a, b]` 报错含 flow 提示且其它字符报错不变。
- **blocked_by**：无。
- **AC**：AC-1、AC-2、AC-3、AC-4（模板部分）。
- **验证**：`cd codex/runtime && python3 -m unittest tests.test_route_policy tests.test_contract tests.test_classification`；
  `bash codex/tests/test-aisoft-entry.sh`；反向证明删提示分支后红。
- **Expected**：先红后绿；未运行写 NOT RUN。

## T02：发布与审查

- **交付/范围**：`codex/tools/usage-bundle.sh --release 1.23.1 --compatibility patch --notes …` 与 `--verify`；
  `bash codex/tests/smoke.sh`；写 verification；`docs/governance/review-evidence-index.md` 追加 #442 行；
  Codex（gpt-6-astra / high，Herdr 只读窗格）审查候选 head 至 PASS。
- **blocked_by**：T01。
- **AC**：AC-4、AC-5。
- **验证**：smoke 输出、`aisoft classify --verify 442` 读回 `projected`。
- **停止条件**：同全局；审查同因三轮 FAIL 升级给人。

## Expected touch points

- T01：`codex/tools/aisoft`、`route_policy.py`、`contract.py`、`classification.py`、summary 模板、四个测试文件。
- T02：`usage/bundle.json`、verification、review-evidence-index.md。

## 数据库迁移

无。
