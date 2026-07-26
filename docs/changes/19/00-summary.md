---
issue: 19
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/19
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 merged-no-deploy 终态并修改共享标签合同、依赖门禁与当前仓库标签数据
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
depends_on: []
status: implemented
branch: change/19
pr_url:
created: 2026-07-26
updated: 2026-07-26
---

## 问题/需求总结

当前七个生命周期标签在交付后只有 `deployed` 终态。应用仓库可以在合并、确定性
部署和健康验证后使用它，但 AISoftPlatform 这类控制仓库以及其它明确无需部署的变更，
在最终 PR 合并后既不能继续保留 `pr-open`，也不能伪标 `deployed`。当前仓库 10 个
已关闭 Issue 已出现两类漂移：四个仍停在 `pr-open`，六个历史 Issue 的 type 与
complexity 也不符合现行合同。

## 影响范围

- 标签清单从 16 个扩展为 17 个，生命周期从七个扩展为八个。
- runtime 与 Gitea adapter 识别 `completed`，并继续强制三维标签正交与生命周期互斥。
- 依赖门禁把 closed + `completed` 或 closed + `deployed` 都视为已交付依赖。
- deployed 回写把 `completed` 视为需要替换的生命周期标签，防止两个终态并存。
- README、流程分册、runtime 分册、全局规则和接入 skill 统一新语义。
- PR 合并后，以 credential-safe API 一次性迁移当前仓库 10 个已关闭 Issue 并读回。

## 初步方案与建议

新增 `completed`，定义为“最终 PR 已合并、该变更明确无需部署，交付完成”。它与
`deployed` 同属互斥终态：需要部署的变更只有在确定性部署和验证成功后使用
`deployed`；无需部署的变更在合并后使用 `completed`。Gitea 的 `Closed` 仍表示
Issue 已关闭，不单独证明部署完成。

当前仓库历史迁移固定为 #1、#3、#4、#5、#6、#7、#11、#12、#13、#17。根据 Issue
内容、已合并 PR 和平台强制风险规则，它们统一修正为 `type/platform`、
`complexity/complex`、`completed`。迁移必须在本 PR 合并后执行，且先 provision
`completed`、再逐项替换 managed labels、最后重新 GET 全部 Issue。

## 风险

- 把 `completed` 当成 `deployed` 会制造虚假部署证据；文档和 dependency gate 必须
  保留两者语义差异。
- 漏改生命周期集合会保留 `pr-open` 或出现两个终态；tests 必须覆盖互斥和替换。
- 在 PR 合并前迁移真实 Gitea 数据会绕过唯一交付闸门；live migration 明确后置。
- 更新标签时若覆盖非 managed label 会丢失审计信息；迁移必须只替换三维 managed
  labels，并保留其它标签。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 新增 merged-no-deploy 终态并修改共享标签合同、依赖门禁与当前仓库标签数据
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改 `LIFECYCLE_LABELS`、dependency readiness 和 Gitea managed-label contract。
- 修改平台治理文档、全局 AGENTS 源和项目接入 skill。
- PR 合并后迁移真实 Gitea Issue metadata，必须提供回滚和读回证据。

### 缺失的 acceptance criteria 或决策

- 无；用户已确认新增完成终态，名称采用 `completed`，并同意前述标签审计结论。
