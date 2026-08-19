---
issue: 130
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/130
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
depends_on: []
status: in-progress
branch: change/130-greenfield-legacy-decouple
pr_url:
created: 2026-08-19
updated: 2026-08-19
---

# Verification：greenfield legacy decoupling

## 边界

本文件只记录 AISoftPlatform source、tests、portable fake bundle 与 PR CI。公司内网、Stage20、安装、
appserver-prod inventory、新 Stage00 archive 和所有 legacy Gitea 操作均 `NOT RUN`。

## Acceptance evidence

| AC | 状态 | 证据 |
|---|---|---|
| AC-1–AC-10 | NOT RUN | 等待 T01–T05 implementation 与 verifier |

## 命令记录

等待实现后填写真实命令、结果、commit、PR 与 CI；未运行项目不得写为 PASS。

## Review

- runtime/schema/template/compatibility/runbook consistency：`NOT RUN`
- zero legacy Docker/API calls：`NOT RUN`
- candidate isolation fail closed：`NOT RUN`
- no-secret/no-raw-output：`NOT RUN`
- protected main / PR / CI readback：`NOT RUN`

## 公司状态

- Stage00 1.1.1：历史 `PASS`，不作为 1.2.0 前置。
- Stage10 1.1.1 SCM：历史 `BLOCKED` evidence 保留，不覆盖。
- Stage10 appserver-prod：`NOT RUN`。
- Stage20–110、Gitea/PostgreSQL/Runner 安装与 legacy mutation：`NOT RUN`。
