---
issue: 121
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/121
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/121-matt-repository-adapter
pr_url:
created: 2026-08-16
updated: 2026-08-16
---

# Implementation plan：AISoftPlatform Matt repository adapter

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | byte-identical `docs/agents` 三配置与 `CLAUDE.md` 唯一 Agent skills 路由（AC-1、AC-2、AC-5） | - | completed |
| T02 | Analyzer-only AISoftPlatform profile、approved set 约束与 `profile-spec` 测试（AC-3、AC-4、AC-5） | T01 | completed |
| T03 | mapped verification、全量验证、唯一 PR 与人工合并交接（AC-6、AC-7） | T01、T02 | in_progress |

## Expected touch points

- **T01**：`CLAUDE.md`、`docs/agents/{issue-tracker,triage-labels,domain}.md`、
  `codex/runtime/tests/test_host_access.py`、`codex/tests/smoke.sh`（把 pre-Matt 的 5 行上限替换为精确
  adapter 结构与 byte-parity gate）。
- **T02**：`codex/config/host-access-broker.json`、
  `codex/runtime/aisoft_host_access/contract.py`、`codex/runtime/tests/test_host_access.py`。
- **T03**：`docs/changes/121-matt-repository-adapter/` 四份 mapped 文档；远端只允许 branch push、唯一 PR
  与状态 read-back。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | canonical template parity：`cmp -s templates/docs/agents/<name> docs/agents/<name>`；focused unittest |
| AC-2 | CLAUDE block 唯一且完整：`rg -n '^## Agent skills$' CLAUDE.md`；focused unittest |
| AC-3 | profile 字段精确：`jq` 脱敏字段投影；focused unittest |
| AC-4 | loader/profile-spec：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access` |
| AC-5 | 禁止项零修改：`git diff --name-only origin/main`（提交前覆盖 index + worktree）与人工 allowlist review；Secret/static scan |
| AC-6 | full validation：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'`; `bash codex/tests/smoke.sh`; `git diff --check origin/main` |
| AC-7 | unique delivery：broker read-back branch/PR/head/body/status；不调用 merge/deploy |

## 部署与回滚

本 PR 不部署、不安装、不 apply profile。合并后只有在独立授权下，才能把合并后的 exact main bytes 安装到
Mac 与本地 `gitea-ci`，再执行 typed `vm.profile.plan → apply → read-back` 和一次手工 Analyzer canary；
timer/service 保持 disabled/inactive，implementation 保持 `none`。

source 回滚为单 PR revert。若 live apply 尚未执行，无 live 回滚；若已执行，使用 typed
`vm.profile.rollback` 固定 backup 并 read-back，禁止手改 protected profile/credential。
