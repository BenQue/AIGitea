---
issue: 227
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/227
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: approved
branch: change/227-bootstrap-test-bounded-wait
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan: 227 有界失败

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | mock `curl` 精确分派与有界 stdin 读取，消除已复现的无界等待 | - | pending |
| T02 | 脚本级看门狗与注入挂起的自检用例，覆盖任何失败路径 | T01 | pending |
| T03 | 稳定性重跑与等待点盘点，产出 verification | T02 | pending |

## Expected touch points

- T01：`codex/tests/test-bootstrap-gitea-service-account.sh` 的 mock `curl` heredoc。
- T02：同一文件顶部（看门狗）与尾部（自检用例）。
- T03：`docs/changes/227-bootstrap-test-bounded-wait/verification-bootstrap-test-bounded-wait-260905.md`。

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 容器内 `mkfifo` 与进程替换的 `/proc/PID/stack` 对照；`strace -e trace=openat`；抽出 mock `curl` 以第三个用户名调用并 `timeout 8` 观测返回码 124 |
| AC-2 | 抽出改后的 mock `curl`，以未知 URL 调用，断言非零退出且 stderr 含 `MOCK_CURL_UNEXPECTED_URL`，且不阻塞 |
| AC-3 | 抽出改后的 mock `curl`，以 `/api/v1/user` 调用但不给 stdin 对端，断言在上界内非零退出且含 `MOCK_CURL_MISSING_CONFIG_STDIN` |
| AC-4 | 脚本内自检用例：注入挂起并把上界压到数秒，断言有界非零退出且含 `AISOFT_TEST_DEADLINE_EXCEEDED`；正常路径 20 次重跑不触发 |
| AC-5 | `docker run ... bash -c 'for i in $(seq 1 20); do ...'`；本机 `bash codex/tests/test-bootstrap-gitea-service-account.sh`；`bash codex/tests/smoke.sh`；`shellcheck` |
| AC-6 | verification 文档中的等待点表 |

## 部署与回滚

无部署影响。回滚为 `git revert` 单一 commit。
