---
issue: 178
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/178
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
branch: change/178-emaintenance-analysis-provider
created: 2026-09-06
updated: 2026-09-06
---

# Verification · emaintenance analysis_provider → none

## 基线与范围

- Commit SHA：见 PR 头（本文件在 PR 开出后不再改结果，只有 summary 回填 `pr_url`）
- 基线：`origin/main` = `3df14be`
- 环境：Mac 开发机，worktree `/private/tmp/issue-178-emaintenance-analysis-provider`；
  Gitea CI 的 `verify` job（只跑 `bash codex/tests/smoke.sh`）
- 本记录负责证明的 acceptance criteria：AC-1、AC-2、AC-R1..AC-R5 已执行；
  **AC-3 与 AC-4 不可达**，它们需要主机侧重装并 provision，属合并后的人工授权动作。
- 未触达：`/usr/local/share/aisoft/host-access-broker.json`（安装态副本）、
  gitea-ci VM 内任何 profile 文件、任何 mutating 的 `vm.profile.*` 操作、
  `aisoft-agent@emaintenance.timer` 的启停。

## 改动前基线（只有现在观测得到）

以下三条在合并并重装之后就无法重放，是「安装态确实还停在旧声明上」的直接证据：

| 观测 | 结果 |
|---|---|
| `diff /usr/local/share/aisoft/host-access-broker.json codex/config/host-access-broker.json`（改动前） | 无输出，退出码 0——安装态与仓库副本一致，#252 那次 manifest 变更的重装有人做过 |
| `host-access-broker --project newemaint --operation vm.profile.plan` | `{"action": "no-op", "identity": "newemaint-agent", "profile": "emaintenance", "project": "newemaint", "status": "PASS", "target": "admin/NewEMaint"}` |
| `host-access-broker --project newemaint --operation vm.profile.read-back` | `{"identity": "newemaint-agent", "profile": "emaintenance", "project": "newemaint", "result": "read-back", "status": "PASS", "target": "admin/NewEMaint"}` |

`plan` 返回 `no-op` 且 `read-back` 返回 `PASS`，合起来意味着 VM 上
`/home/coder/.config/aisoft/projects/emaintenance.env` 的字节与当时的 manifest
声明逐字一致——也就是它此刻确实写着 `ANALYSIS_PROVIDER=claude`。

这同时给出 AC-3/AC-4 的判据形态：合并并重装之后，`vm.profile.plan`
**应当不再是 `no-op`**；`--action apply` 之后 `read-back` 应重新回到 `PASS`。
`plan` 若在重装后仍返回 `no-op`，说明重装漏了一台（踩坑 20），
而不是「没有变化」。

### 裁定所依据的两条只读观测

方向裁定（`none` 而非 `codex`）另有两条本次现场取得的证据：

| 观测 | 结果 |
|---|---|
| `gitea.issue.list --project newemaint --state open` 的标签投影 | 3 条 open Issue（#74、#43、#18），**没有一条带 `needs-analysis`**——今天翻成可用 provider 的即时作用域是空队列，第一次真判级会落在下一条经 broker 新建的 Issue 上 |
| `grep -n timer codex/runtime/aisoft_host_access/profiles.py` | 无匹配。`_profile_bytes`（`profiles.py:289`）只渲染九个键，`timer_unit` 不在其中；全仓对 `aisoft-agent@*.timer` 无任何 `systemctl` 调用（`broker.py:3949` 那处是对 act_runner 的只读 `show`）。故 `timer_unit` 是记录不是开关 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `jq -c '.projects[] \| select(.project_id=="newemaint") \| .vm_profile' codex/config/host-access-broker.json` | PASS | `{"name":"emaintenance","repo_dir":"work/NewEMaint","analysis_provider":"none","implement_provider":"none","timer_unit":"aisoft-agent@emaintenance.timer"}` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` | PASS | `{"contract_version": "host-access-broker/v1", "merge_operation_count": 1, "operation_count": 36, "project_count": 5, "status": "PASS"}` |
| 同一命令跑在 `origin/main` 的两份 manifest 上（计数对照） | PASS | 输出逐字相同——三个计数器未因本变更改变 |
| `profile-spec --profile-name emaintenance`（改动后） | PASS | `analysis_provider` 为 `none`，其余十个字段与改动前逐字相同 |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` | PASS | `Ran 699 tests in 50.141s` / `OK` |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -k emaintenance` | PASS | `Ran 1 test` / `OK`（`test_emaintenance_profile_names_no_analysis_provider`） |
| 反向证明：把 manifest 取值临时改回 `claude` 后跑同一条测试 | PASS（如期变红） | `FAILED (failures=1)`，diff 为 `- claude` / `+ none`；随后已改回 `none` 并确认工作树只剩两个预期文件 |
| `bash codex/tests/smoke.sh` | PASS | 退出码 `0`，含 `Ran 699 tests` / `OK`，末行 `Codex platform static smoke checks passed.` |
| `git diff --quiet origin/main -- codex/config/gitea-governance.json` | PASS | 退出码 `0`——governance manifest 完全未改 |
| `git diff --quiet origin/main -- codex/runtime/aisoft_host_access/contract.py` | PASS | 退出码 `0`——timer 白名单与取值集合完全未改 |
| `git diff --numstat origin/main` | PASS | `1 1 codex/config/host-access-broker.json`（唯一改动是那一个取值）／`65 1 codex/runtime/tests/test_host_access.py`（新增钉住测试 59 行，既有夹具 1 行取值 + 5 行说明注释） |
| 安装态重装（`sudo bash codex/install-host-access-broker.sh`，Mac 与 VM 两台） | **NOT RUN** | 合并后的独立授权动作，见交接项 |
| `project-profile-migration --project newemaint --action apply` | **NOT RUN** | mutating 的 provision 动作，依赖上一行 |
| `project-profile-migration --project newemaint --action read-back` | **NOT RUN** | 依赖上一行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 `analysis_provider == "none"`，且是该文件唯一改动行 | PASS | 上表第 1、11 行；并由 `test_emaintenance_profile_names_no_analysis_provider` 在 CI 内钉住 |
| AC-2 `implement_provider` / `timer_unit` / `name` / `repo_dir` 不变，timer 白名单不变 | PASS | 上表第 1 行的 `jq` 输出；第 10 行 `contract.py` 零 diff；同一测试的 `assertEqual(..., "none")` 与 `assertEqual(timer_unit, "aisoft-agent@emaintenance.timer")` |
| AC-3 VM 上 `ANALYSIS_PROVIDER=none`、`0600 coder:coder` | **NOT RUN** | 不可达：需两台重装 + `--action apply`。文件模式一侧另有静态保证——`profiles.py:289` 只有 `ANALYSIS_PROVIDER=` 那一行受本变更影响，行数、行序与 `0600` 由未被触碰的代码路径决定 |
| AC-4 `read-back` → `PASS` / `identity: newemaint-agent` | **NOT RUN** | 不可达：依赖 AC-3。改动前的 `read-back` 已 `PASS`（见基线表），说明该路径本身是通的，待验证的只是重装后是否重新收敛 |
| AC-R1 manifest validate 计数不变 | PASS | 上表第 2、3 行逐字对照 |
| AC-R2 全量单测 | PASS | 699 tests OK |
| AC-R3 smoke | PASS | 退出码 0 |
| AC-R4 无附带 diff | PASS | 上表第 9、10、11 行 |
| AC-R5 取值被写明依据的测试钉住，且反向证明变红 | PASS | 上表第 6、7 行 |

## ⚠️ 合并后的显式交接项

**合并不等于生效。** broker 运行时读的是安装态副本
`/usr/local/share/aisoft/host-access-broker.json`，仓库里的
`codex/config/host-access-broker.json` 只是源。在重装之前，VM 上
`emaintenance.env` 仍然是 `ANALYSIS_PROVIDER=claude`，timer 每 15 分钟仍会走到
`analyze-claude.sh` 并 fail-closed 空转。

合并后由人依次执行（**本会话不做，全部需要 sudo 与独立授权**）：

1. **两台都重装**：在各自的 AISoftPlatform `main` 检出内
   `sudo bash codex/install-host-access-broker.sh`（幂等、不绑定凭据）。
   Mac 与 gitea-ci VM 缺一不可——只在 Mac 上装过是踩坑 18 的原样重演。
   装之前先 `git -C <checkout> status -sb` 确认没有 `behind`（踩坑 20 变体）。
2. 确认安装态已同步：
   `diff /usr/local/share/aisoft/host-access-broker.json codex/config/host-access-broker.json`
   —— 应无输出。
3. `sudo /usr/local/libexec/aisoft/project-profile-migration --project newemaint --action apply`。
4. `--action read-back` 复核 → 应返回 `status: PASS`、`identity: newemaint-agent`（AC-4）。
5. 读 `/home/coder/.config/aisoft/projects/emaintenance.env`：`ANALYSIS_PROVIDER=none`，
   文件仍为 `0600 coder:coder`（AC-3）。

第 1 步之后、第 3 步之前，`vm.profile.plan` 应当**不再返回 `no-op`**。
若仍是 `no-op`，不要继续——那说明重装漏了一台，而不是「没有变化」。

**不需要**停用 `aisoft-agent@emaintenance.timer`。`none` 之下
`provider-poll.sh:32` 与 `:46` 两个分支都被跳过，timer 每跳取锁、做 profile
校验、干净退出 0。本变更有意不引入任何主机侧顺序依赖。

## 遗留风险与未完成项

1. **AC-3 / AC-4 未执行**，见上方交接项。重装前 VM 侧仍是旧声明——这是预期，
   不是回归。
2. **「NewEMaint 是否启用自动判级」仍是开放决策，本变更明确把它留空。**
   要启用需要三件事同时成立：该仓库自己的只读 canary 产出物（参照 LocalWMS
   #66 / #164 的做法，必须在 VM 上以 `coder` 身份执行——本机 codex-cli
   0.147.0 跑不了 codex-analyzer，broker 的 36 个 typed 操作里也没有任意 VM
   shell）；把取值改为 `codex`；以及有人明确认账「下一条 `needs-analysis`
   Issue 会被真的判级、写标签、写 summary 并推 change 分支」。
   已按用户本轮要求作为遗留项记录并回报，不自行立案。
3. **`analyze-*.sh` 的写路径不经 broker。** `analyze-codex.sh:38` 与
   `analyze-claude.sh:38` 都直接 `git push -u origin "$BRANCH"`，
   `apply-analysis` 也自行写标签与评论。也就是说 provider 一旦启用，该仓上就
   存在一个绕开 broker typed 操作的自动 writer。本变更让这条路径在 NewEMaint
   上保持关闭，但没有改变这个结构事实，它对 `localwms`（已声明 `codex`）同样
   成立。作为衍生发现记录并回报，未立案。
4. **`contract.py:520` 的 timer 白名单只剩一个条目。** 本变更有意不动它——
   条目对应一个真实存在且正在运行的 unit，收紧它需要先真的停用 timer，
   顺序见踩坑 24。将来若按方向 A 或 B 处置，再一并处理。
