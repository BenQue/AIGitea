---
issue: 79
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/79
change_type: docs
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 修正 #77 对齐清扫遗漏的六处外围分册残留，使其与已合并事实（Issue #21/#57 后状态）一致
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-peripheral-docs-fixes-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/79-peripheral-docs-fixes
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

2026-08-11 全面审核（Claude Code）确认：PR #78（Issue #77）完成核心文档对齐后，外围分册仍有
六处表述与已合并事实或现行合同冲突，会把历史状态误当当前状态。

## 影响范围

仅 Markdown 文档，六个文件：

- `07-内网与生产平移路线.md`：§5.1 仍称「AppServer 迁移、数据和回滚未真实验收前不得写成完成」，
  与 Issue #21（2026-08-04 完成迁移与 post-check）及已更新的 01/02/README 冲突；头部状态行把
  Linux 平台侧（已实现）与公司内网/Windows（未实施）混为一谈。
- `02-CI与自动部署流水线.md`：头部日期停在 2026-07-11；§8 仍示范 raw admin token 的
  `grep`+`curl` 拼装，与 01 §2 / 06 §1.0 broker 身份合同抵触；缺迁移后当前部署入口指向。
- `01-基础设施-VM-Gitea-Runner.md`：§3 把「manifest 定义 17 个标签」写错——canonical manifest
  实为 24 个（平台三维 17 + Matt triage 7）。
- `05-通知与多人协作.md`：全册无状态行；两项通知待办（部署失败/回滚通知、Mac 即时通知）
  自 2026-07 起未实施，读者无法分辨设计与现实。
- `archive/11-Codex-Loop运行时实施计划.md`：归档 banner 未说明 checkbox 为历史快照，agent 有
  按 `- [ ]` 重跑已完成任务的风险。
- `README.md`：§5 导航仍写「16 条实证踩坑」（实际 17 条）。

## 初步方案与建议

逐处最小修正为与已合并事实一致的表述；不改任何行为、脚本、治理文件（AGENTS.md/skills），
不批量改写历史 Change 文档。

## 风险

极低：纯文档 restore，单 PR 可 revert。唯一注意点是 07 修正后仍保留「后续环境健康须实时
只读复核」的边界，避免把一次性验收写成永久事实。

## AI 判级

```yaml
change_type: docs
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 修正 #77 对齐清扫遗漏的六处外围分册残留，使其与已合并事实（Issue #21/#57 后状态）一致
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

### 判级证据

- 只修改文档表述，恢复与 `docs/changes/21/03-verification.md`、`codex/config/gitea-labels.json`
  （24 项）、06 §1.0 broker 合同等既有证据的一致性。
- 范围局部（6 文件、20 行插入/12 行删除），不触发任何强制复杂规则。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| 07 不再含「未真实验收前不得写成完成」 | PASS | `grep -c` = 0 |
| 02 §8 不再含 raw `Authorization: token` 示例 | PASS | `grep -c` = 0 |
| 01 §3 含「共定义 24 个规范标签」 | PASS | `grep -c` = 1 |
| README 导航含「17 条实证踩坑」 | PASS | `grep -c` = 1 |
| 05 头部含 2026-08-11 状态行 | PASS | `grep -c` = 1 |
| archive/11 banner 含「进度快照」声明 | PASS | `grep -c` = 1 |
| `git diff --check` | PASS | 无输出 |
| 治理文件未触碰 | PASS | diff 仅 6 个 Markdown，无 AGENTS.md/skills/脚本 |
| 远端 CI / 人工合并 | NOT RUN | 平台仓库当前无 required CI context；人工合并未执行 |
