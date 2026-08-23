---
issue: 152
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/152
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/152-localwms-vm-profile
pr_url:
created: 2026-08-23
updated: 2026-08-23
---

# Implementation plan · 给 LocalWMS 声明 vm_profile

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | manifest 声明 + contract 允许集扩容 + 三处镜像断言同步，一次提交内 manifest 校验与 smoke 全绿 | - | done |
| T02 | 四份 change 文档，含 verification 的重装交接项与疑点结论 | T01 | done |

T01 **必须是一个原子提交**：JSON 声明与 `contract.py` 的允许集是同一条不变量的两半，
拆开提交会留下一个 manifest 加载失败的中间状态，任何在该 commit 上跑 CI 的人都会看到
broker 对全部十个项目 fail closed。这不是洁癖，是让 `git bisect` 和 revert 都保持可用。

## Expected touch points

T01：

- `codex/config/host-access-broker.json` —— `localwms.vm_profile` 由 `null` 变成
  五键对象。
- `codex/runtime/aisoft_host_access/contract.py` —— 允许集加 `"LocalWMS"`，断言文案
  `five` → `six`。
- `codex/runtime/tests/test_host_access.py` —— profile 映射表加一行；
  `path_prepend` 声明表加一行；无 `path_prepend` 的项目循环加 `localwms`；
  新增 `test_localwms_profile_is_analyzer_only_without_a_timer`，把
  `implement_provider=none` / `timer_unit=null` 这两条 Issue 硬边界钉进测试。
- `codex/tests/test-host-access-broker.sh` —— jq 仓库列表加 `"LocalWMS"`。

T02：

- `docs/changes/152-localwms-vm-profile/{summary,spec,plan,verification}-localwms-vm-profile-260823.md`

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 / AC-3 | `jq '.projects[] \| select(.project_id=="localwms") \| .vm_profile' codex/config/host-access-broker.json` |
| AC-2 | `test_localwms_profile_is_analyzer_only_without_a_timer`（新增） |
| AC-4 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` |
| AC-5 | `bash codex/tests/smoke.sh` |
| AC-6 | `git diff origin/main -- codex/config/` 人工复核 |
| AC-7 | `bash codex/tools/project-profile-migration.sh --project localwms --action plan`（在 worktree 内，走仓库副本 manifest） |
| AC-8 | verification 文档 review |

## 部署与回滚

**有部署影响，但本变更不执行部署。**

manifest 是安装态生效的：broker 读 `/usr/local/share/aisoft/host-access-broker.json`。
合并后须由人以 sudo 重装（`codex/install-host-access-broker.sh`，幂等、不绑定凭据），
broker 才会看到新声明。这一步是**独立授权的运维动作**，本变更只把它写成显式交接项，
verification 文档记录预期结果而非「已通过」。

因此本 plan 不安排「两次幂等执行 + 一次故意失败回滚」的部署验收 —— 那属于重装与后续
canary 那次运维动作的验收范围，不是本 PR 的。

回滚：单一 `git revert`。若 installed manifest 已重装过，revert 后须再重装一次。
本变更没有写入任何 VM 状态，所以没有数据需要恢复。
