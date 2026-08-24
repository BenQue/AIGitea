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

# Verification · localwms analysis_provider → codex

## 基线与范围

- Commit SHA：见 PR 头（本文件在 PR 开出后不再改结果，只有 summary 回填 `pr_url`）
- 基线：`origin/main` = `5faffa7`
- 环境：Mac 开发机，worktree `/private/tmp/issue-164-localwms-analysis-provider`；
  Gitea CI 的 `verify` job（只跑 `bash codex/tests/smoke.sh`）
- 本记录负责证明的 acceptance criteria：AC-1、AC-4、AC-R1..AC-R4 已执行；
  **AC-2 与 AC-3 不可达**，它们需要主机侧重装并 provision，属合并后的人工授权动作。
- 未触达：`/usr/local/share/aisoft/host-access-broker.json`（安装态副本）、
  gitea-ci VM 内任何 profile 文件、任何 mutating 的 `vm.profile.*` 操作。

## 改动前基线（只有现在观测得到）

以下三条在合并并重装之后就无法重放，是「安装态确实还停在旧声明上」的直接证据：

| 观测 | 结果 |
|---|---|
| `diff /usr/local/share/aisoft/host-access-broker.json codex/config/host-access-broker.json`（改动前） | 无输出——安装态与仓库副本一致，上一次 manifest 变更的重装有人做过 |
| `host-access-broker --project localwms --operation vm.profile.plan` | `{"action": "no-op", "identity": "localwms-agent", "profile": "localwms", "status": "PASS", "target": "admin/LocalWMS"}` |
| `host-access-broker --project localwms --operation vm.profile.read-back` | `{"identity": "localwms-agent", "profile": "localwms", "project": "localwms", "result": "read-back", "status": "PASS", "target": "admin/LocalWMS"}` |

`plan` 返回 `no-op` 且 `read-back` 返回 `PASS`，合起来意味着：LocalWMS 的 profile
**已经 provision 过**，且 VM 上 `/home/coder/.config/aisoft/projects/localwms.env`
的字节与当时的 manifest 声明逐字一致——也就是它此刻确实写着 `ANALYSIS_PROVIDER=claude`。

这同时给出了 AC-2/AC-3 的判据形态：合并并重装之后，`vm.profile.plan`
**应当不再是 `no-op`**（安装态 manifest 变了，目标字节需要重写）；
`--action apply` 之后 `read-back` 应重新回到 `PASS`。
`plan` 若在重装后仍返回 `no-op`，说明重装漏了一台，而不是「没有变化」。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `jq -c '.projects[] \| select(.project_id=="localwms") \| .vm_profile' codex/config/host-access-broker.json` | PASS | `{"name":"localwms","repo_dir":"work/LocalWMS","analysis_provider":"codex","implement_provider":"none","timer_unit":null}` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` | PASS | `{"contract_version": "host-access-broker/v1", "merge_operation_count": 0, "operation_count": 30, "project_count": 10, "status": "PASS"}` |
| 同一命令跑在 `origin/main` 的 manifest 上（计数对照） | PASS | 输出逐字相同——三个计数器未因本变更改变 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` | PASS | `Ran 520 tests in 27.925s` / `OK` |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -k localwms` | PASS | `Ran 2 tests` / `OK`，含 `test_localwms_profile_is_analyzer_only_without_a_timer` 与 `test_localwms_is_declared_development` |
| `bash codex/tests/smoke.sh` | PASS | 退出码 `0`，末行 `Codex platform static smoke checks passed.` |
| `git diff --quiet origin/main -- codex/config/gitea-governance.json` | PASS | 退出码 `0`——governance manifest 完全未改 |
| `git diff --numstat origin/main -- codex/config/host-access-broker.json codex/runtime/tests/test_host_access.py` | PASS | `1 1 codex/config/host-access-broker.json`（唯一改动是那一个取值）／`10 2 codex/runtime/tests/test_host_access.py`（两处期望值 + 说明依据的注释） |
| 安装态重装（`sudo bash codex/install-host-access-broker.sh`，Mac 与 VM 两台） | **NOT RUN** | 合并后的独立授权动作，见交接项 |
| `project-profile-migration --project localwms --action apply` | **NOT RUN** | mutating 的 provision 动作，依赖上一行 |
| `project-profile-migration --project localwms --action read-back` | **NOT RUN** | 依赖上一行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 `analysis_provider == "codex"` | PASS | 上表第 1 行；并由 `test_localwms_profile_is_analyzer_only_without_a_timer` 在 CI 内钉住，将来改回去会红 |
| AC-2 VM 上 `ANALYSIS_PROVIDER=codex`、`0600 coder:coder` | **NOT RUN** | 不可达：需两台重装 + `--action apply`。文件模式一侧另有静态保证——`profiles.py:301` 只有 `ANALYSIS_PROVIDER=` 那一行受本变更影响，行数、行序与 `0600` 由未被触碰的代码路径决定 |
| AC-3 `read-back` → `PASS` / `identity: localwms-agent` | **NOT RUN** | 不可达：依赖 AC-2。改动前的 `read-back` 已 `PASS`（见基线表），说明该路径本身是通的，待验证的只是重装后是否重新收敛 |
| AC-4 `implement_provider` 仍 `none`、`timer_unit` 仍 `null` | PASS | 上表第 1 行的 `jq` 输出；由同一测试的 `assertEqual(..., "none")` 与 `assertIsNone(timer_unit)` 断言；`contract.py` 另有 `implementation == "none"` 硬断言与 timer 白名单兜底 |
| AC-R1 manifest validate 计数不变 | PASS | 上表第 2、3 行逐字对照 |
| AC-R2 全量单测 | PASS | 520 tests OK |
| AC-R3 smoke | PASS | 退出码 0 |
| AC-R4 无附带 diff | PASS | 上表第 7、8 行 |

## ⚠️ 合并后的显式交接项

**合并不等于生效。** broker 运行时读的是安装态副本
`/usr/local/share/aisoft/host-access-broker.json`，仓库里的
`codex/config/host-access-broker.json` 只是源。在重装之前，VM 上
`localwms.env` 仍然是 `ANALYSIS_PROVIDER=claude`，也就是这条链仍然跑不通。

合并后由人依次执行（**本会话不做，全部需要 sudo 与独立授权**）：

1. **两台都重装**：在各自的 AISoftPlatform `main` 检出内
   `sudo bash codex/install-host-access-broker.sh`（幂等、不绑定凭据）。
   Mac 与 gitea-ci VM 缺一不可——只在 Mac 上装过是踩坑 #18 的原样重演。
2. 确认安装态已同步：
   `diff /usr/local/share/aisoft/host-access-broker.json codex/config/host-access-broker.json`
   —— 应无输出。
3. `sudo /usr/local/libexec/aisoft/project-profile-migration --project localwms --action apply`。
4. `--action read-back` 复核 → 应返回 `status: PASS`、`identity: localwms-agent`（AC-3）。
5. 读 `/home/coder/.config/aisoft/projects/localwms.env`：`ANALYSIS_PROVIDER=codex`，
   文件仍为 `0600 coder:coder`（AC-2）。

第 1 步之后、第 3 步之前，`vm.profile.plan` 应当**不再返回 `no-op`**。
若仍是 `no-op`，不要继续——那说明重装漏了一台，而不是「没有变化」。

## 遗留风险与未完成项

1. **AC-2 / AC-3 未执行**，见上方交接项。在重装前 VM 侧仍是旧声明——这是预期，不是回归。
2. **VM 上 `~/.local/lib/aisoft-loop` 陈旧，且触发点比 Issue #164 描述的更早。**
   Issue 说 over-claim 要「Development Loop 一旦启用」才发生。实际链路是：
   `analyze-codex.sh:29` 在**每一次** analyzer 调用里都跑 `render-analysis`，
   而 `3141620`（#134，2026-08-21）同时给 `_render_analysis`（`cli.py:378`）与
   `_apply_analysis`（`cli.py:409`）加上了 `change_control=`。因此陈旧 runtime 的
   production-only `route()` 会在 **LocalWMS 第一次端到端 analyzer 运行**时就写出
   over-claim 的 `required_docs`，不必等 Loop。canary 没撞上，是因为它直接调
   `codex-analyzer.sh`（`:53` 只到 `validate-analysis`，不碰 `route()`）。
   LocalWMS 是唯一声明 `change_control: development` 的仓库，所以也是唯一一个
   陈旧 runtime 的答案与正确答案不一致的仓库。
   **不阻塞本变更**（`timer_unit: null`，无自动触发），但刷新 VM runtime 应排在
   LocalWMS 第一次端到端 analyzer 运行之前。已开独立 Issue 跟踪。
3. **analyzer 读不到 Issue 评论**（Issue #164 附带发现二）：对「正文之后由评论修订过
   范围」的 Issue 存在系统性盲区。已开独立 Issue 跟踪。
4. **`rsdesign` / `sfm` / `emaintenance` 三条 profile 仍声明 `claude`**，仍然跑不通。
   本变更有意不动（spec §6 非目标 1），已开独立 Issue 跟踪。
