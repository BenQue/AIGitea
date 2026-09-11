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
status: approved
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

## Controller 批准与路由收敛

用户已在原任务明确批准实现#292、本地测试和PR材料，且明确排除实际GitHub推送、凭据配置、安装/启用调度、公司与旧服务操作。Controller本轮只收敛既有合同状态、把plan既定受保护touchpoints明确写入spec并完成路由验证；不实施runtime、不派新任务。文件清单将已有test路径纠正为test_host_access.py，固定计划内新入口文件名，不扩功能。

T01合同步骤完成，T02为下一frontier；所有实现测试/CI/installed/live在有新证据前仍NOT RUN。

- PASS：check-change-documents（changes=133/pass=2/gap=0）、git diff --check。
- PASS：原Controller load_contract以实时type/platform、complexity/complex和当前needs-analysis进行批准前合同校验；production complex路由成立，select_frontier_ticket=T02，四份映射正确。
