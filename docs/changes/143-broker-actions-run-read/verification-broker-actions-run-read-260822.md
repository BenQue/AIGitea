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

# Verification

## 环境与版本

- Gitea: `GET /api/v1/version` → `{"version":"1.26.4"}`，`environment = local-orbstack`
- 调用形式：本分支 runtime + 本分支 manifest，复刻已安装 wrapper 的调用形式（与 #138 verification 同法）
- **已安装的 broker 仍是旧版**：`/usr/local/share/aisoft/host-access-broker.json` 的 `operations` 长度为 27，源码为 29。本 PR 只交付源码与测试，不执行安装

## 1. 端到端：回答 Issue 的原始疑问（run 493）

Issue 的判据是「对 `admin/LocalWMS` 的 run 493 取出步骤级结论，据此给出『那 8 个步骤是否都执行了』的结论」。

run 493 由 `90ca1f945bf7a35939cad8b5298222b538864550`（`docs(change-16): rebase 到 398c92f 后复跑`）触发：

```
$ … broker --project localwms --operation gitea.actions.run.read \
    --sha 90ca1f945bf7a35939cad8b5298222b538864550

run 493 completed/success 17s
  job 493 test success 17s
     0 success      1s  Run actions/checkout@v4
     1 success      0s  Verify runtime
     2 success      2s  Install dependencies
     3 success      0s  Typecheck
     4 success      1s  OpenAPI lint and contract drift gate
     5 success      1s  Error-code registry and dependency audit
     6 success     11s  Tests on ephemeral PostgreSQL 17
     7 success      0s  Assert no residue
```

**结论：8 个步骤全部执行，无一 `skipped`，无一缺失。** 17 秒的构成也一并可读：11s 是 ephemeral PostgreSQL 17 上的 218 条测试，2s 是依赖安装，两道合同/审计闸门各 1s。

LocalWMS #5 / #11 / #16 三次 verification 里那条重复了三遍的「未能进一步核实」，到这里才第一次变成可核实的——不是因为数字变了，而是因为终于有手段去看。

顺带说明为什么这次拿的是 493 而不是别的：同一个 PR #17 的后续 commit `faa8cf5…` 触发了 run 494（同样 8 步、同样 17s）。SHA 键控的代价是「要读哪次运行，就得给出那次运行的 commit」——对刚推完的分支这不成问题，对翻旧账则需要先从 git 历史里找出那个 commit。这是 spec §4 选择 SHA 入参时接受的代价，此处如实记录。

## 2. 端到端：日志读，且掩掉了一个**真实**凭据

```
$ … broker --project localwms --operation gitea.actions.job.logs.read --job 493
{'job': 493, 'original_bytes': 65378, 'returned_bytes': 65378,
 'truncated': False, 'redactions': 1}
```

那一次脱敏命中的是：

```
[command]/usr/bin/git config --local http.http://localhost:3000/.extraheader \
  AUTHORIZATION: basic [redacted]
```

这是 `actions/checkout@v4` 注入的 base64 凭据。**Gitea 自己没有掩它**——它不是注册过的 Actions secret，而是 runner 自动生成的 token。spec §5.1 说第二层存在的理由是「覆盖第一层结构上覆盖不到的东西」；这是它在真实日志里的第一个实例，不是构造出来的。

日志正文正确、可读：首行是 runner 版本与任务号，末行是 `Job succeeded`。

### 2.1 六类脱敏的负向验证

真实日志只能自然命中其中一类，其余五类用单测断言（`test_actions_job_logs_read_redacts_credentials`）：在日志里放入可识别的假凭据，逐条确认返回中不以明文出现——`Authorization` 头值、URL userinfo、`NPM_TOKEN=` 赋值、`ghp_` 前缀 token、PEM 私钥块，以及**本次请求所用凭据的明文**。

同一条测试反向断言：裸 40 位 commit SHA **必须**原样保留。这是 spec §5.3 记录过的裁决——掩掉它会让日志失去最有用的字段，换一个假想的收益。

## 3. 空结果与读取失败可判读地分开

```
$ … --operation gitea.actions.run.read --sha 588cd93efb1db9251549c287439ddb106026db9b
{"runs": [], "sha": "588cd93…", "total_count": 0}                    exit 0

$ … --operation gitea.actions.run.read --sha eeeeeeee…(全 e，不存在的 commit)
{"runs": [], "sha": "eeeeeeee…", "total_count": 0}                    exit 0

$ … --operation gitea.actions.run.read --sha 90ca1f9        （缩写）
{"code": "ARGUMENT_INVALID",
 "message": "Actions run read requires an exact lowercase SHA-1",
 "status": "BLOCKED_EXTERNAL"}                                        exit 20
```

空结果与错误在结构上完全不同形（前者有 `runs`/`total_count`，后者有 `code`/`status`），读者不需要靠猜。

### 3.1 纠正 Issue 的一处前提

Issue 正文把 `gitea.commit.status.read` 在缩写 SHA 上返回 `statuses: []` 称为「假成功」的反面教材。**实测不成立**——对**已安装的**旧版 broker 执行：

```
$ /usr/local/libexec/aisoft/host-access-broker --project localwms \
    --operation gitea.commit.status.read --sha 90ca1f9
{"code": "ARGUMENT_INVALID", "message": "commit status requires an exact lowercase SHA-1", ...}
```

该操作早已有同一条精确 SHA 校验。本变更沿用既有规则，不把一个已被修掉的问题记成自己的功劳。spec §4.1 已相应改写。

## 4. 只读与 project-scoped

- manifest 里两个新操作 `mutating: false`；`test-host-access-broker.sh` 新增断言：所有 `gitea.actions.*` 均 `mutating == false`，且整张操作表中不存在名字含 `rerun`/`dispatch`/`cancel` 的项；
- `test_actions_surface_has_no_typed_write` 逐个钉住五个不该存在的写操作名；
- `test_actions_run_read_is_project_scoped_and_sha_keyed` 断言请求 URL 由 `project.repository` 拼出（`/repos/admin/aisoft-platform/actions/runs?head_sha=…`）。别的仓库的 job id 打到本项目 URL 上得到 `HTTP_404`（`test_actions_job_logs_read_surfaces_an_unknown_job_as_a_failure`）。

## 5. 截断

- 上限 64 KiB，与 `verifier.py` 既有的输出截断上限同一个数字；
- `test_actions_job_logs_read_marks_truncation_instead_of_hiding_it`：断言 `truncated` 为真、`original_bytes` 等于原始长度、首行含截断标记，且**尾部内容仍在**（失败步骤的报错打印在最后，头部截断会正好丢掉要看的东西）；
- 真实 job 493 的日志 65378 字节，恰好未触发截断，因此真实数据这一侧只验证了未截断路径；截断路径由单测覆盖；
- spec §6.1 已写明一个诚实的边界：截断发生在读完整个响应体之后，它限制的是**进入 agent 上下文**的体量，不是 broker 进程的峰值内存。

## 6. 测试与枚举点

```
$ PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access
Ran 98 tests   OK

$ bash codex/tests/test-host-access-broker.sh
host access broker shell and installer tests passed

$ bash codex/tests/smoke.sh
Codex platform static smoke checks passed.   (exit 0)
```

操作计数 27 → 29，同步的枚举点：`contract.py` 的 `EXPECTED_OPERATIONS`、`broker.py` 校验与 dispatch、`codex/config/host-access-broker.json`、`test_host_access.py` 的操作表、`test-host-access-broker.sh` 的 `operation_count` 与 `[.operations[].name] | length`、`cli.py` 的 `--job`。

**发现第七处枚举点**（06 踩坑 20 原记六处）：`test_host_access.py` 的 `test_cli_exposes_only_typed_issue_and_pull_fields` 把 `execute()` 的完整 kwargs 逐字钉死，新增 typed **参数**（不只是新增操作）必须同步，否则以「expected call not found」失败。#138 只加操作不加参数，所以没碰到。已写进 06 踩坑 20。

## 7. 未能进一步核实

- **截断路径的真实数据**：手上没有超过 64 KiB 的 job 日志（job 493 是 65378 字节，差 158 字节）。构造一个需要往目标仓 workflow 里加输出，而「不碰 `.gitea/workflows/`」是本 Issue 明确的范围外。
- **已安装 broker 上的行为**：本 PR 未安装。合并后需在 Mac 与 gitea-ci VM 两台执行 `sudo bash codex/install-host-access-broker.sh`，Mac 那台需要人输密码。判别是否已生效：

```bash
python3 -c "import json;print(len(json.load(open('/usr/local/share/aisoft/host-access-broker.json'))['operations']))"
```

旧版 27，装好后应为 29。未重装时新操作返回 `REQUEST_DENIED: requested operation is not allowlisted`，读起来像身份/权限配置错误，实际只是安装快照落后（06 踩坑 20）。

## 回滚

`git revert` 单个 commit 即可回退源码与 manifest。**但已安装的 broker 不会因 revert 而回退**——安装的是 root-owned 快照，需重新运行 installer（自带同名 `.previous` 备份，二次运行输出 `already current (no-op)`）。本 PR 尚未安装，所以当前不存在需要回滚的安装态。
