---
issue: 225
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/225
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
depends_on: []
status: approved
branch: change/225-actions-read-projection
created: 2026-09-05
updated: 2026-09-05
---

# Verification：actions 只读投影的两个假值

## 基线与范围

- Commit SHA：本 change 分支，见 PR diff
- 基线：`origin/main` = `af15294`
- 环境：Mac 本机 checkout `/private/tmp/issue-225-actions-read-projection`，
  实机 Gitea `gitea-ci.orb.local:3000`（真实 job 与 run 读数走这里）
- 本记录负责证明的 acceptance criteria：AC-1 到 AC-9

**改动前后的对照读数是本文件存在的理由。** installed broker 的旧行为在两台重装之后就不可复现，
而重装恰恰是本次唯一的人工交接项。

**双路径说明。** `installed` 指两台机器上已安装的 `/usr/local/libexec/aisoft/host-access-broker`
（本次改动**尚未**重装，因此它读出的就是改动前的行为）；`candidate` 指本 change 分支的 source：

```bash
PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
  --access-manifest codex/config/host-access-broker.json \
  --governance-manifest codex/config/gitea-governance.json \
  broker --project <id> --operation <op> ...
```

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access` | PASS | `Ran 185 tests ... OK`（改动前 182） |
| `bash codex/tests/smoke.sh` | PASS | `Ran 698 tests in 42.802s ... OK` / `Codex platform static smoke checks passed.` |
| 反向证明：把截断改回只留尾部，跑两条新日志测试 | 按预期红 | `AssertionError: 'checked out 0123…' not found in '[truncated: 254555 leading bytes omitted]…'`；`AssertionError: 65578 not less than or equal to 65536`；`FAILED (failures=2)` |
| 反向证明：把三处投影点改回 `_optional_text`，跑三条新 duration 测试 | 按预期红 | `AssertionError: '1970-01-01T08:00:00+08:00' is not None` ×2、`AssertionError: '0001-01-01T00:00:00Z' is not None`；`FAILED (failures=3)` |
| `git diff --stat` | 只碰三个文件 | `06-运维手册与踩坑集.md`、`broker.py`、`test_host_access.py`；`host-access-broker.json` **未出现** |
| 操作表未动 | PASS | `operations 36 projects 5`，与基线一致 |

反向证明里 running 那一条只在 `started_at`/`completed_at` 断言上红，**`duration_seconds`
在旧代码下本来就是 `None`**——这正面证实了归因：running 一直是对的，漏网的只有「从未开始」。

### 日志截断：installed vs candidate 逐 job 对照

| job | 仓库 | original_bytes | installed returned | candidate returned | candidate 标注行 |
|---|---|---|---|---|---|
| 835 | LocalWMS | 185378 | 65577（超窗 41 字节） | **65532** | `[truncated: 119942 bytes omitted between the leading 16359 bytes and the trailing 49077 bytes]` |
| 1031 | LocalWMS | 272578 | 65578（超窗 42 字节） | **65534** | 同形态 |
| 426 | NewEMaint | 63799 | 63799（未截断） | 63799（未截断） | 无 |

`16359 + 49077 + 119942 = 185378 = original_bytes`，三个数字与原始长度自洽。

### AC-8：真实长 job 的靠前步骤 stdout 可读

对象是 **LocalWMS job 835**——Issue 正文点名的那一次失效（`admin/LocalWMS` PR #195 的 run 835，
185378 字节，`Check out merge preview` 的 SHA 输出丢失）。

installed 路径读出的第一行与全文检索：

```text
first line: [truncated: 119843 leading bytes omitted]
"merge-preview" 出现次数: 0
"已检出 SHA" 出现: False
```

candidate 路径的头段（省略标注在第 205 行，头段共 205 行）实际内容：

```text
2026-08-29T04:29:47.8861355Z gitea-ci-runner(version:v1.0.7) received task 815 of job test, be triggered by event: pull_request
2026-08-29T04:29:49.4708486Z Run Main actions/checkout@v4
2026-08-29T04:29:50.1688690Z HEAD is now at a9abe9f docs(change-193): 回填 pr_url 与 status: pr-open
2026-08-29T04:29:50.1711442Z a9abe9f5af69ca0dd6155c9ce9a40c749b0baefc
2026-08-29T04:29:50.1748296Z   MERGE_PREVIEW_HEAD_SHA: a9abe9f5af69ca0dd6155c9ce9a40c749b0baefc
2026-08-29T04:29:50.2074894Z [merge-preview] PR head = a9abe9f5af69ca0dd6155c9ce9a40c749b0baefc
2026-08-29T04:29:50.2075206Z [merge-preview] base main 当前尖端 = 0f5d9c886cde43ca345ed93d56e6a4b0b5ac870b
2026-08-29T04:29:50.2084800Z [merge-preview] 已检出 SHA = a9abe9f5af69ca0dd6155c9ce9a40c749b0baefc
```

尾段末三行仍是 job 结束处，即失败摘要所在的那一段没有被牺牲：

```text
2026-08-29T04:30:28.0004319Z Success - Post actions/checkout@v4
2026-08-29T04:30:28.0005426Z Cleaning up container for job test
2026-08-29T04:30:28.1237840Z Job succeeded
```

**Issue 说「永远读不到」的那一行现在读得到**，而且头段 16359 字节装下了从 runner banner
一路到整个 `Check out merge preview` 步骤，仍有余量。

### AC-4/AC-5：run 时长的真实读数

Issue 评论点名的两条 run，candidate 路径实读：

| run | status | conclusion | started_at | completed_at | duration_seconds（installed → candidate） |
|---|---|---|---|---|---|
| 1016 | completed | cancelled | `null`（原 `1970-01-01T08:00:00+08:00`） | `2026-09-04T19:50:54+08:00` | **1788522654 → `null`** |
| 1007 | completed | cancelled | `null`（原 `1970-01-01T08:00:00+08:00`） | `2026-09-04T14:32:21+08:00` | **1788503541 → `null`** |
| 1031 | completed | success | `2026-09-05T09:20:51+08:00` | `2026-09-05T09:21:59+08:00` | **68 → 68（不变）** |

run 1016 / 1007 的 sha 分别是 `cae03012013d5e8572fcf664302cb86c646df3a4` 与
`a280c49a94789c34ac27221347be5df3b4cd3915`（`gitea.actions.run.read` 以 sha 为键，不接受 run id）。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 头尾双端 + 中间标注 | PASS | job 835/1031 的标注行；`test_actions_job_logs_read_keeps_both_ends_of_a_long_log` |
| AC-2 `returned_bytes ≤ 65536` | PASS | 65532 / 65534（旧为 65577 / 65578）；`test_actions_job_logs_read_stays_inside_the_window_it_declares` |
| AC-3 未截断日志逐字不变 | PASS | NewEMaint job 426 的 installed 与 candidate `log` 字符串**逐字相等**（程序比对 `True`） |
| AC-4 零值时间戳投影为 `null` | PASS | run 1016 / 1007 实读；三条单测 |
| AC-5 已完成取值不变 | PASS | run 1031 的三个字段与 installed 读数一致；`test_actions_run_read_projects_step_level_conclusions` 仍绿 |
| AC-6 三态单测 | PASS | `..._for_a_run_that_never_started`（cancelled-before-start）、`..._for_a_running_run`（running）、`test_actions_run_read_projects_step_level_conclusions`（completed）；另有 `..._rejects_the_other_zero_clock_gitea_emits` |
| AC-7 文档 | PASS | `06` broker 段「五条要点」第 3、4 条；踩坑表第 27 行 |
| AC-8 真实长 job 靠前步骤可读 | PASS | 上一节，job 835 |
| AC-9 不改 `arguments`，smoke 全绿 | PASS | `operations 36`，`git diff --stat` 不含 manifest；smoke 698 绿 |

## 遗留风险与未完成项

- **两台重装未执行（人工交接项）。** source 合并不改变 installed broker 的字节。
  Mac 与 gitea-ci VM 的 `/usr/local/libexec/aisoft/host-access-broker` 各自重装之前，
  实机调用仍是旧行为：日志只有尾部、`duration_seconds` 在从未开始的 run 上仍是 epoch。
  本文件所有 candidate 读数都是 source 路径的实测，**不构成 installed 生效证据**（`06` 踩坑 20）。
  重装完成后建议对 job 835 与 run 1016 各重跑一次 installed 路径回读。
- **LocalWMS #193 的 tee + 末尾重印绕法保持原样。** 它在两台重装之前仍是该项目唯一可用的手段；
  是否撤掉是 LocalWMS 自己的决定，不在本次范围。
- 头尾配比 1:3（头段占窗口四分之一）是按当前 CI 日志形态裁的。若将来出现头段超过 16 KiB 的工作流，
  调整点是单一常数 `LOG_HEAD_DIVISOR`，不需要改结构。
