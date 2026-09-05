---
issue: 243
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/243
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: []
depends_on:
  - 222
status: pending
branch: change/243-issue-entry-label-sweep
created: 2026-09-05
updated: 2026-09-05
---

# Verification · 243 issue-entry-label-sweep

## 基线与范围

- Commit SHA: `02baf005ed85960056c2d090cb920551d649bdb0`
- 基线：`origin/main` = `87b3aa4af01b8fc9421d82c7ab381e805eb33162`
- 环境：Mac 本机 checkout `/private/tmp/issue-243-issue-entry-label-sweep`，
  Gitea `http://gitea-ci.orb.local:3000`
- 本记录负责证明的 acceptance criteria：AC-1 到 AC-7。

本次变更的验收证据里有三样 required CI 与 diff review 重放不了的东西：一次真实的 Gitea 写入
与读回、安装期操作表与仓库源之间的差值、以及每条新增守卫的反向证明（先把被守卫的内容改坏，
看它变红，再改回去）。这就是 `required_docs` 声明 `verification` 的原因。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（改动前基线，rebase 前） | PASS | `Ran 660 tests ... OK` + `Codex platform static smoke checks passed.` |
| `bash codex/tests/smoke.sh`（T01 之后、rebase 之后基线） | PASS | exit 0，`OK` |
| `bash codex/tests/smoke.sh`（T02 之后，最终） | PASS | `Ran 671 tests in 41.244s ... OK` |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access` | PASS | `Ran 158 tests ... OK` |
| `bash -n codex/tests/smoke.sh` / `bash -n codex/tests/test-host-access-broker.sh` | PASS | 无输出 |
| `aisoft_host_access.cli ... validate`（候选 manifest） | PASS | `{"contract_version": "host-access-broker/v1", "merge_operation_count": 1, "operation_count": 33, "project_count": 10, "status": "PASS"}` |
| 缺 `--entry-label` 建 Issue | 按预期拒绝 | `{"code": "ARGUMENT_MISMATCH", "message": "operation arguments do not match the typed contract", "status": "BLOCKED_EXTERNAL"}` |
| `--entry-label approved`（真实标签但不是流程入口） | 按预期拒绝 | `{"code": "ARGUMENT_MISMATCH", "message": "entry label must be one of the flow entrances a new Issue may start at", "status": "BLOCKED_EXTERNAL"}` |
| 真实建 Issue（候选 manifest，`--entry-label needs-analysis`） | PASS | 新建 Issue #246，创建响应的 `labels` 为 `['needs-analysis']` |
| `host-access-broker --operation gitea.issue.labels.read --number 246`（已安装 wrapper） | PASS | `['needs-analysis']` |
| `host-access-broker --operation host.access.audit` | PASS | `status PASS`；`project_agent` = `aisoft-platform-agent`，scopes `['read:user', 'write:issue', 'write:repository']` |
| 读取已安装操作表 `/usr/local/share/aisoft/host-access-broker.json` | 与仓库源不同（预期） | `installed operation_count 33`，`installed args ['title', 'body']` —— 新参数尚未安装 |
| `codex/tools/apply-classification-labels.sh --repo . --apply 243` 后 `--verify 243` | PASS | `"result":"projected"`，`change_type` `platform`，`complexity` `complex` |

### 新增守卫的反向证明

每条守卫都先把被守卫的内容改坏、跑一次 smoke、再改回去。删除短语而不是给它加字符：
`grep -Fq` 钉的是子串，`## 开放 Issue 清扫X` 仍然包含原短语，第一次用加字符的改法两条守卫
都没有变红，这本身也记在这里。

| 守卫 | 破坏方式 | smoke 结果 |
|---|---|---|
| `## 开放 Issue 清扫`（Claude 侧 skill） | 标题改成 `## 清扫` | exit 1 |
| `## Open-Issue sweep`（Codex 侧 skill） | 标题改成 `## Sweep` | exit 1 |
| `需裁决（n 条）` | 改成 `需裁决 n 条` | exit 1 |
| `### 衍生 Issue 的正文与认领`（03） | 标题截短 | exit 1 |
| `## Derived Issues`（tracker，两份副本同时改以避开 `cmp` 闸门） | 标题截短 | exit 1 |
| `--entry-label`（aisoft-platform skill） | 改成 `--entrylabel` | exit 1 |
| `gitea.issue.labels.set --number N --lifecycle needs-analysis` | 截成 `gitea.issue.labels.set` | exit 1 |

前四条在 rebase 之前跑，尾行为空（守卫自身失败）；后三条第一次跑落在 staleness 闸门上，
尾行是 `On a change branch, rebase onto the upstream instead:`，那不是守卫在响应，因此
rebase 到 `87b3aa4` 之后重跑，重跑前先确认基线 exit 0。

### `06` 踩坑 20 的七处同步

| # | 位置 | 本次改动 |
|---|---|---|
| 1 | `contract.py` 的 `EXPECTED_OPERATIONS` | `arguments` 加 `entry_label` |
| 2 | `broker.py` dispatch | `execute()`/`_gitea()` 参数、创建分支校验与标签 id 解析 |
| 3 | `runner.py` | `issue_create()` 增加 `entry_label` |
| 4 | `codex/config/host-access-broker.json` | 该操作的 `arguments` |
| 5 | `codex/runtime/tests/test_host_access.py` 的操作表 | `("title", "body", "entry_label")` |
| 6 | `codex/tests/test-host-access-broker.sh` | `arguments` 断言；`operation_count` 仍为 33，本次不新增操作 |
| 7 | `test_cli_exposes_only_typed_issue_and_pull_fields` 的逐字 kwargs | 五处 `execute()` 断言各加 `entry_label=None` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | Issue #246 经 broker 建出，`gitea.issue.labels.read` 读回 `['needs-analysis']` |
| AC-2 | PASS | `host.access.audit` 的 `project_agent` 仍是 `aisoft-platform-agent`，scope 与 manifest 一致；本次不新增操作、不新增 identity route，`gitea.issue.create` 的 `identity_route` 与 `mutating` 未变 |
| AC-3 | PASS | 两种 `ARGUMENT_MISMATCH` 已真实执行（见上表）；退役取值与未定义标签的 `TARGET_MISMATCH` 由 `test_issue_create_rejects_an_entrance_the_installed_manifest_dropped` 与 `test_issue_create_fails_closed_when_the_entrance_is_not_defined` 覆盖——平台仓 27 个标签全部已定义，未定义分支在真实仓库上构造不出来 |
| AC-4 | PASS | 七处同步表；`validate` 读回 `operation_count` 33 |
| AC-5 | PASS | 两份 skill 各命中一次清扫节标题；守卫反向证明 |
| AC-6 | PASS | `03` 与 `docs/agents/issue-tracker.md`（含 `templates/` 逐字节副本）各命中一次；守卫反向证明 |
| AC-7 | PASS | `Ran 671 tests ... OK` + 静态检查通过 |

## 遗留风险与未完成项

- **两台重装尚未执行（NOT RUN）**。已安装的操作表仍是 `['title', 'body']`，新参数只在候选
  manifest 上可用。合并后需要在 Mac 与 gitea-ci VM 两台执行
  `sudo bash codex/install-host-access-broker.sh`，再用 `--operation host.access.audit` 确认。
  在那之前，经已安装 wrapper 调用 `gitea.issue.create` 走的仍是旧的两参数合同，会建出无标签
  Issue；这正是本变更要消除的形态，因此重装是合并后的第一件事。
- 装到一半（只装一台）会出现 `REQUEST_DENIED` 形态的假权限问题，见 `06` 踩坑 20。
- 既有的开放 Issue 不在本次范围内，已开 Issue #246 承接。
- 本次不部署，无迁移，无数据回滚需求。回滚方式是 revert 本次 merge commit 并在两台重装。
