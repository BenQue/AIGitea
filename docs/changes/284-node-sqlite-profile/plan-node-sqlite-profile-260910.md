---
issue: 284
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/284
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
status: contract-drafting
branch: change/284-node-sqlite-profile
created: 2026-09-10
updated: 2026-09-10
---

# Implementation plan：Node 22 加 SQLite profile 与三处 architecture 合同裁决

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 裁决 C：migration Issue URL 放宽为绝对 http(s)，含正负 fixture 与测试 | - | pending |
| T02 | 裁决 B：as-built 版本例外，含 schema、validator、lock、release optional key 与测试 | T01 | pending |
| T03 | 裁决 A 与需求 1：新增 profile `linux-node-sqlite-v1` 与两份分环境 fixture | T02 | pending |
| T04 | 裁决 D 与文档：ADR-0006、architecture README、onboarding runbook §9 | T03 | pending |
| T05 | verification 记录：两次 lock byte-identical、全量测试与 smoke 证据 | T04 | pending |

T01 先行是因为 T03 的 profile 要用 transition 表达 Node 22，而 transition 在 http 规则放宽前
无法用真实可读的内网 Issue URL 声明。T02 先于 T03 是因为分环境 fixture 依赖 as-built 才能
如实填写版本。

## Expected touch points

- T01：`codex/runtime/aisoft_architecture/validator.py`（`ISSUE_RE`、`_is_absolute_issue_url`）、
  `codex/runtime/tests/test_architecture_transitions.py`。
- T02：`architecture/schemas/project-architecture-v1.schema.json`、
  `architecture/schemas/architecture-lock-v1.schema.json`、
  `codex/runtime/aisoft_architecture/validator.py`、
  `codex/runtime/aisoft_architecture/lockfile.py`、
  `codex/runtime/aisoft_release/contract.py`、
  `architecture/fixtures/invalid/`、`codex/runtime/tests/test_architecture_lock.py`。
- T03：`architecture/profiles/linux-node-sqlite-v1.json`、`architecture/fixtures/valid/`、
  `codex/runtime/tests/test_architecture_schema.py`。
- T04：`architecture/decisions/0006-*.md`、`architecture/README.md`、
  `skill-for-codex/references/onboarding-runbook.md`。
- T05：`docs/changes/284-node-sqlite-profile/verification-node-sqlite-profile-260910.md`。

范围提示不授权扩大 spec；catalog component 集合与 revision 不在触点内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `aisoft-architecture validate` 对每个 fixture 跑一遍，profile 全量加载通过 |
| AC-2 | 两份分环境 fixture 各跑一次 `validate`，断言 `valid: true` |
| AC-3 | 新增 invalid fixture 与单测，逐条断言 5 个新诊断码 |
| AC-4 | 单测断言 lock `resolved_components` 记录声明版本与 `as_built: true` |
| AC-5 | 既有 `semver-range.json` 等 invalid fixture 仍返回 `PROJECT_VERSION_DRIFT` |
| AC-6 | 单测覆盖 http 接受与相对路径、简写、带凭据、带 query 的拒绝 |
| AC-7 | 人工复核 ADR、README 与 runbook §9 的措辞 |
| AC-8 | `python3 -m unittest discover -s codex/runtime/tests` 与 `bash codex/tests/smoke.sh` |
| AC-9 | 同一 declaration 连续两次 `lock`，`cmp` 两份输出 |

## 部署与回滚

无部署影响。回滚为 `git revert` 单个 merge commit；本变更只新增文件与可选字段，
既有 declaration 与 lock 不受影响。
