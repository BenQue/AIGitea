---
issue: 210
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/210
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: required-context migration changes protected-main governance, CI enforcement, snapshot and rollback behavior, so it is a forced complex platform change.
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-required-context-migration-260826.md
  spec: spec-required-context-migration-260826.md
  plan: plan-required-context-migration-260826.md
  verification: verification-required-context-migration-260826.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/210-required-context-migration
pr_url:
created: 2026-08-26
updated: 2026-08-26
---

## 问题/需求总结

Issue #207 / PR #209 已用两个真实成功的 pull-request Actions 与 commit status，将
AISoftPlatform 的 canonical required context 锁定为唯一的
`CI / verify (pull_request)`。merged source、installed Codex/Claude 与 live repository
均通过 readiness，但 live `main` 仍未启用 status check，context 为空。

现有 governance planner 正确报告 `update-main-protection`，同时以
`status-check-context-drift` 阻止 apply；`reconcile.py` 在 snapshot 和 PATCH 前 fail closed。
这保护了任意 drift，却也缺少把已经由真实 PR evidence 批准的 canonical context 安全迁移到
live 的窄路径。

## 影响范围

- `aisoft_gitea_governance` 的 manifest 合同、plan/apply/rollback 与 evidence 校验。
- `gitea-governance.sh` 的 exact-repository CLI surface。
- governance runtime 单测、shell smoke 入口与运维回滚说明。
- 不涉及 live apply、身份/权限、visibility、merge 能力或部署。

## 初步方案与建议

引入一个 manifest-declared、repo-scoped 的 migration evidence 合同。调用方只能选择
manifest 中已经声明 evidence 的 exact repository，不能传 URL、repo 或 context；runtime 再从
merged canonical manifest 读取唯一目标 context，并核对真实成功 pull-request status evidence。

只有 live protection 的 status-check enable/context 处于声明的迁移起点，且所有其它受管字段
精确等于 manifest 时，plan 才移除该特定 blocker。apply 必须先持久化 snapshot，PATCH 后完整
读回；失败使用同 snapshot rollback。其它 context drift 保持 fail closed。

## 风险

- evidence 绑定不严会把任意 context 注入 protected `main`。
- PATCH/read-back 若只校验 status context，可能静默改变 push、merge、approval 等保护字段。
- snapshot 写入顺序错误会让失败后无法确定性恢复。
- migration 入口若接受 caller-supplied target，会扩大 broker/governance 的权限面。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: required-context migration changes protected-main governance, CI enforcement, snapshot and rollback behavior, so it is a forced complex platform change.
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 修改 `aisoft_gitea_governance` shared runtime 与 protected-main apply/rollback 合同。
- 触及 required CI、安全边界与 live mutation 的 fail-closed 条件。
- 验收包含改动前 live baseline 与历史 PR status 的一次性现场证据，因此需要 verification。

### 缺失的 acceptance criteria 或决策

- 无。
