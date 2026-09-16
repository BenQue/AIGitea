---
issue: 296
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/296
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - deployment
status: approved
branch: change/296-docker28-classic
created: 2026-09-16
updated: 2026-09-16
reason: 新增目标运行时支持和真实部署验证，强制complex
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-docker28-classic-260916.md
  spec: spec-docker28-classic-260916.md
  plan: plan-docker28-classic-260916.md
  verification: verification-docker28-classic-260916.md
override_reason: ''
pr_url: ''
depends_on: []
---

# Docker 28 classic 目标兼容

来源：NewEMaint #80，应用 #84/PR85 的 GitHub 发布和公司镜像清单访问已通过。
公司历史目标为 Engine28.1.1 / Compose2.35.1 / linux-amd64 / classic，平台矩阵没有覆盖。
平台 #290 的 scm-ci/test 角色变更已经合并，不能替代 Docker capability 证据。

固定基线：2b5ac9364795f9e9f2f3722017a47122e7672a79（本轮 broker fetch origin/main）。
用户已于2026-09-16明确“批准实施”，覆盖本合同、两个本地专属VM、隔离fixture迁移/回滚和精确清理。尚未创建VM。

建议以两个全新的任务专属本地 Linux amd64 VM 验证跨 store 交付：
producer29.7.1/5.1.4/containerd → consumer28.1.1/2.35.1/classic。
只增加有证据的精确 consumer 支持，不扩大到所有 Docker28/classic。

当前：调查与四角色草案 PASS；实现/real E2E/PR/installed/company-live NOT RUN。
本次批准已记录，不重复请求同范围实施和本地实验授权。
部署执行器与外部4000入口的安装包由 NewEMaint 后续阶段承接，不与平台兼容混为一次现场操作。
