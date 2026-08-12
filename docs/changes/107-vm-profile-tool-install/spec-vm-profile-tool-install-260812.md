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
status: contract-drafting
branch: change/107-vm-profile-tool-install
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/109
created: 2026-08-12
updated: 2026-08-12
---

# 恢复 VM 侧 project profile typed 操作

## 目标与原因

让 manifest 已声明、allowlist 已放行、但从未真正可用的四个 `vm.profile.*` typed 操作
（`plan` / `apply` / `read-back` / `rollback`）恢复工作，并让同类失败在未来可被立即诊断。

必要性有两层：

1. **能力层**：`private-gitea-access.md` 把「exact project profile + 只读 helper」列为
   authenticated ladder 的 **step 1 首选路径**。该路径当前不可用，只读盘点被迫降级到
   step 4（VM-local admin 只读凭据）。VM 侧 headless Loop 依赖同一 profile 面。
2. **可诊断性层**：定位本缺陷必须绕过 broker 手工复现底层命令。broker 已捕获 stderr 却在
   失败路径丢弃，任何 VM 侧执行问题都表现为同一个无信息的 `HOST_COMMAND_FAILED`。

## Acceptance criteria

### 代码与文档（本 PR 交付）

- [ ] AC-1：`_vm_profile` 在调用迁移工具前执行确定性 preflight，探测其在 VM 内可执行；
      探测不解析 stderr 文本，不依赖 sudo 的本地化消息。
- [ ] AC-2：preflight 失败时抛出**可区分于** `HOST_COMMAND_FAILED` 的 typed 错误码，
      其 message 为固定文案并指向应执行的安装器名，不含凭据、token、profile 内容或
      stderr 原文。
- [ ] AC-3（实施中修订）：preflight 通过后，成功路径与既有实现一致（返回 payload；
      `project` 不匹配仍 `TARGET_MISMATCH`；stdout 非 JSON 仍 `RESPONSE_SCHEMA_INVALID`）。
      **失败路径改为透传工具自身的治理错误契约**：该工具在失败时向 stderr 输出
      `{status, code, message}`（`aisoft_host_access/cli.py`，18 个固定错误码），原实现因
      returncode 非零将其整体丢弃，把 `READ_BACK_MISMATCH` 这类精确诊断塌缩为
      `HOST_COMMAND_FAILED`。透传须对 code 形状（`^[A-Z][A-Z0-9_]{2,47}$`）、message 长度
      与单行性 fail-closed 校验，不匹配退回 `HOST_COMMAND_FAILED`。
      修订理由：这与 AC-1/AC-2 是同一个「可诊断性」缺陷的两个实例，原 AC-3 是在不知道
      工具存在 stderr 错误契约时写下的。
- [ ] AC-3b（实施中新增）：`codex/tools/gitea-readonly.sh` 支持 `GITEA_TOKEN_FILE`。
      迁移把 profile 从内联 `GITEA_TOKEN` 切换为 `GITEA_IDENTITY` + `GITEA_TOKEN_FILE`；
      `codex/agent/common.sh` 已支持该形态，但该 helper 只认内联 token 与 admin 凭据文件，
      迁移后 ladder step 1 会以 `required file not found` 失败。读取须复用同一 mode 400/600
      闸门。修订理由：本 spec「目标与原因」第 1 条明写恢复 ladder step 1 为目标。
- [ ] AC-4：`codex/runtime/tests/test_host_access.py` 覆盖三条分支——工具缺失、工具存在且
      成功、工具存在但执行失败——且不依赖真实 VM。
- [ ] AC-5：`06-运维手册与踩坑集.md` 含安装面归属表（`install-vm.sh` /
      `install-host-role.sh` / `install-host-access-broker.sh` 各自在哪台机器执行、装到哪个
      根、是否需要 root），并在踩坑集新增本次条目。
- [ ] AC-6：`bash codex/tests/smoke.sh` 全绿；改动的 shell 脚本（若有）通过 `bash -n`。
- [ ] AC-7：不修改平台 `AGENTS.md`、`codex/config/*.json` manifest、CI 定义、任何业务仓库，
      不触碰 `change/106-*` 与 `change/101-*` 等他会话在途分支。

### 运维执行（已获用户授权，证据入 verification）

- [ ] AC-8：VM `gitea-ci` 的 `/usr/local/libexec/aisoft/project-profile-migration` 存在且可执行，
      `/usr/local/lib/aisoft-host-access` 非空，两个 manifest 就位于 `/usr/local/share/aisoft/`。
- [ ] AC-9：`vm.profile.read-back --project newemaint` 返回结构化 JSON 且 `project == "newemaint"`。
- [ ] AC-10：`vm.profile.plan --project newemaint` 给出与 `vm_profile_policy` 一致的迁移计划。
- [ ] AC-11：安装器连续执行两次，第二次为幂等 no-op（输出可判定）。
- [ ] AC-12：一次故意失败场景可被正确拒绝或回滚，且不留下半完成状态；证据记入 verification。

## 接口、数据与兼容性影响

- 新增一个 typed 错误码，属 broker 响应合同的**增量**：既有调用方在成功路径与其它错误码上
  行为不变；原先返回 `HOST_COMMAND_FAILED` 的「工具缺失」这一子情形改为新码。
- 无 schema、无数据库、无 CI 定义、无制品或部署流水线变更。
- 安装器本身不改动——它已幂等且 credential-free；本次只补充「在哪执行」的事实与 preflight。

## 风险与回滚约束

- broker 改动限定在 `vm.profile.*` 分支；`_run` 的通用语义不变，其它 21 个 typed 操作路径
  零改动。回滚 = 单文件 revert。
- VM 内安装可回滚：`install-host-access-broker.sh` 对已存在且不同的目标会先写
  `<target>.previous` 再覆盖（见其 `install_versioned`）。
- profile 迁移的回滚由既有 `vm.profile.rollback` 与 `vm_profile_policy.backup_root` 承担；
  故意失败演练必须验证该路径。

## 非目标

- **不重新签发任何 Gitea 令牌**。陈旧内联令牌失效由人处理；本次不读取、不打印、不生成、
  不搬运 token 值，令牌相关验证只观察 HTTP 状态码。
- 不修改平台 `AGENTS.md`（平台合同禁止普通 implementation run 修改本次运行正遵循的
  `AGENTS.md`）；其目录节补充留给独立治理变更。
- 不实现 label 读回 typed 操作，也不实现 `aisoft-project-align` 检查器——属 #106 范围。
- 不修正其它项目 profile（`sfm.env`、`hsdb.env`、`newrsdesign.env`）的同类漂移；
  本次只以 `newemaint` 验证通路，其余项目在通路可用后另行处理。
- 不启用任何 provider、timer 或 service；`IMPLEMENT_PROVIDER=none` 保持不变。

## 未决问题

无。
