---
issue: 35
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/35
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立跨项目治理身份、项目专用自动化身份、private 默认与显式 public 例外，并把人工合并边界复制到本地和公司内网
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
  - deployment
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/35
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

本地 Gitea 由 AISoftPlatform 统一运维，但当前共享 `ci-bot` 同时服务多个项目，Mac checkout
中的现有身份只有 Write，无法读取 branch protection；仓库可见性和保护也存在实际漂移。
用户已批准引入跨项目平台治理账号，同时保留每项目独立账号，且 PR 合并继续只能人工执行。

仓库可见性不再采用“全部 public”或“全部 private”的粗粒度策略。默认必须为 private，只有
显式批准的非内部应用才可 public。当前 public allowlist 精确限定为：

- `admin/aisoft-platform`：平台文档、模板和公开治理合同；
- `admin/myapp`：测试用途；
- `admin/smoke-test`：smoke 测试用途。

公司内部应用 `admin/HSDB`、`admin/NewEMaint`、`admin/rsdesign-new`、
`admin/SapTableMigrate`、`admin/SFMDigitalBoard`、`admin/WMPDA` 必须 private。未来公司内网
Gitea 重建时沿用“private 默认 + 显式 public allowlist”，但不复制本地账号、PAT、Issue、PR
或 Secret。

## 影响范围

- Gitea service account、PAT scope、credential file 与仓库 collaborator 模型。
- 9 个显式受管仓库的 visibility、project agent、platform manager、`main` protection、
  merge allowlist 和合并后分支清理策略。
- 本地 Gitea `DISABLE_REGISTRATION` 与新仓库默认 visibility。
- 私有仓库访问、onboarding、运维排障和公司内网重建文档。
- VM/部署身份合同：平台 operator 与每项目 deploy identity 分离；不在本 Change 创建业务
  runtime、部署应用、修改数据库或操作公司服务器。

## 初步方案与建议

新增一个严格 JSON governance manifest，所有仓库和账号必须显式列入；未知仓库只报告，绝不
自动公开、授权或修改。新增三个 purpose-built 入口：service-account bootstrap、Gitea service
policy check/apply、逐仓库 governance check/apply。所有 apply 都要求精确目标、已合并平台 SHA、
安全 credential file、pre/post snapshot 和读回；默认只读。

身份分层如下：

- `admin`：人工 break-glass、用户/平台引导和唯一 PR merge identity；
- `aisoft-platform-manager`：显式受管仓库 Admin，使用分离的 read-only audit PAT 与 mutation PAT，
  不用于普通 Git、不在 merge allowlist；
- 每项目 `<project>-agent`：仅本项目 Write，用于 Issue/branch/commit/push/PR，不得 Admin 或 merge；
- `ci-bot`：逐项目迁移期间保留，只有新账号/profile/保护验证通过后才从该仓库退出。

## 风险

- visibility 变更可能意外公开内部代码或阻断现有 clone/CI；必须按 exact allowlist 逐仓库应用并
  在每一步读回，不能扫描后批量修改。
- collaborator 或 protection 误配置可能扩大跨项目写权限、允许自动 merge 或阻断正常 PR；
  apply 必须保留现有 required status contexts/approval 字段，并将 merge allowlist 精确限制为
  `admin`。
- `DISABLE_REGISTRATION` 需要修改 `/etc/gitea/app.ini` 并重启 Gitea；必须先备份、语法检查，
  重启后验证 health/login/repo API，失败恢复同一备份。
- 共享 `ci-bot` 过早移除会使现有 project profile 或 Loop 失效；其退出是逐项目后置 Gate。
- 本 PR 合并前所有 live 账号、PAT、visibility、protection、service config 和 VM 变更均为
  `NOT RUN`，不得把本地 mock/smoke 写成部署成功。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立跨项目治理身份、项目专用自动化身份、private 默认与显式 public 例外，并把人工合并边界复制到本地和公司内网
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
  - deployment
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改认证、授权、跨项目平台治理、private/public 外部可见性和 branch protection。
- 修改共享 onboarding/运维工具和公司内网重建合同，并包含 Gitea service restart。
- AGENTS.md 强制将认证/权限/安全、共享组件、CI/部署和 Agent 治理归类为 complex。

### 缺失的 acceptance criteria 或决策

- 无。账号角色、当前 public allowlist、内部应用清单、公司内网策略、人工 merge 和 live 变更
  闸门均已由用户明确批准。
