---
issue: 292
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/292
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - platform-governance
  - shared-core
depends_on: []
status: contract-drafting
branch: change/292-github-main-relay
created: 2026-09-11
updated: 2026-09-11
---

# 验证记录

- Source baseline：a2f8854b69a3b6badeb11fee6fd95a3500083379。
- PASS：私有项目双端main已fresh读回，当前可fast-forward；具体SHA和mirror缺失证据留在私有项目#80。
- PASS：现有平台仅有入站sync，broker操作表无GitHub出站操作；#292为唯一新承接，未重开已完成项目票。
- NOT RUN：T02/T03实现、单元/集成回归、CI、最终PR、installed/live及scheduler验收。
- 本合同步骤无runtime/manifest/live配置/凭据/远端refs变更。

## 授权来源

用户在既有项目任务明确批准单向main自动同步、fast-forward-only、no-force/no-delete；总控收到该任务转交后按原范围建立本票。转交任务id和详细端点只保留私有项目记录。该行为授权不扩大为凭据provision、权限扩展、PR合并或公司部署。
