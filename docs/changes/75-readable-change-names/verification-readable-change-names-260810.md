---
issue: 75
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/75
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
depends_on: []
status: implementation-verified
branch: change/75-readable-change-names
pr_url:
created: 2026-08-10
updated: 2026-08-10
---

# Readable issue-scoped Change naming verification

## Live baseline

| Check | Result | Evidence |
|---|---|---|
| private Gitea Issue #75 | PASS | installed project-scoped broker read：open，title `feat(governance): require readable issue-scoped change names`，0 comments，no labels |
| fresh protected main | PASS | installed broker `git.fetch.main`；`origin/main=2c39fbcf4380824584dec5843ae9c0234206bfd2` |
| canonical checkout protection | PASS | canonical remains on stale `main` with user `.DS_Store` files untouched；development uses isolated `/private/tmp/aisoft-change-75-readable-change-names` |
| readable branch de-dup | PASS | no local/remote `change/75*` existed before creation；isolated branch created from exact `origin/main` |
| GitHub mirror Issue #75 | NOT FOUND / NOT AUTHORITATIVE | connector returned 404；private Gitea remains authority |
| current installed broker readable push | FAIL AS EXPECTED | installed contract regex is exact `change/N` only；candidate bootstrap is required and explicitly constrained by spec |
| Issue labels / approved lifecycle | NOT CONFIGURED FOR #75 | live Issue currently has no labels；this contract run did not bypass label ownership |
| remote PR / final-head CI | NOT RUN | branch not pushed and PR not created during contract-only run |
| merge / exact-main install / downstream migration | NOT RUN | human merge and post-merge gates remain independent |

## Contract validation

| Check | Result | Evidence |
|---|---|---|
| complexity classification | PASS | platform governance + shared controller + authorization/external contract forces `complex` |
| Issue AC coverage | PASS | spec AC-1..AC-9 preserve all Issue criteria and make grammar/legacy/rename/bootstrap decisions measurable |
| AC-to-plan mapping | PASS | plan table maps every AC to deterministic tests or final review/readback |
| governing AGENTS isolation | PASS | current run did not edit root `AGENTS.md`；spec explicitly authorizes a future fresh implementation run |
| semantic directory self-hosting | FAIL AS EXPECTED (bootstrap baseline) | branch/docs use exact `75-readable-change-names`；current protected-main resolver exits 2 with `exactly one new summary document is required` because it only searches `docs/changes/N/`；T02 owns the fix |
| unresolved decisions | PASS | spec declares none；no implementation started in this contract-only run |

## Candidate implementation results

- AC-1 Shared parser：`PASS`。`aisoft_change_name.ChangeName` 统一校验/投影 branch、directory、worktree；valid、legacy internal parse、reserved/all-numeric/length/segment 与 mismatch matrix 通过。
- AC-2 New default and legacy compatibility：`PASS`。analyzer writer 使用 readable tuple；legacy 只能由 resolver、remote ref 或 existing PR evidence 进入维护路径，public CLI 无 legacy flag。
- AC-3 Single active name：`PASS`。directory、remote refs 与 open PR 的 legacy/readable 或 multi-slug 冲突均返回 `CHANGE_NAME_CONFLICT`。
- AC-4 Controller and worktree：`PASS`。analyzer 先校验 slug 后创建 readable worktree；provider/document/PR paths 使用 exact resolved directory；dirty/detached/branch/ancestry 原有门保持通过。
- AC-5 Broker Git boundary：`PASS`。manifest-fixed remote 的 readable first push、exact maintenance、legacy evidence、wrong/force/main/refspec/cross-project/dirty/detached negatives 通过；未增加 remote/URL/refspec/merge surface。
- AC-6 PR binding：`PASS`。new PR 拒绝 numeric head，要求 exact readable head、同 slug summary 与唯一 `Closes #N`；existing legacy PR update 只依赖 readback evidence。
- AC-7 Documentation and scaffolding：`PASS`。fresh governance commit 已更新 root/global AGENTS；本 run 更新 README、03/04/06/07/08/09、skills、templates、agent messages 和 installer tests，历史 change 文档未批量改名。
- AC-8 Verification matrix：`PASS`。325 Python tests、agent/broker installer shell tests、`bash -n`、ShellCheck、`git diff --check` 与 full smoke 均通过。full smoke 对 Issue #65 immutable evidence 临时恢复既定 `0444` mode 后通过，结束已恢复 checkout `0644`，无 tracked diff。
- AC-9 Governed delivery and install：local isolated branch与 candidate broker tests `PASS`；push/PR/CI/protection `NOT RUN`；merge/install/downstream `NOT RUN`。

## Forbidden-scope audit

- canonical checkout tracked/untracked files：`NOT MODIFIED`。
- `ci-bot`、credential/token contents、Keychain、PAT/ACL/permission/protection：`NOT ACCESSED / NOT MODIFIED`。
- remote branch/Issue/PR mutation：`NOT RUN`（下一步只执行 spec 授权的 exact candidate push 与唯一 PR create/readback）。
- VM/service、Docker、Secret、database、migration、deployment、restart、prune、production：`NOT RUN`。
- automatic merge、historical rename/delete/cleanup：`NOT RUN`。

## Post-merge gates

- unique readable branch/PR final-head readback：`NOT RUN`。
- human merge：`NOT RUN`。
- exact protected-main install + second no-op + byte readback：`NOT RUN`。
- `.previous` rollback availability：`NOT RUN`。
- downstream project migration Issues：`NOT RUN`。
