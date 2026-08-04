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
status: verified-local
branch: change/26
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/29
created: 2026-08-04
updated: 2026-08-04
---

# Verification

## 环境与版本

- Approved baseline：`change/26@d6a3eb1262e41854e7e4683c582872d43151f15a`。
- Live remote baseline：`origin/main@8d5dae9569b6e61e88b40490ae04941614c62f8d`。
- Existing platform implementation：`change/26@b2d3ddf`；原 external-gate verification
  commit `a373b5ab4918fc8dcac8b8a3d25eacac8a646545`。本轮从该 clean、已推送 HEAD
  开始，将用户书面批准的合同收敛为 target-only + 一个 umbrella Issue。
- Live Issue readback：AISoftPlatform #26 为 `open`；labels 精确为 `approved`、
  `complexity/complex`、`type/platform`；编辑前无 `change/26` PR。PR 创建后 lifecycle 已
  正常更新为 `pr-open`，Issue 保持 open。
- NewEmaint authority：live `gitea/main@dfdb93ca1e36b222ae38a747e78a5db263302c86`；
  本轮未写 NewEmaint repository。唯一 umbrella migration tracking 为
  [#52](http://gitea-ci.orb.local:3000/admin/NewEMaint/issues/52)。
- Runtime：Python `3.14.4`；Bash `3.2.57`；ShellCheck `0.11.0`。
- Catalog/profile identity：catalog `2026.08.1`；Linux profile
  `linux-node-postgres-v1@1.1.0`；Windows/SQLite profile ID/version 保持不变。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| branch/Issue/remote preflight | PASS | 编辑前位于 `change/26@a373b5a`、upstream `origin/change/26`、worktree clean；live refs 为 `main@8d5dae9`、`change/26@a373b5a`；#26 open + approved |
| revised contract parse + AC map | PASS | `load_contract`：issue 26、complex、branch `change/26`、9 条 AC；`未决问题` 为“无” |
| Context7 + official/upstream evidence | PASS | Node、Prisma、Next.js 分概念 Context7 与 official readback ledger 保持在 `architecture/evidence/official-sources.md`；Next.js 14 继续为 `prohibited` |
| focused architecture tests | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py' -q`：34 tests |
| focused release tests | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release_*.py' -q`：39 tests |
| full platform smoke | PASS | `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`：178 Python tests + shell/static/sync/installer checks；最终输出 `Codex platform static smoke checks passed.` |
| umbrella transition semantics | PASS | 新增正向测试证明 Node 22 与 PostgreSQL 16 可共享同一 umbrella Issue URL，同时 lock 保留两个不同 exception ID；缺失/重复/mismatch/expiry 反例仍 fail closed |
| architecture installer repeatability | PASS | `bash codex/tests/test-architecture-install.sh`：连续安装 manifest identical；未创建 project declaration/lock |
| Docker release installer repeatability | PASS | `bash codex/tests/test-docker-release-install.sh`：连续安装 manifest identical；fake Docker 未被调用 |
| shell syntax / ShellCheck | PASS | 对本分支修改的 `codex/tests/smoke.sh`、`codex/tests/test-architecture-install.sh` 执行 `bash -n` 与 ShellCheck，零 finding |
| target candidate semantic comparison | PASS | 与 approved baseline 比较 `component_id/version/state/digest`，diff empty；project ID 仍为 `newemaint-target-candidate`，只有 revision/profile/checksum 与经审计 catalog metadata 漂移 |
| NewEmaint umbrella Issue #52 | PASS | 创建前 authenticated list 无同标题 Issue；创建后 exact-title count 为 1、state `open`、label `needs-analysis`，正文回读确认 #26/#51、12 个 exact targets 与非授权声明全部存在 |
| `current-transition/` absence | PASS | 目录故意不存在并由 governance test 固化；#52 不使 unsupported Next.js 14 合法，也不替代真实 current bytes |
| `git diff --check` | PASS | revised implementation/docs diff 无 whitespace error |
| branch push | PASS | target-only/umbrella commit `ced969d1957448bb8870efd3ed7645023ba116cf` 已普通 fast-forward push 到 `origin/change/26`，没有 force push |
| Gitea final PR | PASS | [PR #29](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/29) open、mergeable、49 files、base `main`、head `change/26@ced969d`；正文精确且只含 `Closes #26`；Issue #26 为 open + `pr-open` |
| Gitea PR CI | NOT RUN | `ced969d` aggregate 为 `pending`，但 `total_count=0`、statuses 空、匹配 Actions runs 为 0；live main protection `enable_status_check=false`。不得把零 context aggregate pending 写成 CI 运行或通过 |
| NewEmaint consumer/build/migration | NOT RUN | 未修改或运行 NewEmaint package、lockfile、Dockerfile、schema、image、migration 或 application tests |
| Docker/Registry/AppServer/database/Secret | NOT RUN | 未连接 Docker daemon/Registry/AppServer/database，未读取或修改 Secret |
| deployment / production | NOT RUN | 不在授权范围；target candidate、Issue、push 或 local tests 都不是部署证据 |

## Acceptance criteria 结果

| AC | Result | Evidence / boundary |
|---|---|---|
| AC-1 | PASS（platform-local） | Profile schema 为每个 slot 保留唯一 preferred，并新增 strict `transitions` closed allowlist；same-category、global uniqueness、仅 `supported`/`sunset` 与 unknown-field rejection 均有正反测试；3 个 profile ID 不变 |
| AC-2 | PASS（platform-local） | Validator 对 preferred/一个 transition 唯一解析；unknown/duplicate/cross-category/preferred+transition/multiple transition/prohibited/EOL/state/Issue/exception/expiry/mismatch 均 fail closed；两个 component 共享 umbrella URL 时仍保留不同 exception |
| AC-3 | PASS（catalog evidence） | 增加 npm `10.0.0`、Next `14.2.33`、React `18.3.1`、TypeScript `5.8.3`、Node `22.22.3-bookworm-slim` linux/amd64 child digest；保留 Node `22.22.3`、Prisma `5.22.0`、PostgreSQL `16.14`；Next 14 仅作 prohibited evidence |
| AC-4 | PASS（external tracking only） | 创建且只创建 NewEmaint #52；authenticated GET 验证 exact targets、分阶段 Gate、#26/#51 关联和不授权 mutation/deploy/merge 声明。没有生成 current lock |
| AC-5 | PASS（target/preferred compatibility） | Catalog revision 与 Linux profile minor 已递增；Linux/Windows/SQLite preferred fixtures、3 个 committed reference locks 与 target candidate 全部通过。Baseline/current target resolved set semantic diff empty；reference/gap 明确 target-only、current lock 未生成、`NOT MIGRATED`、`NOT DEPLOYED` |
| AC-6 | PASS（platform-local） | Synthetic transition lock 固化 resolved component、absolute migration Issue、exception ID/expiry 与 catalog/profile/declaration checksums；连续生成 byte-identical。Declaration/digest/source checksum/profile/catalog/self-hash/exception tamper tests fail closed |
| AC-7 | PASS（synthetic integration only） | Optional protected `architecture_project_id` 保持旧 v1 profile compatibility；声明后 project/profile/catalog/release checksum/lock self-hash/expiry 均在 Docker 前验证。Substitution/tamper/expired exception 均为零 Docker calls；真实 NewEmaint release 为 NOT RUN |
| AC-8 | PASS | Architecture README、NewEmaint reference/gap、Docker release README 与 onboarding 统一 preferred/transition/current/target/umbrella 边界，并明确 target 不是 migration/deployment evidence、umbrella/transition 不绕过 prohibited/EOL/digest/expiry/checksum |
| AC-9 | PASS（local）/ NOT RUN（PR/external runtime） | 34 architecture + 39 release focused tests、178-test full smoke、双 installer、`bash -n`、ShellCheck、`git diff --check` 均通过。PR CI、NewEmaint consumer、真实 Docker/Registry/AppServer/migration/production 分开记录 |

总体终态：**VERIFIED_LOCAL / PR OPEN**。Platform target components、transition contract、
canonical lock 与 Docker release preflight 已实现；唯一 NewEmaint umbrella tracking #52 已
创建并回读；最终 PR #29 已创建并停在人工合并闸门。没有 CI context 可运行，这不授权迁移、
部署或自动合并。

## 重复执行

- Synthetic transition canonical lock 第一次/第二次：PASS，byte-identical。
- Architecture installer 第一次/第二次：PASS，installed-file manifest 完全一致。
- Docker release installer 第一次/第二次：PASS，installed-file manifest 完全一致且零 Docker。
- Full smoke 最终重跑：PASS，178 tests。
- NewEmaint Issue exact-title readback：PASS，count 精确为 1，仅 #52。
- 真实 NewEmaint deploy 第一次/第二次：NOT RUN。

## 故意失败、自修复与回滚

- Unknown/duplicate/cross-category/multiple transition、preferred+transition ambiguity、
  prohibited component、相对或 credential-bearing transition Issue URL：PASS，validator 非零退出。
- Missing/duplicate/mismatched/expired/>180-day/after-`migrate_by` exception：PASS，lock 不生成。
- Mutable/mismatched OCI digest、source checksum drift、project/profile/catalog substitution、
  unknown lock field、自哈希篡改：PASS，均 fail closed。
- Docker release 的 target/current substitution 与 expiry：PASS，在 `config` 之前拒绝，Docker
  event list empty；没有 mutation 可回滚。
- #52 首次 POST 因一次性脚本错误地让 curl token config 与 JSON body 共用 stdin，Gitea 返回
  `422`。立即 authenticated list 证明同标题 Issue count 为 0；live Swagger 确认字段合同后，
  将非敏感 JSON body 与 token stdin 分离，再次通过 `bash -n`/ShellCheck，第二次 POST 成功创建
  唯一 #52 并回读。一次性脚本已删除，未创建重复 Issue。
- Application/DB rollback：NOT RUN；本 Change 没有 application、schema、image、server 或
  database mutation。Platform 回滚方式是对 implementation commits 建立 revert PR 并重跑同一
  suite，不能回退到 EOL/prohibited 或 checksum 不完整的 lock。

## 外部 handoff 与遗留风险

- NewEmaint #52 当前为 `needs-analysis`；其创建只建立治理入口。实际工作必须在 NewEmaint
  自己的 `change/52`、complex spec/plan、测试和人工 Gate 中另行批准。
- Node `22.22.3` 是 approved exact observed pin，但不是 Context7 当前显示的最新 v22 patch；
  它只可作为有期限的 sunset transition，不能宣称 latest。
- 当前 Next.js 14 已 `prohibited`，因此本 Change 不生成 current lock；#52 必须迁移到 supported
  Next.js，并以真实完整 release bytes 生成 `newemaint` current lock。
- Node/npm、Prisma、PostgreSQL、Next/React、TypeScript、OS/container/proxy 与 OCI/image 的实际
  compatibility、backup/restore、migration、test deploy 和 rollback 全部属于 #52 后续合同。
- Gitea PR #29 已 open；PR CI 因零 status/Actions context 为 `NOT RUN`。人工合并、Issue close/
  terminal lifecycle、真实部署与 production 验收尚未执行。
