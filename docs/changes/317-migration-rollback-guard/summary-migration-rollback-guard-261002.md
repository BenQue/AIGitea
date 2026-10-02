---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在共享发布状态机加入迁移后旧镜像兼容控制及可信依据，涉及数据、外部合同与回滚强制风险。
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-migration-rollback-guard-261002.md
  spec: spec-migration-rollback-guard-261002.md
  plan: plan-migration-rollback-guard-261002.md
  verification: verification-migration-rollback-guard-261002.md
status: spec-drafting
branch: change/317-migration-rollback-guard
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

activate、legacy deploy、显式 rollback 在数据库完成不同 migration identity 后仍可无兼容依据启动旧镜像，阻塞 NewEMaint #229。

## 影响范围

只修改 AISoftPlatform release 合同及 runtime/test/schema；不修改 NewEMaint、应用 pin、现场配置或凭据。

## 初步方案与建议

统一所有旧镜像启动与恢复入口的 fail-closed gate，记录数据库迁移位置；只允许可证明相同位置或 exact、未过期且 operator 管理的兼容依据。

## 风险

- 容器 current_release 不等于当前数据库位置；迁移成功而激活失败后两者会分离。
- 合法旧 state 不包含迁移顺序，读兼容不能变成安全事实默认值。
- 兼容依据自身是权限边界，必须与不可变制品及目标、数据库状态绑定；不得以 producer boolean 代替。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在共享发布状态机加入迁移后旧镜像兼容控制及可信依据，涉及数据、外部合同与回滚强制风险。
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
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

- authoritative origin/main=5c2cd726c9aeaee9d17541d8feb049e33881bbac；共享 main clean。
- #317 正文记录 2026-09-21 批准1,2 的平台先行方向，评论线程为空，无已映射 spec/plan、branch/history/PR。
- FakeDocker public ReleaseRuntime seam 在 activate、legacy v1 deploy、explicit rollback 均复现：不同迁移已完成、兼容依据不存在、旧 SHA 启动 1 次。
- host.onboarding.check=PASS；main 禁止 push/force，唯一 merge identity=admin，required CI=CI / verify (pull_request)，routine disabled。

### 缺失的 acceptance criteria 或决策

- 已批准方向保持；本次首次明确的可信依据、state v3 和治理先行步骤需绑定完整 spec/plan 的合同启动确认。

## 授权与会话

- 本会话：`01a0fc7b-9d82-75e2-975f-d407cd23e34a`；worktree 已 claim。
- Branch/worktree：`change/317-migration-rollback-guard` / `/private/tmp/issue-317-migration-rollback-guard`。
- 既有授权：平台先补控制，人工合并后由 NewEMaint #229 更新 pin；不重复确认此方向。
- 当前只准备可审阅合同与基线证据；尚未把方向批准扩大为新安全接口/state/governance 合同批准。
- `depends_on: []`：#317 无前置；NewEMaint #229 依赖本票，应用层不在本分支修改。
- Delivery policy：`manual`。合同启动确认不授权 push、PR、merge、安装、部署或 Secret。
- 三阶段：合同审阅 → 独立治理合同步骤并停止 → fresh run 重新读取后实施 runtime → 最终 PR 提交确认。
- 所有文档只存在本地；未 push，不提供不存在的远端文档链接。

## 当前投影边界

判级计划为 bugfix/complex。自动审批拒绝 live classification --apply：当前只授权分析、证据与合同草案，未取得精确合同启动确认；无成功标签 mutation。启动确认后才能按 spec 的本票范围执行投影和独立 --verify。远端 needs-analysis 不等于本地分析未完成，更不等于 approved。
