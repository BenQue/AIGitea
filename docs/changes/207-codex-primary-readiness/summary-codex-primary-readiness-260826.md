---
issue: 207
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/207
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: Codex 主处理涉及 Controller、Agent 行为、CI 合同与共享平台说明，触发平台治理强制 complex。
risk_flags:
  - agent-governance
  - ci
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-codex-primary-readiness-260826.md
  spec: spec-codex-primary-readiness-260826.md
  plan: plan-codex-primary-readiness-260826.md
  verification: verification-codex-primary-readiness-260826.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/207-codex-primary-readiness
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/209
created: 2026-08-26
updated: 2026-08-26
---

## 问题/需求总结

Codex 将承担大部分 AISoftPlatform Issue，但当前 development complex 的 Controller
frontier 选择与分类路由不一致，双工具 skills/说明存在可验证的数字和语义漂移，平台
PR 的 required CI context 也尚未形成真实闭环。

## 影响范围

- `aisoft_loop` 合同加载与 frontier 选择。
- Codex/Claude 的平台入口、会话入口、模板和主流程说明。
- Codex 与 Claude 已安装 skill 的只读漂移检查。
- AISoftPlatform 自身 PR CI context 的证据与 canonical governance manifest。

## 初步方案与建议

先修复可复现的 Controller 缺口并补 production 对照测试，再以当前 runtime/manifest 为
事实源统一双工具说明；增加只读 readiness 检查而不自动安装。最后通过本 Issue 的真实
PR 读取成功 context，只有证据成立后才更新 canonical manifest。

## 风险

- 错误放宽 production complex 会绕过 plan 硬门。
- skills、模板与文档若分别维护，可能再次形成第二套流程。
- 把 workflow 文件名猜成 required context 会产生无法满足的保护规则。
- 本 PR 不执行 live protection apply 或全局安装；这些状态必须保持 `NOT RUN`。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: Codex 主处理涉及 Controller、Agent 行为、CI 合同与共享平台说明，触发平台治理强制 complex。
risk_flags:
  - agent-governance
  - ci
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `Classification.route(change_control="development")` 会为 complex 移除 plan，但
  `select_frontier_ticket` 仍要求唯一 plan。
- canonical label manifest 已是 10 个 type、2 个 complexity、8 个 lifecycle、7 个
  triage，共 27 个；多个工具入口仍写旧值。
- 验收依赖本 PR 的一次真实 CI context 观测，不能只靠 diff review 重放，因此需要
  `verification`。

### 缺失的 acceptance criteria 或决策

- 无。
