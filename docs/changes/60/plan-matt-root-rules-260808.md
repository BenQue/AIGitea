---
issue: 60
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/60
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on:
  - 57
status: approved
branch: change/60
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

# Matt root instruction plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 根级 change 文档与仓库初始化合同 | - | completed |
| T02 | VM Codex 的 Matt 主流程与兼容 adapter 路由 | T01 | completed |
| T03 | 静态合同测试、完整验证与最终 PR | T01, T02 | in-progress |

## Tasks

### T01 — Root repository contract

- 更新 `AGENTS.md` 的 change 文档规则，改为语义角色、显式 `documents` mapping 和简短日期命名。
- 保留 Issue #57 前 legacy basename 只读兼容，不批量重命名历史文件。
- 增加仓库初始化路由：先执行平台 onboarding，再通过 `$aisoft-matt-workflow` 调用
  `$setup-matt-pocock-skills` 和三份 `templates/docs/agents/` 配置。
- 保持 complex 授权、Secret、验证、受保护 `main`、人工 merge 和部署边界。

### T02 — Global Codex routing

- 更新 `codex/global-AGENTS.md` 的 authoritative documents 与 non-negotiable rules，使其读取语义 resolver。
- 把 skill routing 改为 Matt 主路径：`triage → to-spec → to-tickets → implement`。
- 将现有 `gitea-*` 定义为平台兼容 adapter；保留 `gitea-platform-ops` 的运维职责。
- 明确 Agent commit、Controller push/PR/CI、human merge、独立 deployment authorization 和
  `IMPLEMENT_PROVIDER=none` 默认值。

### T03 — Verification and delivery

- 在 `codex/tests/smoke.sh` 增加或调整精确静态断言，覆盖 AC-1 至 AC-6。
- 运行 focused tests、完整 Python suite、smoke、相关 `bash -n`、ShellCheck（若可用）、diff 与 Secret
  checks；按实际结果记录 `PASS`、`FAIL`、`SKIP` 或 `NOT RUN`。
- Agent 在 `change/60` 创建包含 `#60` 与 `Txx` 的原子 commits；Controller 验证后 push，并创建唯一
  `Closes #60` PR。停止在人工 merge gate。

## Expected touch points

- T01：`AGENTS.md`
- T02：`codex/global-AGENTS.md`
- T03：`codex/tests/smoke.sh`、`docs/changes/60/`

以上位置是范围提示；不得据此扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | smoke 检查新命名与 legacy read-only 文字；人工审阅 `AGENTS.md` |
| AC-2 | smoke 检查 `$aisoft-matt-workflow`、`$setup-matt-pocock-skills` 与三份模板路径 |
| AC-3 | smoke 检查四步 Matt 路由及 small 分支平台 gate |
| AC-4 | smoke 检查 Matt 为主、`gitea-*` 为 compatibility adapters |
| AC-5 | smoke 检查 Agent/Controller/human 分权、部署授权与 `IMPLEMENT_PROVIDER=none` |
| AC-6 | 静态禁止项检查与人工审阅 |
| AC-7 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'`; `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`; `bash -n`; ShellCheck; `git diff --check`; Secret scan |
| AC-8 | Gitea PR body/数量审阅；确认没有 merge 或 deploy 记录 |

## 部署与回滚

无应用部署。回滚为 revert 最终 PR；不删除 Issue #57 已合并的 Matt snapshot、adapter 或 legacy reader。
最终 PR 只由人工合并。
