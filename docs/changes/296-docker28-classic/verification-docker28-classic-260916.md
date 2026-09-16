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
---

# 验证证据

## 本轮已核实

- PASS：2026-09-16 broker平台open Issue列表为286/287/288/289，无同范围开放票；新建#296。
- PASS：broker git.fetch.main，origin/main=2b5ac9364795f9e9f2f3722017a47122e7672a79。
- PASS：当前matrix2026.08.3没有Engine28行，Engine29 classic拒绝。
- PASS：image-store E2E固定major29；lifecycle E2E固定29.7.1/5.1.4/containerd。
- PASS：check-release-evidence-boundary.py保护旧matrix字节，新增支持需要精确扩展其验收边界。
- PASS（用户回执）：公司GHCR Login Succeeded及api/migration/web manifest PASS；
  仅证明该次认证和清单访问，未读取Token。
- 历史现场版本：Engine28.1.1/Compose2.35.1/classic。本轮未重新访问公司daemon；
  公司安装前须由版本化只读预检重新确认，漂移则拒绝。

## 状态

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
