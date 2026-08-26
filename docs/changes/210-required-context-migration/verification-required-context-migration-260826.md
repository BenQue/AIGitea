---
issue: 210
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/210
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
depends_on: []
status: pending
branch: change/210-required-context-migration
created: 2026-08-26
updated: 2026-08-26
---

# Evidence-approved required-context migration 验证记录

## 基线与范围

- Commit SHA: 待实现完成后填写。
- 基线：`origin/main` = `6e01c877544eb64016006feda76ea699e33a96b6`。
- 环境：macOS 本地 exact worktree；Gitea 只读状态通过受控 broker 读取。
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-9。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| fresh `git.fetch.main` | PASS | broker 返回 exact project/remote PASS；`origin/main` 与 HEAD 均为 `6e01c877544e…` |
| 同类 open Issue 去重 | PASS（受 broker exact-read 能力边界限制） | #208 是不同范围的 auto-merge；#210 创建前不存在；repository docs 无同 slug/change |
| 改动前 live readiness | PASS/GAP | SOURCE、INSTALLED_CODEX、INSTALLED_CLAUDE、LIVE_REPO 均 PASS；LIVE_PROTECTION 为 status check disabled、contexts empty |
| 改动前 governance plan/apply | FAIL（预期基线） | action=`update-main-protection` 同时 blocker=`status-check-context-drift`；apply 在 snapshot/PATCH 前拒绝，live 未 mutation |
| 定向 tests | NOT RUN | 待实现后填写 |
| `python3 -m compileall codex/runtime/aisoft_gitea_governance` | NOT RUN | 待实现后填写 |
| `bash codex/tests/smoke.sh` | NOT RUN | 待实现后填写 |
| shell static checks | NOT RUN | 仅当修改 shell 时执行 |
| live branch protection apply | NOT RUN | 本 Issue 明确禁止 |
| runtime/skills 安装 | NOT RUN | 本 Issue 无安装范围 |
| 部署 | NOT RUN | 本 Issue 无部署范围 |
| final PR create/update | NOT RUN | 等待用户确认 |
| merge | NOT RUN | 永远由用户人工执行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | strict manifest/CLI tests |
| AC-2 | 待填写 | evidence parser tests |
| AC-3 | 待填写 | planner drift matrix tests |
| AC-4 | 待填写 | default fail-closed 与显式 migration plan tests |
| AC-5 | 待填写 | snapshot ordering/failure tests |
| AC-6 | 待填写 | PATCH/read-back/full protection comparison tests |
| AC-7 | 待填写 | rollback tests |
| AC-8 | 待填写 | 定向、静态与 smoke tests |
| AC-9 | 待填写 | diff、NOT RUN 与 PR 前人工闸门核对 |

## 遗留风险与未完成项

- live apply、runtime/skills 安装、部署、final PR 与 merge 均未执行。
- 本地测试只能证明确定性约束；未来 live migration 仍需独立授权、真实 snapshot、apply 后完整
  read-back 与 rollback 演练证据，不能从本 Change 的 source tests 推定 live 已收敛。
