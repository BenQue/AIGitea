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
