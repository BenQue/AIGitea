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
---

# 范围与验收合同草案

## 目标

保持公司 bcncsvds01 现有 Docker 和旧服务原状，通过平台受治理支持消除兼容门禁。
公司 GHCR manifest PASS 仅作为权限证据，不能满足本合同的真实镜像层/生命周期验收。

## 本地实验范围

- 两个新建、任务专属、可丢弃的 Linux amd64 VM：
  aisoft-296-producer、aisoft-296-consumer。已有同名资源则拒绝复用或删除。
- 每台建议最多2 vCPU、4 GiB内存、20 GiB磁盘；创建前只读确认本机资源和工具支持。
  资源不足、只能借用现有环境或需改变共享宿主配置时停止并报告。
- producer精确 Engine29.7.1 / Compose5.1.4 / containerd；consumer精确 Engine28.1.1 / Compose2.35.1 / classic overlay2。
- 必须回读真实daemon ID、server arch/store/version与独立data-root；不能用CLI版本或CPU模拟声明代替server事实。
- 官方软件和fixture按已验证digest/checksum固定；VM创建、安装、fixture配置、执行及清理写入版本化入口。
- 实验只使用本地隔离synthetic Web/migration/PostgreSQL与Registry，不使用业务数据、业务Secret或公司连接。
- 测试环境可执行本任务fixture migration、故意失败/回滚及精确资源清理。
- 保护现有DockerLab、LocalWMS、gitea-ci及其它VM/容器，拒绝daemon共用；不使用shared Docker socket，不做prune。
- 执行前生成approval-plan，记录源码SHA、两端ID、完整资源allowlist、fixture digests与预检；阶段授权只适用于这些自有资源。

## AC

1. 两个真实daemon相互独立，版本/store严格等于上述组合；Registry按digest拉取真实层并验证image/config身份。
2. 同一fixture release同时通过Registry和offline两个transport的public
   verify-artifact → verify-target → stage → migrate → activate → status。
   对应scm-ci/test的受保护fixture profile隔离目录/网络/数据库；不能改生产角色谓词。
3. 重复执行同一SHA的幂等、不同SHA故意失败与A→B→A回滚有真实回执；
   错版本/store、篡改制品/identity等反例在mutation前拒绝。
4. 成功后才在matrix追加精确consumer支持行：
   Engine >=28.1.1,<28.1.2；Compose >=2.35.1,<2.35.2；linux/amd64/classic。
   现有三行及旧evidence保持。独立candidate matrix只能在本任务可丢弃runtime快照中引导实验，
   不得将候选材料预装公司或当成正式支持。真实失败则保留拒绝并报告根因。
5. 回归包括矩阵边界、当前runtime、公用历史证据保护；所提交evidence有source/file hash、
   实际能力、逐阶段结果、负例与资源清理后回读。静态/fake不冒充real。
6. 文档和required CI通过，唯一manual PR经用户合并；公司installed/live仍NOT RUN。

## 允许修改的文件面

- 本Issue四角色文档与脱敏evidence。
- 新的 codex/tests/integration/test-docker28-classic-e2e.sh、
  codex/tests/integration/docker28-classic-driver.py、
  codex/tests/integration/provision-docker28-classic-lab.sh；
  新的 codex/tests/fixtures/docker28-classic/ 最小fixture与fixture manifest。
- 新的 codex/tests/test-docker28-classic-e2e-harness.sh 与
  codex/runtime/tests/test_release_docker28_compatibility.py。
- docker-release/compatibility/image-stores-v1.json：仅revision及经真实验收的精确新增行。
- docker-release/README.md：说明精确支持与证据，不改变目标权限/安装边界。
- codex/tests/check-release-evidence-boundary.py 及其现有回归：当前检查写死旧matrix字节，
  必须把本次唯一新增行纳入精确变更证明，维持其它文件、旧行、旧evidence和执行前后漂移检查；
  禁止把整个matrix排除或取消边界检查。
- codex/tests/smoke.sh：加入新入口默认NOT RUN、fake/边界回归及shell静态检查；
  required CI context不改，不在常规CI偷偷执行真实环境测试。

既有 #27/#65 harness、fixture、evidence、runtime lifecycle/transport/权限实现保持。
若真实复现需要修改runtime语义，先提供最小根因与合同增补；本草案不预授权未知修复。
不改AGENTS、Controller、公司配置、认证或平台安装器。

## 治理与回滚

合同文档先独立提交并停止；后续fresh run读取批准合同再实现，不修改当前遵循的治理文件。
本地实验失败先收集脱敏证据，仅按allowlist清理自有资源，不自动重试不确定migration。
源码可通过受治理revert恢复；公司未应用所以无公司现场回滚。

