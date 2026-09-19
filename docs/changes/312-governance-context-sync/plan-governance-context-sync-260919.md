---
issue: 312
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/312
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
depends_on: []
status: contract-drafting
branch: change/312-governance-context-sync
created: 2026-09-19
updated: 2026-09-19
---

# Implementation plan：#312

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | pilot 声明改成多 context 并与 `status_check_contexts` 有序相等，manifest 同步 `mobile-verify`，合同能加载 | - | pending |
| T02 | 治理合同测试覆盖多 context 与不一致拒绝两条路径 | T01 | pending |
| T03 | 06 文档写入 required context 增删顺序与本例 | - | pending |
| T04 | Mac 侧重装 broker 配置，四个项目 audit 读回并记录 verification | T01, T02 | pending |

T01 与 T02 之间不拆 commit 边界之外的依赖：T01 改完合同即可本地加载，T02 把行为钉死。T04 需要
负责人在确认点 1 一并授权（重装是主机状态变更）。

## Expected touch points

- T01：`codex/config/gitea-governance.json`（NewEMaint 条目）、
  `codex/runtime/aisoft_gitea_governance/contract.py`（`RoutineLivePilot` 数据类、`_exact_keys`
  键集合、两条 `_require`）。
- T02：`codex/runtime/tests/test_gitea_governance.py`。
- T03：`06-运维手册与踩坑集.md`（§1.2 新增小节 + 踩坑表新增一行，号取 32）。
- T04：`docs/changes/312-governance-context-sync/verification-governance-context-sync-260919.md`。

范围提示，不授权扩大 spec。若实现中发现 `required_context` 还有第四个读者，停下来报告而不是顺手改。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `host-access-broker --project newemaint --operation host.access.audit`；`--operation gitea.protection.read` 后与 manifest 的 `status_check_contexts` 排序比对 |
| AC-2 | `bash codex/tests/smoke.sh`；`PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_gitea_governance`（按仓内既有跑法）；新增用例 review |
| AC-3 | `06-运维手册与踩坑集.md` diff review：顺序、后果、日期 2026-09-19 三者齐备 |
| AC-4 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`；`codex/tools/apply-classification-labels.sh --verify 312`；verification 文档中的四项目 audit 表 |

反向证明（写进 verification，改动前才观测得到）：

- 只往 manifest 加一条 context、不动 `contract.py`，`load_contract` 报
  `routine_live_pilot requires one exact status context`。本会话已在 scratch 副本上跑到这条输出。
- 改完之后把 `required_contexts` 故意写成只剩一条，`load_contract` 必须拒绝。

## 部署与回滚

本次不部署应用。主机状态变更只有一处：Mac 上重新运行 `codex/install-host-access-broker.sh`，把新的
manifest 与 `aisoft_gitea_governance` 装到 `/usr/local`。

- 幂等：同一 source 连跑两次，第二次为 no-op，输出的 source provenance 相同。
- 回滚：`git -C <主 checkout> ` 停留在 `origin/main` 后重跑同一 installer；预期 audit 回到
  `PROTECTION_MISMATCH`，即旧合同确实装回去了。
- gitea-ci VM 侧重装：VM 的 source root 是 `/mnt/mac` 下的主 checkout（在 `main` 上），因此按
  合并后收尾处理；实现期先确认 VM 能否读到 change worktree，读不到就如实记为合并后执行。
