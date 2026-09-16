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

## 已批准增补：以已验证内容图识别跨store的同一镜像

用户于2026-09-16明确“了解了，我已经批准。请继续”，批准本节已说明的最小runtime兼容修复与验证。上文“runtime保持”仅对本节明确追加范围以外的文件及语义有效。来源为本次真实evidence/real-identity.json。

### 精确行为

- 保留已发布release.json、registry digest、archive checksum和镜像原字节，不重写image_id来迁就目标机。
- 对docker-release/v2，从已完成严格验证的OCI archive图推导该service唯一linux/amd64的config digest，以及该图已经证明的native descriptor identity。
- Registry仍必须验证exact RepoDigests；offline仍验证整个archive图、checksum、runtime tag、OS/arch。只允许本图证明的等价身份，不接受任意ID或仅RootFS相同。
- 目标的image inspect.Id必须命中该验证结果；激活后的container.Image必须等于重新校验过的目标本地image.Id，同时保留release/service labels、runtime tag与health校验。
- stage receipt仍以原release SHA和原manifest.image_id绑定源制品；每次消费receipt继续严格assert_local_images。无需本次改state格式、旧receipt原字节或数据库。
- legacy v1保持既有严格比较，不默默升级旧合同；index/provenance必须验证唯一可运行amd64图，不允许跨其它平台混配。
- 完整真实Registry/offline public lifecycle、重复部署与失败回滚均通过后，才能按原批准范围增加精确matrix支持行。

### 追加文件范围

允许追加修改 codex/runtime/aisoft_release/transport.py 和 runner.py，以及
codex/runtime/tests/test_release_transport.py、test_release_runner.py；
既有check-release-evidence-boundary.py及test_release_evidence_boundary.py纳入精确本次差异和独立当前行为验证，
保持历史基线与旧真实evidence不变；不能增加广泛豁免或删除检查。
必要的README/本Issue四文档和T02新harness沿用已批准范围。state.py、contract.py、schema、权限gate、AGENTS及公司系统不在新增范围。
如果实现发现还需变更这些文件或放宽其它语义，先报告，不静默扩展。

### 追加验收

1. 真实本次manifest/config分歧成为回归fixture；两个合法native ID路径均通过同一源制品证明。
2. 非本图config、其它平台config、伪造descriptor、替换archive member、错误RepoDigests、stale container.Image以及标签漂移均拒绝。
3. 原containerd和legacy路径回归不退化，原receipt绑定保留；容器最终ID校验必须基于验证后的本地内容而非只有tag。
4. 在重新创建的两个已批准专属VM重复Registry/offline完整lifecycle，保留每阶段和精确清理证据；公司仍NOT RUN。
5. 新源码与当前bytes边界受完整回归验证；当前无关registry-preflight smoke失败独立处理，不将失败改写为PASS。

回滚：本增补源码可通过受治理revert恢复；没有改公司或业务数据。
批准本增补后先做独立合同提交，再由fresh implementation context继续，不重复原VM/fixture测试授权。
