---
issue: 440
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/440
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
depends_on: []
branch: change/440-preprod-batch-flow
created: 2026-11-09
updated: 2026-11-09
---

# 实施计划

## 全局约束与接口

- 「开发阶段」只用既有 `change_control: development` 表达，不加字段；缺省与回落值仍是 `production`。
- `confirm` 的唯一来源是 route-policy 推导表 + 细化规则 `C1`；其余文档引用它，不复述规则表。
- broker、`open-pr`、推送守卫、终态工具、`project.json` 模板与 schema 不改。
- 治理文件（技能、路由表、使用合同、项目 AGENTS 模板）在 T01 单独 commit 后 STOP，fresh run 重读合同再做 T02。
- 停止条件：需要改 broker/推送守卫语义、需要新增机器字段、或 D2–D4 与实现冲突时停下升级。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理与合同文本：route-policy `C1` 与 confirm 闭集、`03` 开发阶段节与来历行、CONTRACT §2/§3/§5、项目 AGENTS 模板、issue-session-flow、aisoft-platform 技能与 getting-started/greenfield-planning/execution-adapter、GLOSSARY、USER-GUIDE | - | pending |
| T02 | runtime 与测试：`resolve_route` 应用 `C1`，`contract` 闭集 `{1,2}` 与 `complex-production` 只配 `2`；路由/合同/会话钉子测试 | T01 | pending |
| T03 | 发布包 1.23.0、全量 smoke、verification、审查证据索引行、Codex 交叉审查 | T02 | pending |

## T01：治理与合同文本

- **交付/范围**：按 spec D2–D4 写入规则。route-policy 细化规则表追加 `C1 | change_control: development | confirm 改为 1`，
  取值闭集 `confirm` 改为 `1`, `2`，说明 `confirm` 含义。`03` §1 增「开发阶段（首次生产发布前）」小节；CONTRACT §2 两个确认点
  一条加开发阶段例外与批次 Issue，§3 加单向切换不变量，§5 `open-pr` 行去掉「确认点 2 之后」的绝对说法。
  issue-session-flow 的确认点 2 节加 `confirm: 1` 段，自主推进节写明 `confirm: 1` 时 `approved` 授权 push/PR。
- **blocked_by**：无。
- **AC**：AC-2、AC-3（文本部分）。
- **验证**：`rg -n "确认点 2" skills usage templates` 逐处复核不与 `confirm: 1` 矛盾；`git diff --stat` 只含 `git_scope` 文件。
- **Expected**：生产阶段原文仍完整可读；不覆盖 runtime 行为。
- **停止条件**：同全局。commit 后 STOP，fresh run 重读 spec、本 plan 与 T01 diff。

## T02：runtime 与测试

- **交付/范围**：`route_policy.resolve_route` 校验细化规则顺序为 `M1,V1,S1,P1,G1,C1`、条件与动作字面量，`C1` 命中时
  `confirm` 取规则值并记入 `matched_rules`；否则 `2`。`contract.ROUTE_VALUES['confirm']` 为 `{"1","2"}`，`validate_route`
  拒绝 `complex-production` + `1`。测试：R2/R5 development 得 `1`、production 得 `2`、R1 不受影响的现有断言更新、
  合同负例、会话技能钉子。
- **blocked_by**：T01。
- **AC**：AC-1、AC-3。
- **验证**：`python3 -m unittest discover -s codex/runtime/tests -t codex/runtime`（或 smoke 内同等调用）。
- **Expected**：全部通过；未运行写 NOT RUN。
- **停止条件**：同全局。

## T03：发布与审查

- **交付/范围**：`codex/tools/usage-bundle.sh --release 1.23.0 --compatibility minor --notes …`；`bash codex/tests/smoke.sh`；
  写 verification（真实命令与结果、交叉审查表）；`docs/governance/review-evidence-index.md` 追加 #440 行；
  Codex（gpt-6-astra / high，Herdr 只读窗格）审查候选 head 至 PASS。
- **blocked_by**：T02。
- **AC**：AC-4、AC-5。
- **验证**：smoke 输出、`aisoft classify --verify 440` 读回 `projected`。
- **停止条件**：同全局；审查同因三轮 FAIL 升级给人。

## Expected touch points

- T01：route-policy.md、`03`、CONTRACT.md、USER-GUIDE.md、templates/project/AGENTS.md、issue-session-flow、aisoft-platform SKILL 与三份 reference、GLOSSARY。
- T02：route_policy.py、contract.py、test_route_policy.py、test_contract.py、test_session_contract.py。
- T03：usage/bundle.json、verification、review-evidence-index.md。

## 数据库迁移

无。
