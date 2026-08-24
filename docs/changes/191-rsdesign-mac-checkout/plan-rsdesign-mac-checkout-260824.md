---
issue: 191
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/191
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/191-rsdesign-mac-checkout
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan：rsdesign-new manifest checkout 对齐

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 改动前基线取证：10 个项目的 `host.onboarding.check` 原样输出，两个候选路径的 toplevel 与 remote 实况 | - | done |
| T02 | manifest `rsdesign-new` 条目：`mac_checkout` 指向真实 checkout、删除 `git_remote_name` | T01 | done |
| T03 | 两处测试断言集合由三项目减为两项目，测试全绿 | T02 | done |
| T04 | 用候选 manifest 复验 AC-1/AC-2：`mac.git.bind` 两次 + `host.onboarding.check` + `git.fetch.main` | T02 | done |
| T05 | 改动后 10 项目横向核对与 `verification` 记录 | T02, T04 | done |

## Expected touch points

- T02：`codex/config/host-access-broker.json`（`rsdesign-new` 条目两行）。
- T03：`codex/tests/test-host-access-broker.sh`（jq 断言）、
  `codex/runtime/tests/test_host_access.py`（`gitea_remote_projects` 集合）。
- T01/T04/T05：无源码改动，产出写进映射的 `verification`。
- 明确不触碰：`codex/runtime/aisoft_host_access/broker.py`、其他项目条目、任何 Git remote。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 候选 manifest 下 `broker --project rsdesign-new --operation host.onboarding.check` |
| AC-2 | `mac.git.bind` ×2 + `host.onboarding.check` + 在 `/Users/benque/Projects/rsdesign-new` 内 `git.fetch.main` |
| AC-3 | 10 项目 `host.onboarding.check` 改动前后两轮，逐项记入 `verification` |
| AC-4 | `git diff origin/main -- codex/runtime/aisoft_host_access/broker.py` 为空 |
| AC-5 | `bash codex/tests/test-host-access-broker.sh`、`python3 -m unittest codex.runtime.tests.test_host_access`、`bash codex/tests/smoke.sh` |
| AC-6 | 变更前后 `git -C <repo> remote -v` 对比（两个 checkout） |

## 部署与回滚

无应用部署。manifest 是安装期固定文件，合并后需人工重装两端
（`sudo bash codex/install-host-access-broker.sh`）才在 `/usr/local/share/aisoft/` 生效；
在此之前本次验收使用候选 manifest 直接调用 broker CLI，已在 `verification` 中标注两种来源。
回滚 = revert 单 PR + 重装。
