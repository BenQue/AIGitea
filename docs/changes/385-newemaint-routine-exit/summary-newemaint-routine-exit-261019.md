---
issue: 385
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/385
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: NewEMaint 的 routine 合并声明从 governance 与 host-access 两份 manifest 撤下，改变 broker 授权面与 audit 行为，属于认证权限与平台治理变更
risk_flags:
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-newemaint-routine-exit-261019.md
  spec: spec-newemaint-routine-exit-261019.md
  plan: plan-newemaint-routine-exit-261019.md
  verification: verification-newemaint-routine-exit-261019.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/385-newemaint-routine-exit
pr_url:
created: 2026-10-19
updated: 2026-10-19
---

## 问题/需求总结

NewEMaint 一直由负责人手动合并，负责人决定撤掉它的 routine merger pilot（NewEMaint #294）。平台侧 manifest 仍声明启用，导致 NewEMaint 的 `host.access.audit` 固定 `BLOCKED_EXTERNAL / HTTP_403`。合同与验收见 spec。

## 影响范围

`codex/config/gitea-governance.json` 与 `codex/config/host-access-broker.json` 的 NewEMaint 条目；`06` 中两处以该账号为 #316 首个现场对象的表述。PAT helper 的 Go 绑定测试与隔离进程测试原先读真实 manifest，改为读合成夹具；整改路线总规则 2 注明退出。运行时代码、测试夹具与使用层发布包不变。

## 初步方案与建议

一个提交里改四个值：governance 禁用、merger 置空、删 pilot 对象；host-access 的 merger 同步置空。合并后两台重装，读回 audit 与保护白名单。

## 风险

只改一边 manifest 会让 broker 全部 fail closed；删账号后回滚只能恢复声明。见 spec。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: NewEMaint 的 routine 合并声明从 governance 与 host-access 两份 manifest 撤下，改变 broker 授权面与 audit 行为，属于认证权限与平台治理变更
risk_flags:
  - security
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

- 改动 broker 授权面（routine merger 身份与 audit routine 段），触发「认证/权限/安全」与「Agent 与平台治理」强制 complex。
- 合并后的验收（两台重装、现场 audit 与保护读回）不能由 diff review 与 required CI 复现，因此声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。
