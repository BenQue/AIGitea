---
issue: 115
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/115
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/115-issue-labels-completed
pr_url:
created: 2026-08-15
updated: 2026-08-15
---

# Implementation plan：`completed` 终态与 Issue 级标签 typed 操作

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `gitea-label-manifest.sh` 新增 `aisoft_label_manifest_lifecycle`；`mark-deployed-issues.sh:77` 硬编码数组改为调用它；smoke 增加「禁止第二处硬编码 lifecycle 列表」断言（AC-7） | - | completed |
| T02 | broker 新增 `gitea.issue.labels.read` 与 `gitea.issue.labels.set` 两个 typed 操作，含 `--lifecycle` 参数与 manifest 派生的取值校验（AC-1、AC-3） | T01 | pending |
| T03 | `set` 的投影语义与守卫：只改 lifecycle 维度、`deployed` 不可被降级为 `completed`、幂等 no-op（AC-2、AC-4、AC-5） | T02 | pending |
| T04 | `codex/tools/mark-completed-issues.sh`：解析已合并 Issue、按 `required_docs` 判定、默认 dry-run、`--apply` 才写（AC-6、AC-8） | T01、T02 | pending |
| T05 | 文档：03 §「合并后收尾」补终态推进责任与命令；runbook §8；PR 交接写明**两台重装 broker** | T02、T04 | pending |

T03 与 T02 同属 broker 实现，拆开是因为 T02 是操作面注册（纯机械、易验证），T03 是语义守卫
（是本 Issue 真正的风险所在），分开能让 review 聚焦。

## Expected touch points

范围提示，不授权扩大 spec。

- **T01**：`codex/agent/gitea-label-manifest.sh`（在 `_canonical` / `_prefixes` / `_retired`
  旁新增第四个 reader）；`codex/tools/mark-deployed-issues.sh:77`；
  `codex/tests/test-gitea-label-manifest.sh`、`codex/tests/test-mark-deployed-issues.sh`、
  `codex/tests/smoke.sh`。
- **T02**：`codex/runtime/aisoft_host_access/contract.py` 的 `EXPECTED_OPERATIONS`、
  `broker.py` 的 dispatch（参照 `:445-448` 的 `gitea.labels.*` 写法）、`runner.py`、
  `cli.py` 新增 `--lifecycle`、`codex/config/host-access-broker.json`。
- **T03**：`broker.py` 的 set 实现；语义参照
  `codex/runtime/aisoft_loop/gitea.py:133-150` 的 `_reconcile_labels`（**复用其语义，不复制其
  代码**——那是 Loop 内的方法，broker 不 import aisoft_loop）。
- **T04**：新增 `codex/tools/mark-completed-issues.sh`；调用
  `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents`。
- **T05**：`03-Issue-Spec-Plan与单闸门开发流程.md`、
  `skill-for-codex/references/onboarding-runbook.md` §8。

### 新增 typed 操作必须同步的六处（#108 T03 实测漏过第 6 处）

1. `contract.py` 的 `EXPECTED_OPERATIONS`
2. `broker.py` 的 dispatch
3. `runner.py`
4. `codex/config/host-access-broker.json`
5. `codex/runtime/tests/test_host_access.py` 的操作表
6. **`codex/tests/test-host-access-broker.sh` 的 `operation_count` 与
   `[.operations[].name] | length`（24 → 26）** ← 漏了会让 smoke 红在很靠后且不打印自身输出

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command |
|---|---|
| AC-1 两个 typed 操作 + 取值 fail closed | `python3 -m unittest tests.test_host_access`；`bash codex/tests/test-host-access-broker.sh`（新增：`--lifecycle bogus` 断言 `ARGUMENT_MISMATCH`） |
| AC-2 只改 lifecycle，其余四类标签不变 | `tests/test_host_access.py` 新增 fixture：Issue 同时挂 `type/*`、`complexity/*`、`triage/*`、`area/*`，断言前后差集恰为 lifecycle 一项 |
| AC-3 标签未 provision 时 fail closed | `tests/test_host_access.py`：仓库标签集缺 `completed`，断言错误信息含 `gitea.labels.provision` |
| AC-4 `deployed` 不可降级 | `tests/test_host_access.py`：当前含 `deployed`、请求 `completed`，断言 `REQUEST_DENIED` 且无 `PUT` 发出 |
| AC-5 幂等 no-op | `tests/test_host_access.py`：目标已是当前 lifecycle，断言 `result == "no-op"` 且 transport 无 `PUT` |
| AC-6 判定取自 `required_docs` | 新增 `codex/tests/test-mark-completed-issues.sh`：两个 fixture summary（含/不含 `verification`），断言前者跳过并给出理由 |
| AC-7 lifecycle 单一事实源 | `bash codex/tests/test-gitea-label-manifest.sh`；smoke 断言仓库内无第二处硬编码 lifecycle 列表 |
| AC-8 零真实标签变更 | `test-mark-completed-issues.sh`：无 `--apply` 时断言 mock broker 零调用；PR review 确认无真实 Issue 被写 |
| AC-9 全绿 | `bash codex/tests/smoke.sh` |

所有断言使用本地 fixture 与 mock transport，不联网、不触碰任何真实 Gitea Issue。

## 部署与回滚

无部署影响，故 `required_docs` 不含 `verification`。

**但有一个安装步骤**：broker manifest 变更后，Mac 与 gitea-ci VM 两台都必须运行
`sudo bash codex/install-host-access-broker.sh` 才生效，否则新操作返回 `REQUEST_DENIED`
（#108 实测，症状形似权限问题）。该步骤需要人执行（安装目录属 `root:wheel`），必须写进 PR
交接说明，不能默认 reviewer 知道。

回滚为单 PR revert：操作表回到 24 项，`mark-deployed-issues.sh` 回到硬编码数组，新工具删除。
因 AC-8 保证零真实标签变更，回滚无残留状态。
