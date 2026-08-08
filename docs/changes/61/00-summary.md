---
issue: 61
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/61
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立 versioned host access broker、project-agent credential/profile 消费闭环，并让 project poll 对 Gitea 外部错误 fail closed
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
depends_on:
  - 35
  - 51
  - 55
status: pr-open
branch: change/61
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/63
created: 2026-08-08
updated: 2026-08-08
---

## 问题/需求总结

Issue #35 已建立最小权限 Gitea manager/project-agent 身份并移除 manifest 仓库中的共享
`ci-bot` collaborator，但正常工具消费仍存在两层缺口：Codex managed sandbox 不能稳定直接访问
`.orb.local`/OrbStack，而 Mac checkout 和 VM project profiles 也没有统一、可审计地绑定到 exact
project-agent。当前 `provider-poll.sh` 还会通过 process substitution 和 `|| echo` 吞掉 Gitea
401/403/404，使 systemd oneshot 错误显示为 `0/SUCCESS`。

本 Change 新增 host access broker v1：调用方只能选择 manifest-declared project 与版本化 operation，
Gitea URL、owner、repository、identity、Mac checkout、OrbStack machine、VM profile 和 credential store
全部由 strict manifest 解析。broker 不接受任意 shell、URL、checkout/credential path 或 merge；人工
`admin` 继续是唯一 merge identity。

同时新增 repo-local Mac Git credential binding 与四个 exact VM profiles（NewEMaint、HSDB、
rsdesign-new、SFMDigitalBoard）的原子 plan/apply/read-back/rollback 工具，并把 project poll 改为
profile/target/identity/token-file fail-closed。合并前只实现和测试 candidate，不安装 broker、不修改
Mac Keychain/Git config、不修改 VM profile/token、不停止或重启 timer/service/VM。

## 影响范围

- 新的 strict host-access manifest、broker runtime、Mac Git credential helper/binding 和 installer。
- VM project profile/token 的 versioned contract、原子安装、备份、read-back、rollback 与 no-op。
- `common.sh`、`project-poll.sh`、`provider-poll.sh`、`install-vm.sh` 和 profile template。
- 平台 smoke/focused tests、私有 Gitea/运维/onboarding 说明及 emergency diagnostics 边界。
- 不修改业务应用、数据库、Gitea 账号/PAT/ACL/protection、公司内网或生产环境。

## 初步方案与建议

broker manifest 只引用 canonical `gitea-governance/v1` 中的仓库与身份，并逐项校验 owner/repository/
project-agent/human merge identity byte-exact。API/Git/project poll 使用 project-agent；cross-project
settings/protection read 使用 manager audit；manager mutation binding 保留为专用、非 Git/非 merge
路由。Secret 只从 fixed macOS Keychain binding 或 fixed mode 400/600 VM token file 读取，不由调用者
传 path，也不写入 argv、日志、Git config 或用户可见输出。

profile migration 一次只处理 manifest 中一个 exact project：先验证 source token mode/symlink 与
live identity，再把 token file 和无 Secret profile 原子替换；备份保存原 bytes/uid/gid/mode/hash，
失败自动恢复，显式 rollback 只使用固定 latest backup。相同目标第二次 apply 必须为 no-op。

## 风险

- credential route 或 target mapping 错误可能造成跨项目访问；strict cross-manifest validation 和
  identity read-back 必须先于 API/Git/profile mutation。
- Git credential helper 的协议输出包含只供 Git 子进程读取的 password 字段；broker terminal 输出、
  argv、日志和 Git config 不得出现 Secret，helper 也不得响应非 exact host/path。
- 多文件 profile/token 更新可能出现半状态；必须用同目录临时文件、受控 backup 与自动恢复形成事务。
- poll 由“静默成功”改为非零可能让现有 timer 显示 failed；这是 fail-closed 预期，post-merge migration
  必须逐 profile 验证后再恢复 timer 调度。
- host broker 仍可能因安装/host runtime 故障失败；只有此时且 host/sandbox 真实状态仍矛盾，才允许
  emergency 使用 `orbstack-access-diagnostics`。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 建立 versioned host access broker、project-agent credential/profile 消费闭环，并让 project poll 对 Gitea 外部错误 fail closed
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

- 新增认证/授权/Secret 路由、共享 Agent runtime、host 安装与回滚合同。
- 修改 active systemd project poll 的错误语义与外部系统契约。
- Issue 已明确要求 `complexity/complex`，且 `AGENTS.md` 对上述风险强制 complex。

### 缺失的 acceptance criteria 或决策

无。Issue、评论与本次独立会话授权已明确实现范围、post-merge live 边界和人工 merge 闸门。
