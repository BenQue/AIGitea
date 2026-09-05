---
issue: 222
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/222
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - authorization
  - platform-governance
depends_on: []
status: approved
branch: change/222-issue-list-state-set
created: 2026-09-05
updated: 2026-09-05
---

# Verification · #222

全部命令在 `change/222-issue-list-state-set` 的 worktree
`/private/tmp/issue-222-issue-list-state-set` 上执行，基线 `origin/main = a790c13`。
实机调用一律使用**候选 manifest**（仓库树里的这一份），不是已安装的那一份——
已安装 broker 的操作表还是 34 项，两台重装是人工交接项，见文末。

## 候选 manifest 的调用前缀

```bash
PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
  --access-manifest codex/config/host-access-broker.json \
  --governance-manifest codex/config/gitea-governance.json \
  broker --project aisoft-platform <操作与参数>
```

## 逐条验收

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 `gitea.issue.list` 合同 | PASS | `test-host-access-broker.sh` 断言 `{"name":"gitea.issue.list","identity_route":"project-agent","mutating":false,"arguments":["state"]}`；三个 state 取值实机各跑通一次 |
| AC-2 `gitea.issue.state.set` 可关可开，写入由受审计身份执行 | PASS | 见下方「写路径实机序列」与「审计姿态读回」 |
| AC-3 `--state all` 被拒 | PASS | `{"code": "ARGUMENT_INVALID", "message": "Issue state must be open or closed", "status": "BLOCKED_EXTERNAL"}`，零 HTTP 请求 |
| AC-4 分页取全、投影不含 body | PASS | `--state all` 实机取回 137 条，翻 3 页；`has body key: False` |
| AC-5 PR 条目不出现且排除数可读 | PASS | 见下方「PR 过滤」 |
| AC-6 操作数 34 到 36，smoke 全绿 | PASS | `validate` 读回 `operation_count: 36`；`bash codex/tests/smoke.sh` → `Ran 692 tests ... OK` + `Codex platform static smoke checks passed.` |
| AC-7 文档写明精确集合语义 | PASS | `06` §1.0 末段与踩坑表第 26 行；实测例子取自本文件的多传测试 |
| AC-8 候选 manifest 免重装验收 | PASS | 本文件所有实机行 |

## 合同读回

```
$ PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
    --access-manifest codex/config/host-access-broker.json \
    --governance-manifest codex/config/gitea-governance.json validate
{"contract_version": "host-access-broker/v1", "merge_operation_count": 1,
 "operation_count": 36, "project_count": 5, "status": "PASS"}
```

## 只读枚举实机

```
$ ... --operation gitea.issue.list --state open
count 6 · pull_requests_excluded 0
条目：#251 #246 #225 #222 #179 #178，各带 number/title/state/labels/created_at/updated_at
```

```
$ ... --operation gitea.issue.list --state all
state all  count 137  excluded 0
max number 254   min number 1   closed 131
has body key: False
```

**分页确实翻了页**：137 条 = 50 + 50 + 37，三页。

**PR 过滤**：仓库当前最大编号是 259（PR #259 是 #228 的合并 PR），而 `--state all`
返回的最大 Issue 编号是 254，PR #256/#259 等一条都不在结果里。服务端 `type=issues`
生效，因此 `pull_requests_excluded` 为 0；客户端的第二道过滤由单元测试
`test_issue_list_projects_and_excludes_pull_requests` 覆盖（构造一条 `pull_request`
非空的条目，断言它不进 `issues` 且计数为 1）。

## 写路径实机序列

用一次性 Issue，不动任何在途 Issue。创建（带 #243 要求的 `--entry-label`）：

```
$ ... --operation gitea.issue.create --title "test(#222): gitea.issue.state.set 验收用一次性 Issue" \
      --body "<说明这是 #222 验收产物>" --entry-label needs-analysis
{"number": 260, "state": "open", "title": "test(#222): gitea.issue.state.set 验收用一次性 Issue"}
```

对 #260 跑完整序列：

| 步骤 | 命令 | 读回 |
|---|---|---|
| 首次关闭 | `--operation gitea.issue.state.set --number 260 --state closed` | `state=closed changed=True` |
| 重复关闭（幂等） | 同上 | `state=closed changed=False` |
| 重开 | `--number 260 --state open` | `state=open changed=True` |
| 收尾关闭 | `--number 260 --state closed` | `state=closed changed=True` |

复核：`--state open` 的 6 条不含 #260；`--state closed` 的 132 条含 #260。
测试 Issue #260 停在 closed，不需要任何人处理。

**一处实测到的事实值得记住**：四次调用读回的 `updated_at` 完全相同
（`2026-09-05T21:49:30+08:00`），Gitea 在开闭变更上不动这个时间戳。
判断有没有真的发生写入**只能读 `changed`**，不能拿时间戳推断。这也是保留
`changed` 字段的直接理由，已写进 `06` §1.0。

## 审计姿态读回（AC-2 的兑现方式）

`host.access.audit` 是**姿态审计**，不是写入流水账；仓库里没有任何 broker 写入日志。
它核对的是执行这次写入的那个身份：

```
$ ... --operation host.access.audit
status: PASS
repository_permission: {"manager": "admin", "project_agent": "write"}
token_scopes.project_agent: ["read:user", "write:issue", "write:repository"]
```

`gitea.issue.state.set` 走 `project-agent` 路由，用的正是上面这条 scope 里的
`write:issue`；audit 在权限或 scope 与 manifest 不符时抛 `PERMISSION_MISMATCH`
或 `TOKEN_SCOPE_MISMATCH`，因此这次 PASS 就是「该写入由受治理、受核对的身份执行」的证据。
逐次状态变化的证据在 Gitea 的 Issue 时间线上，可由 `gitea.issue.read` 读回。

这一条是对 Issue 正文验收标准的**重述**，已在确认点 1 由人确认。

## 精确集合语义的实测（AC-7 的证据）

四次调用，两种失败码互不混淆：

| 调用 | 读回 |
|---|---|
| `gitea.issue.state.set --number 222 --state all` | `ARGUMENT_INVALID: Issue state must be open or closed` |
| `gitea.issue.state.set --number 222 --state closed --title x` | `ARGUMENT_MISMATCH` |
| `gitea.issue.list --state open --number 222` | `ARGUMENT_MISMATCH` |
| `gitea.issue.list`（不传 state） | `ARGUMENT_MISMATCH` |

第二、三行就是本 Issue 要写进文档的那一条：**多传也报 `ARGUMENT_MISMATCH`**。

## 自动化测试

| 命令 | 结果 |
|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_host_access.py'` | `Ran 179 tests ... OK` |
| `bash -n codex/tests/test-host-access-broker.sh` | 通过 |
| `bash codex/tests/test-host-access-broker.sh` | `host access broker shell and installer tests passed` |
| `bash codex/tests/smoke.sh` | `Ran 692 tests in 35.598s / OK` + `Codex platform static smoke checks passed.` |

新增单元用例 10 条，覆盖投影与 PR 排除、body 缺席、翻页、畸形条目 fail-closed、
参数精确集合（少传/多传/非法值）、关闭、重开、幂等无写入，以及
「`gitea.issue.update` 的三个参数不变，改标题不携带关闭的权力」。

## 踩坑 20 的六处同步点

| # | 位置 | 本次改动 |
|---|---|---|
| 1 | `contract.py` 的 `EXPECTED_OPERATIONS` | 两条，34 到 36 |
| 2 | `broker.py` dispatch | 两条校验分支 + 两条 helper 分派 + `_issue_projection`/`_issue_list`/`_set_issue_state` |
| 3 | `runner.py` | `issue_list()`、`issue_state_set()` |
| 4 | `codex/config/host-access-broker.json` | 两条 operations 条目 |
| 5 | `codex/runtime/tests/test_host_access.py` | 10 条新用例 + typed-fields 表两项 |
| 6 | `codex/tests/test-host-access-broker.sh` | `operation_count == 36`、`[.operations[].name] length == 36`、两条逐操作断言 |

**第七处不适用**：本次不新增 CLI 参数，`--number` 与 `--state` 已存在，
`test_cli_exposes_only_typed_issue_and_pull_fields` 逐字钉死的 `execute()` kwargs 不变。
该测试在上表第 5 行的 179 条里照常通过。

## 未执行项（人工交接）

- **两台重装 broker**：`sudo bash codex/install-host-access-broker.sh` 需在 **Mac 与
  gitea-ci VM 两台**执行，本会话无 sudo，**NOT RUN**。重装前
  `/usr/local/libexec/aisoft/host-access-broker --operation gitea.issue.list` 会返回
  `REQUEST_DENIED`——那是安装期操作表陈旧，不是权限问题（踩坑 20）。
  重装应在本 PR 合并且主 checkout `git merge --ff-only origin/main` 之后进行，
  否则 installer 会忠实地装旧 manifest 并报成功（踩坑 20 的 #162 变体）。
  重装后自检：`python3 -c 'import json;print(len(json.load(open("/usr/local/share/aisoft/host-access-broker.json"))["operations"]))'` 应读出 `36`。
- **调度会话改用列表枚举**：`skill-for-claude/issue-session-flow/SKILL.md:46` 写的是
  「`gitea.issue.list` 落地前（#222），用逐号 `gitea.issue.read` 从已知最大编号向下读……
  #222 合并后换成一次列表读取」。这两行在**本仓**，不是外部文件。本 PR **未改**：
  它是 Agent 行为文件，`AGENTS.md` 要求由映射的 spec 明确授权才能修改，而本次 spec
  没有授权它。作为遗留项交回，见 summary。

## 部署验收

不适用：本次变更不涉及部署或迁移。
