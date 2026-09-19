---
issue: 312
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/312
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
depends_on: []
status: pending
branch: change/312-governance-context-sync
created: 2026-09-19
updated: 2026-09-19
---

# Verification：#312

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `95c0f1912b4e224e6f1b37824312cdc2abb0574b`
- 环境：Mac（`/private/tmp/issue-312-governance-context-sync`），Gitea `gitea-ci.orb.local:3000`
- 本记录负责证明的 acceptance criteria: AC-1、AC-2、AC-4，以及 AC-3 的读回

## 改动前基线（只在改动前观测得到）

| 观测 | 结果 | 证据 |
|---|---|---|
| `host.access.audit --project newemaint` | BLOCKED | `{"code": "PROTECTION_MISMATCH", "message": "protected main does not match the governance boundary", "status": "BLOCKED_EXTERNAL"}` |
| `gitea.protection.read --project newemaint` | 两条 context | `"status_check_contexts": ["CI / verify (pull_request)", "CI / mobile-verify (pull_request)"]`；`enable_status_check: true`，`merge_whitelist_usernames: ["admin"]`，`updated_at: 2026-09-19T09:35:22+08:00` |
| manifest NewEMaint `status_check_contexts` | 一条 context | `codex/config/gitea-governance.json` 第 155–156 行仅 `CI / verify (pull_request)` |
| 只加 context 不改 `contract.py` | 合同拒绝加载 | scratch 副本 + `load_contract`：`ContractError routine_live_pilot requires one exact status context: NewEMaint` |
| 四项目 audit | 见下表 | `newemaint` BLOCKED；`localwms`、`sfm-digital-board`、`aisoft-platform` 正常返回 |

### 四项目 audit 状态（改动前，2026-09-19）

| 项目 | 改动前 | 改动后 |
|---|---|---|
| `newemaint` | BLOCKED_EXTERNAL / PROTECTION_MISMATCH | NOT RUN |
| `localwms` | PASS | NOT RUN |
| `sfm-digital-board` | PASS | NOT RUN |
| `aisoft-platform` | PASS | NOT RUN |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待填写 |
| AC-2 | NOT RUN | 待填写 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 待填写。
