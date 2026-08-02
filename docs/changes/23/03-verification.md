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
status: verified-local
branch: change/23
pr_url:
created: 2026-08-02
updated: 2026-08-03
---

# Verification

## 环境与版本

- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- Approved planning baseline：`change/23@9ad75b85971fc58e238572d6f8a406e2a0b5b0e8`
- Candidate branch：`change/23`，跟踪 `origin/change/23`；implementation/governance commits
  `f4f76fc`、`d86e61e`、`02c2749`、`c15305c`
- Live Issue readback：open；labels `approved`、`complexity/complex`、`type/platform`；无评论
- Official lifecycle evidence：PASS，逐 component 使用 Context7 单概念查询并以 official/upstream
  source readback；URL、retrieved/review date、冲突处理与 compatibility evidence 记录在
  `architecture/evidence/official-sources.md`
- Reference projects：NewEmaint authority
  `gitea/main@ecbdc674fde1f785cafdee92c6ee88c691104a34`；Windows/SQLite synthetic reference
- Server inventory：**PASS**。受管 sandbox 路径失败只构成执行路径证据；宿主机
  `orb -m <machine> -u benque` 只读探测确认 `gitea-ci`、`prod-sim` 均在运行且可达，因此先前结果
  已纠正为 `SANDBOX_PATH_BLOCKED`，不是服务器停机。未启动、停止或重启 VM/服务，未读取
  Secret、应用环境、日志、数据库内容或业务数据。

## 脱敏服务器 inventory

| Asset | Exact read-only inventory | Lifecycle / gap conclusion |
|---|---|---|
| `gitea-ci` | Ubuntu 26.04 LTS `aarch64`；kernel `7.0.11-orbstack-00360-gc9bc4d96ac70`；Node `20.20.2`；npm `10.8.2`；Python `3.14.4`；PostgreSQL client/server `18.4 (Ubuntu 18.4-0ubuntu0.26.04.1)` active；NGINX `1.28.3 (Ubuntu)` active；APT `3.2.0`；PM2 package `7.0.3`；Git `2.53.0`；Gitea API `1.26.4` active；.NET/SQLite/Docker/Compose absent | Ubuntu 26.04 是 active LTS 但 catalog 仍禁止采用，等待 26.04.1/soak；Node 20 EOL；NGINX 1.28.3 legacy；Python 3.14 bugfix；PostgreSQL 18.4 active；npm/PM2/Gitea 无固定 per-version EOL。所有 remediation 必须另建 server/runtime/proxy Change。 |
| `prod-sim` | Ubuntu 26.04 LTS `aarch64`；同一 kernel；Node `20.20.2`；npm `10.8.2`；Python `3.14.4`；PostgreSQL client/server `18.4 (Ubuntu 18.4-0ubuntu0.26.04.1)` active；NGINX `1.28.3 (Ubuntu)` active；APT `3.2.0`；PM2 package `7.0.3`；Git/.NET/SQLite/Docker/Compose absent；Gitea service inactive，未据此推测 package/binary presence | 与 `gitea-ci` 相同的 OS/Node/NGINX lifecycle gap；只记录 as-built，不宣称升级、迁移或部署完成。 |

Host scope 未发现可独立列举的 framework/ORM；为遵守授权边界，没有读取应用目录、进程环境、
配置内容或数据库内容。项目级 framework/ORM 只来自已授权的 NewEmaint repository metadata，
不得从服务器进程或目录名推测。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| planning contract parse + AC map | PASS | `load_contract` 通过；14 条 AC 全部映射 |
| catalog/schema/profile fixtures | PASS | 24 components、3 profiles；valid/invalid Schema/runtime fixtures 通过 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -v` | PASS | 26 tests；strict JSON、schema、semantic、lock、CLI、governance |
| validator/lock/CLI tests | PASS | unknown/duplicate/range/EOL/prohibited/sunset/expiry/digest/tamper/drift/source freshness/Secret 全覆盖 |
| installer repeatability | PASS | `bash codex/tests/test-architecture-install.sh` 两次 manifest byte/hash equality；不创建项目 declaration/lock |
| shell syntax / ShellCheck | PASS | `bash -n` 与 `shellcheck` 覆盖 CLI、installer、installer test |
| `bash codex/tests/smoke.sh` | PASS | 实现后重跑：131 Python tests 与全部 shell/static/sync/installer smoke 通过 |
| `git diff --check` | PASS | 无 whitespace error |
| official lifecycle source review | PASS | Context7 ledger、URL、retrieved/review date、冲突处理和 compatibility evidence 已提交 |
| NewEmaint/reference project dry-run | PASS | 3 个 declaration/lock 通过 cross-check；NewEmaint 收集后 `git status` clean |
| formal server exact inventory | PASS | 宿主机 `orb` 只读采集两台运行中服务器；exact metadata、absence、owner/source/time/confidence 与 lifecycle gap 均记录 |
| branch push | PENDING | inventory correction 尚待本地验收完成后的原子 commit 与 fast-forward push |
| Gitea PR CI | NOT RUN | 最终 PR 尚未创建；只在本地验收完成后创建 |
| 项目 migration/test deployment/production | NOT RUN | 不在本 Change 范围 |

## Acceptance criteria 结果

- **AC-1 — PASS**：正式项目/reference scope 与两台正式服务器的脱敏 inventory 已完成；包含
  exact OS/CPU/runtime/framework/ORM/DB/container/proxy/package-manager metadata、absence、owner、
  source、timestamp、confidence 与 lifecycle gap，且不含 Secret/业务数据。
- **AC-2 — PASS**：strict JSON catalog、3 profiles、4 Schemas、ADRs、正反 fixtures 已建立。
- **AC-3 — PASS**：24 components 的 ID/state/exact pin/platform/lifecycle/source/provenance/
  compatibility 完整且 negative tests fail closed。
- **AC-4 — PASS（catalog candidate）**：仅使用 official/upstream evidence，Context7 单概念
  ledger、source conflict 与 next review 已记录；应用级 integration 仍由各项目 Change 验证。
- **AC-5 — PASS**：OS/repository/package/runtime/framework/ORM/DB/container/proxy/frontend/CI
  action/OCI pin policy 完整；`latest`、range 和 mutable-only OCI 失败。
- **AC-6 — PASS**：project declaration 与 canonical lock 包含 resolved versions/digests/
  exception IDs/source checksums/lock SHA256；重复输出 byte-identical。
- **AC-7 — PASS**：required fail-closed routes 和脱敏 machine-readable diagnostics 通过。
- **AC-8 — PASS**：security/patch/minor/major cadence、Issue/CI/rollback/human merge gate 已固化。
- **AC-9 — PASS**：offline mirror/import、checksum、SBOM、provenance/digest contract 已固化；
  runtime 无网络，installer 不创建 updater/timer。
- **AC-10 — PASS**：Windows 同-major、Linux Node/Next/Prisma/PostgreSQL/OCI 与 SQLite
  single-instance/local-disk/WAL/backup/restore 约束均有正反验证。
- **AC-11 — PASS（dry-run only）**：NewEmaint candidate declaration/lock/gap 已生成；未修改应用
  lockfile、Dockerfile、schema、image、server 或 database，major Changes 明确拆分。
- **AC-12 — PASS**：profile 只暴露 delivery contract；#22 只消费 profile/revision/checksum，
  没有复制 release/deploy state machine。
- **AC-13 — PASS**：26 architecture tests、installer、ShellCheck、131-test full smoke 均通过。
- **AC-14 — PASS**：candidate/reference/CI/migration/test deployment/production 状态分开记录。

总体：implementation 与本地 acceptance 已通过。Catalog 和服务器结论都是 candidate/as-built
evidence；项目 migration、测试部署、production 和人工合并均未执行。

## 重复部署/执行

- lock generation 第一次/第二次 byte comparison：PASS（unit + CLI subprocess）
- installer 第一次/第二次：PASS（installed file manifest identical）
- validator offline rerun：PASS（test 将 proxy 指向不可达地址，runtime 无网络依赖）
- 无真实应用部署。

## 故意失败、采集偏差与回滚

- expired exception/EOL/mutable tag/tampered lock：PASS，均在外部 mutation 前返回非零。
- unknown/duplicate/unknown field/semver range/Secret marker：PASS，均 fail closed 且不回显值。
- official source conflict：PASS，Ubuntu Context7 extraction 冲突由 Canonical official readback
  解决；26.04 保持 `prohibited` 直到 point-release/soak Change。
- sandbox execution-path correction：PASS。宿主机只读 probe 成功后，将此前 OrbStack
  `Stopped`/SSH failure 纠正为 `SANDBOX_PATH_BLOCKED`；没有把 sandbox 状态当成服务器状态，
  也没有启动或重启 VM。
- PM2 probe side effect：运行 `pm2 --version` 时在 `prod-sim` 意外拉起一个此前不存在的空用户
  daemon。只读 `pm2 ls --no-color` 显示 0 applications；随即执行 `pm2 kill`，再以
  `ps -u benque -o pid=,comm=` 确认无 PM2 daemon。没有应用进程被停止或修改。后续不再调用会
  自动拉起 daemon 的 PM2 CLI。
- 项目文件 mutation 检查：PASS，NewEmaint `git status --porcelain` empty，authority SHA 未变。
- 回滚：本 Change 无部署/数据库 mutation；代码回滚为 revert PR。项目或服务器 remediation
  必须另建 Change 并提供 backup/restore/service rollback。

## 遗留风险与未完成项

- 两台服务器的 Node 20 已 EOL，NGINX 1.28.3 属 legacy；Ubuntu 26.04 虽在运行但 catalog 尚未
  批准。三类 remediation 都不在本 Change 内，必须建立独立 Change，不能把本 inventory 写成
  runtime/proxy/OS migration 或部署完成。
- npm、PM2、Gitea upstream 未发布固定 per-version EOL；保留 `unknown`，按季度/安全公告复核，
  不把缺失日期解释为无限期支持。
- 最终 PR 仅在本地验收、push 完成后创建；PR CI 和人工合并状态届时单独回读。不会自动合并。
- Catalog candidate/CI 通过不等于项目升级、测试部署或 production 验收。
- #22 必须在 #23 交付后整合 lock contract，不能复制版本事实源。
