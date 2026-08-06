---
issue: 33
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/33
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 更新跨项目 Next.js 与 Prisma 安全精确版本并扩展离线 npm 稳定发布一致性门禁，避免下游在平台合同与 npm 安全公告之间无法收敛
risk_flags:
  - security
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/33
pr_url:
created: 2026-08-06
updated: 2026-08-06
---

## 问题/需求总结

NewEmaint #52 已消费 AISoftPlatform `main@d20811b401b38bbd1b1735757912e2120a3a0a8a`，
并在 Node `24.18.0`、npm `11.19.0` 的 clean lockfile 上完成严格 `npm audit`。原始
comment 2077 显示平台当前的 `next@16.2.11` 与 `prisma@7.8.0` 已进入安全公告影响范围，
建议分别升级到 `16.3.0` 与 `7.9.1`；应用不能自行偏离平台 exact contract。

2026-08-06 对官方 npm Registry 的只读回读确认：`next@16.3.0`、`prisma@7.9.1`、
`@prisma/client@7.9.1` 与 `@prisma/adapter-pg@7.9.1` 均是各自 `latest` 稳定精确版本，
并具有不可变 integrity。Context7 官方文档回读确认 Next.js 16 要求 Node `>=20.9.0` 且接受
React/ReactDOM `^19.0.0`；Prisma 7 packages 要求 Node `^20.19 || ^22.12 || >=24.0`。

## 影响范围

- 更新 architecture catalog、Linux profile、模板/fixtures、NewEmaint target candidate 与全部
  受 catalog checksum 影响的 committed reference locks。
- 将现有 React-only npm stable-release validator 收敛为 component-scoped contract，同时覆盖
  Next.js 单包与 Prisma CLI/Client/PostgreSQL adapter 三包同版本规则。
- 更新 focused/full tests 与 official source ledger；不修改 NewEmaint 或任何 runtime 环境。

## 初步方案与建议

在 `framework.next.16` 和 `orm.prisma.7` 中加入离线 `package_release` snapshot，固定 package
集合、`stable` channel、精确版本、Registry URL、integrity 与发布日期。Validator 只读这些已
提交元数据，拒绝缺失/多余包、可变 dist-tag、范围、预发布、版本不一致和 future dates；lock
生成继续保持离线且 canonical。

## 风险

- 错误的 package snapshot 会 fail closed 并阻止下游生成 lock，因此 metadata、profile 和
  committed locks 必须一次性更新并以 tests/CLI 重建验证。
- Platform-local validation 不能代替 NewEmaint 的 clean install、audit、build、browser、Docker、
  database 或 deployment 验收；这些在本 Change 中保持 `NOT RUN`。
- 最终 Gitea merge commit 只有人工合并后才能产生；合并前不得虚构。NewEmaint #52 必须在
  merge 后读回受保护 `main` 的精确 SHA 再消费。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 更新跨项目 Next.js 与 Prisma 安全精确版本并扩展离线 npm 稳定发布一致性门禁，避免下游在平台合同与 npm 安全公告之间无法收敛
risk_flags:
  - security
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
```

### 判级证据

- 该变更修改跨项目 catalog/profile/lock、shared validator 与下游 dependency contract。
- Issue 显式标记 `complexity/complex`，且安全、兼容性与平台治理均触发强制 complex 规则。

### 缺失的 acceptance criteria 或决策

- 无。Issue #33 与本 Spec 收敛了实现方向；人工合并、合并后 SHA 与 NewEmaint 消费是外部门禁。
