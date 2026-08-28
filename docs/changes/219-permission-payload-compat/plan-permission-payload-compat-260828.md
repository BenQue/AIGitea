---
issue: 219
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/219
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 217
status: spec-drafting
branch: change/219-permission-payload-compat
created: 2026-08-28
updated: 2026-08-28
---

# Gitea collaborator permission payload 兼容实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | #219 Issue、fresh `9f4595c6...` baseline、完整合同读取、official/live schema evidence、四份 semantic docs、semantic validation 与 docs commit | - | completed |
| T02 | legacy/actual-extended 正向与 root/role/user/identity/security 负向 failing tests，覆盖 governance 与 host-access permission surfaces | T01 | pending |
| T03 | 两个固定 variant 的最小 bounded validator implementation；调用方显式传 manifest-derived requested identity | T02 | pending |
| T04 | #217 exact 404、account/project/shared/unknown/cross-project isolation、check GET-only 与 apply zero-mutation/ordering regression | T03 | pending |
| T05 | governance/host-access/routine security、shell/full smoke、semantic/Controller preflight、verification 与原子 commits | T04 | pending |
| T06 | 停在 `AWAITING_PR_CONFIRMATION`，形成唯一 manual PR candidate；后续 install/live 另开授权 | T05 | pending |

## Expected touch points

- T01：`docs/changes/219-permission-payload-compat/`。
- T02/T04：`codex/runtime/tests/test_gitea_governance.py`、`codex/runtime/tests/test_host_access.py`；如需固定
  shell inventory，只允许对应现有 broker installer/smoke test assertions。
- T03：`codex/runtime/aisoft_gitea_governance/reconcile.py`、`codex/runtime/aisoft_host_access/broker.py`；
  不修改 client transport、manifest、CLI surface 或 apply contract。
- T05/T06：本 Issue plan/verification/summary 状态与本地原子 commits；未经第二确认不 push/create PR。

## 数据库迁移

无。Gitea account/PAT/collaborator/protection mutation 均不在本计划执行。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2 | governance/host-access parser focused fixtures：legacy/extended exact root、permission/role allowlist/conflict |
| AC-3、AC-4 | bounded user allowlist/required subset/type matrix；exact login/username/requested identity；is_admin exact false |
| AC-5 | governance target/cross-project + host-access manager/project/routine/cross-project call-site coverage；requested identity derivation review |
| AC-6 | #217 target account-missing 404 positive；present/site-admin/project/manager/shared/unknown/cross-project/auth/server/transport negatives |
| AC-7 | GET-only call inventory；apply missing-evidence denial、live-mode、pre-snapshot-before-write、zero mutation assertions |
| AC-8 | actual sanitized full-known-metadata fixture、legacy fixture、全部 malformed/security negatives与 ordering assertions |
| AC-9 | targeted/security Python、四个 routine shell suites、`bash codex/tests/smoke.sh`、semantic audit、diff/Controller review |

## 实施顺序

1. T01 只写 semantic docs、运行 mapping/check 并提交原子 docs commit；Issue 保持 `spec-drafting`。
2. 用户明确确认合同并允许启动 Development Loop 后，T02 先写 failing tests，证明现有 exact-one-key parser
   拒绝 actual extended response，同时安全负例保持红灯。
3. T03 只实现两个固定 variant 和 requested-identity绑定；不改错误分类、transport、manifest、output 或 apply surface。
4. T04 重放 #217/#215 ordering 与隔离矩阵，确认所有 check/audit methods 为 GET、apply failures mutation=0。
5. T05 跑定向与全量门禁并如实更新 verification；installed/live 层保持 NOT RUN。
6. T06 生成 policy=manual 的唯一 PR handoff，未经第二确认不 push/create PR；即使未来 PR 合并，也不得自动 install/live apply。

## 部署与回滚

无部署。Source 通过 revert #219 唯一最终 PR 回滚；本 Issue live mutation 固定为 0。未来安装与真实 live
readback 必须基于 exact merged SHA 另行授权，预期 readback 是可信 GAP/planned actions，不是自动 apply 或 PASS。
