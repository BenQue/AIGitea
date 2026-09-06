---
issue: 178
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/178
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: approved
branch: change/178-emaintenance-analysis-provider
created: 2026-09-06
updated: 2026-09-06
---

# Implementation plan · emaintenance analysis_provider → none

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 采集改动前基线：`vm.profile.plan` / `read-back` / 安装态 diff | - | done |
| T02 | manifest 取值改为 `none`，并加一条写明依据的钉住测试 + 反向证明 | T01 | done |
| T03 | 修复被 manifest 取值牵动的既有夹具，全量单测与 smoke 转绿 | T02 | done |
| T04 | 四份语义文档与判级投影 | T03 | done |

T01 必须早于 T02：`plan` 返回 `no-op` 这条证据一旦改值并重装就无法重放，
它是「VM 上此刻确实写着 `claude`」的唯一直接证据。

## Expected touch points

- T01：无文件改动，只产出 verification 的基线表。
- T02：`codex/config/host-access-broker.json`（1 行）；
  `codex/runtime/tests/test_host_access.py` 新增
  `test_emaintenance_profile_names_no_analysis_provider`。
- T03：`codex/runtime/tests/test_host_access.py` 的
  `test_undeclared_profile_bytes_are_byte_identical_to_pre_112_shape`
  一处字面量与一段说明注释。
- T04：`docs/changes/178-emaintenance-analysis-provider/` 四份文档。

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `jq -c '.projects[] \| select(.project_id=="newemaint") \| .vm_profile' codex/config/host-access-broker.json`；`git diff --numstat origin/main` |
| AC-2 | 同上 `jq` 输出；`git diff origin/main -- codex/runtime/aisoft_host_access/contract.py` 为空 |
| AC-3 | 两台重装 + `project-profile-migration --action apply` 后读 VM 上的 `emaintenance.env`（合并后交接项） |
| AC-4 | `host-access-broker --project newemaint --operation vm.profile.read-back`（合并后交接项） |
| AC-R1 | `python3 -m aisoft_host_access.cli --access-manifest <候选> --governance-manifest <候选> validate`，与 `origin/main` 同命令对照 |
| AC-R2 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` |
| AC-R3 | `bash codex/tests/smoke.sh` |
| AC-R4 | `git diff --numstat origin/main`；`git diff --quiet origin/main -- codex/config/gitea-governance.json` |
| AC-R5 | 临时把取值改回 `claude`，跑 `-k emaintenance` 确认变红，再改回 |

AC-3 与 AC-4 不可由本会话执行：它们需要主机侧 sudo 重装并 provision。
按 `03` §3 这正是本变更声明 `verification` 的原因。

## 部署与回滚

**无部署。** 本变更不部署制品、不迁移数据。它改的是 governance manifest 的一个
声明字段，生效路径是「合并 → 两台重装 → `--action apply`」，全部由人在独立授权
下执行，写在 verification 的交接项里。

回滚：`git revert` 本 PR；若彼时已重装，再重装一次并重跑 `--action apply`。
