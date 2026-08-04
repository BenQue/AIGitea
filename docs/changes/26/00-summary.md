---
issue: 26
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/26
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为既有 Docker 消费项目增加真实且限时的 architecture transition lock，同时保持标准 profile 和 release checksum 门禁
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

现有 `linux-node-postgres-v1` 只接受每个 profile slot 的 preferred component。首个真实
Docker-first 消费项目 NewEmaint 因此只能在“错误声称 Node/Prisma/PostgreSQL/前端 major
升级已经完成”和“缺少 `docker-release/v1` 要求的 canonical lock”之间二选一。Catalog
已经包含部分现状版本，但 profile、schema 和 validator 没有受治理的过渡语义，缺失的现状
component 与 digest 也无法形成真实 lock。

## 影响范围

- 扩展 architecture profile/schema/validator，使标准 profile 的 preferred slot 可以显式列出
  同 category 的受治理 transition component；不新增 NewEmaint 专用 profile。
- 更新 catalog revision、Linux profile version 和 NewEmaint current/target reference evidence。
- 加强 architecture lock 与 Docker release consumer 的 project identity/checksum 绑定，防止
  target candidate 被当作 current deployment evidence。
- 不修改 NewEmaint package lock、Dockerfile、Prisma schema、image、server、database 或 Secret。

## 初步方案与建议

每个 profile requirement 继续用 `component_id` 表示唯一 preferred component，并可选声明
`transitions` allowlist。每个 transition 仍是 catalog 中的精确 component，必须与 preferred
component 同 category、状态为 `supported` 或 `sunset`，且 project declaration 必须同时提供
真实 migration Issue 和唯一、未过期的 exception。一个 slot 只能解析到 preferred 或一个
transition；缺失、重复或跨 category 一律 fail closed。

NewEmaint reference 分成 `current-transition` 与 `target-candidate` 两个明确目录。current lock
只描述实际 release bytes；target 只作未来 major migration 规划。Protected target profile 绑定
预期 architecture `project_id`，而 manifest checksum 继续绑定 canonical lock bytes。

## 风险

- 宽松的“同 category 即可替换”会误把不同能力组件放进同一 slot，因此必须由 profile 显式
  allowlist，不能由项目自行选择任意 catalog component。
- Catalog revision/profile version 变化会更新 reference lock checksums；必须记录可解释的 drift，
  不能静默重写既有 target evidence。
- NewEmaint 当前没有独立的 major migration Issues。不得伪造 URL 或用 Docker 载体 Issue #51
  冒充升级计划；缺少真实 Issue 时 AC-4 保持 `BLOCKED_EXTERNAL`。
- Platform local tests 不能证明 NewEmaint Docker build、部署或 production 已完成。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为既有 Docker 消费项目增加真实且限时的 architecture transition lock，同时保持标准 profile 和 release checksum 门禁
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

### 缺失的 acceptance criteria 或决策

- 无设计未决项。NewEmaint 独立 migration Issue URL 是实施环境前置；未授权或不存在时必须
  诚实记录 `BLOCKED_EXTERNAL`，不能降低 validator 门禁。
