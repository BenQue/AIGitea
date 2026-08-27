---
issue: 213
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/213
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为单一应用仓库启用 routine merge source，并新增 PAT、身份、权限、安装、live apply、canary 与回滚治理，触发安全、共享核心、CI、回滚和平台治理强制 complex。
risk_flags:
  - security
  - shared-core
  - ci
  - rollback
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-routine-live-pilot-260827.md
  spec: spec-routine-live-pilot-260827.md
  plan: plan-routine-live-pilot-260827.md
  verification: verification-routine-live-pilot-260827.md
confidence: high
override_reason: ''
depends_on:
  - 35
  - 208
status: pr-open
branch: change/213-routine-live-pilot
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/214
created: 2026-08-27
updated: 2026-08-27
---

## 问题/需求总结

Issue #208 已合并通用 routine auto-merge source，但所有仓库仍 disabled，且现有
`host.access.audit` 即使 source/installed bytes 完全一致也不返回 routine credential、identity、scope、
permission、cross-project 与 merge allowlist 元数据。需要为唯一目标 `admin/NewEMaint` 建立一个先
fail closed、后经独立 live 授权才可执行一次真实 canary 的可逆 rollout source contract。

## 影响范围

- canonical governance/host-access manifests 中仅 NewEMaint 的 routine pilot 声明。
- routine merge POST 前的 PAT exact-scope 与 canary Issue gate。
- governance read-only account states、host access routine audit 和 cross-project permission readback。
- routine account/PAT bootstrap、PAT revoke、account retain/delete rollback 与 provenance gate。
- Mac/VM installer byte parity、定向测试、full smoke 与 rollout verification。

## 初步方案与建议

以 Issue #208 merge `8d109b14b6e0936be30f6f287ff6050e48632e0b` 和 Issue #35 merge
`69251fd4d07665385eb6d9142038848c2b9392d7` 为两个不可替代的历史锚，再要求 #213 最终 merged SHA
承载 byte-identical 当前 manifests。source 只将 NewEMaint opt-in，并把首个真实 routine merge 限定为
NewEMaint Issue #74；缺 account/PAT/collaborator/protection 任一层时均返回稳定 GAP/阻塞且 merge POST=0。

## 风险

- 只验证 identity、不验证 PAT exact scope，会让超权 token 进入唯一 merge POST 路径。
- source opt-in 与 live apply 混淆，会在 credential/protection 未就绪时产生假 PASS。
- 不区分 account missing 与 present-site-admin，会把需 bootstrap 与需安全处置的状态混为一谈。
- revoke 后隐式删除账号可能破坏审计归属；retain/delete 必须是显式、可读回的不同路径。
- 只记录 #208 或只记录 #35 都无法证明 routine source 与既有治理基线同时成立。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为单一应用仓库启用 routine merge source，并新增 PAT、身份、权限、安装、live apply、canary 与回滚治理，触发安全、共享核心、CI、回滚和平台治理强制 complex。
risk_flags:
  - security
  - shared-core
  - ci
  - rollback
  - agent-governance
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

- 变更触及 Gitea PAT custody/scope、non-admin account、repository Write、protected-main allowlist 与唯一 merge POST。
- 变更修改 canonical manifests、governance/host-access shared runtime、installer/bootstrap/rollback shell 和 CI smoke。
- 验收包含 source/installed/live 改动前后分层与未来一次性 live canary，不能只由 diff review 重放。

### 缺失的 acceptance criteria 或决策

- 无。
