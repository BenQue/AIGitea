---
issue: 26
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/26
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 NewEmaint 准备受治理的 preferred target components、transition 能力与 release identity 门禁，并由一个应用仓 umbrella Issue 跟踪后续迁移
risk_flags:
  - schema-change
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - compatibility
  - migration
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/26
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

## 问题/需求总结

现有 `linux-node-postgres-v1` 只接受每个 profile slot 的 preferred component，无法表达既有
Docker 消费项目在迁移前的受控版本，也缺少把 architecture identity 与 Docker release
checksum 绑定的门禁。Issue #26 因此需要补齐通用 transition/schema/validator 能力，并为
NewEmaint 生成准确、可重复的 preferred `target-candidate`。

用户于 2026-08-04 进一步明确：本 Change 的交付是为 NewEmaint **准备目标组件**，不是在
AISoftPlatform 中证明应用当前字节已迁移。NewEmaint 后续只需要一个 umbrella migration
Issue 统一追踪整套组件采用，不为每个 component 建立独立 Issue。

## 影响范围

- 扩展 architecture profile/schema/validator，使标准 profile 的 preferred slot 可以显式列出
  同 category 的受治理 transition component；不新增 NewEmaint 专用 profile。
- 更新 catalog revision、Linux profile version 和 NewEmaint target reference evidence。
- 加强 architecture lock 与 Docker release consumer 的 project identity/checksum 绑定，防止
  target candidate 被当作 current deployment evidence。
- 在 NewEmaint 创建并回读一个 umbrella migration Issue，逐项列出全部 preferred target、
  应用/数据库/制品/回滚 Gate 与非授权边界。
- 不修改 NewEmaint package lock、Dockerfile、Prisma schema、image、server、database 或 Secret。

## 初步方案与建议

每个 profile requirement 继续用 `component_id` 表示唯一 preferred component，并可选声明
`transitions` allowlist。每个 transition 仍是 catalog 中的精确 component，必须与 preferred
component 同 category、状态为 `supported` 或 `sunset`，且 project declaration 必须为每个
component 提供唯一、未过期的 exception。多个 component 可以引用同一个真实 umbrella
migration Issue，但每个 component 的 exception、owner、risk、controls 和 expiry 仍分别记录；
一个 slot 只能解析到 preferred 或一个 transition。

NewEmaint reference 只提交 `target-candidate`。`current-transition/` 故意不存在：Next.js 14
已被 upstream 标为 unsupported，不能进入合法 current lock；umbrella Issue 也不是 bypass。
NewEmaint 完成实际迁移后，应用仓再根据真实 supported/preferred bytes 生成 project ID
`newemaint` 的 current lock。

## 风险

- 宽松的“同 category 即可替换”会误把不同能力组件放进同一 slot，因此必须由 profile 显式
  allowlist，不能由项目自行选择任意 catalog component。
- 一个 umbrella Issue 可能掩盖部分组件未完成；Issue 正文必须列出精确 target matrix，并把
  application、database backup/restore、OCI provenance、test deployment 与 production approval
  分成可独立判定的 Gate。只有全部真实字节一致时才可生成 current lock。
- Catalog revision/profile version 变化会更新 reference lock checksums；必须记录可解释的 drift，
  不能静默重写既有 target evidence。
- Platform local tests 不能证明 NewEmaint build、migration、Docker/Registry/AppServer 或
  production 已完成。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 NewEmaint 准备受治理的 preferred target components、transition 能力与 release identity 门禁，并由一个应用仓 umbrella Issue 跟踪后续迁移
risk_flags:
  - schema-change
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - compatibility
  - migration
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改跨项目 JSON schema、profile resolution、canonical lock 和 Docker release integration。
- 变更 catalog/profile identity，并为现有项目引入有期限、带迁移跟踪的例外语义。
- 错误实现会让不真实的 target lock 进入 release manifest，属于 artifact/部署证据边界。
- 外部 umbrella Issue 只建立 NewEmaint 治理入口，不授权应用、数据库或环境 mutation。

### 缺失的 acceptance criteria 或决策

- 无。用户已书面批准 target-only 边界，并授权只创建一个 NewEmaint umbrella migration
  Issue；未授权实际 upgrade、migration、部署、merge 或生产操作。
