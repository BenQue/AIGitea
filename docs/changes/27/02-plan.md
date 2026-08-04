---
issue: 27
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/27
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/27
pr_url:
created: 2026-08-04
updated: 2026-08-04
---

# Implementation plan

## 任务分解

1. 冻结 `origin/main@8d5dae9569b6e61e88b40490ae04941614c62f8d`、Issue #27、#22
   verification 的 `NOT RUN` 边界和 NewEmaint consumer failure；保存 Docker official docs 与
   fixed Moby source commit 的 URL/日期/结论，不用推理替代真实 E2E。
2. 先建立 legacy/v2 manifest、inventory、archive reference 和 capability matrix 正反 fixtures，
   固化四类 identity、deterministic tag naming、exact field sets、compatibility migration 与
   Docker call/mutation ordering。
3. 扩展 strict release parser/model/schema：v2 image fields、offline sub-contract version、
   service/reference/image-ID 唯一性、runtime/transport tag equality、release SHA/source repo/
   service naming、archive/inventory/Compose/architecture checksums；legacy Registry 保持兼容，
   legacy offline 在 load 前拒绝。
4. 扩展 fixed-argv Docker adapter，增加 bounded/redacted server version、Compose version、
   `docker info` store detection、tag 与 exact inspect；unknown/ambiguous output 不回显 daemon
   details或 Secret，且不 fallback。
5. 更新 Registry/Offline transports 与 Compose validator。Registry pull digest 后生成并验证
   runtime tag；offline 先验证 archive refs/checksums/capability，再 load 并按 runtime tag验证
   image ID/platform；两者都由 Compose `--pull never --no-build` 启动并执行 post-start exact ID。
6. 添加 versioned compatibility matrix 和 runtime policy。先把没有真实证据的 classic row 标记
   `rejected`；只有后续同 fixture E2E 完整 PASS 才在同一 Change 中改为 `supported`。
7. 构建 disposable E2E harness：两个独立 daemon/data roots、一个 producer-side ephemeral
   Registry、最小 linux/amd64 health fixture、确定性 manifest/inventory/archive、断网 offline
   consumer、container identity/assertions 和精确 cleanup。Harness 默认只检查先决条件，不自行
   创建 VM、改 daemon config、restart 或 prune。
8. 获得用户对 disposable Docker 环境的单独授权后运行 Engine 29 containerd E2E；记录 exact
   versions/store marker/digests/checksums/image ID/Compose/container/health/cleanup。若另有获准的
   classic daemon，运行同一 harness；否则保持 reject，绝不把它写成 PASS。
9. 更新 NewEmaint synthetic consumer fixture、Docker release README/onboarding/schema/install
   manifest；若 #26 已合并，先整合最新 main 并重跑 architecture-project/current-lock integration，
   不复制或手改 #26 catalog/lock。
10. 运行 focused release unittest、fake adapter、tamper/mutation-order、installer repeatability、
    `bash -n`、ShellCheck、`bash codex/tests/smoke.sh` 与 `git diff --check`；填写
    `03-verification.md`，将所有 real/fake/external状态分开。
11. 在合同获书面批准后才提交实现。满足 local 与必需 containerd real E2E 后推送
    `change/27`，创建仅含 `Closes #27` 的最终 PR，停止在人工合并闸门；不自动 merge/deploy。

## 涉及文件

- `docs/changes/27/{00-summary,01-spec,02-plan,03-verification}.md`
- `docker-release/README.md`
- `docker-release/schema/release-manifest-v1.schema.json`
- `docker-release/schema/target-profile-v1.schema.json`
- `docker-release/schema/image-store-compatibility-v1.schema.json`
- `docker-release/compatibility/image-stores-v1.json`
- `docker-release/templates/**`
- `docker-release/install.sh`
- `codex/runtime/aisoft_release/{contract,docker,transport,compose,runner}.py`
- `codex/runtime/tests/test_release_*.py`
- `codex/runtime/tests/release_test_support.py`
- `codex/tests/fixtures/docker-release/**`
- `codex/tests/integration/test-docker-image-store-e2e.sh`
- `codex/tests/test-docker-release-install.sh`
- `codex/tests/smoke.sh`
- `skill-for-codex/references/onboarding-runbook.md`

## 数据库迁移

无平台或应用数据库迁移。E2E fixture 不连接 PostgreSQL。Release runner 的 migration ordering
只用 fake/no-op fixture 验证；真实 NewEmaint migration、backup、restore、AppServer 与 production
保持独立 Gate 和 `NOT RUN`。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | v2 schema/model/tag naming 正反 fixtures；manifest canonical identity review |
| AC-2 | producer fixture：digest/tag ID equality、save-by-tag、inventory/archive checksum/service/platform assertions |
| AC-3 | legacy Registry positive + legacy offline pre-load reject + mixed/unknown fields negative tests |
| AC-4 | Docker version/info/Compose parser fixtures；containerd/classic/unknown/conflict matrix 与 mutation count 0 |
| AC-5 | offline tamper/load/inspect/Compose/post-start tests；RepoDigests empty positive fixture |
| AC-6 | Registry pull/RepoDigest/tag 与 offline load 对同一 image ID/runtime tag/Compose bytes 的 parity test |
| AC-7 | 获准环境运行 `codex/tests/integration/test-docker-image-store-e2e.sh` containerd mode 并保存脱敏 evidence |
| AC-8 | 同 harness classic mode PASS 后才支持；否则 compatibility row/rejection diagnostic/pre-load zero mutation review |
| AC-9 | 全字段 tamper、wrong store、TOCTOU container mismatch、migration/up ordering 和 rollback fixtures |
| AC-10 | NewEmaint synthetic verifier、focused tests、installer twice、`bash -n`、ShellCheck、full smoke、`git diff --check` 与 verification status review |

## 部署与回滚

本 PR 不部署应用或修改现有 Docker daemon。Disposable E2E 的唯一允许 mutation 是在用户批准的
精确临时环境中 build/tag/push/save/load/up/down 和删除该 fixture 自有 container/image/archive/
Registry；不得触及其它 daemon、VM、volume、network 或数据。每次运行先记录 exact target，
结束后证明 fixture cleanup；失败时停止并保留最小脱敏诊断。平台回滚使用 revert PR，legacy
bundle 不改写，需由受控 producer 重新发布 v2。
