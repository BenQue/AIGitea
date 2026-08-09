---
issue: 73
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/73
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 shared host-access broker 增加 manifest-fixed Gitea remote 与逐项目 fail-closed onboarding contract，同时保留 human-only merge 和 credential 独立审批边界
risk_flags:
  - authentication
  - authorization
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
  summary: summary-manifest-gitea-remote-260809.md
  spec: spec-manifest-gitea-remote-260809.md
  plan: plan-manifest-gitea-remote-260809.md
  verification: verification-manifest-gitea-remote-260809.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/73
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

## 问题/需求总结

Issue #61/#67/#70 已把 Mac host 的 Gitea/Git 操作收敛为 fixed、typed、protected-file
`host-access-broker/v1`，但 project manifest 仍不能表达 Gitea remote name。当前 runtime、fetch/push argv
和 repo binding 都硬编码 `origin`，所以 AISoftPlatform 等 `origin=Gitea` checkout 正常，而保留 GitHub
`origin`、内部 Gitea 使用 `gitea` 的 NewEmaint checkout 在任何 fetch 前 fail closed 为
`TARGET_MISMATCH`。

本 Change 在 platform manifest 中增加调用方不可控的 strict `git_remote_name`：未声明项目兼容
`origin`，NewEmaint 精确声明 `gitea`。所有 Git operation 从 manifest 解析 remote，并继续只接受 exact
`change/N`、fresh protected main、clean worktree、no merge commit 与 non-force same-name push。

同时新增逐项目 read-only `host.onboarding.check`，把已有 protected credential/access audit 与 canonical
checkout、manifest-derived remote URL、repo-local fixed helper binding 组合成一个 fail-closed gate。
`mac.git.bind` 仍只写 repo-local non-secret config；credential provision、permission/protection mutation、项目
adoption 和 live canary 都不由本 Change 执行。

## 影响范围

- `host-access-broker/v1` project schema、contract model、Git runtime 与 typed runner。
- `git.fetch.main`、`git.fetch.change`、`git.push.change`、`mac.git.bind` 的 remote resolution。
- 新的 `host.onboarding.check` 聚合只读 operation 及 protected-file/identity/scope/permission/protection/
  required CI/canonical checkout/remote/helper binding 证据。
- manifest、runtime、helper/controller、installer twice/no-op、security negative、fresh-session integration 与
  full platform smoke tests。
- README、运维与 onboarding 文档；不修改 NewEmaint source 或任何 live Secret/部署状态。

## 初步方案与建议

project schema 只允许缺省或一个 safe identifier `git_remote_name`；缺省解析为 `origin`。调用方 CLI 不增加
remote、URL、owner、repository、refspec、body 或 command 字段。runtime 从 resolved project contract
读取 remote，要求 canonical/current worktree 的该 remote fetch/push URL 都唯一且 byte-equal 于
manifest-derived `base_url/owner/repository.git`，然后用该 remote 构造固定 fetch/push argv。

onboarding 分成三个明确阶段：`host.access.audit` 只读核对 credential/access/protection；
`mac.git.bind` 在 access audit 成功且 remote URL 精确时幂等写 repo-local helper/username/useHttpPath；
`host.onboarding.check` 组合全部只读证据并在任何缺失或 drift 时非零。installer 不创建、复制或更新 token，
不创建 remote，不改 GitHub `origin`，不安装 live candidate。

## 风险

- caller-controlled remote/refspec 可能形成跨仓库写入；interface 与 contract tests 必须证明这些字段不存在。
- 只验证 fetch URL 而忽略 push URL/多值 URL 可能把 read 与 write 路由到不同 target；onboarding 和 Git
  operation 必须同时要求唯一 exact fetch/push URL。
- 错误 repo-local helper/username 或 inherited broad helper 可能绕过 project identity；binding 必须以 local
  empty-helper reset + fixed helper + exact username + `credential.useHttpPath=true` 收敛。
- NewEmaint 当前 credential 已通过 access audit，但 helper binding 缺失；本平台 PR 不因 credential 已存在就
  越界修改 NewEmaint，人工 merge 后仍走独立 adoption Issue。
- remote migration 若误改 GitHub `origin` 或反推内部 merge history 会破坏外部历史；本合同明确禁止创建、
  删除或改写 remote，也不提供 Gitea→GitHub push surface。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为 shared host-access broker 增加 manifest-fixed Gitea remote 与逐项目 fail-closed onboarding contract，同时保留 human-only merge 和 credential 独立审批边界
risk_flags:
  - authentication
  - authorization
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

- 修改 shared authentication/authorization、Git push、manifest schema、controller 与 onboarding 外部合同。
- 涉及跨项目 target、credential binding、protected-main/required-CI fail-closed 规则，命中强制 complex。
- 用户明确要求按 AISoftPlatform complex flow 完成 triage/spec/plan 后才实施。

### 缺失的 acceptance criteria 或决策

无。Issue、用户边界、实时 baseline、测试 seam、post-merge adoption 顺序与人工 merge gate 均已明确。
