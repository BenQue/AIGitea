---
issue: 31
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/31
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
depends_on: []
status: approved
branch: change/31
pr_url:
created: 2026-08-05
updated: 2026-08-05
---

# Implementation plan

## 任务分解

1. 读取 Issue #31、`origin/main@e59359f`、现有 architecture contracts，并只读核对 npm
   Registry 与 Next.js official documentation/peerDependencies。
2. 扩展 catalog schema 和 validator，建立 React stable-release snapshot 的离线 fail-closed
   contract，并用 negative cases 覆盖不可用版本、channel、range 与 package mismatch。
3. 更新 React pin、Linux profile、所有 declaration/fixture/reference identity；通过 CLI 重新
   生成 committed reference locks，禁止手写 checksum。
4. 更新 official evidence、architecture README 和 NewEmaint gap report，写清 #52 的 merge-SHA
   消费条件与 `NOT RUN` 边界。
5. 运行 focused unittest、architecture CLI/install、full smoke 和 diff/JSON checks；提交、推送
   `change/31` 并创建含唯一 closing directive `Closes #31` 的 PR，停止在人工合并闸门。

## 涉及文件

- `docs/changes/31/{00-summary,01-spec,02-plan}.md`
- `architecture/{catalog.json,README.md,evidence/official-sources.md,profiles/**,templates/**,fixtures/**,reference/**,schemas/catalog-v1.schema.json}`
- `codex/runtime/aisoft_architecture/validator.py`
- `codex/runtime/tests/{test_architecture_schema.py,release_test_support.py}`
- `codex/tests/{smoke.sh,test-architecture-install.sh}`

## 数据库迁移

无。该 Change 不连接或变更数据库。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-3 | `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_architecture_schema -v` |
| AC-2 | `architecture/bin/aisoft-architecture validate` for three committed references; lock regeneration and `git diff --check` |
| AC-4 | Review source ledger, profile and NewEmaint gap report against npm Registry and Next.js peer metadata |
| AC-5 | `bash codex/tests/test-architecture-install.sh`; focused architecture/release unittest; `bash codex/tests/smoke.sh` |

## 部署与回滚

无部署。回滚是对该最终 PR 的 revert；没有 Docker/Registry/server/database/Secret mutation。未来
NewEmaint #52 在此 PR 合并后从其 exact merge commit 更新基线和两包 lockfile，并独立验证和审批。
