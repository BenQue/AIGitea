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

# Implementation plan

## 任务分解

1. 建立正式项目/服务器清单和只读采集表。逐项目核对 package/lock、Dockerfile/image、
   schema/tool outputs 与实际 runtime metadata；逐服务器核对 OS/CPU/runtime/DB/container/
   proxy 版本。只记录脱敏 metadata，并标注 source、owner、timestamp 和 confidence。
2. 使用 Context7/official upstream docs 分组件收集 lifecycle/EOL/support policy；对 Node、
   .NET、Prisma/EF Core、PostgreSQL、SQLite、Docker/Compose、Ubuntu/Windows、Nginx/IIS 和
   前端 toolchain 分开查询，保存 URL、retrieved date、版本结论与冲突处理。
3. 创建 `architecture/schemas/`、`catalog.json`、三个 profiles 和 decisions，先用正反
   fixtures 锁定 JSON fields、unknown-field rejection、states、dates、pins 和 compatibility。
4. 在 `codex/runtime/aisoft_architecture/` 实现 stdlib-only strict parser/validator、UTC
   lifecycle/exception rules、deterministic resolver/canonicalizer/hash；JSON Schemas 与 runtime
   对同一 fixture 集必须给出一致结果。
5. 提供稳定 CLI `validate`、`lock`、`explain` 和无 Secret templates。`lock` 连续两次输出
   byte-identical；`explain` 只输出来源、状态、约束和 remediation，不输出环境值。
6. 实现 profile/catalog/project declaration/lock cross-check，覆盖 delivery contract、OCI
   digest、sunset migration Issue、exception expiry 与 offline provenance/SBOM/checksum fields。
7. 添加 unit/CLI/installer/smoke tests，覆盖 invalid/unknown/duplicate/EOL/boundary/tamper、
   repeat lock、Secret marker、official-source freshness 和无网络 runtime。
8. 更新 README、07/09/12、onboarding 和项目模板，定义季度 catalog refresh、半年 audit、
   emergency security flow、major Change 与例外 lifecycle。
9. 对 NewEmaint 和至少一个 Windows、一个 SQLite reference project 运行 read-only dry-run，
   生成候选 declaration/lock/gap report；任何实际文件修改和 upgrade 拆到项目独立 Issue。
10. 填写 `03-verification.md`，运行定向 tests、`git diff --check` 与全量 smoke；提交并推送
    `change/23`，创建 `Closes #23` 的最终 PR，停止在人工合并闸门。
11. PR 合并后 provision 不涉及外部 mutation；各项目后续采用 catalog 时分别创建 Change、
    CI gate 和迁移验证。#22 在 #23 达到 terminal 后整合 lock contract。

## 涉及文件

- `docs/changes/23/{00-summary,01-spec,02-plan,03-verification}.md`
- `architecture/README.md`
- `architecture/catalog.json`
- `architecture/profiles/{linux-node-postgres-v1,windows-dotnet-postgres-v1,small-embedded-sqlite-v1}.json`
- `architecture/schemas/{catalog,profile,project-architecture,architecture-lock}-v1.schema.json`
- `architecture/decisions/*.md`
- `architecture/templates/project-architecture.example.json`
- `architecture/fixtures/{valid,invalid}/*`
- `architecture/bin/aisoft-architecture`
- `architecture/install.sh`
- `codex/runtime/aisoft_architecture/*.py`
- `codex/runtime/tests/test_architecture_*.py`
- `codex/tests/test-architecture-install.sh`
- `codex/tests/smoke.sh`
- `README.md`
- `07-内网与生产平移路线.md`
- `09-v3平台简化与Loop-Engineering文档改造规划.md`
- `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`
- `skill-for-codex/references/onboarding-runbook.md`

## 数据库迁移

无数据库或应用数据 migration。本 Change 只生成 catalog/profile/declaration/lock 与 gap
evidence。NewEmaint/其它项目的 PostgreSQL major、Prisma/EF migration、SQLite eligibility
调整都必须建立独立 Change、backup、compatibility test 和 rollback Gate。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | inventory completeness/dedup/source/timestamp checks 与人工抽样回读 |
| AC-2 | JSON Schema 正反 fixtures、profile IDs/versions 唯一性 tests |
| AC-3 | catalog validator：missing/duplicate/unknown state/date/source/pin failures |
| AC-4 | official source URL/retrieved date/freshness review + compatibility evidence table |
| AC-5 | pin fixtures：semver range、latest、mutable tag、missing OCI digest 均失败 |
| AC-6 | `aisoft-architecture lock` 两次 byte/hash equality 与 lock drift tests |
| AC-7 | invalid profile/EOL/sunset/exception/tamper fixtures 与 machine-readable diagnostics |
| AC-8 | policy tables + security/patch/minor/major route fixture review |
| AC-9 | provenance/SBOM/checksum/offline fields tests；无 production updater 扫描 |
| AC-10 | 三 profile compatibility/SQLite eligibility 正反 fixtures |
| AC-11 | NewEmaint dry-run gap report；`git status` 证明应用仓未被修改 |
| AC-12 | profile delivery contract fixtures 与 #22 ownership/integration review |
| AC-13 | unit/CLI/install tests、`bash -n`、ShellCheck、full smoke、Secret scan |
| AC-14 | `03-verification.md` 的 candidate/dry-run/CI/migration/deploy 状态审查 |

## 部署与回滚

无应用部署。Installer 只复制 versioned catalog/runtime/schema/template，不创建项目声明、
修改 CI、访问公网或 enable timer；在临时目录运行两次验证幂等。Deliberate failure 使用过期
例外、EOL component、mutable OCI tag 和 tampered lock，必须在任何外部 mutation 前失败。
代码/目录回滚走 revert PR；实际项目升级与环境回滚不在本 Change。
