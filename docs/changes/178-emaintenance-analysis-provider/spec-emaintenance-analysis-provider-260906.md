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

# Spec · emaintenance analysis_provider → none

## 1. 目标与原因

让 `emaintenance` 的 `vm_profile.analysis_provider` 停止声明一个在 `gitea-ci`
VM 上跑不通的运行时，并且**不**借这次订正启用任何 provider。

今天的状态是一条假声明加一次每 15 分钟的空转：manifest 说 `claude`，而
`claude-analyzer.sh:13` 的 `command -v claude || exit 2` 在第一行硬失败
（二进制在 `~/.npm-global/bin`，不在 `coder` 的 PATH 上，且那个文件是指向
`claude.exe` 的软链）。`aisoft-agent@emaintenance.timer` 是三条 vm_profile
里唯一 active 的，所以只有这一条 profile 的假声明是承重的。

取值定为 `none` 而不是 `codex`。理由在 summary「三个方向与裁定」，要点是：
命名一个可用 provider 等于断言一条可用链路，而按平台合同这是**每项目独立的
验收门**，需要该仓库自己的只读 canary 产出物；NewEMaint 还没有这份证据。
`localwms` 是先有 LocalWMS #66 的 canary、#164 才改的值。

## 2. Acceptance criteria

- [ ] **AC-1** `codex/config/host-access-broker.json` 中 `newemaint` 的
  `vm_profile.analysis_provider` 等于 `none`，且这是该文件唯一的改动行。
- [ ] **AC-2** 同一 profile 的 `implement_provider` 仍为 `none`，
  `timer_unit` 仍为 `aisoft-agent@emaintenance.timer`，`repo_dir` 与 `name` 不变；
  `contract.py` 的 timer 白名单不变。
- [ ] **AC-3** 两台重装 + `--action apply` 后，VM 上
  `/home/coder/.config/aisoft/projects/emaintenance.env` 的
  `ANALYSIS_PROVIDER=none`，文件仍为 `0600 coder:coder`。
- [ ] **AC-4** `vm.profile.read-back` 返回 `status: PASS` 与
  `identity: newemaint-agent`、`profile: emaintenance`。
- [ ] **AC-R1** 候选 manifest 的 `validate` 三个计数器与 `origin/main` 逐字相同
  （`operation_count` 36、`project_count` 5、`merge_operation_count` 1）。
- [ ] **AC-R2** `codex/runtime/tests` 全量单测通过。
- [ ] **AC-R3** `bash codex/tests/smoke.sh` 退出码 0。
- [ ] **AC-R4** 无附带 diff：`gitea-governance.json` 与其余四个项目条目零改动。
- [ ] **AC-R5** 取值被一条写明依据的测试钉住，且该测试对「改回 `claude`」
  确实变红（反向证明）。

## 3. 接口、数据与兼容性影响

无外部接口、无 schema、无数据迁移。`analysis_provider` 的取值集合在
`contract.py:514` 已是封闭的 `{claude, codex, none}`，`none` 本来就合法，
校验、CLI、`ProfileMigrator` 一律不动。

行为面唯一的变化在 `provider-poll.sh:32`：`ANALYSIS_PROVIDER=none` 让整个
analysis 分支被跳过。配合已有的 `IMPLEMENT_PROVIDER=none`，timer 每跳会取锁、
做 profile 校验、然后干净退出 0，不再走到 analyzer 的硬失败。

profile 文件的字节形态不变：`profiles.py:289` 渲染九个键，本变更只影响
`ANALYSIS_PROVIDER=` 那一行的值，行数、行序与 `0600` 由未被触碰的代码路径决定。

## 4. 风险与回滚约束

- **合并不等于生效**：broker 运行时读安装态副本，重装前 VM 侧仍是旧声明。
- **重装漏一台**：判别方法是重装后 `vm.profile.plan` 应不再是 `no-op`。
- **回滚** = revert 本 PR；若已重装，需再重装一次并重跑 `--action apply`。
  无 schema、无迁移、无数据，回滚代价与前进代价对称。

## 5. 非目标

1. **不启用任何 provider。** 不把 `emaintenance` 设为 `codex`，因为那需要
   NewEMaint 自己的只读 canary 产出物，本会话取不到（本机 codex-cli 0.147.0
   跑不了 codex-analyzer，broker 的 36 个 typed 操作里也没有任意 VM shell）。
2. **不动 `timer_unit`，不动 `contract.py` 的 timer 白名单。** timer 当前
   确实 active，manifest 如实记录；`timer_unit` 是记录不是开关
   （`profiles.py:289` 不渲染它，全仓无代码对 `aisoft-agent@*.timer` 调
   `systemctl`），改它不会停 timer，只会让 manifest 说假话。
3. **不停用 timer。** 那是 VM 上的 sudo 动作，不属本变更，也不需要——
   `none` 之下 timer 触发是无害的空转。
4. **不启用 Development Loop。** `implement_provider` 保持 `none`。
5. **不处理 `rsdesign` / `sfm`。** 两条已随 #252 退出平台并从 manifest 删除。
6. **不修 VM runtime 陈旧问题。** 前置 #179 已闭合（VM 上
   `~/.local/lib/aisoft-loop` 已按 af15294 刷新，`change_control` 路径齐全）。

## 6. 未决问题

无。三个方向的选择由人在确认点 1 授权本会话按证据裁定，结论见 summary。
「NewEMaint 是否启用自动判级」作为遗留项记录并回报，不在本变更内立案。
