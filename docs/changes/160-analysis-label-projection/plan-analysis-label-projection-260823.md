---
issue: 160
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/160
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/160-analysis-label-projection
created: 2026-08-23
updated: 2026-08-23
---

# Implementation plan · 判级标签的交互会话投影路径（#160）

## Ticket graph

| Ticket | 内容 | 依赖 |
|---|---|---|
| T01 | broker 新增 typed 操作 `gitea.issue.labels.classify`（7 处同步点） | — |
| T02 | `codex/tools/apply-classification-labels.sh` 与其测试 | T01 |
| T03 | `03` §11 与 `skill-for-claude/aisoft-platform/SKILL.md` 合同记录 | T01, T02 |

顺序执行；T02 的测试用假 broker，不依赖 T01 已安装。

## Expected touch points

### T01 —— 新增 typed 操作的 7 处同步点（`06` 踩坑 20 的清单）

1. `codex/runtime/aisoft_host_access/contract.py` —— `EXPECTED_OPERATIONS` 新增
   `"gitea.issue.labels.classify": ("project-agent", True, ("number", "change_type", "complexity"))`，
   并改写 `gitea.issue.labels.*` 段的注释：原文说 `type/`/`complexity/` 没有 typed 写入口，
   现在要说清楚新入口为什么不构成绕过。
2. `codex/runtime/aisoft_host_access/broker.py` —— `execute()` 与 `_gitea()` 增加
   `change_type` / `complexity` 两个 kwarg 与 `arguments` 字典条目；新增维度校验分支、
   `_type_labels()` / `_complexity_labels()`（与 `_lifecycle_labels()` 同一条派生规则）
   与 `_set_issue_classification()`。
3. `codex/runtime/aisoft_host_access/runner.py` —— `issue_labels_classify(number, change_type, complexity)`。
4. `codex/config/host-access-broker.json` —— `operations` 新增一条（29 → 30）。
5. `codex/runtime/tests/test_host_access.py` —— 操作表断言、新操作的行为测试、
   `test_cli_exposes_only_typed_issue_and_pull_fields` 里逐字钉死的 `execute()` kwargs。
6. `codex/tests/test-host-access-broker.sh` —— `operation_count == 30`、
   `[.operations[].name] | length == 30`、新操作的 `arguments`/`mutating` 断言。
7. `codex/tests/smoke.sh` —— 无需改动（它只跑上面这些测试），确认后不动。

`_set_issue_classification()` 的行为按 `_set_issue_lifecycle()` 逐条对齐：
attaching is not defining（未定义 → `TARGET_MISMATCH` 指向 `gitea.labels.provision`）、
两维都已正确 → 不发 PUT、其余标签按 id 带过。

### T02 —— 执行者工具

- `codex/tools/apply-classification-labels.sh`，结构照抄 `mark-completed-issues.sh`：
  同一套参数解析、`--range` 的 `Closes #N` 抽取、`emit()` 的一行 JSON、
  broker 定位（同目录优先，其次 `/usr/local/libexec/aisoft/host-access-broker`）、
  `PYTHONPATH` 注入与 `resolve-documents` 调用。
- 差异点：
  - front matter 取 `change_type` 与 `effective_complexity` 两个标量键（`mark-completed`
    取的是 `required_docs` 列表），用同一段 awk fence 计数逻辑读第一段 front matter。
  - 多一次 broker `gitea.issue.read` 判 `state`；`closed` → 跳过，理由 `issue-closed`。
    这次读在 dry-run 也做——不然计划会把最终不会写的 Issue 列成会写。
  - `--apply` 调 `gitea.issue.labels.classify`，失败时原样透出 broker 的 `code`，
    因为重装缺失的症状（`REQUEST_DENIED`）必须能被认出来。
- `codex/tests/test-apply-classification-labels.sh`（新增），照
  `codex/tests/test-mark-completed-issues.sh` 的假 broker + 临时 repo 夹具写。
- `codex/tests/smoke.sh` 注册三处：`bash -n` 列表、`shellcheck` 列表、执行列表。

### T03 —— 合同记录

- `03-Issue-Spec-Plan与单闸门开发流程.md` §11 新增「谁投影 `type/*` 与 `complexity/*`」，
  与既有「谁推进 `completed`」同构：谁在什么时候跑、判定取自哪里、closed Issue 为何不补写。
- `skill-for-claude/aisoft-platform/SKILL.md` 会话标准动作在「写文档」与「commit/开 PR」
  之间插入一步，原 4–6 步顺延为 5–7。

## 数据库迁移

无。

## 测试与验收映射

| AC | 验证方式 |
|---|---|
| AC-1 | `test_host_access.py`：新操作写入后 `after` 含两个新维度且旧的 lifecycle/`triage/*` 标签仍在 |
| AC-2 | `test_host_access.py`：`--complexity standard`（retired）与未知 `--change-type` 均被 `ARGUMENT_MISMATCH` 拒绝，且不发出任何请求 |
| AC-3 | `test_host_access.py`：只给 `--change-type` 时 `ARGUMENT_MISMATCH` |
| AC-4 | `test_host_access.py`：仓库未定义 `type/platform` 时 `TARGET_MISMATCH`，消息含 `gitea.labels.provision` |
| AC-5 | `test_host_access.py`：两维已正确时 `result == "no-op"` 且无 PUT |
| AC-6 | `test-apply-classification-labels.sh`：dry-run 零 broker 写调用；`--apply` 调用参数逐字断言取自 front matter |
| AC-7 | `test-apply-classification-labels.sh`：closed / 无文档 / 无 summary / 缺 `effective_complexity` 四条跳过路径各一例 |
| AC-8 | `bash codex/tests/smoke.sh` 全绿 |
| AC-9 | `smoke.sh` 既有的文档 grep 段落 + 人工 review |

补充证据（非 AC，但要在 PR 里给）：在本分支 runtime + 本分支 manifest 上对**真实 Gitea**
跑一次工具 dry-run，证明它认出 #160 是 open、判级值读得对、且零写入。

## 部署与回滚

- 本 PR 不部署。合并后由人执行 broker 重装（Mac 与 gitea-ci 两台），新操作才可用：

  ```
  sudo bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
  orb -m gitea-ci sudo bash /mnt/mac/Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh
  ```

  installer 自带 `.previous` 备份，二次运行输出 `already current (no-op)`。
  验收用 `jq '.operations|length' /usr/local/share/aisoft/host-access-broker.json` == 30。
- 回滚：revert PR 后重跑同一条重装命令。
