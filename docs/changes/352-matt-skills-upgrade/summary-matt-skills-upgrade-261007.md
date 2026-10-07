---
issue: 352
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/352
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: Matt 技能增删、调用和领域文档约定改变，并涉及共享 Controller 的 PR 证据与安装回滚，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - rollback
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-matt-skills-upgrade-261007.md
  spec: spec-matt-skills-upgrade-261007.md
  plan: plan-matt-skills-upgrade-261007.md
  verification: verification-matt-skills-upgrade-261007.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/352-matt-skills-upgrade
pr_url:
created: 2026-10-07
updated: 2026-10-07
---

## 问题/需求总结

平台与本机受管 Matt 技能仍为 v1.2.2。用户在本会话阅读版本核验与视频分析后，于 2026-10-07 直接回复“批准你的建议”。本合同承接已确认的 v1.3.1 受控升级、术语表兼容、PR 证据和人工 retro；保留确定性 Controller，并行写入编排另行评估。

本次批准允许在该范围内完成合同、source 实施、测试、修复和本地原子 commit，不重复询问相同范围。按照根 AGENTS.md 的治理约束，本轮 T01 **仅固定这四份语义合同及其审查证据，验证、本地 commit 后 STOP**；下一 fresh run 重读后实施 T02。批准不包括 push/PR、merge、全局安装、VM、Claude-owned plugin、Secret、服务或部署。最终 PR 仍保留 exact Issue/branch/manual 第二确认，安装在 source 合并后按目标和回滚单独验收。

## 影响范围

| 对象 | 绑定或范围 |
|---|---|
| Repository / Issue | admin/aisoft-platform / #352 |
| Branch | change/352-matt-skills-upgrade |
| Worktree | /private/tmp/issue-352-matt-skills-upgrade |
| 单写者 | Codex session 01a11682-fafc-70c1-80f2-a5d0d470bca1，已通过 claim-worktree 正式认领 |
| fresh main / 本地基线 | 11628709e659dac48f5cb66bade81f1617974546 |
| 上游固定目标 | v1.3.1 / 24fe0ef7737efae15c87225755e9f6f5965e4888 |
| 当前步骤 | T01 四角色治理合同与证据；没有 runtime 变更 |
| 后续 source | 完整 vendor、安装器及其校验、Matt adapter、domain/tracker 模板、最小 glossary、PR 正文生成和相应测试 |
| Merge policy | manual；required CI 为 CI / verify (pull_request) |

## 初步方案与建议

按 [spec](spec-matt-skills-upgrade-261007.md) 固定兼容与权限边界，按 [plan](plan-matt-skills-upgrade-261007.md) 顺序实施。v1.3.1 候选已在隔离目录完成来源校对；新技能文件存在不代表已安装、正确加载或已获运行权限。

Matt 视频 1:49–3:16 仍推荐确定性循环，因此不以 implement-spec 替代平台 Controller。pr 只提升正文质量；retro 只输出人工审查的环境改进候选。术语表改名与安装归属、技能名称冲突一起处理。

## 风险

- 新版有 3 个新增技能、1 个移除技能；不得覆盖无关技能，或留下旧受管悬空链接。
- 本机旧 skills.sh 锁文件不再代表受管安装；gstack 与 Matt 的 retro 同名，必须明确来源。
- CONTEXT 的历史业务规则不等于 glossary；迁移必须保全，不批量重写下游仓库或历史 Change。
- source/local/CI 不证明 installed/live；当前 35/35 哈希一致只证明旧 v1.2.2 安装完整。
- upstream implement-spec 的 reset、子代理 merge 和提前 PR 不进入本票运行授权；本票的两个确认点和部署边界不变。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: Matt 技能增删、调用和领域文档约定改变，并涉及共享 Controller 的 PR 证据与安装回滚，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - rollback
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

平台 classify_update 对 v1.2.2 → v1.3.1 的结果为 complex。涉及技能集、关键技能、Agent 治理、共享 Controller 和安装回滚；verification 承载上游及本机一次性观察，不声明部署。

### 缺失的 acceptance criteria 或决策

无。源实现的验证要求已固定；目标主机安装尚未纳入本次执行授权。具体结果见 [verification](verification-matt-skills-upgrade-261007.md)。
