---
issue: 275
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/275
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: contract-drafting
branch: change/275-onboard-sfmdigitalboard
created: 2026-09-07
updated: 2026-09-07
---

# Implementation plan 重新接入 SFMDigitalBoard

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 两份 manifest 加条目 + 封印重算 + 花名册断言对齐 + 文档活语句，`validate` 与 `smoke.sh` 全绿 | - | done |

单一 vertical slice：manifest、封印与断言在契约层互相强制（集合相等 + 摘要封印），
拆开任何一步都会让中间 commit 无法通过 `validate`，不存在可独立验收的更小切片。

## Expected touch points

- `codex/config/host-access-broker.json` — `projects[]` +1
- `codex/config/gitea-governance.json` — `repositories[]` +1，封印重 pin
- `codex/tests/test-host-access-broker.sh` — `project_count`、`git_remote_name` 断言
- `codex/runtime/tests/test_host_access.py` — 项目计数、`gitea_remote_projects`
- `codex/runtime/tests/test_gitea_governance.py` — 仓库计数、private 集合
- `03-Issue-Spec-Plan与单闸门开发流程.md`、`README.md` — 活语句

## 验证顺序

1. `validate` 读 `project_count: 6`（不重装也能验收）
2. `bash codex/tests/test-host-access-broker.sh` 单跑
3. `bash codex/tests/smoke.sh` 全套，与 `origin/main` 基线对比退出码
4. `git diff --stat origin/main -- <两个 contract.py> <smoke.sh>` 须为空
5. AC-7 回滚演练
6. `check-change-documents --repo <checkout>`

## 人工交接（PR 合并后）

H-1 Mac 重装（先确认 checkout 无 `behind`）→ H-2 解除 `sfm-board-agent`
`prohibit_login` 并重发 token → H-3 token 落盘 mode 600 → H-4 `mac.git.bind`
后 `host.onboarding.check` 回读。顺序与 #252 的退出顺序相反。
