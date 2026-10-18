---
issue: 383
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/383
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 删除 docker-release 与 company-delivery 参考实现、发布运行时与公司交付模块、一个 installer、发布证据闸门和 smoke 硬门段，属于共享核心、安装、CI 与平台治理变更
risk_flags:
  - shared-core
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-reference-impl-exit-261019.md
  spec: spec-reference-impl-exit-261019.md
  plan: plan-reference-impl-exit-261019.md
  verification: verification-reference-impl-exit-261019.md
confidence: high
override_reason: ''
depends_on:
  - 380
status: approved
branch: change/383-reference-impl-exit
pr_url:
created: 2026-10-19
updated: 2026-10-19
---

## 问题/需求总结

整改路线 R8：把项目实例化的参考实现迁出平台 `main`，使平台对任何项目实例没有硬依赖。合同与验收见 spec。

## 影响范围

`docker-release/`、`company-delivery/`、`codex/runtime/aisoft_release/`、`codex/runtime/aisoft_company_delivery/`、四个 `aisoft_company_baseline` 模块、`architecture/reference/newemaint/`，以及只为它们存在的测试、harness、夹具、证据闸门、smoke 段、installer 登记和活文档链接。

## 初步方案与建议

一个 PR 删除全部对象，`archive/` 只留一份迁出说明（路径、最后 commit、去向）。PR 提交等 NewEMaint 回告脱钩通知第 4 步。

## 风险

NewEMaint 公司两 VM 路线按平台 main 原路径引用 `company-delivery/`，未 pin；提前合并会断。DockerLab 上有 docker-release 已安装副本，平台不再提供重装来源。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 删除 docker-release 与 company-delivery 参考实现、发布运行时与公司交付模块、一个 installer、发布证据闸门和 smoke 硬门段，属于共享核心、安装、CI 与平台治理变更
risk_flags:
  - shared-core
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

- 删除 installer 与 runtime 模块、修改 smoke 硬门与漂移检查，属强制 complex 的 CI、安装、共享核心与治理类别。
- 改 `AGENTS.md` 与使用层发布包成员（onboarding runbook），属治理文件，需受控步骤与发布包升版。
- 验收含删除后对外部引用的核对与已安装副本处置，不能只靠 diff review 与 CI 重放，故声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。负责人 2026-10-18 在线程内选择“现在实现、PR 等 NewEMaint 第 4 步”并确认合同。
