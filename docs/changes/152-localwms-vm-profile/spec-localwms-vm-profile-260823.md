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

# Spec · 给 LocalWMS 声明 vm_profile

## 目标与原因

让 `localwms` 在 host-access broker 的 governance manifest 中拥有一份 **analyzer-only** 的
VM profile 声明，从而解开 M3 退出门前的第一道锁：`project-profile-migration --project
localwms --action plan` 不再以 `TARGET_DENIED / project has no approved VM profile
migration` 拒绝。

本 spec 的范围**只到声明**。profile 的实际 provision（VM 内写入 `.env` 与 token 文件）、
analyzer 的安装与低风险 Issue 判级验证，都是需要独立授权的运维动作，不在本变更内。

## Acceptance criteria

- [ ] AC-1：`codex/config/host-access-broker.json` 中 `projects[].project_id == "localwms"`
      的 `vm_profile` 非 `null`，且键集合与同类项目一致
      （`name`/`repo_dir`/`analysis_provider`/`implement_provider`/`timer_unit`，不含
      `path_prepend`）。
- [ ] AC-2：该 profile 的 `implement_provider` 为 `"none"`，`timer_unit` 为 `null`。
- [ ] AC-3：`name` 为 `"localwms"`，`repo_dir` 为 `"work/LocalWMS"`，
      `analysis_provider` 为 `"claude"`。
- [ ] AC-4：`aisoft_host_access.cli validate` 对新 manifest 返回 `status: PASS`，
      `project_count: 10`、`operation_count: 29`、`merge_operation_count: 0` 不变。
- [ ] AC-5：`bash codex/tests/smoke.sh` 通过（含 508+ 条 Python 合同测试与
      `test-host-access-broker.sh` 的 jq 断言）。
- [ ] AC-6：除 `localwms` 外，`codex/config/host-access-broker.json` 中其它九个项目条目
      的 `git diff` 为空；`codex/config/gitea-governance.json` 完全未改。
- [ ] AC-7：在仓库副本 manifest 下运行 `codex/tools/project-profile-migration.sh --project
      localwms --action plan`，返回码不再是 `TARGET_DENIED`。
- [ ] AC-8：verification 文档写明「合并后须 sudo 重装 manifest」这一交接步骤，并写明重装后
      在 VM 内的预期结果。

## 接口、数据与兼容性影响

**合同校验面（`codex/runtime/aisoft_host_access/contract.py`）。** manifest 校验里有一条
双向相等断言：

```python
_require(
    profile_repositories
    == {"aisoft-platform", "NewEMaint", "HSDB", "rsdesign-new", "SFMDigitalBoard"},
    "VM profile migration set must contain exactly the five approved repositories",
)
```

它不是子集检查，所以**只改 JSON 会让整份 manifest 加载失败**，进而让 broker 对全部十个项目
fail closed。允许集必须在同一个变更里扩到六个，断言文案的 `five` 同步改为 `six`。

这是设计意图，不是要绕开的摩擦：JSON 是「谁声明了 profile」，contract 的允许集是「平台批准了
谁」。两处分开，意味着任何新增 VM profile 都必须经过本仓库的 Issue/PR，而不能靠改一个配置值
悄悄生效。

**广播面。** 同一事实还镜像在两处断言里，必须同步，否则 smoke 变红：

- `codex/runtime/tests/test_host_access.py::test_exact_projects_profiles_and_no_merge_surface`
  的 profile 映射表。
- `codex/runtime/tests/test_host_access.py::test_declared_and_undeclared_projects_parse_exactly`
  的 `path_prepend` 声明表。
- `codex/tests/test-host-access-broker.sh` 的 jq `[.projects[] | select(.vm_profile != null)
  | .repository] | sort` 列表（jq 按码点排序，`LocalWMS` 落在 `HSDB` 与 `NewEMaint` 之间）。

**运行时行为变化。** `aisoft_host_access.cli` 的 `profile` 子命令先查 manifest 门
（`TARGET_DENIED`），再构造 `ProfileMigrator`（可能抛 `RUNTIME_USER_MISSING`）。本变更之后：

- 在 **Mac** 上直接跑 `project-profile-migration --project localwms --action plan` 会从
  `TARGET_DENIED` 变成 `RUNTIME_USER_MISSING` —— 这是**通过了 manifest 门**的证据，
  不是新缺陷。该工具是 VM-local 的，Mac 上没有 `coder` 用户。
- 在 **VM** 内（或经 broker `vm.profile.*` 由 `orb -m gitea-ci` 代跑）才会真正进入
  凭据与字节比对逻辑。
- broker 的 `vm.profile.plan/apply/read-back/rollback` 对 `localwms` 不再返回
  `TARGET_UNAVAILABLE`。**这四个操作里 `apply` 和 `rollback` 是 mutating 的，本变更不执行。**

**兼容性。** 没有 schema 版本变化（`contract_version` 保持 `host-access-broker/v1`），
没有既有项目的行为变化，没有数据迁移。

## 风险与回滚约束

- **合并不等于生效。** broker 读 `/usr/local/share/aisoft/host-access-broker.json`，
  仓库副本只是源。合并后须 sudo 重装 —— 这是显式人工交接项，写在 verification 里。
- **回滚**：单一 revert commit 即可（改动只是声明 + 允许集 + 三处断言，无迁移、无状态）。
  若已重装过 installed manifest，回滚后须再重装一次才能让 broker 回到旧声明。
- **误开执行面的风险**：`implement_provider` 被 contract 硬断言锁死为 `none`；
  `timer_unit` 的白名单只有 `aisoft-agent@emaintenance.timer` 与 `aisoft-agent@sfm.timer`，
  想给 LocalWMS 加 timer 必须再改一次 contract。也就是说，本变更在语法层面就无法误开 Loop。

## 非目标

- 不执行 analyzer canary，不在 VM 内 provision LocalWMS 的 profile 或 token。
- 不启用任何 timer，不 `systemctl --user enable`。
- 不改动其它项目的 `vm_profile`。
- 不改 `codex/config/gitea-governance.json`。
- 不修复 VM 侧运维状态（见 verification 的「已查清的疑点」一节）。
- 不重装 installed manifest —— 那是合并后的独立授权动作。

## 未决问题

无。
