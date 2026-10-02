---
issue: 287
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/287
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变共享 architecture lock 外部哈希合同并新增版本化 lock schema，强制 complex/manual
risk_flags:
  - shared-core
  - schema-change
  - external-contract
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-profile-semantic-lock-261002.md
  spec: spec-profile-semantic-lock-261002.md
  plan: plan-profile-semantic-lock-261002.md
  verification: verification-profile-semantic-lock-261002.md
depends_on: []
status: approved
branch: change/287-profile-semantic-lock
pr_url:
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

profile 的说明性散文进入全量 canonical JSON 哈希，使机器合同未变的下游 lock 报 LOCK_DRIFT。#287 起始 open/needs-analysis；分析后已投影 type/platform 与 complexity/complex，用户随后确认合同启动。

## 影响范围

architecture 哈希、lock schema、CLI 版本解析、兼容测试与说明。#288 的 Dockerfile evidence 独立处理，不改其它仓库。

## 初步方案与建议

建议 A：新 V2 lock 使用 profile-machine-v1 语义哈希，仅排除 description/compatibility_rules；保留 constraints 与其它字段。V1 继续严格全量验证，旧 lock 由应用独立 Change 显式迁移一次。version 保留为身份约束，不能替代内容哈希。纯散文以后不要求 V2 下游 relock；机器变化仍需项目审阅并自行 relock，不自动跨仓广播。

## 风险

- V1 不能无损推导旧 profile 的机器投影，故不把旧 hash 偷换为新语义。
- constraints 包含人类运维约束，仍入哈希；对它的措辞修改也仍会漂移，属于保守边界。
- 散文排除不授权更改实际运维约束或以散文承载新机器规则。
- 必须先独立应用 architecture 文档合同并停止，fresh run 后才能 schema/runtime 实现。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变共享 architecture lock 外部哈希合同并新增版本化 lock schema，强制 complex/manual
risk_flags:
  - shared-core
  - schema-change
  - external-contract
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

- broker git.fetch.main/host.onboarding.check PASS；起点 5c2cd726c9aeaee9d17541d8feb049e33881bbac。
- broker #287 正文与完整评论已读；2026-09-15 延后调度由 2026-10-02 明确派单覆盖。
- 历史 6121838→97b09a7 profile_sha256 6eb2458f…→7ed962a2…；实验复现 LOCK_DRIFT。
- profile.version 原已为 1.0.0，两 head 相同；移除合法 delivery 取值但不 bump 也复现 LOCK_DRIFT。
- 现有 architecture 基线 57 tests PASS；非现场/SFM/CI 验收。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 会话与合同状态

- 唯一写者：`01a0fc7c-027e-70a3-8871-beb484e4a8d8`。
- Worktree：`/private/tmp/issue-287-profile-semantic-lock`，已经 claim。
- Branch：`change/287-profile-semantic-lock`；已确认合同的本地工作，未 push、无 PR。
- `depends_on: []`：#287 无硬依赖；#288 仅共享模块协调，#286/#289 的调度顺序不是代码依赖。
- 用户已在本聊天回复“确认”，批准完整合同与 T01/T02/T03；本阶段仅执行 T01。
- 采用 A 后无需为纯散文广播；自动发现消费者、开票/投递 `needs-relock` 不在本次方案内。
- Matt `triage/bug` 与 `triage/ready-for-agent` 是建议结果；现有 broker 未提供这两个维度的 typed projector，不能借 extension 或直接 API 写入。

## 判级与草稿合同读回（2026-10-02）

- 正式 classification projector dry-run 后 apply，再独立 `--verify 287`：`projected`；type/platform、complexity/complex 均读回。
- broker lifecycle 读回：`spec-drafting`，未设置 `approved`。
- 使用实际 Issue labels，以 `allowed_lifecycle=(spec-drafting,)` 调用 contract loader，仅做草稿结构检查：8 个 AC、4 个映射文档、branch 一致、depends_on 空；未调用 provider/Loop。
- type/complexity/lifecycle 不替代缺失的 typed Matt triage projector，后者仍为 GAP。

## 合同启动确认

2026-10-02 用户回复“确认”。确认绑定 #287、当前 spec/plan 与 manual 流程；receipt 见 `contract-start-approval.json`。不包含 PR 提交、合并或部署授权。T01 应用 architecture 文档合同并停止，后续 fresh run 无需重问启动确认。

## T01 完成状态

architecture README 与 ADR-0007 的受控文档步骤已应用。T02/T03 待 fresh run，runtime/V2 功能尚未实现；Issue 不关闭、聊天不归档。新 run 延续已记录的启动批准，不再询问合同确认。
