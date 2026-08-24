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

# Spec · 让 localwms 声明一个这台 VM 上真的存在的 analyzer 运行时

## 1. 目标

把 `codex/config/host-access-broker.json` 中 `project_id: localwms` 的
`vm_profile.analysis_provider` 从 `claude` 改为 `codex`，使该声明与 `gitea-ci`
VM 上实际可用的运行时一致，并让 `test_host_access.py` 的取值断言携带新的依据。

## 2. 非目标之外的一条硬边界：本变更不部署

本 PR 只改仓库里的 manifest 源。broker 运行时读的是安装态副本
`/usr/local/share/aisoft/host-access-broker.json`，本会话**不重装、不 provision、
不执行任何 mutating 的 `vm.profile.*` 操作**。生效路径见 §7 的交接项。

## 3. 可测验收标准

取自 Issue #164 正文，逐字保留，不增不减：

- **AC-1**：manifest 中 `localwms.vm_profile.analysis_provider == "codex"`。
- **AC-2**：重装并重跑 provision 后，`/home/coder/.config/aisoft/projects/localwms.env`
  中 `ANALYSIS_PROVIDER=codex`，文件仍为 `0600 coder:coder`。
- **AC-3**：`project-profile-migration --project localwms --action read-back`
  返回 `status: PASS`、`identity: localwms-agent`。
- **AC-4**：`IMPLEMENT_PROVIDER` 仍为 `none`，`timer_unit` 仍为 `null`，不启用任何 timer。

附加的仓库侧回归门（不是 Issue 的 AC，是平台既有硬门）：

- **AC-R1**：`aisoft_host_access.cli validate` 仍 `PASS`，且
  `project_count` / `operation_count` / `merge_operation_count` 与改动前一致。
- **AC-R2**：`python3 -m unittest discover -s codex/runtime/tests` 全绿。
- **AC-R3**：`bash codex/tests/smoke.sh` 退出码 0。
- **AC-R4**：`codex/config/gitea-governance.json` 与其余九个项目条目零差异。

AC-2 与 AC-3 只能在主机侧重装并 provision 之后取证，属合并后的人工交接项，
在本 PR 内记为 `NOT RUN` 并写明可达条件（`03` §3：不可达项显式写明，
不得把 `NOT RUN` 改写为通过）。

## 4. 接口 / 数据 / 兼容影响

**Schema：无变化。** `contract.py:430` 的
`_require(analysis in {"claude", "codex", "none"}, ...)` 本来就接受 `codex`；
`VMProfileContract` 的字段集合、`required_vm_keys` 的五键约束、`timer_unit`
白名单、`implement_provider == "none"` 硬断言全部不动。

**生成的 profile 字节：**`profiles.py:301` 逐行拼装 env 文件，
`ANALYSIS_PROVIDER={project.vm_profile.analysis_provider}` 是唯一受影响的一行。
行数、行序、其余键值、文件模式（`0600`）全不变——所以 AC-2 里的
「文件仍为 `0600 coder:coder`」不需要额外机制来保证，它由未被触碰的代码路径保证。

**运行时行为：**`provider-poll.sh:12` 的取值校验对 `codex` 与 `claude` 同样通过；
`:39` 由 `analyze-claude.sh` 切到 `analyze-codex.sh`。由于 `localwms` 的
`timer_unit` 是 `null`，没有 systemd 单元会自动触发这条链，切换只在人工调用时生效。

**向后兼容：**其余九个项目条目一律不动，其中 `newemaint` / `sfm` / `rsdesign`
继续声明 `claude`（见 §6）。`test_undeclared_profile_bytes_are_byte_identical_to_pre_112_shape`
钉的是 `newemaint` 的字节形状，不受本变更影响。

## 5. 逐文件授权

按 `AGENTS.md`「只有 complex 变更映射的 spec 明确授权时，才能修改治理文件」，
本 spec 授权且仅授权以下两个文件：

| 文件 | 授权范围 |
|---|---|
| `codex/config/host-access-broker.json` | 仅 `projects[]` 中 `project_id == "localwms"` 条目的 `vm_profile.analysis_provider` 一个值。同条目其余键、其余项目条目、`operations[]`、`vm_profile_policy` 均不得改动 |
| `codex/runtime/tests/test_host_access.py` | 仅 `test_localwms_profile_is_analyzer_only_without_a_timer`：两处 `analysis_provider` 期望值，以及说明新依据的注释。其他测试函数不得改动 |

**明确不授权**（本 spec 不允许触碰）：`codex/config/gitea-governance.json`、
`codex/agent/**` 下任何脚本、`codex/runtime/aisoft_loop/**`、
`codex/runtime/aisoft_host_access/**` 的非测试代码、`AGENTS.md`、
`codex/install-*.sh`、任何 CI 或部署脚本。

## 6. 非目标

1. **不改 `rsdesign` / `sfm` / `emaintenance` 三条同病 profile。** 裁定依据见
   summary「范围裁定」一节：证据只覆盖 localwms；`sfm` 与 `emaintenance` 有活的
   15 分钟 timer，翻它们等于把 fail-closed 空转变成两个应用仓上活的写入链，
   属「启用」而非「订正」，须各自带 canary 与验收标准另开 Issue。
2. **不刷新 VM 上陈旧的 `~/.local/lib/aisoft-loop`。** 修复方式是以 `coder` 身份跑
   `codex/install-vm.sh`，但它同时刷新 agent 脚本与 systemd unit 模板，影响 VM 上
   所有项目，须独立评估（Issue #164 附带发现一；本 spec 补充了它比 Issue 描述更早
   触发的证据，见 summary 风险第一条）。另开 Issue。
3. **不给 VM 侧补 Issue 评论读取路径**（Issue #164 附带发现二）。另开 Issue。
4. **不启用 Development Loop**：`implement_provider` 保持 `none`，`timer_unit` 保持 `null`。
5. **不执行任何主机侧动作**：不重装、不 provision、不跑 mutating 的 `vm.profile.*`。
6. **不修订历史文档**：`docs/changes/152-localwms-vm-profile/` 记录的是当时的真实判断，
   保持原样；本变更以新 change 目录记录推翻的依据。

## 7. 合并后的生效路径（人执行，本会话不做）

1. 人合并本 PR。
2. Mac 与 gitea-ci VM **两台**都 `sudo bash codex/install-host-access-broker.sh`。
3. `sudo /usr/local/libexec/aisoft/project-profile-migration --project localwms --action apply`。
4. 同一工具 `--action read-back` 复核 → AC-2 / AC-3。

第 2 步漏掉任何一台，broker 侧就仍是旧声明；这是踩坑 #18 的同族失败模式
（「Mac 上装了」不等于 VM 也装了）。
