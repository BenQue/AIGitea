---
issue: 213
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/213
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 35
  - 208
status: approved
branch: change/213-routine-live-pilot
created: 2026-08-27
updated: 2026-08-27
---

# 单仓 routine auto-merge live pilot 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | #213 mapped summary/spec/plan/verification、fresh source/installed/live baseline 与授权边界 | - | completed |
| T02 | NewEMaint-only manifest/provenance/account-state/apply contract 与回归 | T01 | completed |
| T03 | broker PAT exact scope、routine host audit、Issue #74 canary gate 与回归 | T02 | completed |
| T04 | deterministic bootstrap/revoke/retain-delete rollback、installer byte parity 与 shell 回归 | T03 | completed |
| T05 | full verification、controller preflight、原子 commits 与最终 PR candidate | T04 | completed |

## Expected touch points

- T01：`docs/changes/213-routine-live-pilot/`。
- T02：`codex/config/gitea-governance.json`、`codex/config/host-access-broker.json`（仅 strict pilot binding
  所需字段）、`codex/runtime/aisoft_gitea_governance/{contract,reconcile,cli}.py` 与对应 tests。
- T03：`codex/runtime/aisoft_host_access/{contract,broker}.py`、`codex/runtime/tests/test_host_access.py`、
  `test_routine_merge.py`、`codex/tests/test-host-access-broker.sh`。
- T04：`codex/tools/bootstrap-gitea-service-account.sh`、新增 exact routine rollback/readback tool、
  `codex/install-host-access-broker.sh`、installer/bootstrap shell tests 与 `codex/tests/smoke.sh` 清单。
- T05：本 Issue verification/plan/summary 状态；不 push、不创建 PR、不触碰 live。

## 数据库迁移

无。Gitea account/PAT/live repository mutation 属于后续独立授权的 rollout，不在本计划执行。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2、AC-7、AC-13 | governance contract/reconcile/CLI tests；manifest non-target byte comparison；provenance ancestor/byte fake Git tests |
| AC-3 | governance check account present/missing/present-site-admin tests |
| AC-4、AC-9、AC-10 | bootstrap/rollback fake Gitea/curl/sudo tests；mutation counts；ownership/retain/delete/readback 负例 |
| AC-5、AC-6、AC-8 | host-access/routine merge tests：exact scope、metadata、cross-project、protection、Issue #74、zero POST/fallback |
| AC-11、AC-12 | installer target inventory tests、temporary install root 两次安装、逐文件 cmp/readiness receipt review |
| AC-14 | targeted unittest/shell；修改 shell `bash -n`/ShellCheck；`bash codex/tests/smoke.sh`；`resolve-documents`/`check-change-documents`；controller preflight |

## 实施顺序

1. 完成 T01，验证 semantic mapping 并原子 commit。
2. T02 先写 manifest/contract/check/apply failing tests，再实现 only-NewEMaint pilot 与 dual provenance。
3. T03 先写 routine scope/audit/canary failing tests，再实现 broker hardening；所有失败断言 merge POST=0。
4. T04 用 fake transports 实现 bootstrap/revoke/account-policy/readback 与 installer parity，不调用 live endpoint。
5. T05 跑定向与全量验证，填写 verification；形成本地原子 commits与 controller preflight。
6. 停在 `AWAITING_PR_CONFIRMATION`，输出唯一 manual PR title/body；未经新确认不得 push/create PR。

## 部署与回滚

无部署。Source 通过 revert #213 唯一 PR 回滚。未来 live rollback 必须按 spec AC-10 的固定顺序运行，
默认 retain account；delete 必须显式选择并满足 ownership/readback。当前任务所有 live mutation 为 `NOT RUN`。
