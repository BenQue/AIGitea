---
issue: 97
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/97
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - operations
depends_on:
  - 96
  - 101
status: ready-for-review
branch: change/97-guard-error-classification
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

# Spec

## 目标与原因

在不改变 host-role 安全决策的前提下，把不可读 contract path 与 malformed JSON 分开诊断，并让
运维手册以真正具备 `root:gitea-runner 640` profile read 权限的身份执行 live probe。

## Acceptance criteria

- [x] AC-1 secure owner/mode 检查之后，对 profile/schema/catalog 分别验证 caller readability；不可读
      返回 rc=30 + `decision=invalid-profile reason=<kind>-permission-denied`。
- [x] AC-2 对三个输入分别执行 JSON syntax 检查；malformed 返回 rc=30 +
      `reason=<kind>-invalid-json`，stderr 不含输入内容或 marker。
- [x] AC-3 既有 path owner/mode、schema/catalog shape、identity、capability、allow=0、deny=20 保持。
- [x] AC-4 06 §1 的 live probe 固定 `gitea-runner`，解释普通用户 permission denial 不是迁移信号，
      禁止放宽 mode、改 group 或复制 profile 绕过。
- [x] AC-5 Mac Bash 3.2 syntax/ShellCheck/targeted/full smoke 与 VM Bash 5.3 targeted tests 通过。
- [x] AC-6 不修改 live profile/group、installed guard、service、标签、required context 或部署。

## 接口、数据与兼容性影响

exit code 与 allow/deny 输出不变；rc=30 的 reason 从笼统 `invalid-json` 细分为六个稳定原因。
调用方若匹配 reason，应按新分类更新；不得把 permission denial 当作 schema/profile 回归。

## 风险与回滚约束

TOCTOU 下 `jq` 失败后再次检查 readability：若已变不可读归 permission，否则归 malformed；两类都
fail closed。回滚为人工 revert PR；安装上一版需独立授权，本 Change 不执行。

## 非目标

- 不迁移或修改 live profile/schema/catalog。
- 不改变 capability allowlist、owner/mode allowlist、identity 或 exit code。
- 不处理 #101 sync stat runtime，也不翻转 required context。
- 不合并、不部署、不改标签、不处理 #95。

## 未决问题

无；用户已批准改题与实现边界。
