---
issue: 191
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/191
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/191-rsdesign-mac-checkout
created: 2026-08-24
updated: 2026-08-24
---

# Spec：rsdesign-new 的 manifest checkout 声明与主机实况对齐

## 目标与原因

让 `rsdesign-new` 的 Mac 侧 typed git 通路恢复可用，方式是把 manifest 声明改成与主机实况
一致，而不是放宽 broker 的断言。断言本身正确——正是它们把这个不符暴露出来。

事实由人在 2026-08-24 定为 **B1**：Gitea `admin/rsdesign-new` 的真实 Mac checkout 是
`/Users/benque/Projects/rsdesign-new`，其 Gitea remote 名为 `origin`。

## Acceptance criteria

- [ ] **AC-1**　`host-access-broker --project rsdesign-new --operation host.onboarding.check`
  返回 `PASS`，不再是 `ONBOARDING_MISMATCH`。
- [ ] **AC-2**　`git.fetch.main` 对 `rsdesign-new` 可用（`status: PASS`），且 `mac.git.bind`
  之后 `host.onboarding.check` 的 credential binding 检查通过；`mac.git.bind` 第二次执行
  返回 `result: no-op`（幂等）。
- [ ] **AC-3**　对 manifest 里全部 10 个项目跑 `host.onboarding.check`，改动前与改动后的
  结果逐项记入映射的 `verification`，并对每个非 `PASS` 的项目写明原因与预期形态。
- [ ] **AC-4**　`codex/runtime/aisoft_host_access/broker.py` 的 `_onboarding_check` 与
  `_validated_remote` 零 diff——不得为让自检变绿而放宽任一断言。
- [ ] **AC-5**　`bash codex/tests/test-host-access-broker.sh`、
  `python3 -m unittest codex.runtime.tests.test_host_access`、`bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-6**　不新增、改名、删除或重写任何 Git remote；`/Users/benque/Projects/RSDesignTool`
  与 `/Users/benque/Projects/rsdesign-new` 的 remote 集合在本次变更前后一致。

## 接口、数据与兼容性影响

- `git_remote_name` 是 #73 引入的可选字段，缺省即 `"origin"`（contract.py:398）。删除
  `rsdesign-new` 的声明不改变 schema，也不影响 `newemaint`/`sfm-digital-board` 的声明。
- `codex/agent/aisoft-project-target.sh` 遍历全部 remote 的 fetch/push URL，与 remote 名无关，
  无需改动；#184 之后「rsdesign-new 的 checkout 判定不出项目」是本 Issue 的下游症状，
  manifest 修正后自动消失。
- VM 侧 `vm_profile` 不变；本次不涉及 VM profile 或凭据迁移。
- manifest 是安装期固定文件：合并后需人工重装两端（Mac `sudo bash codex/install-host-access-broker.sh`，
  VM 同）才在 `/usr/local/share/aisoft/host-access-broker.json` 生效。

## 风险与回滚约束

- 错误声明会被 strict schema 与 `_validated_remote` fail-closed 拒绝，不会静默放行。
- 回滚 = revert 单 PR + 重装两端。`mac.git.bind` 写入的是 repo-local credential 配置
  （`credential.useHttpPath`、`credential.<url>.username`、`credential.<url>.helper`），
  可 `git config --local --unset` 撤销，不触碰仓库内容与任何 remote。

## 非目标

- 不修改 `_onboarding_check`/`_validated_remote` 的任何断言（AC-4）。
- 不处理 `mac_checkout: null` 的四个项目（`myapp`/`sap-table-migrate`/`smoke-test`/`wmpda`）
  当前返回 `CREDENTIAL_UNAVAILABLE` 而非 `TARGET_UNAVAILABLE` 的错误码语义问题——
  人在 2026-08-24 决定只记录、另开 Issue。本 spec 只要求把现象写进 `verification`。
- 不重写 #116 的历史文档，也不改 `newemaint`/`sfm-digital-board` 的 `git_remote_name`。
- 不在 `/Users/benque/Projects/rsdesign-new` 里新增名为 `gitea` 的 remote（那是被否决的 B2）。

## 未决问题

- 无。A/B/C 已由人定为 B1；null-checkout 错误码语义已定为「只记录、另开 Issue」。
