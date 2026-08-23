---
issue: 150
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/150
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - deployment-boundary
  - platform-governance
depends_on: []
status: approved
branch: change/150-systemd-native-profile
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/151
created: 2026-08-23
updated: 2026-08-23
---

# Implementation plan：systemd 原生 profile 与 `systemd-native/v1`

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 两处 schema 枚举加 `systemd-native/v1`，新增 `linux-node-systemd-postgres-v1@1.0.0` profile，新增候选 fixture；`validate` 得 `valid: true` | - | done |
| T02 | lock 连续两次 byte-identical 与 `validate --lock` 无 drift，写成 CI 内回归（profile 计数、被排除 category、双 fixture lock 幂等） | T01 | done |
| T03 | ADR-0005 与 ADR-0003 交叉引用，runbook §4.1 与 §9 的适用条件/边界 | T01 | done |

Ticket 之间是纵向切片：T01 交付可校验的合同对象，T02 把 Issue 的硬验收固化进 CI，T03 交付人可读的合同边界。

## Expected touch points

- T01：`architecture/schemas/profile-v1.schema.json`、`architecture/schemas/project-architecture-v1.schema.json`、`architecture/profiles/linux-node-systemd-postgres-v1.json`、`architecture/fixtures/valid/linux-systemd-project.json`
- T02：`codex/runtime/tests/test_architecture_schema.py`、`codex/runtime/tests/test_architecture_cli.py`
- T03：`architecture/decisions/0005-systemd-native-delivery-profile.md`、`architecture/decisions/0003-profile-exception-and-ownership.md`、`skill-for-codex/references/onboarding-runbook.md`

范围提示，不授权扩大 spec：不动 catalog、validator、lockfile、既有 profile 与既有项目声明。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| 新 profile 通过 profile schema 与语义校验 | `test_catalog_and_all_profiles_validate`（glob 全部 profile，计数 4） |
| profile 不含 container/OCI/proxy/ORM/framework/frontend slot | `test_systemd_native_profile_has_no_container_or_frontend_slot` |
| 两处枚举含 `systemd-native/v1` 且 schema 通过 | 同上两项 + `jq empty`（smoke 对 `architecture/**/*.json`） |
| 候选声明 `validate` 得 `valid: true` | `architecture/bin/aisoft-architecture validate --project architecture/fixtures/valid/linux-systemd-project.json` |
| lock 连续两次 byte-identical | `test_lock_twice_is_byte_identical_and_validates`（linux + linux-systemd 两个 fixture） |
| 既有 profile/声明不被破坏 | `test_valid_fixtures_pass_schema_and_runtime`、`test_invalid_fixtures_fail_runtime`、`test_committed_reference_locks_cross_check`、`bash codex/tests/test-architecture-install.sh` |
| runbook §4/§9 同步 | 人工复核 + `test_governance_docs_keep_candidate_and_delivery_boundaries` |

全量门：`bash codex/tests/smoke.sh`（CI 的唯一 job）。

## 部署与回滚

无部署影响。本变更只新增平台合同对象与文档，不触碰任何目标机、service、timer 或凭据，因此没有重复部署与故意失败回滚可做。回滚方式是 revert 本 PR。
