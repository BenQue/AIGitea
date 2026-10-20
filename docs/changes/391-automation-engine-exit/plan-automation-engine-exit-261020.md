---
issue: 391
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/391
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
  - agent-governance
  - platform-governance
depends_on:
  - 389
status: approved
branch: change/391-automation-engine-exit
created: 2026-10-20
updated: 2026-10-20
---

# #391 plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理文件：`AGENTS.md` 四处与 `codex/global-AGENTS.md` 改写，单独 commit 后停下重读（AC7） | - | pending |
| T02 | Loop 代码退出：`aisoft_loop` 模块与 CLI、`codex/agent` Loop 脚本、systemd、`install-vm`、`templates/agent`、相关测试、smoke、漂移检查与 source guard（AC2、AC5） | T01 | pending |
| T03 | broker 与 governance：五个操作退役、profile 工具、routine 策略与 pilot、audit routine 段、两份真实与夹具 manifest（AC3、AC4） | T02 | pending |
| T04 | 文档、技能、模板与迁出说明；路线图状态；发布包 1.3.0（AC1、AC6、AC8） | T03 | pending |
| T05 | 全量验证、Codex 只读交叉审查、判级投影；合并后清理命令清单（AC8、AC9、AC10） | T04 | pending |

## Expected touch points

- T01：`AGENTS.md`、`codex/global-AGENTS.md`
- T02：`codex/runtime/aisoft_loop/`、`codex/runtime/tests/`、`codex/agent/`、`codex/systemd/`、`codex/install-vm.sh`、`templates/agent/`、`codex/tests/smoke.sh`、`codex/tests/test-agent-runtime.sh`、`codex/tests/test-installer-source-guard.sh`、`codex/tools/check-installed-drift.py`、`codex/tests/fixtures/installed-drift/`
- T03：`codex/config/host-access-broker.json`、`codex/config/gitea-governance.json`、`codex/tests/fixtures/manifests/`、`codex/runtime/aisoft_host_access/`、`codex/runtime/aisoft_gitea_governance/`、`codex/tools/project-profile-migration.sh`、`codex/install-host-access-broker.sh`、`codex/tests/test-host-access-broker.sh`、`codex/tests/test-install-host-access-broker.sh`、`codex/tests/check-project-leak.py`、`codex/config/project-leak-baseline.json`
- T04：`archive/`、README、`03`、`04`、`06`、`08`、`GLOSSARY.md`、`skills/`、`templates/`、`docs/agents/`、`usage/`、`docs/governance/remediation-roadmap.md`
- T05：`docs/changes/391-automation-engine-exit/verification-automation-engine-exit-261020.md`

## 数据库迁移

无。manifest schema 变化见 spec「接口、数据与兼容性影响」。

## 验证

每张 ticket 结束跑相关单测与 `bash -n`/ShellCheck；T04 后全量 `bash codex/tests/smoke.sh`；T05 跑两份 manifest validate、源码 runtime 的七项目 audit、`check-installed-drift --source-only`、`usage-bundle.sh --verify`、AC1 的 `git grep`，再请 Codex 只读审查。
