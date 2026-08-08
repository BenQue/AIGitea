---
issue: 46
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/46
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 full smoke 仍要求已验证 containerd compatibility row 为 rejected 的过期断言
risk_flags:
  - ci-change
  - compatibility
  - artifact
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on:
  - 27
status: pr-open
branch: change/46
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/47
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #27 的真实 disposable Engine 29 containerd E2E 已把 committed compatibility matrix 的
`engine-29-containerd-linux-amd64` 固定为 `supported + real-e2e evidence`；classic row 继续
`rejected + evidence:null`。runtime focused test 与 Issue #27 verification 都精确要求这一合同。

`codex/tests/smoke.sh` 仍保留 evidence 写回前的旧断言，要求两个 rows 全部 rejected。exact
`origin/main@3b01e29dad23e6d78d83c48014d69ea78a37a83e` 因此在 216 个 Python tests 全部通过后退出 1。
Issue #45 没有修改 matrix 或该断言，只是首次在 exact-main worktree 中如实读取到尾部门禁失败。

本 Change 只把 smoke assertion 对齐 committed exact row identities/status/evidence；不修改 matrix、
runtime、Docker、VM、制品、部署或 Issue #27 的 real evidence。首次修复该断言后，full smoke 又暴露
同一 Issue #35 commit 中的第二个既有失败：静态门禁要求 skill 出现 exact `retire-shared-bot`
subcommand，但 skill 只描述了相同的逐仓库 retirement gate，未给出命令名。本 Change 同时在现有
语义内补上 purpose-built subcommand，不改变 retirement 前置证据或授权边界。

## AI 判级

这是恢复既有合同的单一静态断言修复，但直接影响 CI、制品兼容性和平台治理门禁，按照
`AGENTS.md` 强制归类为 `complex`。
