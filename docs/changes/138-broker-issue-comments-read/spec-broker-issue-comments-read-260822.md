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
---

# Spec · broker 补 gitea.issue.comments.read（#138）

## 目标

让 agent 能通过 broker 的 typed 操作读回一个 Issue 的评论，从而使「验收标准分散在正文与评论两处」的 Issue 可被完整消费。

非目标：评论的 update/delete（见 §4）；评论的搜索或跨 Issue 聚合；PR review comment（不同端点、不同治理语义）。

## 1. 操作定义

```python
"gitea.issue.comments.read": ("project-agent", False, ("number",)),
```

| 维度 | 取值 | 依据 |
|---|---|---|
| identity_route | `project-agent` | 与 `gitea.issue.read`、`gitea.issue.labels.read` 一致；这是项目级读 |
| mutating | `False` | 纯读，不进 mutation 审计路径 |
| arguments | `("number",)` | 与 `gitea.issue.labels.read` 完全同型 |
| HTTP | `GET {repo_api}/issues/{number}/comments?limit=50&page=N` | 与写操作 `gitea.issue.comment`（POST 同一 URL）共用端点 |

**token scope 不变。** `project-agent` 现有 scope 为 `read:user` / `write:issue` / `write:repository`，Gitea 的 `write:issue` 已蕴含读。这是刻意的：一个只读操作不该成为放宽凭据的理由。

## 2. 命名

`contract.py` 里已写明的约定有两条：带 `issue.` 段的是「挂到某个 Issue 上」（对比 `gitea.labels.read` 是「定义仓库级标签」）；集合用复数。既有的 `gitea.issue.labels.read` / `gitea.issue.labels.set` 就是这个模式。

因此：

- `gitea.issue.comment`（**单数**，保持不变）= 发一条评论；
- `gitea.issue.comments.read`（**复数**）= 读评论集合。

单复数在这里承载语义，不是随手写的。

## 3. 响应形状：投影而非透传

原始 Gitea comment 对象包含 `id`、`body`、`created_at`、`updated_at`、`html_url`、`issue_url`、`assets`、`reactions`，以及一个内嵌的完整 `user` 对象（含 `email`、`avatar_url`、`is_admin`…）。

本操作返回**投影后**的数组，每项恰好四个字段：

```json
{"id": 3437, "author": "localwms-agent", "created_at": "2026-08-22T08:31:25+08:00", "body": "..."}
```

三条理由：

1. **形状稳定性**——透传会让一个治理读接口的形状随上游 Gitea 版本变动；投影把它钉住；
2. **最小披露**——内嵌 user 对象带 `email` 与 `is_admin`，评论正文本身不需要这些；
3. **可收窄性**——日后加字段是向后兼容的；先透传再想收窄则是破坏性变更。

`_issue_comments` 对每一项做 schema 校验（`id` 为非 bool 的 int、`body`/`created_at` 为 str、`user.login` 为 str），不合抛 `RESPONSE_SCHEMA_INVALID`，与 `_issue_labels` 的既有做法一致。

## 4. 刻意不做 update / delete

`contract.py` 给 `gitea.labels.*` 写的那条注释确立了原则：**「retiring a label is a human migration decision, and a typed delete would make it silently automatable」**。改写或删除他人评论比退休一个标签更重——评论是讨论与决策的记录。因此本操作只有 read 一半，没有写回的另一半（发新评论仍走既有的 `gitea.issue.comment`）。

测试 `test_comment_surface_has_no_typed_update_or_delete` 把这条钉住，防止日后有人「顺手补全 CRUD」。

## 5. 分页

评论数量无上界。按 `_open_pulls` 的既有做法：`limit=50` 逐页取，取到不足 50 条即返回；扫到第 100 页仍未结束则抛 `RESPONSE_SCHEMA_INVALID`。

**不接受只读第一页**：一段被截断的讨论看起来和完整讨论毫无区别，而本操作存在的全部理由就是"别漏掉评论里的验收项"。静默截断会精确地重现它要解决的那个 bug。

## 6. 参数校验

- 缺 `--number` → `ARGUMENT_MISMATCH`（typed 元组要求它）；
- `--number 0` / 负数 → `ARGUMENT_INVALID`（`_positive_number`）；
- 传 `--comment`（属写操作那一半）→ `ARGUMENT_MISMATCH`。

> **对 Issue #138 正文的一处订正**：正文的验收标准写成「缺 `--number`、`--number 0`、`--number -1` 均以 `ARGUMENT_INVALID` 拒绝」。实际 broker 把「参数缺失」与「参数值非法」区分为两个错误码，且这个区分是既有且更好的——`gitea.issue.labels.set` 缺 `lifecycle` 同样是 `ARGUMENT_MISMATCH`。因此按实际行为落地并订正验收口径，而不是为了对齐一句话去改一个正确的机制。

## 7. 枚举点

新增一个 typed 操作要同步**三处**枚举，不是两处（Issue 正文只点了两处）：

| 位置 | 内容 |
|---|---|
| `codex/config/host-access-broker.json` | 安装期 manifest 的 operations 数组 |
| `codex/runtime/aisoft_host_access/contract.py` | `EXPECTED_OPERATIONS`（manifest 与运行时的一致性校验源） |
| `codex/tests/test-host-access-broker.sh` | `operation_count == 26` 与 `[.operations[].name] | length == 26` 两处 jq 断言 |

第三处是治理 guard：它保证没有任何 typed 操作能不经人显式改数字就进入操作表。本次即被它拦住一次（见 verification §3）。

## 8. 验收口径

- `--operation gitea.issue.comments.read --number N` 返回投影后的评论数组，长度等于 `gitea.issue.read` 的 `comments` 计数；
- 超过 50 条时正确翻页，不静默截断；
- 上游返回缺字段的条目时抛 `RESPONSE_SCHEMA_INVALID`；
- 参数校验按 §6（含订正后的错误码）；
- 该操作 `mutating=False` 且走 `project-agent`；
- 不存在 typed 的评论 update/delete；
- 未新增或放宽 token scope；
- `operation_count` 为 27；
- `bash codex/tests/smoke.sh` 通过；python 单测全绿。
