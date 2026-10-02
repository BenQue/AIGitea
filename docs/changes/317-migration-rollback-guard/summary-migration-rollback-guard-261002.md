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
status: approved
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

- 无；2026-10-02 用户直接批准完整 spec/plan。

## 授权与会话

- 本会话：`01a0fc7b-9d82-75e2-975f-d407cd23e34a`；worktree 已 claim。
- Branch/worktree：`change/317-migration-rollback-guard` / `/private/tmp/issue-317-migration-rollback-guard`。
- 既有授权：平台先补控制，人工合并后由 NewEMaint #229 更新 pin；不重复确认此方向。
- 2026-10-02 用户在本会话直接回复“批准”，当前完整 spec/plan 已获合同启动授权；receipt 见 evidence/contract-start-approval.json。
- `depends_on: []`：#317 无前置；NewEMaint #229 依赖本票，应用层不在本分支修改。
- Delivery policy：`manual`。合同启动确认不授权 push、PR、merge、安装、部署或 Secret。
- 三阶段：合同审阅 → 独立治理合同步骤并停止 → fresh run 重新读取后实施 runtime → 最终 PR 提交确认。
- 所有文档只存在本地；未 push，不提供不存在的远端文档链接。

## 当前投影边界

判级为 bugfix/complex。首次自动审批在完整合同批准前拒绝 live classification --apply，未写入标签；2026-10-02 用户直接批准后允许按 spec 执行本票投影，并独立 --verify 读回。历史拒绝不再是当前缺授权 blocker；不存在的 triage typed surface 仍不绕过。


## T01 进度

2026-10-02 合同已获用户直接批准。Fresh base 不变；已独立应用 release 治理文档。
classification --verify 两维真实 projected，远端 lifecycle=approved。
完整合同 loader 读到10条 AC、frontier=T01。runtime/schema/test、PR CI、installed/live 均 NOT RUN。
Matt triage typed 写缺口记录为 GAP，本票不改 broker 或通过其他身份绕过。


T01 治理合同应用及两轴文档 review 已完成；3项发现已修复复核，无未解决review finding。
本运行按已批准合同停止。T02/T03必须由下一fresh run重读后实施，沿用当前批准，不追加合同确认。
批准记录已发布至Issue评论12027；无remote branch/PR，尚无可供应用采用的新merged SHA。
