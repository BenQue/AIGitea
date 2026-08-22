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
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/141
created: 2026-08-22
updated: 2026-08-22
---

# Verification · broker 补 gitea.issue.comments.read（#138）

环境：worktree `/private/tmp/issue-138-broker-issue-comments-read`，基线 `origin/main` = `760497e`。

## 1. 缺口复现（改动前）

```
$ host-access-broker --project localwms --operation gitea.issue.comment.list --number 6
{"code": "REQUEST_DENIED", "message": "requested operation is not allowlisted", "status": "BLOCKED_EXTERNAL"}
```

`gitea.issue.read --number 6` 返回 `"comments": 1`——计数有，正文无。匿名 API 对私有仓返回 `404`（属 `private-gitea-access` 的歧义证据，不构成「评论不存在」）。缺口成立。

## 2. 端到端：用它自己读回起因的那条评论

用本分支 runtime + 本分支 manifest（复刻已安装 wrapper 的调用形式）对**真实 Gitea** 执行：

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
    --access-manifest codex/config/host-access-broker.json \
    --governance-manifest codex/config/gitea-governance.json \
    --label-manifest codex/config/gitea-labels.json \
    broker --project localwms --operation gitea.issue.comments.read --number 6

评论条数 = 1
--- 3437 localwms-agent 2026-08-22T08:31:25+08:00
## 追加：请求体上的第二处值漂移（写 plan 时发现）
...
```

返回 1 条，等于 `gitea.issue.read` 报的 `comments` 计数。`author`、`created_at` 与 Gitea 页面一致；`body` 与人工逐字核对一致（该评论追加了 `batchSelectionMode` 的 `LOCKED` → `MES_LOCKED`，并记录 `lineDesiredState` 属功能缺口不在范围）。

投影生效：返回对象恰好 `id` / `author` / `created_at` / `body` 四个键，上游内嵌 user 的 `email`、`is_admin`、`avatar_url` 均未出现。

**这条评论正是本 Issue 的起因**——LocalWMS Issue #6 因读不到它而只能靠人工转述。用新操作把它读回来，是这个变更最直接的证明。

## 3. 被治理 guard 拦下一次（值得记录）

首轮 `smoke.sh` 退出 1，且**日志零错误输出**，最后一行是 `host-role installer tests passed`。`bash -x` 才定位到真凶：

```
+ jq -e '
  .operation_count == 26 and
  ...
' .../validate.json
```

`codex/tests/test-host-access-broker.sh` 把 operation 总数钉死在 26，我加了第 27 个。`jq -e` 断言失败时静默返回 1，叠加 `set -euo pipefail` 就成了无输出退出。

**这个 guard 是对的**：它保证没有任何 typed 操作能不经人显式改数字就进入治理操作表——正是本次这种「给 agent 加一条读路径」的变更最该被人看见的地方。代价是可诊断性差，`bash -x` 是唯一入口。

Issue #138 正文只点了两处枚举点（`test_host_access.py:114` 与 `:857`），**漏了这第三处**。spec §7 已把三处列全。

## 4. 对 Issue #138 验收标准的一处订正

正文写「缺 `--number`、`--number 0`、`--number -1` 均以 `ARGUMENT_INVALID` 拒绝」。实测 broker 区分两种失败：

| 输入 | 错误码 |
|---|---|
| 缺 `--number` | `ARGUMENT_MISMATCH` |
| `--number 0` / `-1` | `ARGUMENT_INVALID` |
| `--number 6 --comment x` | `ARGUMENT_MISMATCH` |

这个区分是既有且更好的（参数缺失 vs 参数值非法），`gitea.issue.labels.set` 缺 `lifecycle` 同样是 `ARGUMENT_MISMATCH`。因此**按实际行为落地并订正验收口径**，而不是为对齐一句话去改一个正确的机制。测试断言相应写成两段。

## 5. 测试

```
$ bash codex/tests/test-host-access-broker.sh
host access broker shell and installer tests passed          exit 0

$ bash codex/tests/smoke.sh                                   exit 0
Ran 462 tests in 33.207s
OK
```

`test_host_access.py` 由 81 → 86 个用例，新增 5 个：

| 用例 | 钉住什么 |
|---|---|
| `test_issue_comments_read_projects_and_is_number_bound` | 四字段投影；URL 精确；所有请求都是 GET（读不得改） |
| `test_issue_comments_read_pages_past_the_first_fifty` | 72 条跨两页全取回、顺序稳定；断言实际请求了 page=1,2 |
| `test_issue_comments_read_rejects_a_malformed_entry` | 缺 `body` 的上游条目 → `RESPONSE_SCHEMA_INVALID` |
| `test_issue_comments_read_takes_only_a_positive_number` | §4 的三种参数失败；且这些失败**一次网络请求都不发** |
| `test_comment_surface_has_no_typed_update_or_delete` | 操作表里不存在评论的 update/delete——防止日后「顺手补全 CRUD」 |

分页用例的 fixture 刻意带上 `assets`、`reactions`、内嵌完整 `user` 等噪声字段，这样投影一旦退化成透传就会立刻红。

## 6. 验收标准逐条核对

- [x] 返回评论数组含 `body`、作者、`created_at`，长度等于 `gitea.issue.read` 的 `comments` 计数（真实 Gitea 上 1 = 1）
- [x] 参数校验按 §4 订正后的口径；三种失败均不触网
- [x] 传写操作才有的 `--comment` → `ARGUMENT_MISMATCH`
- [x] 走 `project-agent` 且 `mutating=False`（shell jq 断言 + python 用例双重钉住）
- [x] `test_host_access.py` 的枚举断言同步；**并补上 Issue 正文漏掉的第三处**（`test-host-access-broker.sh` 的两处计数）
- [x] 未新增或放宽任何 token scope
- [x] `bash codex/tests/smoke.sh` 通过

## 7. 未做与后续

- **已安装的 broker 仍是旧版**。`/usr/local/libexec/aisoft/host-access-broker` 指向已安装的 runtime，本变更合并后需按平台既有方式重装，新操作才对日常会话可用。本 PR 只交付源码与测试，不执行安装。
- 评论的 update/delete 按 spec §4 刻意不做。
- PR review comment（`/pulls/{n}/reviews`）是不同端点与不同治理语义，不在本 Issue 范围。
