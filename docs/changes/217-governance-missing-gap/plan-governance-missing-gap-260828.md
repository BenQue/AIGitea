---
issue: 217
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/217
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
  - 215
status: approved
branch: change/217-governance-missing-gap
created: 2026-08-28
updated: 2026-08-28
---

# governance missing collaborator GAP 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | #217 mapped summary/spec/plan/verification、fresh #215 baseline、改前复现与 manual/live-mutation=0 边界 | - | completed |
| T02 | exact account-missing + collaborator 404 正向、present/schema/auth/ordering/apply 负向测试 | T01 | completed |
| T03 | governance check 最小 evidence-derived missing 实现与 targeted regression | T02 | completed |
| T04 | governance/security/host-access/full smoke、semantic/Controller preflight、verification 与独立自检 | T03 | completed |
| T05 | local atomic commits、canonical manual PR payload 与最终 PR 前 handoff | T04 | completed |

## Expected touch points

- T01：`docs/changes/217-governance-missing-gap/`。
- T02：`codex/runtime/tests/test_gitea_governance.py`。
- T03：`codex/runtime/aisoft_gitea_governance/{cli,reconcile}.py`。
- T04：本 Issue plan/verification status；除必要 source/test/docs 外不扩范围。
- T05：本地 Git commits 与 Controller/payload preflight；不 push、不创建 PR。

## 数据库迁移

无。Gitea account/PAT/collaborator/protection mutation 均不在本计划执行。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2 | `test_gitea_governance.py` missing 404/readable plan、account三态、account-before-permission call order |
| AC-3、AC-4 | strict 200 malformed matrix；account present 404；401/403/5xx/transport；unknown/shared identity negatives |
| AC-5 | existing desired protection、target Write、cross-project read/write/admin/owner、required context与apply tests |
| AC-6、AC-7 | GET-only call inventory；apply verify/pre-snapshot-before-write tests；CLI/output key regression与diff review |
| AC-8 | targeted Python；governance/host-access/routine security suites；四个 shell suites；full smoke；semantic/Controller preflight |

## 实施顺序

1. 完成 T01，运行 semantic mapping/check 并原子 commit；投影 Issue 为 `approved`。
2. T02 先增加改前稳定失败的 exact account-missing + permission 404 test，再补 present/schema/auth/ordering/apply matrix。
3. T03 只在 `_check` 内派生 known-missing evidence；mutation caller 保持默认 fail-closed。
4. T04 重放定向与全量门禁，如实更新 verification；任何安全合同扩大立即停止升级。
5. T05 形成原子 commits、local Controller/payload preflight，停在 `AWAITING_PR_CONFIRMATION`。

## 部署与回滚

无部署。Source 通过 revert #217 唯一最终 PR 回滚；本任务 live mutation 固定为 0。
