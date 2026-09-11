---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: approved
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
reason: 既有host-role权限增加仅测试例外，强制complex
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-scm-test-deploy-260911.md
  spec: spec-scm-test-deploy-260911.md
  plan: plan-scm-test-deploy-260911.md
  verification: verification-scm-test-deploy-260911.md
override_reason: ''
pr_url: ''
depends_on: []
---

# SCM 测试部署

用户已批准部署工具把测试系统部署在scm-ci上。来源NewEMaint #79后续部署需求，目标平台仓，无未完成依赖。当前基点64f1cda（执行时exact Git commit为事实源）。不新建role，不改scm-ci服务器身份。

## AI 判级

权限与部署规则改变，change/platform/complex；已有environment=test|production可表达边界，无须新增schema字段。

本轮仅独立治理合同步骤；遵循AGENTS，提交合同后停止，下一轮重读再实施runtime。不是追加合同审批，沿用用户本次授权。最终唯一manual PR，提交前确认。
