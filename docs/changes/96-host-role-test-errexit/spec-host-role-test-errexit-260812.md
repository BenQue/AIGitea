---
issue: 96
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/96
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
  - security
depends_on:
  - 101
status: ready-for-review
branch: change/96-host-role-test-errexit
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/100
created: 2026-08-12
updated: 2026-08-12
---

# Spec

## 目标与原因

使 host-role guard/installer 测试在 Mac Bash 3.2 与 gitea-ci Bash 5.3 上具有相同控制流和可诊断
失败，恢复平台 PR CI 的真实安全验证能力。production guard、schema、catalog 与 live profile 不变。

## Acceptance criteria

- [ ] AC-1 guarded mutation 测试直接捕获 guard rc；仅 rc=0 才能触达 marker，deny 必须为 rc=20 且 marker 不存在。
- [ ] AC-2 guard 测试的 allow/deny/invalid/identity/mode/secret 断言失败均输出明确 `FAIL:` 原因。
- [ ] AC-3 installer 测试所有幂等、文件、mode 与非目标断言失败均输出明确 `FAIL:` 原因。
- [ ] AC-4 `bash -n` 与两个 targeted tests 在 Mac Bash 3.2 通过。
- [ ] AC-5 两个 targeted tests 在 gitea-ci Bash 5.3 通过。
- [ ] AC-6 `bash codex/tests/smoke.sh` 通过；PR final head 的 `CI / verify (pull_request)` 通过。
- [ ] AC-7 后续 GNU/BSD 可移植性调查只允许 test-only 调整；不得通过 fake probe 掩盖 production
      runtime 缺陷。若 runtime 修改是必要条件，停止并升级独立 Issue。

## 接口、数据与兼容性影响

只修改 shell tests 与 Change docs。测试输出新增 `FAIL:` 前缀；成功输出不变。无 runtime、API、
profile、schema、catalog、环境或部署影响。

## 风险与回滚约束

回滚为 revert 本 PR。禁止通过删除 deny/marker 断言或放宽期望 rc 使 CI 变绿。

## 非目标

- 不修改 live guard 或 #97 错误分类。
- 不翻转 required context，不修改 governance manifest/fixtures，不执行 governance apply。
- 不安装、部署、合并或修改标签。

## 未决问题

AC-1 至 AC-5 已完成。AC-6 的远端部分被 #101 阻塞：用户于 2026-08-12 批准 T02 test-only
调查，同时明确 runtime 必须另立 Issue；实证确认无法在不掩盖 runtime 缺陷的前提下只改测试。
