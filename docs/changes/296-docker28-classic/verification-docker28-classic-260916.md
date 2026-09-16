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

# 验证证据

## 首次实验准备期记录

- PASS：2026-09-16 broker平台open Issue列表为286/287/288/289，无同范围开放票；新建#296。
- PASS：broker git.fetch.main，origin/main=2b5ac9364795f9e9f2f3722017a47122e7672a79。
- PASS：当前matrix2026.08.3没有Engine28行，Engine29 classic拒绝。
- PASS：image-store E2E固定major29；lifecycle E2E固定29.7.1/5.1.4/containerd。
- PASS：check-release-evidence-boundary.py保护旧matrix字节，新增支持需要精确扩展其验收边界。
- PASS（用户回执）：公司GHCR Login Succeeded及api/migration/web manifest PASS；
  仅证明该次认证和清单访问，未读取Token。
- 历史现场版本：Engine28.1.1/Compose2.35.1/classic。本轮未重新访问公司daemon；
  公司安装前须由版本化只读预检重新确认，漂移则拒绝。

## 首次实验准备期状态（历史）

| 项目 | 结果 |
|---|---|
| 根因定位、去重立项、方案草案 | PASS |
| 代码实现/新增兼容行 | NOT RUN |
| 创建本地专属VM、fixture真实E2E | NOT RUN |
| 当前公司目标runtime兼容支持 | BLOCKED |
| 公司镜像层拉取/执行器安装/verify-target | NOT RUN |
| 公司迁移/启动/入口4000业务验收 | NOT RUN |
| PR/required CI/人工合并 | NOT RUN |

当前没有更改已有runtime、matrix、shared Docker、公司服务或数据库。


- PASS：2026-09-16用户“批准实施”，范围包括spec所列本地专属环境与synthetic fixture操作；不含公司现场。

## T02前置核验

- 已批准合同独立提交：de26edc。
- Host预检：48GiB物理内存、14 CPU、248GiB可用磁盘；已有AppServer/DockerLab/gitea-ci，两个任务名称均不存在。
- 实际orbctl create --help确认支持--isolated/--mount/--memory/--cpus/--disk/--arch amd64；未改共享全局资源配置。
- 四个官方精确版本安装包已下载并记录SHA256；Compose官方.sha256与两个实物分别匹配。固定来源与hash见evidence/official-software-pins.json。
- Registry linux/amd64 manifest已从官方公开仓回读，digest固定；尚未拉取到测试daemon。
- 源码风险：containerd与classic的inspect Id可能不同，而当前_ verify_content要求严格等于manifest.image_id。下一步先真实复现身份兼容门，不预先修改runtime或supported矩阵。

## 实际验证结果（取代上文准备期NOT RUN状态）

- 实现HEAD：90b8150f29c5eb7c7bf512881e363476796b1235。
- 两方面代码审阅初次各2项恢复问题，f65a7a2修复后复核PASS；后续CLI参数和tar根目录修复单独提交并经故障回归。
- 真实preflight PASS：producer29.7.1/5.1.4/containerd；consumer28.1.1/2.35.1/classic；linux/amd64，daemon ID不同。
- Registry层拉取、producer save、空consumer offline load均完成；manifest原始字节SHA严格匹配reference，三端RootFS一致。
- producer.Id = sha256:e3a3867cedf0659bc2ed8b4634bc76cdf45f6b698dfaf13d5314b456fb3fdf04（manifest digest）。
- consumer Registry与offline.Id均 = sha256:f2778dda1d3b52a5e47f467983b943f5ea60a9d532a1a4e58f0107dee8bbe5b8（config digest）。
- 原runtime身份比较两次均BLOCKED/INVALID_CONTRACT：image ID does not match manifest for service identity。
- 完整public lifecycle、migration、activation、业务health NOT RUN；不能把最小身份门冒充AC2通过。
- cleanup PASS：仅删除aisoft-296-producer/aisoft-296-consumer；回读保留AppServer/DockerLab/gitea-ci。
- 最终release unittest：140 tests / OK；专项16项、bash-n、ShellCheck和diff PASS。
- 完整smoke FAIL于未修改的registry-preflight负例：“停掉 registry 之后：期望退出 1，实际 0”；宿主narrow复现一次同因失败，未改旧检查。
- 新增source/矩阵支持、公司installed/live均尚未通过；status=NEEDS_HUMAN_DECISION，待spec增补。

证据文件：real-preflight.json、real-identity.json、registry-manifest.json、identity-archive.tar（8192bytes）、
executed-original-plan.json、executed-resume-plan.json、executed-identity-plan.json、cleanup.json、code-review.json。
所有软件/测试数据均为本任务fixture，未读取业务凭据、访问公司主机或改变既有应用。

## 增补批准

2026-09-16用户明确“了解了，我已经批准。请继续”。已授权spec追加的transport/runner身份兼容、精确边界与回归，以及继续此前批准的两个本地专属VM测试。公司现场仍NOT RUN。

## T08 身份增补实现

- 批准合同提交806ecc6；runtime提交b34e299；精确源码pin完成于63ea74f。
- Standards/Spec双轴审阅PASS；b34e299尚未填写的pin在63ea74f补齐，未将后续结果倒算到旧提交。
- 152项release测试PASS；历史fake harness与当前source boundary PASS。
- 原registry-preflight负例在清洁进程环境下完整PASS；旧FAIL记录保留，尚未据此宣称完整smoke通过。
- 新完整lifecycle harness仍在实施；矩阵支持与公司现场NOT RUN。
- 新证据保存在evidence/amendment/，不覆盖前次实验原始回执。

## 本轮完整真实验收（当前结论）

- 实际源码843672a6a6a40fe453da94cffbd483e8d8e7d4d4；source/file hashes、两端实际capabilities、固定fixtures与执行计划均已保存。
- 两个独立amd64任务VM预检PASS：producer29.7.1/5.1.4/containerd；consumer28.1.1/2.35.1/classic。
- 64阶段PASS：Registry与offline的verify-artifact/verify-target/stage/migrate/activate/status，A/B重复部署零mutation，A→B→A、故意unhealthy激活后恢复A。
- 每transport独立synthetic PostgreSQL三个迁移marker的计数均为1；没有重复迁移。所有应用镜像source native ID与consumer config ID不同而严格验证通过。
- capability故障注入与artifact/identity篡改按预期拒绝；artifact负例零Docker调用。
- cleanup PASS：只删除aisoft-296-producer/consumer；回读保留AppServer/DockerLab/gitea-ci。
- matrix2026.09.1只增加精确28.1.1/2.35.1/linux-amd64/classic行；旧三行保持，29classic继续拒绝。
- runtime和harness的Standards/Spec双轴审阅均PASS。正式矩阵前完整smoke 922 tests/OK；正式矩阵后的46项能力/边界专项PASS。
- 测试环境修正：清洁PATH保留Python3.14；保留原HOME/USER和系统原TMPDIR，避免macOS /private/tmp的组继承与权限fixture预期不一致。旧registry-preflight完整负例在该环境PASS，未修改旧脚本/断言。
- 原失败与旧实验证据不覆盖；本轮证据独立存放evidence/amendment/。
- 实际NewEMaint应用、公司现场、PR/required CI/人工合并均NOT RUN。
