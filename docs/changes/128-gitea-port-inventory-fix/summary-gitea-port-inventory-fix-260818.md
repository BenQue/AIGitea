---
issue: 128
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/128
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-delivery 的固定 greenfield 端口、systemd preflight 语义、legacy health 脱敏诊断和 portable operator 版本，命中外部合同、共享核心、部署、兼容与平台治理强制 complex 规则
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
  summary: summary-gitea-port-inventory-fix-260818.md
  spec: spec-gitea-port-inventory-fix-260818.md
  plan: plan-gitea-port-inventory-fix-260818.md
  verification: verification-gitea-port-inventory-fix-260818.md
status: approved
branch: change/128-gitea-port-inventory-fix
pr_url: null
created: 2026-08-18
updated: 2026-08-18
---

## 问题/需求总结

公司侧 operator 1.1.0 Stage 00 已完成 strict evidence，Stage 10 `scm-ci/preflight` 随后生成了结构有效但
outcome=`BLOCKED` 的 inventory。脱敏事实表明 legacy Docker Gitea 在批准端口 `8080` 上存在，但固定
loopback version probe 未确认健康；原 greenfield 端口 `127.0.0.1:3000` 已被其它既有 Docker 应用占用；
Ubuntu 24.04 将部分 missing/template systemd unit 表现为 `not-found/inactive` 或
`disabled/inactive`，与 collector 1.1.0 的严格预期不一致。人工决定保留 legacy 全部资源不变，并把新
systemd Gitea 的唯一固定 HTTP target 改为 `127.0.0.1:8888`。Stage 10 `appserver-prod` 未运行。

## 影响范围

本 Change 影响 `company-delivery` 的 fixed target、inventory/transition strict schema、collector/validator、
compatibility matrix、templates、runbook、portable operator version 和对应 runtime/smoke/package tests。预计主要
修改 `codex/runtime/aisoft_company_delivery/{collector.py,contract.py}`、
`codex/runtime/tests/test_company_delivery.py`、`company-delivery/{VERSION,README.md,runbook.md}`、
`company-delivery/schema/*.json`、`company-delivery/templates/*.json` 与 compatibility JSON。通用本地
AISoftPlatform Gitea 的 `127.0.0.1:3000` 以及非 company-delivery 测试不属于修改范围。

## 初步方案与建议

将 operator 升至 `1.1.1`，使 collector、transition target、schema、template、compatibility 和 runbook 共同锁定
新端口 `8888`。对 systemd probe 先按一对 fixed `is-enabled/is-active` 结果做组合归一化：只有
`is-enabled=not-found` 且 `is-active=inactive|not-found` 才投影为 confirmed missing；generic custom unit
仍要求 missing，PostgreSQL fixed template 在 resource absent/expected-empty 前提下额外允许
`disabled/inactive`。legacy HTTP 失败只保存 `http-status-3xx|4xx|5xx`、`request-failed`、
`response-invalid` 等固定枚举，不保存 body/header/URL/raw exception。测试明确证明 `3000=occupied` 不再影响
候选、`8888=free` 才能通过，且任何 `8888=occupied|unknown`、unsafe unit 或 raw/sensitive output 都 fail closed。

## 风险

- 把 systemd 状态归一化得过宽会把已存在或可自动启动的 unit 误判为安全，必须只接受 exact safe pairs。
- PostgreSQL template 已存在不等于目标 cluster 已创建，必须同时保持 fixed data path absent/expected-empty、
  fixed target inactive/disabled 和 port free。
- HTTP 诊断若保存 raw body/header/status text，可能泄漏公司配置或认证信息；只能输出固定枚举。
- operator version、transition const、templates、compatibility 与 handoff 若未同步，会错误复用 1.1.0 Stage 00。
- 8888 目前只是人工声明空闲，只有更新后的公司 collector 实测才可写成 Stage 10 PASS。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-delivery 的固定 greenfield 端口、systemd preflight 语义、legacy health 脱敏诊断和 portable operator 版本，命中外部合同、共享核心、部署、兼容与平台治理强制 complex 规则
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
