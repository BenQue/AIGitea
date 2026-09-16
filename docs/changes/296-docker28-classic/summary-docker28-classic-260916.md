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

已完成用户批准的身份兼容修复与本地真实验收。公司已发布的 NewEMaint 镜像不重建；
后续继续 GitHub 构建/GHCR → 公司 Runner 拉取 → 外部4000隔离测试实例的既定路线。

## 当前交付

- 平台基线：2b5ac9364795f9e9f2f3722017a47122e7672a79；唯一分支 change/296-docker28-classic。
- 原合同提交de26edc；用户增补批准固化于806ecc6；身份修复b34e299。
- 真实执行源码843672a6a6a40fe453da94cffbd483e8d8e7d4d4：两个独立任务VM的64阶段PASS。
- producer29.7.1/5.1.4/containerd → consumer28.1.1/2.35.1/classic，linux/amd64。
- Registry/offline完整public lifecycle、重复部署、数据库迁移计数、A→B→A和故障恢复均PASS。
- 两个任务VM精确清理PASS，保留AppServer、DockerLab、gitea-ci；旧实验文件原字节归档保留。
- matrix2026.09.1仅追加精确consumer支持行，旧三行与历史evidence保持。
- runtime与harness双轴审阅PASS；正式matrix及其精确smoke断言更新后，完整smoke 922 tests PASS。

## 边界

公司执行器/profile/grants/端口4000安装包由NewEMaint后续阶段承接。公司installed/live、
公司实际镜像层拉取、迁移与业务验收仍NOT RUN；公司旧emaintenance/gitea未操作。
最终manual PR、required CI与人工合并尚未执行。

## 证据

首次身份差异与原runtime拒绝保存在evidence/原文件；本轮成功证据独立位于
evidence/amendment/，其中real-lifecycle-843672a.json记录64阶段，cleanup-843672a.json记录精确清理。

本轮全部实现及本地测试已获用户批准；不重复请求同范围授权。

当前：LOCAL_COMPLETE / AWAITING_PR_CONFIRMATION。已准备唯一人工合并PR候选，未推送、未创建PR。
