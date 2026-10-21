---
issue: 396
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/396
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - platform-governance
depends_on:
  - 391
status: approved
branch: change/396-site-externalization
created: 2026-10-20
updated: 2026-10-20
---

# #396 plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理文件：`skills/aisoft-platform/SKILL.md:14`、`references/onboarding-runbook.md`、`references/private-gitea-access.md` 的站点值改指向 manifest `site`；`templates/project/ci/ci.yml` registry 占位与注释；`registry-preflight.sh` 去站点轶事。单独 commit 后停下重读（AC3） | - | pending |
| T02 | manifest `site` 段（真实与夹具）；`contract.py` 结构校验；`broker.py`、`credential_rotation.py` 改读 `site`；单测换值 PASS 与非法值拒绝（AC1、AC4） | T01 | pending |
| T03 | 泄漏守卫两组集合与 `site_files` 基线；反向证明用例；`01`/`07`/`13`/`README` public allowlist 指向 manifest；四处代码注释去站点值（AC2、AC3） | T02 | pending |
| T04 | 发布包升版；路线图 R13 状态；全量 smoke；Codex 只读交叉审查；verification；判级投影（AC5） | T03 | pending |

## Expected touch points

- T01：`skills/aisoft-platform/SKILL.md`、`skills/aisoft-platform/references/onboarding-runbook.md`、`skills/aisoft-platform/references/private-gitea-access.md`、`templates/project/ci/ci.yml`、`templates/project/ci/registry-preflight.sh`，以及钉住这些文本的测试（`codex/tests/test-project-check.sh` 等）
- T02：`codex/config/host-access-broker.json`、`codex/tests/fixtures/manifests/host-access-broker.json`、`codex/runtime/aisoft_host_access/{contract,broker,credential_rotation}.py`、`codex/runtime/tests/test_host_access*.py`、`codex/runtime/tests/test_credential_rotation.py`、`codex/runtime/tests/rotation_cli_fixture.py`、`codex/tests/test-host-access-broker.sh`
- T03：`codex/tests/check-project-leak.py`、`codex/config/project-leak-baseline.json`、`codex/runtime/tests/test_project_leak.py`、`01`、`07`、`13`、`README.md`、四个注释文件
- T04：`usage/bundle.json` 与发布记录、`docs/governance/remediation-roadmap.md`、本目录 verification

## Verification

每个 ticket 结束跑相关单测；T03、T04 跑 `bash codex/tests/smoke.sh` 全量。合并后两台重装与读回记在 verification 的 AC6。
