---
issue: 164
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/164
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
branch: change/164-localwms-analysis-provider
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · localwms analysis_provider → codex

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 采集改动前基线：安装态 manifest 与仓库副本是否一致、`vm.profile.plan` / `read-back` 当前返回什么 | - | done |
| T02 | manifest 中 `localwms.vm_profile.analysis_provider` 改为 `codex` | T01 | done |
| T03 | `test_host_access.py` 的两处期望值随之更新，注释改写为「运行时必须在那台主机上真的存在」的依据 | T02 | done |
| T04 | 回归门：`validate` / `unittest` / `smoke.sh` / 零附带 diff | T03 | done |
| T05 | 四份语义文档，verification 记录 T01 的基线与 T04 的实测输出，AC-2/AC-3 记 `NOT RUN` 并写明交接 | T04 | done |

T01 **必须先行**且不可事后补：`vm.profile.plan` 在改动前返回 `no-op`，
这条证据一旦合并重装就永久不可重放，而它恰恰是「安装态确实处在旧声明上」的唯一直接证明。
T02 与 T03 不可拆到两个 commit——测试钉着 manifest 取值，分开提交会留下一个红的中间态。

## Expected touch points

**T02**
- `codex/config/host-access-broker.json`：`projects[]` 中 `project_id == "localwms"`
  条目的 `vm_profile.analysis_provider`，`"claude"` → `"codex"`。仅此一行。
  用带唯一性断言的脚本替换（`assert s.count(old) == 1`），不用行号定位——
  同名键在其它九个条目里也出现，按行号改是把别的项目改错的标准姿势。

**T03**
- `codex/runtime/tests/test_host_access.py`：
  - `test_localwms_profile_is_analyzer_only_without_a_timer` 的
    `assertEqual(project.vm_profile.analysis_provider, ...)`；
  - 同一函数内 `profile-spec` 期望 payload 的 `"analysis_provider"`；
  - 函数头注释追加一段：#152 按同类项目类推选了 `claude` 而非按证据，canary 证明该链
    从未跑通（`claude-analyzer.sh:13` 第一行即失败），此处声明的 provider 必须是那台
    主机上真的存在的运行时。
- **不改**同文件的 `test_undeclared_profile_bytes_are_byte_identical_to_pre_112_shape`：
  它钉的是 `newemaint` 的 `ANALYSIS_PROVIDER=claude`，本变更不动 `newemaint`。

**T05**
- `docs/changes/164-localwms-analysis-provider/` 下四份
  `<role>-localwms-analysis-provider-260824.md`，summary 的 `documents` 显式映射四个角色。

零改动确认：`contract.py`（取值集合已含 `codex`）、`profiles.py`、`cli.py`、
`provider-poll.sh`、`gitea-governance.json`、`install-*.sh` 一律不动。

## 数据库迁移

无。

## 部署与回滚

**本变更不部署。** 主机侧生效是合并后的人工交接项（spec §7）：两台重装 broker →
`project-profile-migration --action apply` → `--action read-back`。

回滚 = `git revert` 本 PR。若彼时已经重装过安装态 manifest，revert 之后还须再执行一次
`sudo bash codex/install-host-access-broker.sh` 并重跑 `--action apply`，broker 与 VM
才会回到 `claude`。无 schema 变更、无数据迁移、无外部持久状态。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `jq '.projects[] \| select(.project_id=="localwms") \| .vm_profile.analysis_provider' codex/config/host-access-broker.json` → `"codex"`；并由 T03 的测试断言在 CI 内钉住 |
| AC-2 | **NOT RUN**（合并后交接）。可达条件：两台重装 + `--action apply`。届时读 `/home/coder/.config/aisoft/projects/localwms.env` 与其文件模式 |
| AC-3 | **NOT RUN**（合并后交接）。`project-profile-migration --project localwms --action read-back` → `status: PASS`、`identity: localwms-agent` |
| AC-4 | 同一测试函数的 `assertEqual(implement_provider, "none")` 与 `assertIsNone(timer_unit)`；另有 `contract.py` 的 `implementation == "none"` 硬断言与 timer 白名单双重兜底 |
| AC-R1 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` |
| AC-R2 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` |
| AC-R3 | `bash codex/tests/smoke.sh` |
| AC-R4 | `git diff --quiet origin/main -- codex/config/gitea-governance.json`；`git diff origin/main -- codex/config/host-access-broker.json` 只有 1 行 |
