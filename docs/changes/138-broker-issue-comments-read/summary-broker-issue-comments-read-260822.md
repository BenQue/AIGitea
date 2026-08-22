---
issue: 138
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/138
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: pr-open
branch: change/138-broker-issue-comments-read
pr_url:
created: 2026-08-22
updated: 2026-08-22
reason: 变更 host-access broker 的 typed 操作表，属 Agent/治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-broker-issue-comments-read-260822.md
  spec: spec-broker-issue-comments-read-260822.md
  plan: plan-broker-issue-comments-read-260822.md
  verification: verification-broker-issue-comments-read-260822.md
---

## 问题/需求总结

typed 操作表里与 Issue 评论有关的只有 `gitea.issue.comment`——一个 `mutating=True` 的**写**操作。**没有任何 typed 操作能把评论读回来。** `gitea.issue.read` 只返回 `"comments": <int>` 计数，不含正文。

2026-08-22 在 LocalWMS Issue #6 上撞成实际阻塞：该 Issue 的验收标准分散在正文与一条评论两处，评论里追加了第二处合同漂移（`batchSelectionMode`）和一项明确排除（`lineDesiredState`）。agent 读不到评论，只能靠人在会话里口头转述，并在 verification 文档里写明「评论原文未能读取，需人工复核」。

一个由 agent 驱动 Issue→PR 的平台，读不到 Issue 的一半内容，是治理面的硬缺口——评论正是澄清、追加验收项、记录排除理由的地方。

## 影响范围

| 文件 | 变更 |
|---|---|
| `codex/config/host-access-broker.json` | 新增 `gitea.issue.comments.read` 条目（`mutating: false`，`arguments: ["number"]`） |
| `codex/runtime/aisoft_host_access/contract.py` | `EXPECTED_OPERATIONS` 新增同名条目 + 命名/无写对应物的理由注释 |
| `codex/runtime/aisoft_host_access/broker.py` | 参数校验分支 + 分派分支 + `_issue_comments` helper（分页 + schema 校验 + 字段投影） |
| `codex/tests/test-host-access-broker.sh` | `operation_count` 26 → 27（两处），并钉住新操作的 arguments 与 `mutating: false` |
| `codex/runtime/tests/test_host_access.py` | typed 元组表补一行；新增 5 个用例 |

CLI 无需改动：`--number` 早已存在，`--operation` 是自由文本并由 manifest 校验。**未新增或放宽任何 token scope**——`project-agent` 现有的 `write:issue` 已蕴含读。

## 初步方案与建议

只读孪生操作，与写操作共用 URL、只改 HTTP method，和 `gitea.issue.read`/`gitea.issue.update` 共用 `/issues/{number}` 完全同构。命名 `gitea.issue.comments.read` 依据 `contract.py` 已写明的约定（带 `issue.` 段=挂到某个 Issue；复数=集合），与 `gitea.issue.labels.read`/`gitea.issue.labels.set` 同型。

**不加 update/delete 评论的 typed 操作**——理由与 `gitea.labels.provision` 那条注释一致：改写或删除他人评论是人的决定，typed 化等于给出一条可自动化的抹除讨论记录的路径。

**响应做投影而非透传**：原始 Gitea comment 内嵌完整 user 对象、reactions、assets。原样倒出会让一个治理读接口的形状随上游 API 变动。只保留 `id`、`author`、`created_at`、`body` 四个字段——交付合同实际会读的东西。

## 风险

- **静默的枚举 guard**：`test-host-access-broker.sh` 用 `jq -e` 把 operation 总数钉死。它失败时零输出（`jq -e` 静默返回 1 + `set -e`），只有 `bash -x` 才定位得到。这是**刻意**的严格性——任何新增 typed 操作都不可能悄悄溜进治理面——但代价是可诊断性差。本次即被它拦住一次，已在 verification §3 记录。
- **分页**：评论数量无上界。只读第一页会让一段被截断的讨论看起来是完整的。已按 `_open_pulls` 的既有做法做有界分页（最多 100 页），超界抛 `RESPONSE_SCHEMA_INVALID` 而非静默截断。
- **投影丢字段**：若日后治理流程需要 `updated_at` 或 `html_url`，得再改一次。可接受——加字段是向后兼容的，而透传后再想收窄就是破坏性变更。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags: [agent-governance, platform-governance]
required_docs: [summary, spec, plan, verification]
override_reason: ''
```

`type/platform` 本身即强制 complex；`agent-governance` 与 `platform-governance` 两个风险标签同样强制。`contract_effect: add`——新增操作，既有 26 个操作的行为一字未变。

## 结论

新增 `gitea.issue.comments.read`，operation 表 26 → 27。已用本分支的 runtime 对真实 Gitea 端到端验证：成功读回 LocalWMS Issue #6 的那条评论，正文与人工核对逐字一致。`codex/tests/smoke.sh` 通过，python 单测 86 pass。
