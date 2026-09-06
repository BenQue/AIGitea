---
issue: 270
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/270
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - deployment
depends_on:
  - 268
status: approved
branch: change/270-company-platform-bootstrap
created: 2026-09-06
updated: 2026-09-06
---

# Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立严格 bundle、verify-handoff、schema/模板与可重复/负向测试 | - | complete |
| T02 | 脱敏 inventory、采用分流、apply/readback/rollback 和六类动作合同/测试 | T01 | complete |
| T03 | runbook、兼容回归、双轴审查、真实证据与最终 PR 卡 | T02 | complete |

## Expected touch points

- T01/T02：platform-bootstrap/；codex/runtime/aisoft_platform_bootstrap/；codex/runtime/tests/test_platform_bootstrap.py。
- T03：同上、README.md 导航、本目录四角色文档。现有 company-delivery 不修改。
- 每个本地提交包含 #270 与 Txx。全部在 exact worktree，本任务是唯一实施所有者，不改其他 Issue 的工作区。

## 验收映射

| AC | 验证 |
|---|---|
| AC-1/AC-3/AC-5 | test_platform_bootstrap 的 CLI 与 archive 集成测试；clean actual source 两次构建记录 |
| AC-2/AC-4 | 采用决策矩阵、每类动作前置/no-op/故意失败/恢复测试 |
| AC-6 | 命令块行数、check-change-documents、diff check、分层验证记录 |
| 兼容性 | test_company_delivery 与 Python runtime suite；新增 shell 入口的 bash -n、smoke、可用时 ShellCheck |

## 数据库迁移与部署

无。新工具 source 可普通 revert。现场 rollback 只提供版本化合同/dry-run，不触碰 Gitea DB、配置或已存在仓库；first-install 回退恢复 uninstalled 状态，adopt 使用核验过的 snapshot identity。合并不包含现场执行授权。

## T03 完成回执

双轴审查代码 finding 全部关闭，35 targeted 与完整 C-locale smoke（734 Python tests）PASS；默认 locale F8 外部 GAP 单列。
实际 clean implementation pin、archive/handoff 摘要、两次构建、checksum/identity 拒绝、rollback dry-run/unbound executor 负向及未执行层次见 verification。
当前状态 `AWAITING_PR_CONFIRMATION`，唯一最终 PR 尚待用户确认；本轮不 push/PR/merge/deploy。
