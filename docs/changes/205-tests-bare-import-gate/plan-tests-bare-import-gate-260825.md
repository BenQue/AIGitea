---
issue: 205
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/205
change_type: test
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: contract-drafting
branch: change/205-tests-bare-import-gate
created: 2026-08-25
updated: 2026-08-25
---

# Implementation plan：tests 目录内裸模块名互导的回归闸门

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 在**未改动的** `d8e2f97` 上取基线：不带 `-t` 与带 `-t` 两次 discover 的测试 ID 集合逐条对比 | - | done |
| T02 | `codex/tests/smoke.sh` 的 discover 加 `-t "$ROOT/codex/runtime"`，附解释性注释 | T01 | done |
| T03 | 新增 `codex/runtime/tests/test_import_hygiene.py`：AST 扫描闸门 + 扫描器自测 | - | done |
| T04 | 故意红／恢复绿的现场对比，写进 verification | T02, T03 | done |

T01 必须在 T02 之前执行且必须在**同一 commit** 上取两次读数——`-t` 一旦落地，
「不带 `-t` 会发现什么」就无法在同一棵树上重放，AC-3 的对比基线就丢了。

## Expected touch points

- T02：`codex/tests/smoke.sh`（只改 discover 那一条调用及其上方注释）。
- T03：`codex/runtime/tests/test_import_hygiene.py`（新增）。
- T04：`docs/changes/205-tests-bare-import-gate/verification-tests-bare-import-gate-260825.md`。
- **零 touch**：`codex/runtime/tests/` 下任何既有文件（AC-4 的可机检形式）。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 改回裸名后 `bash codex/tests/smoke.sh`；断言 exit≠0 且输出含「裸模块名互导」与违规 `file:line` |
| AC-2 | 恢复包路径后 `bash codex/tests/smoke.sh`；断言以 `Codex platform static smoke checks passed.` 结束 |
| AC-3 | 同一 commit 上两次 `python3 -m unittest discover -v`（带／不带 `-t`），提取测试 ID、去掉 `tests.` 前缀后 `diff` |
| AC-4 | `git diff --stat` 复核：既有测试文件不出现在 diff 里 |

## 部署与回滚

无部署影响。回滚为纯 revert（撤 `smoke.sh` 的 `-t` 与新增测试文件），无状态、无迁移、
不触及任何主机侧对象。
