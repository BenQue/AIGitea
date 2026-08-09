---
issue: 66
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/66
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 docker-release/v2 对合法外部敏感环境变量引用的误判，同时保持其它 artifact、target 和 state 敏感字段边界 fail closed
risk_flags:
  - security
  - external-contract
  - shared-core
  - artifact
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-external-env-secrets-260809.md
  spec: spec-external-env-secrets-260809.md
  plan: plan-external-env-secrets-260809.md
  verification: verification-external-env-secrets-260809.md
confidence: high
override_reason: ''
depends_on: []
status: implementing
branch: change/66
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

## 问题/需求总结

`docker-release/v2` producer 必须把 normalized Compose model 固定为 release bytes，并由
`verify-target` 与 target-side `docker compose config` model 做精确相等比较。合法 model 因而需要保留
`JWT_SECRET: "${JWT_SECRET:?required}"` 等外部环境变量引用，但当前
`load_release_artifact()` 在 Compose security validation 前对整个 model 使用通用敏感 key 扫描，
仅因 `JWT_SECRET` 的键名即拒绝 artifact。

这与 Compose contract 已有的“environment value 必须是外部引用”规则冲突，并阻塞 NewEmaint
Issue #59 对 PR #64 merged `docker-release/v2` 的采用。

## 影响范围

- normalized Compose model 的敏感字段扫描与外部引用语法。
- producer artifact、target-side Compose model、CLI/runner 与 phase regression tests。
- docker-release/v2 adopter guidance 和本 Change 的确定性验证记录。

不修改 manifest、architecture lock、offline inventory、target profile 或 state 的通用敏感字段规则；
不修改 producer/target model equality、compatibility matrix 或任何消费项目。

## 初步方案与建议

使用 Compose 专用的路径感知扫描：仅当当前字段精确位于
`services.<service>.environment.<key>`，且 value 精确为 `${NAME}` 或
`${NAME:?required}` 时，敏感命名的 key 才可通过。其它位置继续调用相同的通用敏感 key 规则；
`${NAME:-literal}`、`${NAME:+literal}`、literal URL/Secret/token/password 与未知敏感字段全部拒绝。

同一检查同时用于 producer artifact loader 与 Compose security validator，防止 target-side model
绕过。`verify-target` 仍在两边分别验证后执行 byte-equivalent Python model equality。

## 风险

- 路径判断过宽会把未知字段或嵌入默认值的表达式误当外部引用，造成 credential 进入 release bytes。
- 路径判断过窄会继续阻塞合法 adopter；必须覆盖 `JWT_SECRET` 与 `DATABASE_URL` 的正例。
- 只修 producer loader 而不修 target-side Compose validator 会造成两阶段语义不一致。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 docker-release/v2 对合法外部敏感环境变量引用的误判，同时保持其它 artifact、target 和 state 敏感字段边界 fail closed
risk_flags:
  - security
  - external-contract
  - shared-core
  - artifact
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 修改共享 `docker-release/v2` artifact/security contract，命中 security、external contract、shared
  core 与 deployment 强制 complex 规则。
- Issue #66 已提供可测正反例、zero-call 边界、equality 边界和明确非目标，不存在会改变实现方向的未决问题。
- 用户明确要求完整 `docs/changes/66`、单一 `change/66`/PR、final-head CI 与人工 merge。

### 缺失的 acceptance criteria 或决策

- 无。Issue #65 真实 Docker E2E、NewEmaint 修改、deployment、Secret/数据库与 Gitea 权限均明确排除。
