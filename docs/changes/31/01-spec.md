---
issue: 31
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/31
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - compatibility
  - platform-governance
depends_on: []
status: approved
branch: change/31
pr_url:
created: 2026-08-05
updated: 2026-08-05
---

# Spec

## 目标与原因

用可安装、可审计且相同的 `react@19.2.8`/`react-dom@19.2.8` 修正不存在的 `19.3.0`
稳定基线，并让 architecture runtime 对固定的 npm stable-release snapshot fail closed。该
snapshot 是离线、可复现的审计输入，不是联网 dependency updater。

## Acceptance criteria

- [ ] **AC-1** `frontend.react.19` 的 catalog version/pin、`react`、`react-dom` 三处均为
  `19.2.8`，两个 npm package 均有 exact Registry URL、integrity、发布日期，通道为 `stable`。
- [ ] **AC-2** Linux profile、template、valid/invalid fixtures 与 NewEmaint target candidate
  declaration/lock 均引用 `19.2.8`；catalog/profile identity 和全部 committed reference lock
  通过 canonical CLI 重建后保持一致。
- [ ] **AC-3** Validator 和 tests 拒绝 catalog 未被 stable snapshot 覆盖的版本、Canary、
  `latest`、版本范围、`react-dom` 与 `react` 不一致，以及缺少/多余 package metadata。
- [ ] **AC-4** Evidence 文档准确记录 npm Registry 核验、`next@16.2.11` peer compatibility，
  并明确 NewEmaint #52 必须使用本 PR merge commit 后同时更新两包和应用 lockfile。
- [ ] **AC-5** Existing architecture、release、Linux/Windows/SQLite/Docker platform-local tests
  继续通过；NewEmaint consumer/build/browser/Docker/deployment/migration 均明确为 `NOT RUN`。

## 接口、数据与兼容性影响

Catalog V1 component 可选增加 `package_release`。仅 `frontend.react.19` 要求其声明两个固定
npm packages；其它 components 不受该字段影响。`next@16.2.11` 的 Registry peerDependencies
允许 `^19.0.0`，所以 pair `19.2.8` 与该 framework pin 兼容；应用仍须自行完成 build/browser
验收。

## 风险与回滚约束

错误 metadata 会阻止 lock validation，优先 fail closed。回滚使用 revert PR 回到此前已合并
catalog revision；不能把 `19.3.0` 作为回滚目标。不得联网修改 lock、自动改 NewEmaint 或执行
Docker/server/database/Secret 操作。

## 非目标

- 不改 NewEmaint package.json/package-lock、Next.js、Dockerfile、数据库、服务器或部署。
- 不把 npm `latest` 动态解析、Canary/Experimental、范围或自动升级器引入平台。
- 不声称 NewEmaint #52 已恢复、已测试、已迁移或已部署。

## 未决问题

无。
