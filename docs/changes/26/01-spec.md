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

让已经运行在非 preferred major 上的项目可以采用 `docker-release/v1`，同时生成与实际
release bytes 一致、可重复、可审计且有明确退出期限的 architecture lock。标准 profile
继续表达目标架构；transition 只是 profile 显式允许的临时状态，不成为第四个永久 profile，
也不把 major migration 宣称为已经完成。

本 Change 只改变平台 catalog/profile/schema/validator/reference/release integration。它不执行
NewEmaint package、schema、image、server 或 database migration。

## Acceptance criteria

- [ ] **AC-1** `profile-v1` schema 在每个 `required_components` slot 上保留唯一 preferred
  `component_id`，并允许显式 `transitions` allowlist；每个 transition 必须引用唯一 catalog
  component、与 preferred component 同 category、声明仅允许 `supported`/`sunset`，三个标准
  profile ID 保持不变且 schema 继续拒绝 unknown fields。
- [ ] **AC-2** Validator 对每个 slot 只能解析到 preferred 或一个 allowlisted transition。
  跨 category、未知/重复 alternative、同 slot 同时声明 preferred 与 transition、多个
  transition、prohibited/EOL、state 不允许、缺少或格式无效的 migration Issue、缺失/重复/
  过期 exception、exception 与 component 的 migration Issue 不一致均 fail closed；preferred
  路径不需要 exception。
- [ ] **AC-3** Catalog 增加准确表示 NewEmaint current runtime 的 exact entries：npm 10、
  Next 14.2.33、React 18.3.1、TypeScript 5.8.3，以及 tag + linux/amd64 digest 固定的 Node
  22.22.3 OCI base；保留 Node 22.22.3、Prisma 5.22.0、PostgreSQL 16.14 既有事实。每项均有
  official/upstream URL、exact pin、lifecycle/review date、compatibility、mirror/checksum/SBOM
  policy；来源冲突或无法验证 digest 时不得加入可用 transition。
- [ ] **AC-4** 建立独立 `current-transition` declaration/lock，精确包含 Ubuntu、Node 22、npm
  10、Prisma 5.22、PostgreSQL 16、Docker/Compose/Nginx、Next 14、React 18、TypeScript 5 和
  批准的 Node 22 OCI digest。每个非 preferred component 都有 owner、risk、controls、创建日、
  最迟为 component `migrate_by` 且不超过 180 天的 expiry，以及 NewEmaint 中真实存在、可读且
  对应实际 major migration 的 Issue URL；不得用 #51 或虚构 URL 代替。前置 Issue 不存在或
  未获创建授权时，本 AC 为 `BLOCKED_EXTERNAL`，不能生成伪 current lock。
- [ ] **AC-5** 既有 Linux/Windows/SQLite preferred fixtures 和 NewEmaint target candidate
  继续通过。Catalog revision 与 Linux profile version 明确递增；target resolved component
  集除身份/checksum 和经审计的 catalog metadata 外不发生 silent reinterpretation，reference
  目录和 gap report 明确区分 `current-transition`、`target-candidate`、`NOT MIGRATED`、
  `NOT DEPLOYED`。
- [ ] **AC-6** Canonical lock generation 对相同输入连续两次 byte-identical；transition lock
  固化 resolved component、migration Issue、exception IDs 和 catalog/profile/declaration
  checksums。篡改 declaration、exception、digest、source checksum、profile/catalog identity
  或 lock self-hash 均失败。
- [ ] **AC-7** Docker release integration 在 protected target profile 声明预期 architecture
  `project_id` 时，要求 target profile、release manifest checksum 与 lock project/profile/
  catalog identity 全部一致。NewEmaint current release 接受 `newemaint` current lock；替换为
  `newemaint-target-candidate`、篡改 lock 或过期 exception 时必须在任何 Docker mutation 前
  拒绝。未声明该可选 identity 的既有 target profile 保持 v1 compatibility。
- [ ] **AC-8** Architecture README、onboarding、gap report 和 Docker release 文档解释
  preferred、transition、current、target 与 migration Issue 的边界，明确 target lock 不能
  成为部署证据，也不能用 transition 规避 EOL/prohibited/digest/expiry/checksum 门禁。
- [ ] **AC-9** Focused schema/validator/lock/CLI/release integration tests 覆盖所有正反路径；
  installer 连续两次输出一致，`bash -n`、ShellCheck、full platform smoke 和
  `git diff --check` 通过。Gitea PR CI、NewEmaint consumer、真实 Docker/Registry/AppServer、
  migration 与 production 分开记录，未执行保持 `NOT RUN`。

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
声明实际 component；validator 用 profile slot 解析 preferred/transition，并把 exception 与
同一 component 和 migration Issue 一一绑定。

### Reference identity

```text
architecture/reference/newemaint/
├── README.md
├── current-transition/
│   ├── architecture.json
│   └── architecture.lock.json
├── target-candidate/
│   ├── architecture.json
│   └── architecture.lock.json
└── gap-report.md
```

Current project ID 固定为 `newemaint`；target project ID 固定为
`newemaint-target-candidate`。Protected Docker target profile 可选声明
`architecture_project_id`；一旦声明就必须与 lock 相等，不能由 release 目录覆盖。

### 版本与兼容策略

- Catalog revision 递增，Linux profile minor version 递增；profile ID 不变。
- Existing profile documents without `transitions` 继续按 exact preferred 语义解释。
- Existing Docker target profiles without `architecture_project_id` 保持兼容；NewEmaint adoption
  必须声明该字段，后续再由独立版本升级决定是否变为全局 required。
- Strict JSON、sorted canonicalization 和现有 lock self-hash 算法不改变。

## 风险与回滚约束

- Transition allowlist 错配会扩大所有消费者的可选范围；schema/runtime 必须共同检查 category、
  state、唯一性、expiry 与 migration Issue，且无 bypass flag。
- Official lifecycle 或 OCI digest 无法回读时，component 不进入 active catalog；不得复制应用
  候选值来让测试通过。
- 外部 migration Issues 只建立治理跟踪，不授权升级、部署或生产变更。
- 平台代码回滚走 revert PR；catalog/profile/lock 回滚只能回到仍在支持期且 checksums 完整的
  revision。任何 NewEmaint 文件或环境 mutation 均不属于本 Change。

## 非目标

- 不升级 NewEmaint Node/npm/Prisma/PostgreSQL/Next/React/TypeScript 或 lockfile。
- 不修改 NewEmaint Dockerfile、Compose、release bytes、schema、server、database 或 Secret。
- 不新增项目专用 profile，不放宽 strict JSON、EOL、exception expiry、digest 或 checksum。
- 不实现自动 dependency update、自动创建/执行 migration、自动 merge 或 deployment。
- 不把 NewEmaint #51 当成任何 major component 的 migration Change。

## 未决问题

无。独立 NewEmaint migration Issue 的创建属于显式外部授权 Gate；授权缺失只会令 AC-4
保持 `BLOCKED_EXTERNAL`，不会改变 transition contract 的实现方向。
