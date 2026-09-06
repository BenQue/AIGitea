---
issue: 266
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/266
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: README §4 时序图一行消息文本里的半角分号被 Mermaid 当成语句分隔符导致整图解析失败，改为全角分号恢复渲染，不改任何语义
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-readme-mermaid-semicolon-260906.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/266-readme-mermaid-semicolon
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/267
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

README §4「端到端流程（双路径、单合并闸门）」的 `sequenceDiagram` 在 Gitea/GitHub 页面渲染为
`Parse error on line 32 … got 'NEWLINE'`，整张时序图不显示。第 135 行消息文本

```
G->>U: 📬 邮件通知(Mailpit);issue 被 Closes 自动关闭
```

里的半角 `;` 被 Mermaid 当作语句分隔符，后半句被当成新语句解析而失败。该行自 2026-07-11
v2.0 重构（846365c）起就是这样，#264 把 README 推到 GitHub 镜像后才被看到。

## 影响范围

- `README.md` 第 135 行：半角 `;` 改为全角 `；`，与同图其它行的写法一致。
- 全仓 mermaid 块扫描（README、01–15，排除 docs/changes 与 archive）只有这一处半角 `;`
  出现在 sequenceDiagram 消息文本里；02/12 的 `&lt;`/`&gt;` 在 flowchart 引号标签内，合法。

## 初步方案与建议

单字符替换，不改其它内容。用户明确要求不走判级仪式直接修，本文只作为 broker
`gitea.pull.create` 要求的 summary 存在。

## 风险

- 无行为风险。README 短语被 `codex/runtime/tests` 的 assertIn 钉住，已确认没有测试钉住这一行；
  `codex/tests/smoke.sh` 在本分支实跑。

## AI 判级

```yaml
change_type: docs
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: README §4 时序图一行消息文本里的半角分号被 Mermaid 当成语句分隔符导致整图解析失败，改为全角分号恢复渲染，不改任何语义
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: restore`：恢复本应正常渲染的既有文档图，不新增、不改变任何合同语句。
- `change_type: docs`：只动 README 一行，非治理文件、非 CI/部署脚本、非 Agent 行为。
- 范围局部、单字符、可简单 revert；`risk_flags` 空。

### 缺失的 acceptance criteria 或决策

- 无。
