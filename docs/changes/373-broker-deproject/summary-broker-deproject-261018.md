---
issue: 373
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/373
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 删除一个 broker typed 操作并放宽治理合同中的写死校验，属于凭据隔离与治理共享核心
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-broker-deproject-261018.md
  spec: spec-broker-deproject-261018.md
  plan: plan-broker-deproject-261018.md
confidence: high
override_reason: ''
depends_on:
  - 371
status: pr-open
branch: change/373-broker-deproject
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/374
created: 2026-10-18
updated: 2026-10-18
---

## 问题/需求总结

整改路线 R4。broker（K1）与 governance（K2）合同里写死了项目 id、仓库名、Issue 号、SHA 与一个应用目标，违反 ADR 0001 D2/D3。本票把这些写死项改为 manifest 自洽校验，并退役一个从未有消费方的项目专属 typed 操作。

## 影响范围

`aisoft_host_access`（contract、broker、runner、cli，删除 `application_preflight.py`）、`aisoft_gitea_governance/contract.py`、两份 canonical manifest 中的 host-access 一份、相关测试与 smoke、`06` 中 #340 单票段落、CI 参考模板一处注释、泄漏基线、整改路线与 ADR D5 一行。

## 初步方案与建议

见 mapped spec。要点：`application.target.preflight.read` 退役（39 → 38 个操作），采集器归档；routine pilot 行为不变，只去掉代码里的项目常量；VM profile 集合、timer 白名单与公开仓库白名单改为 manifest 自洽。

## 风险

改动 broker 合同加载路径，写错会让全部 broker 调用 fail closed；现有 manifest 下的 validate、pilot 回归与全量 smoke 控制该风险。删除 typed 操作是破坏性变更，但没有调用方（LocalWMS main 与平台工具均不调用）。合并后两台 broker 需要重装，Mac 侧由负责人执行。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 删除一个 broker typed 操作并放宽治理合同中的写死校验，属于凭据隔离与治理共享核心
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 改 broker typed 操作表与 manifest 字段（外部契约、凭据隔离），改治理合同加载校验（共享核心、平台治理），强制 complex。
- 证据由源码 runtime 的 validate、单测与全量 smoke 复现；安装层是合并后的独立步骤，不在本票 PR 内声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。负责人 2026-10-18 在项目线程裁决：pilot 保留、预检接口退役（以确认点 1 的回复为准）。
