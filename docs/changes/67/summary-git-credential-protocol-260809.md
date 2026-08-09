---
issue: 67
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/67
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 shared host-access credential helper 对 Git 合法多值属性的误拒绝，同时保持 scalar identity 与 target 路由严格 fail closed
risk_flags:
  - authentication
  - security
  - external-contract
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-git-credential-protocol-260809.md
  spec: spec-git-credential-protocol-260809.md
  plan: plan-git-credential-protocol-260809.md
  verification: verification-git-credential-protocol-260809.md
confidence: high
override_reason: ''
depends_on:
  - 61
status: pr-open
branch: change/67
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/68
created: 2026-08-09
updated: 2026-08-09
---

## 问题/需求总结

Issue #61 / PR #63 已合并，host access broker、Git credential helper 与 AISoftPlatform repo-local
binding 已从 protected-main SHA `97445947fff79a4c2db6fa764feb21660e281556` 安装。当前
`git version 2.50.1 (Apple Git-155)` 对真实 HTTP push 发出的 helper `get` 请求包含两个合法重复的
`capability[]`，随后是唯一 scalar `protocol`、`host`、`path`、`username` 和一个 `wwwauth[]`。

merged parser 先把所有 key 放入同一 scalar dictionary，并在 allowlist 前拒绝任何重复 key，导致
合法 `capability[]` 被误判为 `CREDENTIAL_PROTOCOL_INVALID: Git credential field is duplicated`。
真实 `git push --dry-run` 因此 fail closed，未产生远端写入。

## 影响范围

- `host-access-broker/v1` Git credential protocol parser 与 private helper pipe。
- host-access unit、credential-helper、真实 protocol-shape 与 security negative tests。
- host broker 运维说明和本 Change verification。
- 不修改 credential catalog、Keychain service/account、账号/PAT、ACL、protected `main`、merge 权限、
  业务项目、VM/service/timer/profile、数据库或部署环境。

## 初步方案与建议

把 credential request 分成唯一 scalar 与有序 multi-valued attributes：`protocol`、`host`、`path`、
`username` 继续使用严格 allowlist 且各自最多一次；以 `[]` 结尾的合法 key 逐项保留输入顺序，再忽略
不影响 basic username/password route 的 values。unknown scalar、malformed line 和既有 identity/host/
path/cross-project mismatch 继续非零 fail closed。

## 风险

- 若把 unknown scalar 也静默忽略，可能绕过未来 credential route 的安全决策；本合同明确禁止。
- 若把 multi-valued attributes 扁平为 scalar，仍会与当前及后续 Git capability negotiation 不兼容。
- helper success path 会在只供 Git 消费的私有 pipe 返回 password；tests、verification、adapter、Issue/PR
  和终端输出不得回显真实字段值或 Secret。
- post-merge 若未从 exact protected-main bytes 重装，live canary 不能证明交付字节已生效。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复 shared host-access credential helper 对 Git 合法多值属性的误拒绝，同时保持 scalar identity 与 target 路由严格 fail closed
risk_flags:
  - authentication
  - security
  - external-contract
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 修改 fixed credential helper 的认证协议解析和 shared host runtime，命中 authentication、security、
  external-contract、shared-core 与 platform-governance 强制 complex 规则。
- Git 官方 `git-credential` 文档明确 `key[]` 是有序多值字段并允许重复，unknown attributes/
  capabilities 应被忽略；现 merged parser 与该外部合同冲突。
- 用户已明确限定 scalar allowlist、安全负向测试、唯一 PR、人工 merge 与 post-merge live 边界。

### 缺失的 acceptance criteria 或决策

- 无；Issue #67 与本次用户授权已明确实现方向、验证矩阵、bootstrap adapter 和人工 merge 闸门。
