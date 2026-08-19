---
issue: 130
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/130
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-delivery greenfield collector、inventory、transition、post-install 与 non-interference 外部合同，触及共享核心、部署、兼容和平台治理
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-greenfield-legacy-decouple-260819.md
  spec: spec-greenfield-legacy-decouple-260819.md
  plan: plan-greenfield-legacy-decouple-260819.md
  verification: verification-greenfield-legacy-decouple-260819.md
status: spec-drafting
branch: change/130-greenfield-legacy-decouple
pr_url:
created: 2026-08-19
updated: 2026-08-19
---

## 问题/需求总结

公司 Pilot 采用完全独立的 greenfield binary + systemd Gitea。1.1.1 Stage10 已确认 candidate 8888/55432、路径、unit 和自动化入口的隔离事实，但当前合同仍强制探测并绑定 OUT OF SCOPE 的 legacy Docker Gitea health/version/baseline，导致与部署目标无关的 4xx 阻塞。Issue #130 要求 greenfield 路径完全移除该依赖，同时保留 candidate collision 与 non-interference 的 fail-closed 证明。

## 影响范围

主要影响 codex/runtime/aisoft_company_delivery/{collector.py,contract.py}、对应 strict schemas/templates、company-delivery compatibility/README/runbook/VERSION、codex/runtime/tests/test_company_delivery.py 和 portable bundle tests。controlled-upgrade 语义必须与 greenfield 明确分离；公司现场、legacy Docker resources、Stage20 和安装均不在本次执行范围。

## 初步方案与建议

为 greenfield inventory/transition 引入明确的 legacy not-applicable 语义：collector 不执行 docker ps 或 legacy HTTP，CLI 不再要求 legacy port；preflight 只验证固定 candidate 端口、路径、unit、tools 和 automation。transition/post-install 只依赖 candidate identity/health 与 zero-touch contract；controlled-upgrade 保留其自身 legacy 前置。同步 strict validator/schema/template/matrix/runbook 和 operator version，并以 spy/call-count 测试证明 greenfield legacy probe 为零调用。

## 风险

- 过度放宽可能削弱 candidate collision、unit 或 automation fail-closed 规则。
- 若 greenfield 与 controlled-upgrade 共用字段但语义未分离，会让旧 receipt 被误接受。
- 只删除 health 判断但仍调用 Docker/API，会违反完全解耦与公司边界。
- operator、schema、template、matrix 与 runbook 版本不同步会造成 handoff 漂移。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-delivery greenfield collector、inventory、transition、post-install 与 non-interference 外部合同，触及共享核心、部署、兼容和平台治理
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
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

- origin/main e6a6992 的 Issue #128 spec 明确把 greenfield Stage10 PASS 绑定 legacy healthy/baseline。
- 1.1.1 公司 inventory 的 candidate 8888 与 55432 均 free、candidate resources absent、automation disabled，但唯一 pending 为 LEGACY_GITEA_UNHEALTHY。
- collector.py 当前在 scm-ci 路径固定执行 docker ps publish probe 与 127.0.0.1 legacy /api/v1/version 请求。
- runbook Stage10/20/50 当前把 legacy healthy/baseline 作为 greenfield 硬前置。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。
