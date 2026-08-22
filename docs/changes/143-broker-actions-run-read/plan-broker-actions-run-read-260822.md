---
issue: 143
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/143
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - security
depends_on: []
status: approved
branch: change/143-broker-actions-run-read
created: 2026-08-22
updated: 2026-08-22
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 端点核实（本机 swagger）并写进 spec §2 | - | done |
| T02 | 操作表与参数校验：contract / manifest / CLI `--job` | T01 | done |
| T03 | `gitea.actions.run.read` 执行器与投影 | T02 | done |
| T04 | 脱敏与截断（`gitea.actions.job.logs.read`） | T02 | done |
| T05 | 单测与 shell 计数枚举点（27 → 29） | T03, T04 | done |
| T06 | 06 踩坑手册补记；真实数据验证与 verification | T05 | done |

## T02 — 枚举点

新增 typed 操作要同步的点（06 踩坑 20 的清单）：

1. `codex/runtime/aisoft_host_access/contract.py` 的 `EXPECTED_OPERATIONS`；
2. `codex/runtime/aisoft_host_access/broker.py` 的参数校验与 dispatch；
3. `codex/config/host-access-broker.json`；
4. `codex/runtime/tests/test_host_access.py` 的操作表；
5. `codex/tests/test-host-access-broker.sh` 的 `operation_count` 与 `[.operations[].name] | length`（**最容易漏**，漏了会让 `smoke.sh` 以零输出退 1）；
6. `codex/runtime/aisoft_host_access/cli.py`：新增 `--job`，并把它接进 `execute(...)` 的 `arguments` 字典——`supplied != set(operation.arguments)` 那条校验依赖它。

`runner.py` 不动（spec §9）。

## T03 — `run.read` 执行器

- `GET {repo_api}/actions/runs?head_sha={sha}&limit=50&page=N`，有界分页，比照 `_open_pulls` / `_issue_comments`；
- 对每个 run 再取 `{repo_api}/actions/runs/{id}/jobs`，同样有界分页；
- **投影而非透传**：上游 `ActionWorkflowRun` 内嵌完整 `Repository` 与两个 `User` 对象。原样倒出会让治理读接口的形状随上游变动，也多披露身份信息。保留 run 的 `id/workflow/event/head_branch/status/conclusion/started_at/completed_at/html_url`，job 的 `id/name/status/conclusion/started_at/completed_at/runner_name`，step 的 `number/name/status/conclusion`；
- 三层都补 `duration_seconds`（由 `started_at`/`completed_at` 计算，任一缺失则为 `null`）——「各步骤花多久」是 Issue 的原始疑问，让调用方自己去减时间戳等于把这个操作做了一半；
- 任一字段类型不符 → `RESPONSE_SCHEMA_INVALID`，与既有读操作一致。

## T04 — 日志

- `_request_text`：与 `_request_json` 同一条错误码路径，只是不做 JSON 解码；
- 先脱敏后截断。顺序重要：**先截断会让被截掉那半的凭据永远不被计数**，而 `redactions` 是给读者的信号；
- 脱敏规则见 spec §5.2，替换为 `[redacted]`；
- 截断取尾部 64 KiB，置 `truncated` / `original_bytes` / `returned_bytes`，正文前置一行显式标记。

## T05 — 测试

- 正向：SHA → run → job → step 投影正确，`duration_seconds` 计算正确；
- 空结果：`total_count: 0` 且 `runs: []`，与 BrokerError 明确不同形；
- 缩写 SHA / 非法 SHA → `ARGUMENT_INVALID`（无请求发出）；
- 日志：截断标记、`original_bytes`/`returned_bytes`、六类脱敏各一条负向断言（含「本次凭据明文」这一条）、40-hex 不被掩掉的正向断言；
- 钉住「不存在 Actions 写操作」的断言（比照 #138 对评论 update/delete 的处理）；
- project-scoped：断言请求 URL 由 `project.repository` 拼出。

## 回滚

`git revert` 单个 commit 即可回退代码与 manifest。**但已安装的 broker 不会因 revert 而回退**：安装的是 root-owned 快照，需重新运行 installer（自带 `.previous` 备份）。这一点写进 verification 的回滚段。

## 已知人工前置

合并后需在 Mac 与 gitea-ci VM 两台重装：

```
sudo bash <repo>/codex/install-host-access-broker.sh
```

VM 那台 agent 可自行执行（`orb -m gitea-ci sudo bash /mnt/mac/...`），Mac 那台必须由人执行。未重装时新操作返回 `REQUEST_DENIED`，读起来像权限问题——判别法是比对 `/usr/local/share/aisoft/host-access-broker.json` 的 `operations` 长度（旧 27 / 新 29）。
