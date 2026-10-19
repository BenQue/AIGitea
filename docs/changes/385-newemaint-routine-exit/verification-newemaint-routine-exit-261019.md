---
issue: 385
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/385
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - platform-governance
depends_on: []
status: pending
branch: change/385-newemaint-routine-exit
created: 2026-10-19
updated: 2026-10-19
---

# #385 验证记录

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `f49f15a`
- 环境: macOS 本机源码 runtime（`codex/tools/host-access-broker.sh` 在源码树内读仓库 manifest）；gitea-ci 本地 Gitea
- 本记录负责证明的 acceptance criteria: AC1–AC6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 `host.access.audit --project newemaint`（仓库 manifest） | BLOCKED_EXTERNAL | `{"code": "HTTP_403", "status": "BLOCKED_EXTERNAL"}`，退出码 20，2026-10-19 |
| 改动前 `gitea.protection.read --project newemaint` | PASS | `merge_whitelist_usernames: ["admin"]`，`updated_at` 2026-09-19 |
| 候选 manifest 下同一条 audit | PASS | `routine_merge.enabled=false`、`identity=null`、`merge_allowlist_state=converged` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | 待填写 | 待填写 |
| AC2 | 待填写 | 待填写 |
| AC3 | 待填写 | 待填写 |
| AC4 | 待填写 | 待填写 |
| AC5 | NOT RUN | 待填写 |
| AC6 | NOT RUN | 合并后执行 |

## 遗留风险与未完成项

- AC6 需负责人在合并后执行两台重装；会话内 sudo 不可用。
- 删除 `newemaint-routine-merger` 账号与凭据文件由负责人在 AC6 读回 PASS 之后做，之后回告 NewEMaint #294。
