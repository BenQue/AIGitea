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

# Implementation plan

## 任务分解

1. 冻结 `origin/main@8d5dae9569b6e61e88b40490ae04941614c62f8d`、Issue #26、已完成
   #22/#23 contract 和 NewEmaint authoritative metadata；只读核对真实 current versions，
   不读取 Secret、业务数据或运行环境值。
2. 使用 Context7 与 official/upstream sources 逐项回读 Node/npm/Prisma/PostgreSQL/Next/React/
   TypeScript 和 official Node OCI image 的 lifecycle、兼容性与 exact digest；将 URL、retrieved/
   review date、pin、mirror/checksum/SBOM policy 与冲突处理写入 catalog evidence。
3. 先用正反 fixtures 固化 profile slot contract：preferred exact path、显式 transition allowlist、
   same-category、唯一解析、allowed state、migration Issue 与 exception 一一绑定、UTC expiry/EOL
   boundary；再同步修改 JSON Schema 和 validator。
4. 增加所需 catalog components，递增 catalog revision 与 Linux profile version，为每个可用
   current component 只加入必要 transition allowlist；unsupported Next.js 14 只保留 prohibited
   现状证据。Windows/SQLite profile 只更新 revision/checksum，不改变 resolved target semantics。
5. 在用户书面授权后，只在 NewEmaint 创建一个 umbrella migration Issue。Issue 列出
   target-candidate 的 12 个 exact components、应用兼容性、数据库 backup/restore/rollback、
   OCI provenance、test deployment、production approval 和非授权边界；关联 #26 与 #51，使用
   authenticated GET 回读，绝不创建第二个 component migration Issue。
6. 将现有 NewEmaint target reference 迁移到明确的 `target-candidate` 目录，只生成/比对 target
   lock 与 gap report；记录 catalog/profile revision 导致的预期 checksum drift。明确
   `current-transition/` 不存在，禁止修改 resolved target component 集来掩盖差异。
7. 在 `aisoft_release` target profile parser 增加可选受保护 `architecture_project_id`，并在
   release file validation 中于 Docker 调用前校验 lock project/profile/catalog/checksum；添加
   target/current substitution、tamper 和 expiry integration fixtures。
8. 更新 architecture/Docker release README、onboarding 与 installer manifest；补充多个
   component 共享一个 umbrella Issue 仍保留独立 exception 的测试；连续运行两次 architecture/
   release installer，证明安装内容和 generated lock byte-identical。
9. 运行 focused architecture/release unittest、CLI fixtures、`bash -n`、ShellCheck、
   `bash codex/tests/smoke.sh` 与 `git diff --check`；填写 `03-verification.md`，将 platform-local、
   external Issue、PR CI、NewEmaint consumer、Docker/Registry/AppServer/migration/production 分开。
10. 完成全部 revised acceptance 后推送 `change/26`，创建正文只含唯一 closing directive
    `Closes #26` 的最终 PR，回读 final head/CI 后停止在人工合并闸门；不自动 merge 或部署。

## 涉及文件

- `docs/changes/26/{00-summary,01-spec,02-plan,03-verification}.md`
- `architecture/catalog.json`
- `architecture/profiles/linux-node-postgres-v1.json`
- `architecture/profiles/{windows-dotnet-postgres-v1,small-embedded-sqlite-v1}.json`
- `architecture/schemas/{profile,project-architecture,architecture-lock}-v1.schema.json`
- `architecture/reference/newemaint/**`
- `architecture/evidence/official-sources.md`
- `architecture/README.md`
- `codex/runtime/aisoft_architecture/{validator,lockfile}.py`
- `codex/runtime/aisoft_release/contract.py`
- `codex/runtime/tests/test_architecture_*.py`
- `codex/runtime/tests/test_release_architecture_integration.py`
- `codex/tests/fixtures/architecture/**`
- `codex/tests/test-architecture-install.sh`
- `codex/tests/test-docker-release-install.sh`
- `codex/tests/smoke.sh`
- `docker-release/README.md`
- `skill-for-codex/references/onboarding-runbook.md`

## 数据库迁移

无。本 Change 只维护 platform catalog/profile/schema/lock/reference、release preflight，并创建一个
NewEmaint 治理 Issue。该 Issue 后续必须在 NewEmaint 自己的 Change 中设计 PostgreSQL
backup/restore、兼容性测试、migration 和 rollback；本 Change 不连接或修改数据库。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | Profile JSON Schema 正反 fixtures；三个 profile ID/slot/category/transition allowlist review |
| AC-2 | `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_architecture_schema codex.runtime.tests.test_architecture_governance codex.runtime.tests.test_architecture_transitions -v` 与 fail-closed diagnostics |
| AC-3 | Catalog validation + official source ledger + exact OCI tag/digest readback；source/digest 失败 fixture |
| AC-4 | Live NewEmaint Issue list preflight、duplicate-safe creation、exact-title count 1、authenticated GET readback、正文 target/gate/non-authorization assertions；`current-transition/` absence |
| AC-5 | preferred fixtures/target lock semantic diff 与 catalog/profile revision migration review |
| AC-6 | `aisoft-architecture lock` 连续两次 byte/hash equality；declaration/exception/digest/checksum/self-hash tamper tests |
| AC-7 | `test_release_architecture_integration.py` 的 identity/checksum、target/current substitution/tamper/expired reject 与 Docker call count 0 |
| AC-8 | Architecture/Docker/onboarding/NewEmaint reference/gap docs review 与 forbidden-claim assertions |
| AC-9 | focused unittest、两个 installer repeatability、`bash -n`、ShellCheck、full smoke、`git diff --check` 和 final-head CI status |

## 部署与回滚

本 Change 不部署应用、不安装/启动 Docker、不操作 Registry/AppServer/database/Secret。Installer
只在临时目录连续运行两次。故意失败至少覆盖 category mismatch、duplicate transition、EOL、
expired exception、fake migration Issue format、target/current substitution 和 lock tamper，均须在
Docker mutation 前停止。代码/contract 回滚使用 revert PR；NewEmaint umbrella Issue 可关闭或
重定范围，但不能作为应用字节回滚。真实项目升级与环境回滚另行批准。
