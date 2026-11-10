---
issue: 444
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/444
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
branch: change/444-dev-complex-plan-required
created: 2026-11-10
updated: 2026-11-10
---

# 开发阶段 complex 一律要求 plan · 实施计划

## 全局约束与接口

- 合同以映射 spec 为准；未决问题 a/b/c 在确认点 1 定案后写入 spec，本计划按定案执行。
- 治理文件（路由表、技能、AGENTS、使用合同、模板）在 T01 独立 commit 后 STOP，fresh run 重读批准合同与 diff 再进 T02。
- 停止条件：合同冲突、范围扩张、同一根因连续三次失败。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 路由表与全部文档措辞改为开发阶段 complex 要求 plan | - | pending |
| T02 | runtime 文档义务、旧合同兼容与测试 | T01 | pending |
| T03 | 发布 bundle 1.24.0、全量验证与交叉审查证据 | T02 | pending |

## T01：路由表与文档措辞

- **交付/范围**：`route-policy.md` D3 plan → `required`，相关段落改写；git_scope 内分册、技能、模板、使用合同、GLOSSARY 同步。
- **blocked_by**：无
- **AC**：AC-1（表本身）、AC-5
- **接口/约束**：不改推导表与技能列；不改 change 模板。
- **验证**：`rg` 旧表述（`含高风险 flag 时另写 plan`、`require a plan only when`、`无高风险 flag 的 development complex`）只剩兼容描述。
- **Expected**：无现行规则仍写免 plan。
- **停止条件**：治理 commit 后 STOP，fresh run 再继续。

## T02：runtime 与测试

- **交付/范围**：`classification.py` development complex 最小文档含 plan；`ticket_execution.py` D3 旧合同兼容；`route_policy.py`、`contract.py` 注释；四个测试文件更新与新增用例。
- **blocked_by**：T01
- **AC**：AC-1、AC-2、AC-3、AC-4
- **接口/约束**：兼容判据只读 summary 的 `status` 与 `required_docs`。
- **验证**：`python3 -m unittest discover codex/runtime/tests`；反向证明：去掉兼容分支跑对应用例变红后恢复。
- **Expected**：全绿；反向证明红在兼容用例。
- **停止条件**：同上。

## T03：发布与验证

- **交付/范围**：`usage-bundle.sh --release` 发 1.24.0；`bash codex/tests/smoke.sh`；Codex 交叉审查；verification 与 review-evidence-index 行。
- **blocked_by**：T02
- **AC**：AC-6、AC-7、AC-8
- **接口/约束**：未运行写 NOT RUN。
- **验证**：smoke 退出码 0；bundle status 读回 1.24.0。
- **Expected**：PASS；交叉审查 PASS。
- **停止条件**：同上。

## Expected touch points

- T01：route-policy.md、AGENTS.md、usage/CONTRACT.md、templates/project/AGENTS.md、03、08、GLOSSARY.md、skills 下各 SKILL.md 与 references。
- T02：codex/runtime/aisoft_loop 与 codex/runtime/tests。
- T03：usage/bundle.json、docs/governance/review-evidence-index.md、本目录 verification。

## 数据库迁移

无。
