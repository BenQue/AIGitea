---
issue: 101
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/101
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - credential-boundary
  - sync-runtime
  - ci-change
depends_on: []
status: approved
branch: change/101-sync-stat-portability
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/105
created: 2026-08-12
updated: 2026-08-12
---

# Spec

## 目标与原因

恢复 sync private-file mode gate 在 GNU/Linux 与 BSD/macOS 的一致 fail-closed 行为。实现不再假定
错误平台的 `stat` 选项一定返回非零，而是按 GNU-first、BSD-fallback 顺序探测并验证结果形态。

本 spec 明确授权修改以下 protected runtime/test 文件，除此之外不得扩大实现范围：

- `sync/inbound-sync.sh`
- `sync/git-credential-token-file.sh`
- `sync/tests/test-inbound-sync.sh`
- `sync/tests/test-install.sh`

## Acceptance criteria

- [x] AC-1 两个 runtime 的 mode probe 优先执行 GNU `stat -c '%a'`；仅当命令失败或输出不是
      3–4 位 octal mode 时回退 BSD `stat -f '%Lp'`，fallback 输出也必须通过相同格式验证。
- [x] AC-2 inbound profile、GitHub/Gitea token 与 credential helper 继续只接受 `400/600`；`644`
      和无法解析的 mode 必须非零 fail closed，并给出不含路径内容或 token 的稳定诊断。
- [x] AC-3 tests 必须复现“GNU `stat -f` rc=0 但输出文件系统信息”的原缺陷，并证明 runtime 使用
      有效 GNU mode；Mac 真实 BSD stat 与 gitea-ci VM 真实 GNU stat 的 targeted suites 均通过。
- [x] AC-4 修改的 shell/test 文件通过 `bash -n` 和 ShellCheck（若环境可用）；完整
      `bash codex/tests/smoke.sh` 通过。
- [ ] AC-5 readable tuple、mapped docs、原子 commits、broker typed push 和唯一 `Closes #101` PR
      均成立；PR final-head `CI / verify (pull_request)` 真实通过后停在人工合并。
- [x] AC-6 不安装 sync runtime、不 enable/start timer、不读取或打印真实 token、不执行真实
      GitHub/Gitea sync、不部署、不改标签、不改 required context。

## 接口、数据与兼容性影响

CLI、配置字段、允许的 mode、credential protocol 和同步行为不变。唯一外部可观察修复是 GNU/Linux
不再把合法 `400/600` 文件误报为宽权限。无法确定 mode 时仍非零退出；不新增兼容开关或环境后门。

## 风险与回滚约束

- 错误接受宽权限文件会越过 credential boundary；因此命令成功但输出不合规也必须继续 fallback，
  两种 probe 均无合法 mode 时必须失败。
- tests 只能用临时文件、fake `stat` 与本地 bare repositories；不得接触真实 token 或远端同步。
- 回滚为人工 revert 本 PR；本 Change 没有 live install，因而不包含主机回滚操作。

## 非目标

- 不重构 inbound sync 的 Git/Gitea PR 逻辑、credential format 或 systemd units。
- 不修改 `sync/install.sh` runtime 行为；只允许修正其对应 test 的 mode 探测断言。
- 不安装 runtime、创建 profile、启用 timer、执行真实镜像或处理 GitHub #95。
- 不修改 CI workflow、governance manifest、branch protection 或 required context。
- 不合并 PR、不部署、不改标签。

## 未决问题

无；用户已明确批准实现和验证边界。
