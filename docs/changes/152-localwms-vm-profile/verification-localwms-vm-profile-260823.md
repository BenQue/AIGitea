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

# Verification · 给 LocalWMS 声明 vm_profile

## 环境与版本

- Commit SHA: 见 PR 头（本文件在 PR 开出后只回填 `pr_url`，不改结果）
- Artifact: 无（纯 manifest / 合同校验变更，无构建产物）
- Environment: Mac 开发机（worktree `/private/tmp/issue-152-localwms-vm-profile`）+
  Gitea CI（`.gitea/workflows/ci.yml` 的 `verify` job，只跑 `bash codex/tests/smoke.sh`）
- 未触达：gitea-ci VM 的安装态 manifest（`/usr/local/share/aisoft/host-access-broker.json`）
  与 VM 内任何 profile 文件 —— 见下方交接项。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `jq '.projects[] \| select(.project_id=="localwms") \| .vm_profile' codex/config/host-access-broker.json` | PASS | `{"name":"localwms","repo_dir":"work/LocalWMS","analysis_provider":"claude","implement_provider":"none","timer_unit":null}` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json validate` | PASS | `{"contract_version": "host-access-broker/v1", "merge_operation_count": 0, "operation_count": 29, "project_count": 10, "status": "PASS"}` |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests` | PASS | `Ran 508 tests ... OK` |
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -k localwms` | PASS | `test_localwms_profile_is_analyzer_only_without_a_timer ... ok`（另含 #148 的 `test_localwms_is_declared_development`） |
| `bash codex/tests/smoke.sh` | PASS | 退出码 `0`，末行 `Codex platform static smoke checks passed.` |
| `bash codex/tools/project-profile-migration.sh --project localwms --action plan`（worktree 内，走仓库副本 manifest） | PASS（锁已解开） | 由 `TARGET_DENIED / project has no approved VM profile migration` 变为 `RUNTIME_USER_MISSING / VM runtime user is unavailable`。见下方说明 |
| `git diff --quiet origin/main -- codex/config/gitea-governance.json` | PASS | 退出码 `0`，governance manifest 完全未改 |
| `git diff origin/main -- codex/config/host-access-broker.json` | PASS | 唯一改动是 `localwms` 的 `vm_profile`（`-1/+7` 行），其余九个项目条目零差异 |
| 安装态重装（`sudo codex/install-host-access-broker.sh`） | **NOT RUN** | 合并后的独立授权动作，见交接项 |
| VM 内 `vm.profile.plan --project localwms` | **NOT RUN** | 依赖上一行，且需 `localwms-agent` 的 VM 侧凭据 |
| analyzer 低风险 canary | **NOT RUN** | 明确不在本变更范围（Issue「后续」一节） |

### 关于 `RUNTIME_USER_MISSING` 是「通过」而不是「失败」

`aisoft_host_access.cli` 的 `profile` 子命令顺序是：先查 manifest 门（`TARGET_DENIED`），
**再**构造 `ProfileMigrator`（`pwd.getpwnam("coder")` 失败则 `RUNTIME_USER_MISSING`）。
`project-profile-migration` 是 **VM-local** 工具，Mac 上没有 `coder` 用户，所以在 Mac 上
只能走到第二道门。错误码从第一道门前进到第二道门，正是「manifest 这道锁已经解开」的证据。

## Acceptance criteria 结果

| AC | 结果 | 说明 |
|---|---|---|
| AC-1 键集合一致 | PASS | 五键，无 `path_prepend`（只有 SFMDigitalBoard 需要） |
| AC-2 `implement_provider=none` / `timer_unit=null` | PASS | 由新增测试钉住；contract 另有硬断言与 timer 白名单双重兜底 |
| AC-3 `name`/`repo_dir`/`analysis_provider` | PASS | `localwms` / `work/LocalWMS` / `claude` |
| AC-4 manifest validate | PASS | `project_count: 10`、`operation_count: 29`、`merge_operation_count: 0` 与改动前一致 |
| AC-5 smoke | PASS | 退出码 0 |
| AC-6 不改其它项目、不改 governance | PASS | 见上表最后两行 |
| AC-7 不再 `TARGET_DENIED` | PASS | 见上一节 |
| AC-8 交接项写入 verification | PASS | 见下一节 |

## ⚠️ 合并后的显式交接项：重装 manifest

**合并不等于生效。** broker 在运行时读的是安装态副本
`/usr/local/share/aisoft/host-access-broker.json`，仓库里的
`codex/config/host-access-broker.json` 只是源。PR 合并后，必须由人以 sudo 重装，
broker 才会看到 LocalWMS 的新声明。

本变更前已核实 installed 与仓库副本 `diff` 为空 —— 说明上一次 manifest 变更的重装有人做过，
**但它不是自动的，也没有任何 CI 或 hook 会替你做**。

合并后依次执行（在 Mac 上，AISoftPlatform 的 `main` 检出内）：

1. 重装：`sudo bash codex/install-host-access-broker.sh`（幂等、不绑定凭据）
2. 确认安装态已同步：
   `diff /usr/local/share/aisoft/host-access-broker.json codex/config/host-access-broker.json`
   —— 应无输出
3. 确认锁已在 broker 侧解开（**只读**）：
   `/usr/local/libexec/aisoft/host-access-broker --project localwms --operation vm.profile.plan`
   —— **不应**再返回 `TARGET_UNAVAILABLE / project has no approved VM profile`
   （本变更前实测就是这个）。它会经 `orb -m gitea-ci` 在 VM 内跑 VM-local 工具，
   因此不会再撞 `RUNTIME_USER_MISSING`。

第 3 步之后仍可能出现 `CREDENTIAL_UNAVAILABLE` —— 那表示 VM 上
`/home/benque/.config/aisoft/credentials/localwms-agent-project-agent.token` 还没配好。
**这是 canary 的前置运维项，不是本变更的回归**：`vm.profile.plan` 会先读源凭据并校验身份，
再和目标字节比对。

`vm.profile.apply` 是 mutating 操作，属需要独立授权的 provision 动作，**不要**顺手执行。

## 已查清的疑点：`RUNTIME_USER_MISSING` 不会挡住 canary

Issue 正文记录了一条勘察结论：VM 上 `coder` 用户存在（`uid=1000`），但
`project-profile-migration --project rsdesign-new --action read-back` 返回
`RUNTIME_USER_MISSING`，且 `/home/*/.config/aisoft/projects/` 在整台 gitea-ci 上都不存在 ——
怀疑「即便 manifest 改完仍然走不通」。

**结论：该结论不成立，根因是调用入口用错了，VM 侧其实是好的。**

证据（本次会话实跑，全部只读）：

1. `id coder` 在 **Mac** 上返回 `no such user`。`codex/tools/project-profile-migration.sh`
   的文件头就写着 "VM-local exact project profile lifecycle" —— 它是给 VM 内用的。
   `ProfileMigrator.__init__` 里 `pwd.getpwnam(policy["runtime_user"])` 查不到 `coder`
   就抛 `RUNTIME_USER_MISSING`。在 Mac 上直接调这个工具，必然是这个结果，与 VM 状态无关。
2. 正确入口是 broker 的 `vm.profile.*`：`broker.py` 用
   `orb -m gitea-ci -u <user> sudo -n <vm_profile_tool>` **在 VM 内**执行同一个工具。
   实跑
   `/usr/local/libexec/aisoft/host-access-broker --project rsdesign-new --operation vm.profile.read-back`
   返回：
   `{"identity": "rsdesign-agent", "profile": "rsdesign", "project": "rsdesign-new", "result": "read-back", "status": "PASS", "target": "admin/rsdesign-new"}`
3. `read_back` 不是空转：它比对 `/home/coder/.config/aisoft/projects/rsdesign.env` 与
   `/home/coder/.config/aisoft/credentials/rsdesign.token` 的**字节内容与文件模式**。
   它返回 PASS，意味着这两个文件在 VM 上确实存在且与 manifest 声明一致 ——
   即 rsdesign-new **已经 provision 过**，「整台 VM 没有该目录」的观察不成立
   （多半是在 Mac 上、或在 orb 之外的上下文里看的）。

这与 `06-运维手册与踩坑集.md` 踩坑 #18 是同一族错误：**「Mac 上有这个文件」不等于 VM 也有，
反过来「Mac 上跑不通」也不等于 VM 跑不通**。判断 VM 状态只能用 broker 的 `vm.*` 操作，
不能在 Mac 上直接调 VM-local 工具。

因此：这条疑点**不会**挡住后续 canary，也不需要在本 Issue 之外开 VM 侧运维单。
真正待验证的前置项只剩 `localwms-agent` 的 VM 侧凭据（见上一节第 3 步）。

## 重复部署

- 第一次：**NOT RUN** —— 本变更不执行部署。安装态重装是合并后的独立授权动作。
- 第二次：**NOT RUN** —— 同上。

`codex/install-host-access-broker.sh` 的幂等性由 `codex/tests/test-host-access-broker.sh`
在 smoke 内以临时 install root 覆盖（两次执行后 `shasum` 清单一致），本变更未改动该脚本。

## 故意失败与回滚

- 失败场景：**NOT RUN** —— 无部署动作可失败。
- 停止/回滚结果：**NOT RUN**。回滚方式为单一 `git revert`；若彼时已重装过安装态 manifest，
  revert 后须再执行一次 `sudo bash codex/install-host-access-broker.sh` 才能让 broker 回到旧声明。
- 数据恢复验证：**不适用** —— 本变更未写入任何 VM 状态或持久化数据。

## 遗留风险与未完成项

1. **安装态重装未执行**（合并后的人工交接项，见上）。在重装前，broker 对 `localwms` 仍会返回
   `TARGET_UNAVAILABLE` —— 这是预期，不是回归。
2. **`localwms-agent` 的 VM 侧凭据未验证**。重装后第一次 `vm.profile.plan` 可能返回
   `CREDENTIAL_UNAVAILABLE`，需运维补齐源凭据。
3. **profile 尚未 provision**。`vm.profile.apply` 是 mutating 操作，需独立授权。
4. **analyzer canary 未执行**。VM 侧 env 文件 mode 600、只读工作克隆、装
   `$aisoft-platform` 与 `$gitea-analyze-change`、拿低风险 Issue 验证确定性判级 ——
   全部属于 Issue「后续」一节，需另行安排与独立授权。
