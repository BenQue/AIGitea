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
status: spec-drafting
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
用户已于2026-09-16明确“批准实施”，覆盖本合同、两个本地专属VM、隔离fixture迁移/回滚和精确清理。已完成两个VM的实际预检和身份前置测试，随后精确清理。

建议以两个全新的任务专属本地 Linux amd64 VM 验证跨 store 交付：
producer29.7.1/5.1.4/containerd → consumer28.1.1/2.35.1/classic。
只增加有证据的精确 consumer 支持，不扩大到所有 Docker28/classic。

当前：T02身份前置实现与T03真实预检PASS；Registry/offline实际传输成功，但旧runtime身份合同拒绝；完整lifecycle BLOCKED；PR/installed/company-live NOT RUN。
本次批准已记录，不重复请求同范围实施和本地实验授权。
部署执行器与外部4000入口的安装包由 NewEMaint 后续阶段承接，不与平台兼容混为一次现场操作。

## 实施检查点：NEEDS_HUMAN_DECISION

两个任务VM已真实运行并清理PASS。相同manifest、相同RootFS，经Registry和offline的consumer.Id均为config digest，而producer.Id为manifest digest。
原runtime transport._verify_content严格相等比较两次均INVALID_CONTRACT；runner健康检查也绑定该原生ID。
这是首次真实复现，不能仅添加matrix行。当前runtime/matrix未改。
按已批准spec的“未知runtime语义变更先增补合同”条款，现提供下列spec末尾的未批准增补建议。
本次批准范围内的测试和清理已经执行；不重复请求该范围授权。后续需要批准的是新runtime身份投影语义。
