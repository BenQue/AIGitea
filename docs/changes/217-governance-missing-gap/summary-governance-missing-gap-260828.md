---
issue: 217
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/217
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 #213/#215 后 governance check 在 routine account 明确缺失且 exact collaborator permission 返回 404 时仍无法生成只读计划的缺陷；变更触及 security、shared governance runtime 与平台治理，强制 complex/manual。
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
  summary: summary-governance-missing-gap-260828.md
  spec: spec-governance-missing-gap-260828.md
  plan: plan-governance-missing-gap-260828.md
  verification: verification-governance-missing-gap-260828.md
confidence: high
override_reason: security 与 shared governance runtime 风险使既有行为恢复仍强制 complex
depends_on:
  - 215
status: approved
branch: change/217-governance-missing-gap
pr_url:
created: 2026-08-28
updated: 2026-08-28
---

## 问题/需求总结

#215 已使 supported `host.access.audit` 在 NewEMaint routine account、PAT、collaborator 均未 provision
时返回结构化 `GAP`。后续只读 live preflight 发现，installed/source
`aisoft_gitea_governance.cli check --repository NewEMaint` 仍会在 account 明确 missing、exact
collaborator permission GET 返回 404/no-collaborator 的状态下失败，不能输出可信 planned actions。

本地独立重放确认当前 `_check` 先执行 `capture_snapshot`，再读取 account state；因此 exact permission
404 在 missing precondition 建立前就抛出 `ApiError`。该缺陷不授权通过 bootstrap/apply 把 live 状态
“修到可检查”，只允许先恢复只读规划能力。

## 影响范围

- `aisoft_gitea_governance.cli._check` 的 account-state/read-only planning 顺序。
- `aisoft_gitea_governance.reconcile` 的 exact collaborator permission 404 兼容分流。
- `codex/runtime/tests/test_gitea_governance.py` 中 missing/present/schema/auth/ordering/apply regression。
- 本 Issue 四份 semantic docs 与验证记录。

不修改 canonical manifests、host-access typed operations、live account/PAT/collaborator/protection 或部署合同。

## 初步方案与建议

`check` 先以 exact account endpoint 固定 project/routine account 三态，再把明确 `missing` identity 集合作为
只读 evidence 传入 snapshot 与 cross-project audit。只有该集合中的 exact identity 对应 permission GET
返回 HTTP 404 时才投影 `missing`；200 仍进入 exact `{permission: string}` parser，account present 的 404
与所有 401/403/5xx/transport 继续 fail closed。

`apply_repository` 不传 missing evidence，并继续先验证 enabled routine account 为 exact non-admin；其
pre-snapshot-before-write、blockers、target Write、protection readback 与 mutation ordering 不变。

## 风险

- 若把任意 collaborator 404 当 missing，会掩盖 repository/ACL/identity drift。
- 若在 account read 之前形成 missing，会重现 #215 修复前的非证据化兼容。
- 若复用兼容分支到 apply，会让 live mutation 在 account 尚未安全 provision 时继续。
- 若放宽 200 permission schema，会吞掉额外字段、未知权限或类型漂移。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 #213/#215 后 governance check 在 routine account 明确缺失且 exact collaborator permission 返回 404 时仍无法生成只读计划的缺陷；变更触及 security、shared governance runtime 与平台治理，强制 complex/manual。
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
override_reason: security 与 shared governance runtime 风险使既有行为恢复仍强制 complex
```

### 判级证据

- 产品合同影响为 `restore`：恢复 #213/#215 已要求的 bootstrap 前可读 `GAP`，不新增 live 能力。
- touched runtime 处理 manager audit credential、repository collaborator permission 与 apply 前安全门。
- 验收包含改前只读 defect replay、ordering 与本地 planned-action 证据，不能只由 diff review 重放。

### 缺失的 acceptance criteria 或决策

- 无。Issue 已固定 exact missing/404 分流、严格失败边界、read-only ordering、manual policy 与 live mutation=0。
