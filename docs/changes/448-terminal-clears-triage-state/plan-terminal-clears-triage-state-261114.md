---
issue: 448
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/448
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
branch: change/448-terminal-clears-triage-state
created: 2026-11-14
updated: 2026-11-14
---

# 终态写入清除 triage 状态标签 · 实施计划

## 全局约束与接口

- 合同以映射 spec 的「方案与决策」D1–D5 为准。
- 不新增 broker 操作，不改参数集合与 manifest；只改 `_set_issue_lifecycle` 的维度与守卫。
- 存量清理（D5）与两台重装是合并后的 installed/live 动作，不在本 PR 的 ticket 里执行。
- 停止条件：合同冲突、范围扩张、同一根因连续三次失败。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | broker 终态写入清除 triage 状态、wontfix 拒写，两条来源的单测与反向证明 | - | pending |
| T02 | 03、triage-labels 文档与模板、使用合同措辞，发布包发版 | T01 | pending |
| T03 | 全量验证、Codex 交叉审查、verification 与证据索引、重装与清理步骤 | T02 | pending |

## T01：broker 行为与单测

- **交付/范围**：`broker.py` 的 `_set_issue_lifecycle` 在目标为 `completed`/`deployed` 时把 triage 状态（`triage/*` 减 category）并入被替换的维度，`triage/wontfix` 在守卫里拒写；`contract.py` 中「neither can drop ... triage/」注释同步。`test_host_access.py` 改写原先钉住「终态保留 `triage/ready-for-agent`」的断言，新增 AC-1–AC-4 用例；`test_project_declared_source.py` 加项目来源用例。
- **blocked_by**：无
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5
- **接口/约束**：返回体形状不变；拒写用 `REQUEST_DENIED`；category 字面量带注释说明来源。
- **验证**：先写用例在旧代码上跑，记录变红；实现后 `python3 -m unittest codex.runtime.tests.test_host_access codex.runtime.tests.test_project_declared_source`（按仓库现有调用方式）全绿。
- **Expected**：新用例旧代码红、新代码绿；既有 lifecycle 用例除被改写的那条外不变。
- **停止条件**：同全局。

## T02：文档与发版

- **交付/范围**：`03` §4 Matt triage 段补终态收口规则；`docs/agents/triage-labels.md` 与 `templates/docs/agents/triage-labels.md` 同步一句；`usage/CONTRACT.md` 的 complete 行按需补一句；`usage-bundle.sh --release` 发新版本。
- **blocked_by**：T01
- **AC**：AC-6
- **接口/约束**：先 `rg` 测试目录确认没有钉住被改的短语；发布包版本按 `usage-bundle.sh` 规则取下一个号。
- **验证**：`bash codex/tools/usage-bundle.sh` 校验；`aisoft check-change-documents`。
- **Expected**：校验通过，模板与平台自用副本一致。
- **停止条件**：同全局。

## T03：验证、交叉审查与收尾准备

- **交付/范围**：`python3 -m unittest discover codex/runtime/tests`、`bash codex/tests/smoke.sh`；经 Herdr 可见会话请 Codex 只读审查候选 head；verification 记录真实结果、反向证明、交叉审查、两台重装命令与读回步骤、D5 清理命令；`docs/governance/review-evidence-index.md` 加一行。
- **blocked_by**：T02
- **AC**：AC-5、AC-7
- **验证**：命令真实运行，未运行写 NOT RUN。
- **Expected**：全绿；交叉审查 PASS 或修复后 PASS。
- **停止条件**：同全局。

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/aisoft_host_access/contract.py`、`codex/runtime/tests/test_host_access.py`、`codex/runtime/tests/test_project_declared_source.py`
- T02：`03-Issue-Spec-Plan与单闸门开发流程.md`、`docs/agents/triage-labels.md`、`templates/docs/agents/triage-labels.md`、`usage/CONTRACT.md`、`usage/bundle.json`
- T03：本目录 verification、`docs/governance/review-evidence-index.md`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | T01 单测：终态写入移除状态、保留 category 与其他维度 |
| AC-2 | T01 单测：已终态重写为 updated；已正确为 no-op 无 PUT |
| AC-3 | T01 单测：wontfix 拒写无 PUT |
| AC-4 | T01 单测：非终态写入不碰 triage；降级仍拒绝 |
| AC-5 | 反向证明记录 + 全量 unittest + smoke |
| AC-6 | usage-bundle 校验 + 文档 diff review |
| AC-7 | verification 中的命令与步骤；合并后 Issue 评论 |

## 执行证据

<!-- execution-evidence:start -->
尚未执行。实际记录 ticket_base、起始状态、provider/入口来源、验证结果、candidate_head、
审查范围与 findings；可引用本 Issue 映射 verification，不另建证据权威。
<!-- execution-evidence:end -->

## 部署与回滚

无应用部署。installed 层：合并后负责人两台重装 broker（Mac 与 VM），命令写在 verification；回滚为 revert 后同命令重装。
