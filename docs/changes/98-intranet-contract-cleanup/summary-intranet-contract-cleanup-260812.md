---
issue: 98
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/98
change_type: docs
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 清理 #93 双权威持续协作合同的残余旧文本，不引入新的内网或部署行为
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-intranet-contract-cleanup-260812.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/98-intranet-contract-cleanup
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/102
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

Issue #93 已把内网目标模型确定为：本地 Gitea 长期承担开发权威、私有 GitHub 作为搬运中继、
公司 Gitea 承担部署权威；一次性冻结本地和 remote 切换仅为未来彻底下线的备选路径。但 README、
07、13 §13 与 14 Gate G 仍残留旧模型，可能使执行者错误停掉本地开发。

## 影响范围

- README 当前状态与术语。
- 07 的权威分工、阶段 F 与回滚表。
- 13 的持续协作投运完成定义。
- 14 Gate G 的持续同步验收。

## 初步方案与建议

所有当前路径统一指向 13 §0；旧冻结/remote 切换语义只在明确标题和条件下引用 13 §11。

## 风险

低。纯文档 restore，不改实现、环境或部署。风险是误删备选灾备边界；通过保留 §11 链接及
“执行备选切换后不回切旧副本”的限定语义控制。

## AI 判级

```yaml
change_type: docs
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 清理 #93 双权威持续协作合同的残余旧文本，不引入新的内网或部署行为
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

### 判级证据

- 用户明确要求恢复已合并 #93 的目标模型；没有新产品/部署合同决策。
- 变更只触及指定文档，局部、可 revert、无需环境 mutation。

### 缺失的 acceptance criteria 或决策

无；用户已批准文本方向与 small/docs 判级。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| 指定残余文本 | PASS | 当前路径均为双权威；冻结/切换/唯一权威仅在备选限定语境 |
| 脚本/runtime/manifest | NOT CHANGED | diff 仅 4 份权威文档 + 本 summary |
| `bash codex/tests/smoke.sh` | PASS | 325 tests OK；Codex platform static smoke checks passed |
| 远端 PR candidate CI | FAIL | head `e761badaa7a384514fd407b471fb75b95b1cf8cd`，run/job #408，4s；该分支未含 #96，按 smoke 顺序与已知 VM 缺陷推断先在 host-role tests 早停，typed status 不含 job log |
| 部署/环境/标签 | NOT RUN | 本 Change 不授权 |
