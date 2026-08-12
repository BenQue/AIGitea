---
issue: 107
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/107
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: verified
branch: change/107-vm-profile-tool-install
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Verification

## 环境与版本

- 安装源：AISoftPlatform protected `main` = `ac44e08`（canonical checkout，安装前已 fast-forward）
- 变更源：worktree `/private/tmp/issue-107-vm-profile-tool-install`
- Artifact: 无应用制品；本次为 VM 侧工具安装与 project profile 布局迁移
- Environment: OrbStack VM `gitea-ci`（非生产；平台自身基础设施）
- VM: Python 3.14.4、ripgrep 15.1.0

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 迁移前基线：VM 三路径盘点 | **PASS**（确认缺失） | `libexec` 仅 `verify-host-role`；`lib/aisoft-host-access` 空目录；`share/aisoft` 仅 host-role 两文件 |
| 新 preflight 分支（安装前，源码树 broker） | **PASS** | `{"code": "VM_TOOL_UNAVAILABLE", "message": "VM profile tool is not installed; run codex/install-host-access-broker.sh on the VM"}` |
| `install-host-access-broker.sh` 第一次（VM，sudo） | **PASS** | `installed host-access-broker/v1 candidate` |
| `install-host-access-broker.sh` 第二次 | **PASS**（幂等） | `host-access-broker/v1 candidate already current (no-op)` |
| 安装后三路径盘点 | **PASS** | `libexec`: `git-credential-aisoft-host host-access-broker project-profile-migration verify-host-role`；`lib/aisoft-host-access`: `aisoft_change_name.py aisoft_gitea_governance aisoft_host_access`；`share/aisoft`: 含 `gitea-governance.json` `host-access-broker.json` |
| `vm.profile.plan` | **PASS** | `{"action": "apply", "identity": "newemaint-agent", "profile": "emaintenance", "project": "newemaint", "status": "PASS", "target": "admin/NewEMaint"}` |
| `vm.profile.apply` 第一次 | **PASS** | `{"backup": "latest", "result": "applied", "status": "PASS", ...}` |
| `vm.profile.apply` 第二次 | **PASS**（幂等） | `{"action": "no-op", "result": "no-op", "status": "PASS", ...}` |
| `vm.profile.read-back` | **PASS** | `{"identity": "newemaint-agent", "profile": "emaintenance", "project": "newemaint", "result": "read-back", "status": "PASS", "target": "admin/NewEMaint"}` |
| 结构化错误透传（真实环境） | **PASS** | 迁移前 `read-back` 由 `HOST_COMMAND_FAILED` 变为 `READ_BACK_MISMATCH: profile read-back bytes mismatch` |
| 故意失败 1：无 VM profile 的项目 | **PASS**（fail closed） | `myapp` → `{"code": "TARGET_UNAVAILABLE", "message": "project has no approved VM profile"}` |
| 故意失败 2：`vm.profile.rollback` | **PASS** | `{"backup": "latest", "result": "rolled-back", "status": "PASS"}`；profile 精确回到 pre-#61 内联形态 |
| 回滚后 `read-back` | **PASS**（正确失败） | `READ_BACK_MISMATCH`——证明确实回到迁移前状态，非假回滚 |
| 回滚后重新 `apply` + `read-back` | **PASS** | 恢复到迁移后状态，`read-back` 再次 `PASS` |
| `unittest test_host_access` | **PASS** | 57 tests OK（含新增 VmProfilePreflightTests 9 例） |
| `bash codex/tests/smoke.sh`（VM 内执行） | **PASS** | `Ran 332 tests ... OK` + `Codex platform static smoke checks passed`，exit 0 |
| `bash codex/tests/smoke.sh`（Mac host） | **BLOCKED** | Mac 未安装真实 ripgrep（`rg` 仅为 Claude Code 注入的 shell function），`smoke.sh:6` 的 `command -v rg` 在非交互 bash 下失败、`set -e` 静默 exit 1。与本变更无因果关系，见「遗留风险」 |
| `bash -n codex/tools/gitea-readonly.sh` | **PASS** | 无输出 |

## Acceptance criteria 结果

- AC-1 preflight 确定性探测：**PASS**
- AC-2 可区分 typed 错误码且不泄露：**PASS**（`VM_TOOL_UNAVAILABLE`；单测断言 message 不含 `token`/`sudo:`/`command not found`）
- AC-3 preflight 通过后行为一致：**已修订，见下**
- AC-4 三分支测试覆盖：**PASS**（并扩充至 9 例）
- AC-5 06 文档安装面归属表 + 踩坑条目：**PASS**
- AC-6 smoke 全绿：**PASS（VM）/ BLOCKED（Mac host，环境前置缺失）**
- AC-7 未越界：**PASS**（`git diff --stat` 仅 6 个文件；未动平台 `AGENTS.md`、manifest、CI、他会话分支）
- AC-8 VM 安装面就位：**PASS**
- AC-9 `read-back` 结构化 JSON：**PASS**
- AC-10 `plan` 与 policy 一致：**PASS**
- AC-11 安装器两次幂等：**PASS**（apply 亦幂等）
- AC-12 故意失败被正确拒绝且可回滚：**PASS**

## 实施中的 spec 修订（两处，均由验证发现）

1. **AC-3 放宽**：原文要求「preflight 通过后行为与既有实现一致」。验证发现工具在失败时会
   向 **stderr** 输出自己的治理错误契约（`aisoft_host_access/cli.py` 的
   `print(..., file=sys.stderr)`，18 个固定错误码），而 broker 因 returncode 非零直接丢弃，
   把 `READ_BACK_MISMATCH` 这类精确诊断塌缩成 `HOST_COMMAND_FAILED`。这正是本 spec
   「可诊断性层」目标要解决的同一缺陷的第二个实例，故实现改为**透传**该错误契约，并对
   code 形状（`^[A-Z][A-Z0-9_]{2,47}$`）、message 长度与单行性做 fail-closed 校验，
   不匹配则退回 `HOST_COMMAND_FAILED`。
2. **新增 `gitea-readonly.sh` 的 `GITEA_TOKEN_FILE` 支持**：迁移把 profile 从内联
   `GITEA_TOKEN` 切换为 `GITEA_IDENTITY` + `GITEA_TOKEN_FILE`（#61/#70 的既定合同）。
   `codex/agent/common.sh` 已支持该形态，但 `gitea-readonly.sh` 只认内联 token 与 admin
   凭据文件，迁移后 ladder step 1 会以
   `required file not found: /home/benque/gitea-ci-credentials.txt` 失败。本 spec
   「目标与原因」明写恢复 ladder step 1 为目标，故一并补齐，使用与 profile 相同的
   mode 400/600 闸门。

## 重复部署

- 第一次：`installed host-access-broker/v1 candidate`（安装器）；`result: applied`（迁移）
- 第二次：`already current (no-op)`（安装器）；`action: no-op`（迁移）

## 故意失败与回滚

- 失败场景 1：对 manifest 中 `vm_profile: null` 的 `myapp` 请求 `vm.profile.read-back`
  → `TARGET_UNAVAILABLE`，fail closed，未触达 VM（单测断言 probe 调用数为 0）。
- 失败场景 2：`vm.profile.rollback` → `rolled-back`；profile 精确回到 pre-#61 内联形态，
  且随后的 `read-back` 正确报 `READ_BACK_MISMATCH`（证明是真回滚而非空操作）。
- 恢复验证：重新 `apply` → `read-back` `PASS`，ladder step 1 复检返回 repo JSON。
- 数据恢复验证：不适用——本次不涉及任何数据库或业务数据。

## 结论修正：令牌无需重新签发

Issue #107 正文把「陈旧内联令牌失效」列为需人工处理的 Secret 事项。迁移后实测
**ladder step 1 直接恢复**（`repo` 端点返回 JSON 而非 404），说明有效令牌一直存在于
`vm_profile_policy.source_credential_root`，等待迁移安装；失效的只是 pre-#61 profile 里
内联的那一份。**因此不需要任何令牌重签操作。** 全程未读取、未打印、未生成、未搬运任何
token 值；所有相关验证只观察 HTTP 响应形态。

同理，`ANALYSIS_PROVIDER` 漂移也由迁移一并修正（现为 `claude`，与 manifest 声明一致），
不需要单独处理。

## 遗留风险与未完成项

- **Mac host 缺少真实 ripgrep**：`smoke.sh` 第 6 行 `command -v rg >/dev/null` 在
  `set -euo pipefail` 下会**无任何输出**地 exit 1，极易被误读为测试挂死或本次改动导致。
  本次在 VM 内执行 smoke 取得全绿证据。是否在 Mac 安装 ripgrep、或让 smoke 对缺失前置
  条件给出显式提示，留给独立决策，不在本 Change 范围。
- 其它项目 profile（`sfm`、`hsdb`、`newrsdesign`）仍是 pre-#61 布局，未迁移。通路现已可用，
  可按同一流程逐项目执行；`newrsdesign.env` 的文件名与 manifest 声明的 `rsdesign` 不一致，
  需先核对再迁移。
- 本次仅在 VM 侧安装了 `install-host-access-broker.sh` 产物；`install-host-role.sh` 与
  `install-vm.sh` 的既有安装未改动。
