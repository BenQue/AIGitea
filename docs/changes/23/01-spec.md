---
issue: 23
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/23
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - external-contract
  - compatibility
  - migration
  - platform-governance
depends_on: []
status: approved
branch: change/23
pr_url:
created: 2026-08-02
updated: 2026-08-02
---

# Spec

## 目标与原因

建立 AISoftPlatform 的企业技术架构事实源，使新项目选择、现有项目审计和升级计划都基于
同一 versioned catalog/profile/exception contract，而不是目录名、个人记忆或“latest”。
CI 生成 deterministic `architecture.lock.json`，对未知、EOL、例外过期、未 pin digest 和
profile 不兼容 fail closed；它不会自动升级或部署任何项目。

V1 canonical 文件统一使用 strict JSON 与 JSON Schema。选择 JSON 是为了在当前离线、
stdlib-first runtime 中避免新增未治理的 YAML parser、隐式类型和 canonicalization 差异。

## Acceptance criteria

- [ ] **AC-1** 对全部正式项目与服务器形成脱敏 inventory：OS/CPU、runtime、framework、
  ORM、DB、Docker/Compose、Nginx/IIS、package manager、exact version、来源、用途、owner、
  lifecycle/EOL 与采集时间；禁止按目录名推测，Secret 和业务数据不得进入输出。
- [ ] **AC-2** 建立 versioned JSON catalog、三个 profile、JSON Schemas、正反 fixtures 和
  决策记录：`linux-node-postgres-v1`、`windows-dotnet-postgres-v1`、
  `small-embedded-sqlite-v1`。
- [ ] **AC-3** 每个 component 记录 unique ID、preferred/supported/sunset/prohibited、精确
  version/pin rule、适用 OS/CPU、upstream support/EOL、source URL、retrieved/review/migrate
  dates、mirror/digest policy 和 compatibility notes；缺关键字段、重复 ID 或未知状态失败。
- [ ] **AC-4** 第一版矩阵只使用 upstream/official documentation 与真实兼容测试决定，
  记录 decision rationale 和 next-review date。Issue 中 Ubuntu/Windows/.NET/Node/Prisma/
  PostgreSQL 候选只是输入，不得未经证据直接标为 approved catalog。
- [ ] **AC-5** pin policy 覆盖 OS image/repository、Node/.NET SDK/runtime、npm、Prisma/EF
  Core、PostgreSQL、SQLite、Docker Engine/Compose、Nginx/IIS、前端 toolchain、CI actions 和
  OCI base digest；禁止 `latest` 和只有 mutable tag 的 production identity。
- [ ] **AC-6** 项目提交 `.aisoft/architecture.json`，声明 profile ID/version、catalog
  revision、components、delivery contract 和例外；工具生成 canonical/sorted
  `architecture.lock.json`，包含 resolved versions、digests、exception IDs、source checksums
  与 lock SHA256。同输入重复生成必须 byte-identical。
- [ ] **AC-7** Validator 对未知 profile/component、catalog/profile mismatch、EOL/prohibited、
  sunset 无 migration Issue、例外过期、缺 owner/reason/risk/controls/expiry/migration Issue、
  mutable base image 和 lock drift fail closed，并输出不含 Secret 的机器可读诊断。
- [ ] **AC-8** 定义 security patch、patch、minor、major 四类更新节奏与测试/回滚 Gate：安全
  修复可快速通道但仍保留 Issue、CI 和人工合并；major 永远走独立 Change/migration。
- [ ] **AC-9** 定义 offline mirror/import、checksum、SBOM 与 source provenance。Catalog
  更新本身走 Issue/spec/plan/PR/CI，不由定时任务自动修改 production lock。
- [ ] **AC-10** Windows profile 明确 Windows Server/IIS 与 .NET/ASP.NET Core/EF Core 同
  major support；Linux profile 明确 Node/Prisma/PostgreSQL/OCI compatibility；SQLite profile
  明确单实例、本机磁盘、WAL、容量/并发/可用性上限、online backup 和 restore drill。
- [ ] **AC-11** 对 NewEmaint 只生成 read-only architecture declaration candidate、lock 和
  gap/migration plan，区分 Node 22/18、Prisma 声明/lock、PostgreSQL 15/16 与 OCI pin；不
  修改应用 lockfile/image/schema，不把 Node/Prisma/PostgreSQL major 合为一次升级。
- [ ] **AC-12** #22 只引用 `profile_id`、`catalog_revision` 和 lock checksum；#23 不复制
  release/deploy state machine。Profile 可声明 `docker-release/v1` 或 `pm2-legacy`，但实际
  部署能力由 #22/应用 Change 提供。
- [ ] **AC-13** Unit/fixture/CLI tests、重复 lock generation、过期例外、EOL date boundary、
  unknown field、checksum tamper、official-source freshness 和 Secret marker tests 全部通过，
  并接入平台 smoke。
- [ ] **AC-14** `03-verification.md` 分开记录 schema/catalog candidate、reference projects
  dry-run、CI gate、项目迁移、测试部署和 production；后四类未执行时保持 `NOT RUN`。

## 接口、数据与兼容性影响

### Canonical tree

```text
architecture/
├── catalog.json
├── profiles/*.json
├── schemas/*.schema.json
├── decisions/*.md
├── templates/project-architecture.example.json
└── README.md
```

项目接口：

```text
.aisoft/architecture.json       # 人工维护、接受 review
architecture.lock.json          # deterministic generator 输出并提交
```

V1 不接受 YAML 输入；发现 `.aisoft/architecture.yaml` 时输出明确 migration diagnostic，
不会静默选择两个事实源。未来增加 YAML 必须另建 Change 并固定 parser/canonicalization。

### 所有权边界

- #23 owns component/profile/version/exception/lock validity。
- #21 owns host role/capability，不把服务器运行态塞入项目 architecture lock。
- #22 owns release manifest/deploy state，不自行维护版本 catalog。
- 应用仓 owns declared components 和迁移实现；平台只验证。

## 风险与回滚约束

- Catalog 错误可能阻断所有项目；validator 支持 pinned catalog revision 和清晰诊断，但不
  提供 `--ignore-all`。紧急例外仍须完整、短期且可审计。
- 时间判断统一 UTC date，边界 tests 覆盖 review/expiry/EOL 当日，避免时区漂移。
- 代码回滚走 revert PR；项目 lock 回滚只能回到仍受支持的 catalog/profile revision。
- 发现官方 source 冲突或兼容测试失败时，component 保持 candidate/sunset/prohibited，不能
  为通过 CI 降低 gate。
- 任何实际 OS/runtime/framework/database upgrade 都有独立 backup/rollback，不在本 Change。

## 非目标

- 不自动修改 package lock、Dockerfile、OCI image、数据库、服务器 OS 或 production。
- 不要求 Node 与 C# 使用同一 ORM，不统一所有 UI framework。
- 不把 SQLite 扩展到多实例、中等规模或高可用企业应用。
- 不建立通用 CVE scanner、资产 CMDB 或自动 dependency updater。
- 不读取/提交 `.env`、token、连接串、license key 或业务数据。

## 未决问题

无。第一版具体版本值由官方证据和兼容测试产出，失败时保持非 preferred 状态。
