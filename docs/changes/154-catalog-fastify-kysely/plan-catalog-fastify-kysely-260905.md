---
issue: 154
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/154
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - shared-core
depends_on: []
status: contract-drafting
branch: change/154-catalog-fastify-kysely
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | catalog 新增两条组件、revision 递增、证据入档 | - | pending |
| T02 | systemd 原生 profile 升 1.1.0 加两个 slot，并完成 revision 级联与 lock 重生成 | T01 | pending |
| T03 | LocalWMS 形状候选声明实测、全量测试与验证记录 | T02 | pending |

## Expected touch points

- T01：`architecture/catalog.json`、`architecture/evidence/official-sources.md`。
- T02：`architecture/profiles/`（四个文件）、`architecture/fixtures/valid/`（五个）、
  `architecture/fixtures/invalid/`（六个带 `catalog_revision` 的）、
  `architecture/templates/project-architecture.example.json`、
  `architecture/reference/` 三份声明与三份重新生成的 lock、
  `architecture/reference/newemaint/gap-report.md`、
  `codex/runtime/tests/release_test_support.py`、
  `codex/runtime/tests/test_architecture_cli.py`、
  `codex/runtime/tests/test_architecture_schema.py`、
  `codex/runtime/tests/test_architecture_transitions.py`、
  `codex/runtime/tests/test_architecture_lock.py`、
  `codex/runtime/tests/test_release_architecture_integration.py`、
  `codex/tests/test-architecture-install.sh`、`codex/tests/smoke.sh`。
- T03：`docs/changes/154-catalog-fastify-kysely/verification-catalog-fastify-kysely-260905.md`。

这是范围提示，不授权扩大 spec。测试文件只允许改动钉住的日期与 revision 常量，不改断言语义。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `architecture/bin/aisoft-architecture explain --component framework.fastify.5` 与 `--component orm.kysely.0-29` |
| AC-2 | catalog diff review 加任意一次 validate 输出里的 `catalog_revision` |
| AC-3 | profile diff review 加 `git diff` 确认 1.1.0 与两个 slot |
| AC-4 | `git diff` 对既有三个 profile 与 fixtures 只见 `catalog_revision` 一行变化；五个 valid fixture 逐个 validate 仍 `valid:true` |
| AC-5 | 对三个 reference 各跑一次 `lock`，与提交的 lock 逐字节比较，再跑第二次确认 byte-identical |
| AC-6 | 在临时目录用 LocalWMS 形状候选声明跑 `validate` |
| AC-7 | `bash codex/tests/smoke.sh` 与 architecture 单测 |
| AC-8 | 验证记录的「遗留风险与未完成项」写明重装交接 |

改动前的基线证据（39 个 architecture 单测 OK、五个 valid fixture 全 `valid:true`、
smoke rc=0）必须抄进验证记录，合并后无法重放。

## 部署与回滚

无部署。回滚为 revert 唯一最终 PR 并重跑同一验证集。
`architecture/install.sh` 的合并后重装是交接项，不在本 PR 内执行。
