---
issue: 58
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/58
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
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 22
  - 27
  - 37
  - 40
status: approved
branch: change/58
pr_url: null
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

## 任务分解

1. 冻结 fresh Gitea main、Issue #58、protected branch、branch/PR/CI 基线，确认 canonical checkout
   dirty/untracked 内容并仅在独立 `change/58` worktree 开发。
2. 增加 strict `docker-release/v2` manifest/schema 与 producer normalized Compose model checksum；保留
   v1 parser 和 legacy command compatibility，新增 artifact-only loader/validator。
3. 将 runner 分成 artifact、readiness、stage、migrate、activate 内部原语和公开命令；旧 `deploy`
   组合这些原语，旧 `verify/status/rollback` 在兼容边界内保持原调用方式。
4. 引入 `docker-release-state/v2` staging receipt，验证 exact release/image identity，提供 strict v1→v2
   state migration；对 missing/uncertain/identity drift fail closed。
5. 增加 fixed-action command gate、strict grant schema/template 与 installer 交付；固定 action、target、
   full SHA、profile、CLI argv，并记录 started/completed audit event。
6. 扩展 unit/fake integration tests，逐阶段断言 allowed/forbidden call counts；覆盖 legacy v1 positive、
   v2 strict validation、state migration、rollback 和 gate negative cases。
7. 更新 docker-release README、平台相关分册、安装说明与 adopter migration guidance；明确 artifact
   conformance、target readiness、real consumer E2E 和 deployment 状态互不替代。
8. 运行 focused Python、fake harness、installer twice、`bash -n`、ShellCheck（若可用）、full smoke、
   `git diff --check`。真实 Docker/VM/PostgreSQL/health/browser/rollback E2E 未获授权则保持 BLOCKED。
9. 更新 `03-verification.md`、提交并推送 `change/58`，创建 `Closes #58` PR；核对 exact final head
   required CI/status，停止在人工 merge gate，不自动 merge 或 deploy。

## 主要涉及文件

- `docs/changes/58/{00-summary,01-spec,02-plan,03-verification}.md`
- `docker-release/README.md`
- `docker-release/schemas/release-manifest-v2.schema.json`
- `docker-release/schemas/state-v2.schema.json`
- `docker-release/schemas/command-gate-v1.schema.json`
- `docker-release/templates/**`
- `docker-release/bin/**`
- `codex/runtime/aisoft_release/{cli,contract,runner,state,transport,gate}.py`
- `codex/runtime/tests/{release_test_support,test_release_*}.py`
- `codex/tests/test-docker-release-install.sh`
- 相关现行平台分册与 onboarding 文档（以最小一致性 diff 为准）

## 数据库迁移

没有平台或应用数据库 schema/data migration。本 Change 只实现可单独授权的 migration phase；测试使用
fake adapter，不连接真实 PostgreSQL。真实 migration、backup、restore 全部 `NOT RUN`。

## AC 到验证映射

| AC | 验证 |
|---|---|
| AC-1 | artifact-only unit/fake test；Docker/Compose/target/Secret call count = 0 |
| AC-2 | readiness positive/negative tests；所有 mutation calls = 0 |
| AC-3 | Registry/offline staging tests；migration/up calls = 0，state receipt strict |
| AC-4 | staged/migration receipt tests；transport/up calls = 0，uncertain fail closed |
| AC-5 | activation prerequisite/health/identity tests；transport/migration calls = 0 |
| AC-6 | CLI parser/contract version/legacy v1 positive/migration guidance review |
| AC-7 | read-only status与 v2 local-only rollback tests；legacy rollback regression |
| AC-8 | gate unit/installer tests；arbitrary action/path/short SHA/shell rejection |
| AC-9 | state v1→v2/malformed/identity drift/rollback tests |
| AC-10 | matrix diff must remain unchanged；README evidence gate review |
| AC-11 | explicit adapter event/call-count assertions per phase |
| AC-12 | separately authorized real harness；否则 `NOT RUN / BLOCKED` |
| AC-13 | focused/full/installer/shell/diff checks + documentation review + final-head CI readback |

## 部署与回滚

本 PR 不部署。平台代码回滚使用 revert PR；新 schema/artifact/state 不原地修改。真实 Docker/VM
mutation只在后续精确授权且 disposable target identity 明确时运行；不得触碰现有 daemon resources、
DockerLab、AppServer、production、Secret 或真实 PostgreSQL。
