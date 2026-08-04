---
issue: 26
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/26
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - compatibility
  - migration
  - platform-governance
depends_on: []
status: approved
branch: change/26
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

# Spec

## 目标与原因

让平台能够表达 preferred component 与受治理 transition，并为 NewEmaint 提供可解析、可重复、
可审计的 preferred `target-candidate`。本 Change 交付目标组件目录、canonical lock 与 Docker
release identity 门禁；不要求、也不允许把 NewEmaint 当前 unsupported bytes 伪装成有效
current lock。

NewEmaint 的实际采用由应用仓中一个 umbrella migration Issue 统一跟踪。一个 Issue 可以覆盖
多个相互依赖 component，但必须逐项保留版本、兼容性、测试、数据库、制品、回滚和环境 Gate；
Issue 创建本身不授权执行任何迁移或部署。

## Acceptance criteria

- [ ] **AC-1** `profile-v1` schema 在每个 `required_components` slot 上保留唯一 preferred
  `component_id`，并允许显式 `transitions` allowlist；每个 transition 必须引用唯一 catalog
  component、与 preferred component 同 category、声明仅允许 `supported`/`sunset`，三个标准
  profile ID 保持不变且 schema 继续拒绝 unknown fields。
- [ ] **AC-2** Validator 对每个 slot 只能解析到 preferred 或一个 allowlisted transition。
  跨 category、未知/重复 alternative、同 slot 同时声明 preferred 与 transition、多个
  transition、prohibited/EOL、state 不允许、缺少或格式无效的 migration Issue、缺失/重复/
  过期 exception、exception 与 component 的 migration Issue 不一致均 fail closed；preferred
  路径不需要 exception。多个不同 component 可引用同一 umbrella Issue，但仍各自需要唯一
  exception。
- [ ] **AC-3** Catalog 增加准确表示 NewEmaint observed runtime 的 exact entries：npm 10、
  Next 14.2.33、React 18.3.1、TypeScript 5.8.3，以及 tag + linux/amd64 digest 固定的 Node
  22.22.3 OCI base；保留 Node 22.22.3、Prisma 5.22.0、PostgreSQL 16.14 既有事实。每项均有
  official/upstream URL、exact pin、lifecycle/review date、compatibility、mirror/checksum/SBOM
  policy；unsupported/prohibited component 只作现状证据，不得加入可用 transition。
- [ ] **AC-4** 在 NewEmaint 创建且只创建一个真实、可读的 umbrella migration Issue，正文
  关联 AISoftPlatform #26 与 #51，列出 target-candidate 的全部 exact components，并明确
  application compatibility、PostgreSQL backup/restore/rollback、OCI provenance、test
  deployment、production approval 等分阶段 Gate。Issue 必须声明“创建只用于治理跟踪，不
  授权 package/image/schema/server/database/Secret mutation、部署或合并”。创建后执行
  authenticated GET 回读；不生成 `current-transition` declaration/lock。
- [ ] **AC-5** 既有 Linux/Windows/SQLite preferred fixtures 和 NewEmaint target candidate
  继续通过。Catalog revision 与 Linux profile version 明确递增；target resolved component
  集除身份/checksum 和经审计的 catalog metadata 外不发生 silent reinterpretation，reference
  目录和 gap report 明确区分 `target-candidate`、`CURRENT LOCK NOT GENERATED`、
  `NOT MIGRATED`、`NOT DEPLOYED`。
- [ ] **AC-6** Canonical lock generation 对相同输入连续两次 byte-identical；synthetic
  transition lock 固化 resolved component、migration Issue、exception IDs 和
  catalog/profile/declaration checksums。篡改 declaration、exception、digest、source checksum、
  profile/catalog identity 或 lock self-hash 均失败。
- [ ] **AC-7** Docker release integration 在 protected target profile 声明预期 architecture
  `project_id` 时，要求 target profile、release manifest checksum 与 lock project/profile/
  catalog identity 全部一致。Target/current substitution、篡改 lock 或过期 exception 必须在
  任何 Docker mutation 前拒绝；未声明该可选 identity 的既有 target profile保持 v1
  compatibility。所有 NewEmaint 真实 consumer/deploy 结果保持 `NOT RUN`。
- [ ] **AC-8** Architecture README、onboarding、NewEmaint reference/gap report 和 Docker
  release 文档解释 preferred、transition、current、target 与 umbrella Issue 的边界，明确
  target lock 不能成为 migration/deployment 证据，也不能用 umbrella Issue 或 transition
  规避 prohibited/EOL/digest/expiry/checksum 门禁。
- [ ] **AC-9** Focused schema/validator/lock/CLI/release integration tests 覆盖所有正反路径，
  包括多个 component 共享一个 umbrella Issue；installer 连续两次输出一致，`bash -n`、
  ShellCheck、full platform smoke 和 `git diff --check` 通过。Gitea final PR CI、NewEmaint
  consumer、真实 Docker/Registry/AppServer、migration 与 production 分开记录，未执行保持
  `NOT RUN`。

## 接口、数据与兼容性影响

### Profile slot

```json
{
  "component_id": "runtime.node.24",
  "allowed_states": ["preferred"],
  "transitions": [
    {
      "component_id": "runtime.node.22",
      "allowed_states": ["sunset"]
    }
  ]
}
```

`transitions` 是 profile owner 维护的 closed allowlist，不是 category wildcard。Project 仍只
声明实际 component；validator 用 profile slot 解析 preferred/transition，并把每个 component
与自己的 exception 一一绑定。不同 component 的 `migration_issue` 可以是同一 umbrella URL；
这不合并 exception，也不表示任一 component 已迁移。

### Reference identity

```text
architecture/reference/newemaint/
├── README.md
├── inventory.json
├── gap-report.md
└── target-candidate/
    ├── architecture.json
    └── architecture.lock.json
```

Target project ID 固定为 `newemaint-target-candidate`。`current-transition/` 在本 Change 中必须
不存在。NewEmaint 实际迁移完成后，应用仓基于真实 supported/preferred bytes 生成 project ID
`newemaint` 的 current lock；不得复制或重命名 target candidate。

### 版本与兼容策略

- Catalog revision 递增，Linux profile minor version 递增；profile ID 不变。
- Existing profile documents without `transitions` 继续按 exact preferred 语义解释。
- Existing Docker target profiles without `architecture_project_id` 保持兼容；声明该字段后必须
  由 release 与 lock identity 共同校验。
- Strict JSON、sorted canonicalization 和现有 lock self-hash 算法不改变。
- 一个 umbrella Issue 可以承载多个 component workstreams，但 current lock 仍只表达同一时点
  的真实完整 release bytes，不能表达“部分完成”。

## 风险与回滚约束

- Transition allowlist 错配会扩大所有消费者的可选范围；schema/runtime 必须共同检查 category、
  state、唯一性、expiry 与 migration Issue，且无 bypass flag。
- Umbrella Issue 可能让部分进度被误认为整体完成；Issue 必须保留 exact component matrix 和
  分阶段 Gate，最终 current lock、release checksum 与应用测试必须共同证明全部完成。
- Official lifecycle 或 OCI digest 无法回读时，component 不进入 active catalog；不得复制应用
  候选值来让测试通过。
- 外部 umbrella Issue 只建立治理跟踪，不授权升级、部署或生产变更。
- 平台代码回滚走 revert PR；catalog/profile/lock 回滚只能回到仍在支持期且 checksums 完整的
  revision。任何 NewEmaint 文件或环境 mutation 均不属于本 Change。

## 非目标

- 不升级 NewEmaint Node/npm/Prisma/PostgreSQL/Next/React/TypeScript 或 lockfile。
- 不修改 NewEmaint Dockerfile、Compose、release bytes、schema、server、database 或 Secret。
- 不生成 NewEmaint `current-transition` lock，不把 target candidate 当 current。
- 不新增项目专用 profile，不放宽 strict JSON、EOL、exception expiry、digest 或 checksum。
- 不实现自动 dependency update、自动执行 migration、自动 merge 或 deployment。
- 不把 NewEmaint #51 当作组件已迁移的证据；新 umbrella Issue 与 #51 只建立关联。

## 未决问题

无。用户已书面批准 target-only 合同，并精确授权只创建一个 NewEmaint umbrella migration
Issue；实际 migration/deployment 仍需在 NewEmaint 独立会话、分支、spec/plan 和人工 Gate 中
另行批准。
