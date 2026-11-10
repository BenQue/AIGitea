---
issue: 445
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/445
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
depends_on: []
branch: change/445-project-template-scope
created: 2026-11-10
updated: 2026-11-10
---

# Plan：项目来源规范模板 scope

## 全局约束与接口

负责人已确定：只更新 fresh main 已存在的规范模板，首次新增仍拒绝；不得把项目声明、`git_scope` 或 summary 状态冒充独立授权。只在本票 claimed 工作区工作，不触碰 #444 或项目 #98 工作区。站点登记、真实项目数据、凭据、全局安装、部署、merge 均不在范围。治理变更本地提交后 STOP，fresh run 重读再执行 runtime。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 固化已批准的模板来源安全边界 | - | in-progress |
| T02 | 在项目来源实现边界并验证安全拒绝 | T01 | pending |
| T03 | 验证完整流程、发布包候选及独立审核 | T02 | pending |

## T01：治理边界

- **交付/范围**：按负责人选择补充 ADR 0003 D4 与本票合同：仅更新 fresh main 已存在模板，首次新增拒绝；明确项目来源和站点来源的信任差异，不重写历史。
- **blocked_by**：无。
- **AC**：AC-1, AC-2。
- **验证**：审查 ADR 与 spec 的约束一致性并运行 `aisoft check-change-documents`。
- **Expected**：安全选择、范围、非目标和回滚边界明确；没有运行时行为变更。
- **停止条件**：真实安全边界不清或治理 commit 完成；提交治理后 STOP/fresh run。

## T02：来源与范围守卫

- **交付/范围**：实现与 fresh main 的 exact 路径逐一绑定的项目来源模板上下文；新增首次创建、main/HEAD 漂移等负向隔离 Git/broker fixture，保留站点来源行为。
- **blocked_by**：T01。
- **AC**：AC-1, AC-2, AC-3。
- **验证**：运行 `PYTHONPATH=codex/runtime python3 -m unittest tests.test_project_declared_source tests.test_main_integration`；覆盖身份、scope、类型、符号链接、历史和远端移动。
- **Expected**：合法情形通过、全部越界情形拒绝；不访问真实服务或更改权限。
- **停止条件**：须改变已批准的安全假设、身份/授权模型不成立或试验涉及真实数据时停止。

## T03：端到端与交叉审核

- **交付/范围**：验证 open-pr 的隔离首推、PR 查重、回填和第二次推送；形成新的使用包候选并核对并行 #444 的发布基线；对固定候选安排独立 Claude 审核。
- **blocked_by**：T02。
- **AC**：AC-4, AC-5, AC-6。
- **验证**：运行 `PYTHONPATH=codex/runtime python3 -m unittest tests.test_project_source_e2e`、`bash codex/tests/smoke.sh`、`bash codex/tools/usage-bundle.sh --verify`；核对固定 BASE/HEAD 与审核报告。
- **Expected**：fixture 和必要回归通过，包成员与版本一致；source、安装、项目采用和真实远端结果分别记录，未运行项为 NOT RUN。
- **停止条件**：#444 发布状态冲突、需安装/部署/迁移或远端执行超出授权时停止。

## Expected touch points

- T01：`docs/adr/0003-adoption-access-decoupling.md` 与本票合同。
- T02：`codex/runtime/aisoft_host_access/project_source.py`、`codex/runtime/aisoft_main_integration.py` 及对应 tests。
- T03：项目来源 E2E fixture、`usage/bundle.json`、本票 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 项目来源合法模板 push fixture |
| AC-2 | 防越权和 site source 回归测试 |
| AC-3 | Git/broker fixture 的正向与负向覆盖 |
| AC-4 | 项目来源 open-pr E2E fixture |
| AC-5 | bundle verify、版本与发布基线检查 |
| AC-6 | 同一候选 HEAD 的独立 Claude 审核与真实验证记录 |

## 部署与回滚

本票不安装或部署；回滚与项目重新采用须分别确认。
