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

# Implementation plan：actions 只读投影的两个假值

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 日志截断保留头尾两端，标注计入预算，单测覆盖头尾/上界/短日志 | - | pending |
| T02 | 零值时间戳投影为 `null`，`duration_seconds` 随之为 `null`，单测覆盖三态 | - | pending |
| T03 | 06 broker 段写明窗口与方向，踩坑表新增一行；用真实长 job 取证 | T01, T02 | pending |

T01 与 T02 相互独立，改的是同一文件的不同函数。T03 依赖两者，因为它记录的是它们的实测读数。

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/broker.py` 的 `LOG_MAX_BYTES` 邻近常数与
  `_actions_job_logs`；`codex/runtime/tests/test_host_access.py` 的截断相关测试。
- T02：同文件的 `_optional_text` / `_duration_seconds` 邻域与 `_actions_runs` /
  `_actions_jobs` 的时间戳投影点；同测试文件的 `_gitea_run` / `_gitea_job` 夹具与 run.read 测试。
- T03：`06-运维手册与踩坑集.md`；`docs/changes/225-actions-read-projection/verification-*.md`。

范围提示，不授权扩大 spec。特别地：`codex/config/host-access-broker.json` 不在触碰范围内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `test_actions_job_logs_read_keeps_both_ends`：断言头段首行与尾段末行同时出现 |
| AC-2 | 同上，断言 `returned_bytes <= 65536` |
| AC-3 | `test_actions_job_logs_read_leaves_a_short_log_untouched`（既有，须仍绿） |
| AC-4 | `test_actions_run_read_reports_no_duration_for_a_run_that_never_started` |
| AC-5 | `test_actions_run_read_projects_step_level_conclusions`（既有，须仍绿） |
| AC-6 | 上述三条 + `test_actions_run_read_reports_no_duration_for_a_running_run` |
| AC-7 | diff review：`06` broker 段与踩坑表 |
| AC-8 | 候选路径对 LocalWMS job 835（185378 字节）实读，比对头段可读的步骤名，记入 verification |
| AC-9 | `bash codex/tests/smoke.sh`；`git diff --stat` 不含 `host-access-broker.json` |

`python3 -m unittest` 跑 `codex/runtime/tests/test_host_access.py` 全量，
每个 ticket 结束都跑一次全量 `bash codex/tests/smoke.sh`。

AC-8 用候选路径实读，免两台重装：

```bash
PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
  --access-manifest codex/config/host-access-broker.json \
  --governance-manifest codex/config/gitea-governance.json \
  broker --project localwms --operation gitea.actions.job.logs.read --job 835
```

## 部署与回滚

无部署产物。但**生效需要两台重装**（Mac 与 gitea-ci VM 的
`/usr/local/libexec/aisoft/host-access-broker`），source 合并不改变 installed 字节。
重装不在本次交付内，作为人工交接项写进 verification 的未完成项，并在最终报告里点名。

回滚：revert 本 PR 即可。无状态、无迁移、无制品。
