---
issue: 360
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/360
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正共享Git范围授权判据并绑定canonical资源与holder，涉及安全和Controller治理
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-canonical-template-scope-261015.md
  spec: spec-canonical-template-scope-261015.md
  plan: plan-canonical-template-scope-261015.md
  verification: verification-canonical-template-scope-261015.md
confidence: high
override_reason: ''
depends_on: []
status: analyzed
branch: change/360-canonical-template-scope
pr_url:
created: 2026-10-15
updated: 2026-10-15
---

## 问题/需求总结

`admin/aisoft-platform#360` 修正共享 Git scope reader 对 canonical vendored 模板的误判。
已合并源码 `afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8` 的
`GitRepository.scope()` 将所有不在本票目录内的 `docs/changes/` 路径视为另一 Issue；
`docs/changes/_template/{summary,spec,plan,verification}.md` 即使逐项列在获批 spec 的
`git_scope` 中也会被拒绝。Controller 和 broker 共用这个 reader。

本轮状态为 **ANALYSIS_COMPLETE / NEEDS_HUMAN_DECISION**。四份映射文档和 spec 内的
**D-SCOPE360-1 完整实施验收卡**可供一次审阅；不把本轮文档批准转换成产品 `approved`。
live Issue 保持 fresh 读回的 `open / needs-analysis`，未投影标签。

## 影响范围

- exact tuple：`change/360-canonical-template-scope`、本目录、
  `/private/tmp/issue-360-canonical-template-scope`。
- 唯一分析 writer：`01a13b2a-e69a-78e2-9c6f-a00284afda90`，已正式 claim。
- fresh manifest main / 文档起点：`afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8`。
- future reader、Controller、broker、分发/漂移映射及真实 Git fixtures 的精确路径见 mapped spec。
- 当前实际 delta 只允许本目录四份文档；不写上述产品路径，不执行产品测试。

## 初步方案与建议

推荐 D-SCOPE360-1 的 **A：精确资源授权**：只有 manifest 绑定项目是合法 holder、
已提交的同票映射 summary/spec 生命周期及绑定合法、精确 scope 明列目标路径时，
才允许四个 canonical 文件中相应的文件。未获批文件没有隐含授权。
trusted policy 从已核对的 canonical manifests 生成，不能取目标候选中的 manifest 或环境变量替身。
逐提交 delta、历史锚点、R0/R/M/H 祖先、两 parent tree、普通 FF 与 guard 全部保留。

**真正待裁定的安全语义**：这个例外是资源范围授权，还是还要新增“每个历史版本均须与某个
获批平台模板快照逐字节一致”的内容锁门？A 的完整方案与验收已列好；后者为 B，会增加版本映射、
历史来源与安装制品合同，不能用 reader 中一行 whitelist 冒充交付。
本轮不代选、不启用任何一项。A 不证明人类批准不可伪造；仍是 #327 的 cooperative checks。

## 风险与依赖

- 平台模板原件在 `templates/docs/changes/_template/`，下游副本在 `docs/changes/_template/`；
  两者不互换，`vendors_change_templates=false` 不得凭路径获得下游例外。
- `git_history_paths` 同样必须核对 canonical 例外，不能用于漂白另一 Issue 或 add/revert 的中间 delta。
- 当前 source 不含 holder/policy 检查；source、fixture、CI、两机 installed 与 HSDB adoption 分层记证。
- 无启动依赖。`admin/aisoft-platform#358` 独立；`admin/HSDB#15` 是受影响消费者，
  不是本票启动前置。本票不向 `depends_on` 填外仓裸编号，不修改 #358 或 #15。
- HSDB #15 原 owner、worktree、固定 OID `82a5aba9e46a002b78e3aca9896ef9a26e4aa5cd`
  均保留；本轮未操作或 fresh 验证它们。公司试运行继续 PAUSED。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正共享Git范围授权判据并绑定canonical资源与holder，涉及安全和Controller治理
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

Issue 标题虽为 fix，但变更涉及共享安全判据、Controller 和 broker，强制 complex；
`contract_effect=change` 描述范围判定的可观察变化，不按纯文档或局部 bugfix 降级。
manifest 将平台仓定义为 public-platform、production 默认、routine disabled，policy 固定 manual。
Matt triage 文档判定为 `bug / ready-for-human`，尚未投影 live triage 标签。
verification 是独立保留现场/归属/安装证据的义务，不代表本次部署。

### 授权与下一步

直接批准来源：HSDB 调度 2026-10-15 用户“批准调度创建两个分析会话”；仅授权独立 WT/claim、
合同分析文档、完整方案、文档检查及线性本地文档提交。批准记录和 fresh 证据位置见 verification。

等待用户一次裁定 D-SCOPE360-1 的安全语义并批准 exact #360 的实施范围。
若批准 A，先按 plan T02 独立应用治理合同并停止，后续 fresh run 重读后实施 T03–T05；
不把这次实施批准当成 push/最终 PR、merge、安装或 HSDB 采用授权。
