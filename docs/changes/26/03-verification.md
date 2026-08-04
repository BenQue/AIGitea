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
status: blocked-external
branch: change/26
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

# Verification

## 环境与版本

- Approved baseline：`change/26@d6a3eb1262e41854e7e4683c582872d43151f15a`。
- Live remote baseline：`origin/main@8d5dae9569b6e61e88b40490ae04941614c62f8d`。
- Platform-local implementation：`change/26@b2d3ddf`，已 fast-forward push 到
  `origin/change/26`，没有 force push。
- Live Issue readback：#26 为 `open`；labels 精确为 `approved`、`complexity/complex`、
  `type/platform`。
- NewEmaint authority：live `gitea/main@dfdb93ca1e36b222ae38a747e78a5db263302c86`；
  只读解析 Git object。canonical checkout 在采集前已 dirty，本 Change 未写入 NewEmaint。
- Runtime：Python `3.14.4`；Bash `3.2`；ShellCheck `/opt/homebrew/bin/shellcheck`。
- Catalog/profile identity：catalog `2026.08.1`；Linux profile
  `linux-node-postgres-v1@1.1.0`；Windows/SQLite profile ID/version 保持不变。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| branch/Issue/remote preflight | PASS | 编辑前位于 `change/26`、HEAD 精确等于 approved baseline、upstream `origin/change/26`、worktree clean；live Issue 为 open + approved；remote refs 如上 |
| Context7 + official/upstream readback | PASS | Node、Prisma、Next.js 分概念 Context7 查询；Node archive、npm/React/TypeScript registry metadata、PostgreSQL policy/release、Next support policy 和 Docker Registry manifest 另行回读；ledger 在 `architecture/evidence/official-sources.md` |
| focused architecture tests | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -q`：33 tests |
| focused release tests | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release_*.py' -q`：39 tests |
| full platform smoke | PASS | `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：177 Python tests + shell/static/sync/installer checks；最终输出 `Codex platform static smoke checks passed.` |
| transition lock repeatability | PASS | 同一 transition fixture 连续两次 canonical 输出 byte-identical；两份 SHA256 均为 `9436731219de767a10fd8b71667035c60a2c0d8d8bb7dbdf070c5894987a4b92` |
| architecture installer repeatability | PASS | `bash codex/tests/test-architecture-install.sh` 连续安装两次，manifest identical；未创建 project declaration/lock |
| Docker release installer repeatability | PASS | `bash codex/tests/test-docker-release-install.sh` 连续安装两次，manifest identical；fake Docker 未被调用 |
| shell syntax / ShellCheck | PASS | `bash -n codex/tests/smoke.sh codex/tests/test-architecture-install.sh` 与对应 `shellcheck` 零 finding |
| target candidate semantic comparison | PASS | 与 approved baseline 比较 `component_id/version/state/digest`，diff empty；project ID 仍为 `newemaint-target-candidate`，只有 revision/profile/checksum 与经审计 catalog metadata 漂移 |
| `git diff --check` | PASS | implementation/staged diff 无 whitespace error |
| NewEmaint migration Issue gate | **BLOCKED_EXTERNAL** | authenticated read-only Issue 检索只匹配 #51 Docker-first delivery 和两个已关闭 Prisma baseline Issue；没有满足各实际 major transition 的独立 migration Issues，且未获创建授权 |
| Gitea final PR / PR CI | NOT RUN | AC-4 未满足；按合同未创建 PR，因此没有 final-head CI 可报告 |
| NewEmaint consumer/build/migration | NOT RUN | 未修改或运行 NewEmaint package、lockfile、Dockerfile、schema、image、migration 或 application tests |
| Docker/Registry/AppServer/database/Secret | NOT RUN | 未连接 Docker daemon/Registry/AppServer/database，未读取或修改 Secret |
| deployment / production | NOT RUN | 不在授权范围；candidate、push 或 local tests 都不是部署证据 |

## Acceptance criteria 结果

| AC | Result | Evidence / boundary |
|---|---|---|
| AC-1 | PASS（platform-local） | Profile schema 为每个 slot 保留唯一 preferred，并新增 strict `transitions` closed allowlist；same-category、global uniqueness、仅 `supported`/`sunset` 与 unknown-field rejection 均有正反测试；3 个 profile ID 不变 |
| AC-2 | PASS（platform-local） | Validator 对 preferred/一个 transition 唯一解析；unknown/duplicate/cross-category/preferred+transition/multiple transition/prohibited/EOL/state/Issue/exception/expiry/mismatch 均 fail closed；preferred 无 exception 通过 |
| AC-3 | PASS（catalog evidence） | 增加 npm `10.0.0`、Next `14.2.33`、React `18.3.1`、TypeScript `5.8.3`、Node `22.22.3-bookworm-slim` linux/amd64 child digest；保留 Node `22.22.3`、Prisma `5.22.0`、PostgreSQL `16.14`；每项含 exact pin、source、lifecycle/review、compatibility 与 mirror/checksum/SBOM policy。Next 14 因官方 unsupported 被记录为 `prohibited`，未加入 allowlist |
| AC-4 | **BLOCKED_EXTERNAL** | 未获授权创建 NewEmaint migration Issues，因此没有生成 `current-transition/` declaration/lock；没有使用 #51 或 fixture URL。另有独立合同冲突：官方 policy 已将 Next.js 14 标为 unsupported，故即使创建 Issues，现有 bytes 仍不能形成合法 current lock |
| AC-5 | PASS（target/preferred compatibility） | Catalog revision 与 Linux profile minor 已递增；Linux/Windows/SQLite preferred fixtures、3 个 committed reference locks 与 target candidate 全部通过。Baseline/current target resolved set semantic diff empty；reference/gap 明确 `current-transition`、`target-candidate`、`NOT MIGRATED`、`NOT DEPLOYED` |
| AC-6 | PASS（platform-local） | Transition lock 固化 resolved component、absolute migration Issue、exception ID/expiry 与 catalog/profile/declaration checksums；连续生成 byte-identical。Declaration/digest/source checksum/profile/catalog/self-hash/exception tamper tests fail closed |
| AC-7 | PASS（synthetic integration only） | Optional protected `architecture_project_id` 保持旧 v1 profile compatibility；声明后 project/profile/catalog/release checksum/lock self-hash/expiry 均在 Docker 前验证。Synthetic `newemaint` current lock通过；`newemaint-target-candidate` substitution 与 expired exception 均为零 Docker calls。真实 NewEmaint release 为 NOT RUN |
| AC-8 | PASS | Architecture README、NewEmaint reference README/gap、Docker release README 与 onboarding 统一 preferred/transition/current/target/Issue 边界，并明确 target 不是 migration/deployment evidence、transition 不绕过 prohibited/EOL/digest/expiry/checksum |
| AC-9 | PASS（local）/ NOT RUN（external） | 33 architecture + 39 release focused tests、177-test full smoke、双 installer、`bash -n`、ShellCheck、`git diff --check` 均通过。PR CI、NewEmaint consumer、真实 Docker/Registry/AppServer/migration/production 分开保持 NOT RUN |

总体终态：**BLOCKED_EXTERNAL**。Platform-local transition、canonical lock 与 Docker release
preflight 已实现并推送，但 required AC-4 未满足，所以不能创建最终 PR、不能生成伪 current lock，
也不能进入人工合并闸门。

## 重复执行

- Transition canonical lock 第一次/第二次：PASS，byte 与 SHA256 完全一致。
- Architecture installer 第一次/第二次：PASS，installed-file manifest 完全一致。
- Docker release installer 第一次/第二次：PASS，installed-file manifest 完全一致且零 Docker。
- Full smoke 在最终 implementation commit `b2d3ddf` 上重跑：PASS，177 tests。
- 真实 NewEmaint deploy 第一次/第二次：NOT RUN。

## 故意失败与回滚

- Unknown/duplicate/cross-category/multiple transition、preferred+transition ambiguity、
  prohibited component、相对或 credential-bearing Issue URL：PASS，validator 非零退出。
- Missing/duplicate/mismatched/expired/>180-day/after-`migrate_by` exception：PASS，lock 不生成。
- Mutable/mismatched OCI digest、source checksum drift、project/profile/catalog substitution、
  unknown lock field、自哈希篡改：PASS，均 fail closed。
- Docker release 的 target/current substitution 与 expiry：PASS，在 `config` 之前拒绝，
  Docker event list empty；没有 mutation 可回滚。
- Application/DB rollback：NOT RUN；本 Change 没有 application、schema、image、server 或
  database mutation。Platform 回滚方式是对 implementation commit 建立 revert PR 并重跑同一
  suite，不能回退到 EOL/prohibited 或 checksum 不完整的 lock。

## 外部 Gate 与所需授权

要继续 AC-4，必须由用户另行精确授权在 NewEmaint 创建真实、独立、可读的 component migration
Issues；该授权只允许建立治理跟踪，不授权实施 upgrade、migration、部署或数据库操作。

但 Issue 创建本身仍不足以解除当前 blocker：<https://nextjs.org/support-policy> 已把 Next.js
14 标为 unsupported。安全路径是先在 NewEmaint 的独立 Change 中把实际 Next.js bytes 迁移到
受支持 major 并通过应用验收，再基于真实 bytes 生成 project ID `newemaint` 的 current lock。
在此之前必须维持 `BLOCKED_EXTERNAL`，不得放宽 `prohibited`/EOL gate。

## 遗留风险与未完成项

- Node `22.22.3` 是批准的 exact pin，但不是 Context7 当前显示的最新 v22 patch；它只可作为
  有期限的 sunset transition，不能宣称 latest。
- Node/npm、Prisma、PostgreSQL、Next/React、TypeScript 与 OCI/image 的实际迁移、兼容性、
  backup/restore 和 rollback 都属于 NewEmaint 独立 Changes。
- `target-candidate/` 只表达 preferred 目标；`current-transition/` 当前故意不存在。
- Gitea PR、PR CI、人工合并、Issue close/lifecycle 更新、真实部署与 production 验收均未执行。
