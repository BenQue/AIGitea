---
issue: 215
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/215
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Issue #213 AC-6 已定义的 routine 未 provision 状态审计兼容性；变更触及 security、shared host-access runtime 与平台治理，强制 complex/manual。
risk_flags:
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-routine-missing-audit-260827.md
  spec: spec-routine-missing-audit-260827.md
  plan: plan-routine-missing-audit-260827.md
  verification: verification-routine-missing-audit-260827.md
confidence: high
override_reason: security 与 host-access 平台治理风险使既有行为恢复仍强制 complex
depends_on:
  - 213
status: approved
branch: change/215-routine-missing-audit
pr_url:
created: 2026-08-27
updated: 2026-08-27
---

## 问题/需求总结

Issue #213 合并后的 source 已要求 routine account、credential 或 repository apply 尚未完成时，
`host.access.audit` 返回可读 `GAP`，不能把 source opt-in 写成 live `PASS`。当前 NewEMaint routine
account 尚未创建时，account read 明确返回 404/missing；随后 cross-project collaborator permission 的
exact GET 同样返回 404/no-collaborator，却被送入只接受 200 permission object 的 strict parser，最终误报
`RESPONSE_SCHEMA_INVALID`，使预期的 rollout GAP 无法阅读。

## 影响范围

- `aisoft_host_access.broker.HostAccessBroker._access_audit` 的 routine cross-project permission readback。
- `codex/runtime/tests/test_host_access.py` 中 #213 audit 正向、负向与 ordering 回归。
- semantic docs 与本地验证记录。

不改变 live account、PAT、collaborator、protection、required CI、allowlist、安装或部署状态。

## 初步方案与建议

先读取并固定 routine account state。只有 account 明确为 `missing`，且某个 exact cross-project
collaborator permission GET 返回 404 时，才把该 repository 投影为结构化 `state: absent` evidence，
并保持整个 routine audit 为 `GAP`。所有 200 response 继续经过 exact schema/permission parser；
account present 时的 404、401/403/5xx、transport 和 malformed 继续 fail closed。

## 风险

- 把任意 404 都解释为 absent 会掩盖 account present 时的权限读回异常。
- 放宽 200 permission schema 会吞掉 Gitea schema drift 或异常权限值。
- 改变 target repository Write、routine identity/scope、merge allowlist 或 push/force 门会削弱 #213。
- 把 account missing 状态写成 `PASS` 会错误放行后续 live apply。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 Issue #213 AC-6 已定义的 routine 未 provision 状态审计兼容性；变更触及 security、shared host-access runtime 与平台治理，强制 complex/manual。
risk_flags:
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: security 与 host-access 平台治理风险使既有行为恢复仍强制 complex
```

### 判级证据

- 产品合同影响是 `restore`：不新增 rollout 能力，只恢复 #213 AC-6 已承诺的 readable GAP。
- touched runtime 处理 manager audit credential、cross-project permission 与 routine merger 安全边界。
- 必须重放真实 canonical broker read-only audit 与 security suites，证据不能只由 diff review 复现。

### 缺失的 acceptance criteria 或决策

- 无。Issue 已固定 exact missing/404 兼容路径、严格失败边界、mutation=0 与 manual policy。
