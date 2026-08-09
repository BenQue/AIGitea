---
issue: 67
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/67
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - security
  - external-contract
  - shared-core
  - platform-governance
depends_on:
  - 61
status: approved
branch: change/67
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

# Git credential protocol compatibility plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | strict scalar 与 ordered multi-valued protocol parser 及 unit/security regressions | - | completed |
| T02 | credential-helper/live-shape regression、runbook 与完整本地验证 | T01 | completed |
| T03 | 原子提交、受控 bootstrap push、唯一 PR 与 final-head remote gate | T01, T02 | in-progress |

## Tasks

### T01 — Parser and security matrix

- 先增加 live key shape positive fixture 和 scalar/multi-valued negative matrix，使 merged parser 重现失败。
- 抽取 credential protocol parser，分别返回唯一 scalar 与 ordered multi-valued values。
- 只允许四个 scalar；required scalar、identity/host/path/cross-project 检查保持原顺序与错误边界。
- 允许并忽略不影响 basic route 的合法 `key[]`；不把 multi-valued values 传给 resolver 或输出。

### T02 — Helper boundary and full verification

- 通过 synthetic resolver/identity verifier 覆盖 credential helper success，不访问真实 Keychain。
- shell negative tests 验证 malformed/unknown scalar 在 credential resolve 前返回脱敏 exit 20。
- 更新 `06-运维手册与踩坑集.md` 的 helper protocol/fail-closed 说明。
- 运行 focused unit、helper shell、完整 smoke、syntax/ShellCheck、JSON、Secret 与 diff checks；更新本目录
  verification，严格区分 candidate、live、remote CI 和 post-merge 状态。

### T03 — Delivery gate

- 复核 `change/67` 仅包含 spec 授权文件并创建原子 commit。
- 标准 fixed helper bootstrap push 失败时，仅用单进程 compatibility adapter 推送 exact
  `refs/heads/change/67`；adapter 不记录字段值/Secret，并在 verification 留证。
- 创建唯一 `Closes #67` PR，读回 base/head/files/merged 状态与 final-head status contexts。
- 停止在人工 merge gate；post-merge install/no-op/live push/read-back 只在人工 merge 后另行执行。

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/tests/test_host_access.py`。
- T02：`codex/tests/test-host-access-broker.sh`、`codex/tests/fixtures/host-access/`、
  `06-运维手册与踩坑集.md`、`docs/changes/67/`。
- T03：只更新 `docs/changes/67/` 的 handoff metadata/evidence；不修改 runtime contract。

以上位置是范围提示，不授权修改 root `AGENTS.md`、Issue #66 或其它项目。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2 | focused `HostAccessBrokerTests` scalar/multi-valued parser matrix |
| AC-3 | wrong protocol/host/path/username/cross-project unit negatives；断言 resolver 未调用 |
| AC-4, AC-5 | synthetic CLI `credential-helper get/store/erase` regression；Secret 只在 captured private pipe |
| AC-6 | `bash codex/tests/test-host-access-broker.sh` 的 early-fail helper negatives；live field-name-only probe evidence |
| AC-7 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_host_access -v`; `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/test-host-access-broker.sh`; `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`; `bash -n`; ShellCheck；JSON/Secret/diff checks |
| AC-8 | remote branch/PR/status/protection read-back；确认没有 merge/protection/ACL mutation |
| AC-9 | 合并前 `NOT RUN`；人工 merge 后 exact protected-main install/no-op 与 live Git canary evidence |

## 部署与回滚

本 PR 不部署。候选回滚为 revert。post-merge host helper 安装只允许从 exact merged protected-main
bytes 执行，并沿用 previous runtime/helper 回切；live canary 失败时停止并报告，不扩大权限。
