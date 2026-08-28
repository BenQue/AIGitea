---
issue: 219
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/219
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 #213/#215/#217 已定义的 bootstrap 前只读治理计划能力，并让 governance 与 host-access 对 Gitea 1.26.4 官方 collaborator permission 扩展响应执行有界、身份绑定、fail-closed 的兼容解析；变更触及 security、shared core 与平台治理，强制 complex/manual。
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
  summary: summary-permission-payload-compat-260828.md
  spec: spec-permission-payload-compat-260828.md
  plan: plan-permission-payload-compat-260828.md
  verification: verification-permission-payload-compat-260828.md
confidence: high
override_reason: security 与 shared governance/host-access runtime 风险使既有行为恢复仍强制 complex
depends_on:
  - 217
status: approved
branch: change/219-permission-payload-compat
pr_url:
created: 2026-08-28
updated: 2026-08-28
---

## 问题/需求总结

#217 已使 configured routine account 明确 missing 且 target permission GET 返回 404 时，governance
`check` 能形成 evidence-derived planned action。#217 合并并安装后，真实只读 readback 暴露另一层兼容缺口：
Gitea 1.26.4 对 collaborator permission 的 HTTP 200 response 是
`permission + role_name + user`，而 governance strict parser 只接受 exact `{permission}`，因此 installed
`check --repository NewEMaint` 以 `collaborator permission response is invalid` 退出，无法给出可信计划。

## 影响范围

- `aisoft_gitea_governance.reconcile` 的 target 与 cross-project collaborator permission 解析。
- `aisoft_host_access.broker` 中同一 endpoint 的 manager/project/routine/cross-project readback，防止 account
  provision 后再次撞到相同 1.26.4 payload gap。
- governance/host-access 的 legacy、actual-extended、安全负例、404 隔离、ordering 与 zero-mutation tests。
- 本 Issue 四份 semantic docs 与改前/改后分层验证记录。

不修改 canonical manifests、credential、account/PAT、collaborator/protection、required CI、allowlist、merge 或部署状态。

## 初步方案与建议

定义两个且只有两个顶层 variant：legacy exact `{permission}`；Gitea 1.26.4 extended exact
`{permission, role_name, user}`。两者都要求 `permission` 为既有 allowlist string。extended 额外要求
`role_name` 为同一 allowlist string 且 exact 等于 `permission`；`user` 只能包含官方 v1.26.4 `User`
schema 的已知字段，至少要求 `login`、`username`、`is_admin`，并将两个 identity 字段 exact 绑定到当前
请求的 collaborator，`is_admin` 必须是 boolean `false`。其余已知 metadata 只在类型验证后忽略，未知 nested
字段继续 fail closed。

请求 identity 必须由当前 repository contract 与 fixed call graph 派生并显式传给 validator；不得从 response、
CLI/env 或可写 snapshot 反推。#217 的 exact account-missing + target 404 分流保持原样；任何其它 404、auth、server、
transport、schema、identity 或 security drift 都不得降级。

## 风险

- 直接删除 extra-field 检查会接受任意 root/nested payload，掩盖 API 漂移或身份替换。
- 只检查 `permission` 而不约束 `role_name` 会吞掉互相矛盾的 repo role evidence。
- 只检查 `user` 是 object 而不绑定 login/username/is_admin，会让另一个 identity 或 site-admin payload 冒充目标。
- 只修 governance 会让未来 account provision 后的 `host.access.audit` 在同一 Gitea 1.26.4 schema 上再次失败。
- 把目标描述成 `PASS` 会混淆“parser 可读”与“live account/PAT/apply 已完成”；预期仍是可信 `DRIFT/GAP`。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 #213/#215/#217 已定义的 bootstrap 前只读治理计划能力，并让 governance 与 host-access 对 Gitea 1.26.4 官方 collaborator permission 扩展响应执行有界、身份绑定、fail-closed 的兼容解析；变更触及 security、shared core 与平台治理，强制 complex/manual。
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
override_reason: security 与 shared governance/host-access runtime 风险使既有行为恢复仍强制 complex
```

### 判级证据

- 产品合同影响为 `restore`：恢复已承诺的只读 GAP/planned-action 能力，不新增 live mutation 或 merge 能力。
- touched parser 处理 manager audit credential、repository permission、cross-project isolation 与 apply 前安全门。
- 验收包含只能在当前 installed/live 1.26.4 环境观察的改前 payload shape 和错误，因此需要独立 verification。

### 缺失的 acceptance criteria 或决策

- 无。两个 variant、identity/security 校验、404 隔离、mutation=0、manual policy 与后置 live rollout 均已固定。
