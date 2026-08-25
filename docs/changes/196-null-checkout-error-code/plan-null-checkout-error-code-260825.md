---
issue: 196
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/196
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - external-contract
  - shared-core
depends_on: []
status: approved
branch: change/196-null-checkout-error-code
created: 2026-08-25
updated: 2026-08-25
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 改动前 10 项目基线取证（已安装 broker + 候选 manifest 两轮） | - | done |
| T02 | 失败测试：`有凭据 + mac_checkout: null` → `TARGET_UNAVAILABLE`；以及该判定先于凭据解析 | T01 | done |
| T03 | `_onboarding_check` 判定上移 + 错误码改为 `TARGET_UNAVAILABLE`，测试转绿 | T02 | done |
| T04 | 改动后 10 项目复跑与前后对照，写入映射的 `verification` | T03 | done |

T01 必须先于 T03：基线只在改动前观测得到，合并后无法重放。

## Expected touch points

- T02/T03：`codex/runtime/aisoft_host_access/broker.py`（`_onboarding_check` 开头五行）、
  `codex/runtime/tests/test_host_access.py`（`HostAccessBrokerTests` 新增两个测试）。
- T01/T04：只读执行，无文件改动；产物落在 `verification`。
- 不触碰 `codex/config/host-access-broker.json`——本次不改任何声明。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli --access-manifest codex/config/host-access-broker.json --governance-manifest codex/config/gitea-governance.json --label-manifest codex/config/gitea-labels.json broker --project wmpda --operation host.onboarding.check`，比对 `_git` 路径同条件的 broker.py:1311 逐字一致 |
| AC-2 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access.HostAccessBrokerTests.test_null_mac_checkout_onboarding_check_is_target_unavailable`（先看着红，再看它绿） |
| AC-3 | `cd codex/runtime && PYTHONPATH=. python3 -m unittest discover -s tests -t tests` 全绿（含既有 `test_onboarding_check_combines_access_remote_and_repo_binding`）；并 review diff 确认 `mac_checkout` 非 null 时逐行未变 |
| AC-4 | 对 10 个项目各跑一次 `host.onboarding.check`，改动前后各一轮，结果写成对照表 |

补充闸门：`bash codex/tests/smoke.sh`。

## 部署与回滚

无部署。合并后本机 `/usr/local/libexec/aisoft/host-access-broker` 仍是安装期旧
runtime，需要独立授权的 `sudo bash codex/install-host-access-broker.sh` 才会生效；
该重装不属于本变更范围。回滚方式：`git revert`（无状态、无迁移）。
