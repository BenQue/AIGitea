---
issue: 31
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/31
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正跨项目 Linux Web 架构基线并新增 React npm 稳定发布一致性门禁，防止下游安装、lockfile 和框架兼容合同再次漂移
risk_flags:
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/31
pr_url:
created: 2026-08-05
updated: 2026-08-05
---

## 问题/需求总结

NewEmaint #52 在采用 AISoftPlatform `frontend.react.19` 时发现 `19.3.0` 不是可安装的
stable npm release。2026-08-05 对 npm Registry 的只读核验显示，`react` 与 `react-dom` 的
`latest` 均为精确的 `19.2.8`；`next@16.2.11` 的 peerDependencies 接受 `^19.0.0`。

## 影响范围

- 更新 catalog、Linux profile、项目模板/fixtures 和 NewEmaint target-candidate/reference lock。
- 在离线 architecture validator 中加入 React 两包 stable-release snapshot gate。
- 更新稳定发布和下游恢复路径的证据文档；不修改 NewEmaint、服务器、Docker、数据库或 Secret。

## 初步方案与建议

将 `react@19.2.8` 与 `react-dom@19.2.8` 的 exact Registry metadata 和 integrity 固化为
`frontend.react.19` 的 stable-release snapshot。validator 只接受 `stable`、两包齐全、相同
精确版本、精确 Registry URL 与非未来日期；它不在 CI/lock 生成时访问网络。catalog/profile
revision 递增，所有 committed reference lock 使用 CLI 再生成。

## 风险

- 静态 snapshot 不是自动更新器：未来版本必须经新的 Issue、Registry/官方证据与人工 PR 更新。
- Platform-local tests 不能证明 NewEmaint 安装、build、browser、Docker、部署或迁移；这些保持
  `NOT RUN`，由 NewEmaint #52 在消费合并 commit 后继续。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正跨项目 Linux Web 架构基线并新增 React npm 稳定发布一致性门禁，防止下游安装、lockfile 和框架兼容合同再次漂移
risk_flags:
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
```

### 判级证据

- 该变更修改跨项目 catalog/profile/lock 的 shared platform contract，并影响下游 package 安装。
- 新增 validator 规则与测试，错误基线会使 NewEmaint #52 无法产生符合平台的 lockfile。

### 缺失的 acceptance criteria 或决策

- 无。Issue #31 的验收标准明确，用户已批准在 `change/31` 实施；不授权下游或环境 mutation。
