---
issue: 108
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/108
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - cross-module
  - credential-handling
depends_on: []
status: contract-drafting
branch: change/108-label-provisioning
pr_url:
created: 2026-08-14
updated: 2026-08-14
---

# Implementation plan：标签 provision 与 taxonomy 扩展点

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | manifest 结构演进为 `schema_version: 2`，含 `canonical` / `project_extensions` / `retired`，附独立结构校验器与测试 | - | completed |
| T02 | `sync-gitea-labels.sh` 适配新结构，实现 create/update/skip-retired 幂等 provision | T01 | completed |
| T03 | broker 新增 `gitea.labels.read` 与 `gitea.labels.provision` 两个 typed 操作 | T01 | completed |
| T04 | `aisoft-project-check.sh` 的 `labels-readback` 改为按声明校验，冲突与 retired 附所属 Issue 清单 | T01 | completed |
| T05 | onboarding-runbook §5 散文步骤替换为确定性命令，并接入 `host.onboarding.check` 步骤序列 | T02, T03 | pending |
| T06 | UQ-1 落地：按人拍板结果调整 canonical type 集合与判级证据描述 | T01 + 人决策 | pending |

T02 / T03 / T04 在 T01 之后互不依赖，可并行。T06 独立于实现路径，只改 manifest 数据与
判级文档，故不阻塞 T02–T05 的编码。

**T06 未获人决策前不得开始**——这是 spec UQ-1 的闸门，不是排期问题。

## Expected touch points

范围提示，不授权扩大 spec。

- **T01**：`codex/config/gitea-labels.json`；新增
  `codex/runtime/aisoft_loop/`（或 `codex/agent/`）下的 manifest 校验入口；
  `codex/tests/test-sync-gitea-labels.sh` 新增结构用例。
- **T02**：`codex/tools/sync-gitea-labels.sh:76-96`（当前只增不删的循环）；
  `codex/tests/test-sync-gitea-labels.sh`。
- **T03**：`codex/runtime/aisoft_host_access/contract.py:163-185`（`EXPECTED_OPERATIONS`）、
  `broker.py:424-440`（URL dispatch）、`runner.py:47` 附近；
  `codex/runtime/tests/test_host_access.py:107` 的操作表、
  `codex/tests/test-host-access-broker.sh`。
- **T04**：`codex/tools/aisoft-project-check.sh:233-313`（`check_remote_labels`，含
  `:269-286` 的 drift/unmanaged 计算与 `:288-307` 的 case 分支）；
  `codex/tests/test-project-check.sh`；
  `skill-for-codex/references/project-align.md`（checklist 第 4 行是本检查的人类可读描述，
  判定依据变了就必须同步，否则文档与工具互相矛盾）。
- **T05**：`skill-for-codex/references/onboarding-runbook.md:225-247`；
  若 `host.onboarding.check` 有步骤清单则同步。
- **T06**：`codex/config/gitea-labels.json` 的 `canonical` 数组、
  `skill-for-codex/references/onboarding-runbook.md:241`、判级证据描述所在文档。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 结构 + fail-closed 拒绝旧格式 | `bash codex/tests/test-sync-gitea-labels.sh`（新增：旧裸数组输入必须非零退出并给出明确错误） |
| AC-2 幂等 provision | `bash codex/tests/test-sync-gitea-labels.sh`（新增：fixture 双次执行，第二次断言 `created=0 updated=0` 且退出码 0） |
| AC-3 两个 typed 操作 + 无删除 | `python3 -m pytest codex/runtime/tests/test_host_access.py` 与 `bash codex/tests/test-host-access-broker.sh`（新增：`gitea.labels.delete` 断言 `REQUEST_DENIED`） |
| AC-4 按声明校验（含拼写错误场景） | `bash codex/tests/test-project-check.sh`（新增：`area/web` → PASS、`aera/web` → GAP 两个 fixture） |
| AC-5 GAP 附 Issue 清单 | `bash codex/tests/test-project-check.sh`（新增：受管冲突与 retired 各一个 fixture，断言输出含 Issue 编号） |
| AC-6 onboarding 确定性命令 | 人工 review `onboarding-runbook.md` diff；确认 §5 无残留「建…标签」散文步骤 |
| AC-7 无删除路径 | 复用 AC-3 的 `REQUEST_DENIED` 断言 + review `sync-gitea-labels.sh` 无 `DELETE` 调用 |
| AC-8 全绿 | `bash codex/tests/smoke.sh` |

所有断言使用本地 fixture，不联网、不触碰任何真实 Gitea 仓库的标签。

## 部署与回滚

无部署影响。本变更不产出制品、不触及 AppServer/production、不修改 `ops/` 与
`docker-release/`，故 `required_docs` 不含 `verification`。

回滚为单 PR revert：manifest 回到裸数组、两个消费者回到旧解析、broker 操作表回到 22 项。
各项目仓库的实际标签在本变更全程零改动，故回滚无残留状态。
