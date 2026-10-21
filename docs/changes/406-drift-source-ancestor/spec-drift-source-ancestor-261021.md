---
issue: 406
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/406
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on:
  - 397
status: approved
branch: change/406-drift-source-ancestor
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - codex/tools/check-installed-drift.py
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - docs/changes/406-drift-source-ancestor/summary-drift-source-ancestor-261021.md
  - docs/changes/406-drift-source-ancestor/spec-drift-source-ancestor-261021.md
  - docs/changes/406-drift-source-ancestor/plan-drift-source-ancestor-261021.md
  - docs/changes/406-drift-source-ancestor/verification-drift-source-ancestor-261021.md
---

# 漂移检查：安装源提交只需是当前 HEAD 的祖先

## 目标与原因

broker 安装面的轮换记录绑定的是安装那一刻的提交。检查器要求它等于当前 HEAD，于是 main 的任何合并都让 Mac 与 VM 变 GAP，#397 的棘轮再把它报成 regressed。真正要守的是「装的字节就是 main 上的字节」，这由逐字节比对负责；提交号只需证明来源在 main 历史里。

## Acceptance criteria

- [ ] AC-1：安装后 main 前进一个只改文档的提交，broker 安装面 PASS。
- [ ] AC-2：前进一个改了轮换受管文件的提交，GAP（`rotation-file-digest-differ`）。
- [ ] AC-3：安装记录 `source_sha` 不是 HEAD 的祖先（含不存在的提交、非 SHA 字符串），GAP（`rotation-source-binding`）。
- [ ] AC-4：声明 helper 时，凭证 `source_commit` 等于安装记录 `source_sha` 且 main 前进只改文档的提交，PASS；`source_commit` 不等于记录 `source_sha`，GAP；helper 源码之后改动，GAP（`helper-source-differ`）。
- [ ] AC-5：反向证明：把新判定临时改回「等于 HEAD」，AC-1/AC-4 的 PASS 用例变红。
- [ ] AC-6：全量 smoke 绿；Codex 只读交叉审查通过。
- [ ] AC-7：合并后 Mac 与 VM 重装读回 `RESULT PASS`；之后再有一次文档合并仍 PASS（取证晚于合并，记在交接里）。

## 接口、数据与兼容性影响

只改检查器判定，不改安装记录 schema、不改安装器、不改轮换工具。原先 PASS 的状态（`source_sha == HEAD`）仍 PASS，因为提交是自身的祖先。

## 风险与回滚约束

`source_sha` 进 git 命令前必须先过 SHA 格式校验，防止以 `-` 开头的参数注入。仍只用只读 git 子命令（审计测试钉住）。回滚：revert 本 PR。

## 非目标

- 不改 `credential_rotation.py` 的 `installation_receipt` / `validate_grant` 闸门。
- 不改其它安装面的判定。

## 未决问题

无。
