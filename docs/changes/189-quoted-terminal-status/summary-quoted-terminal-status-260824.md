---
issue: 189
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/189
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: backfill-pr-url 里 status 仍用原始行切分取值，引号包裹的终态被判成非 PR 承载态并降级重写成 pr-open；修法是把取值来源统一到 resolve_summary 已解析的 front matter，改动落在 aisoft_loop 治理运行时这一共享核心，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-quoted-terminal-status-260824.md
  spec: spec-quoted-terminal-status-260824.md
  plan: plan-quoted-terminal-status-260824.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/189-quoted-terminal-status
pr_url:
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`backfill_pr_url` 推进 `status` 时用 `lines[status_index].split(":", 1)[1].strip()` 从
原始行取值，引号原样留下。于是引号包裹的终态 `status: 'deployed'` 被判为「非 PR 承载
态」，降级重写成 `pr-open`；引号包裹的 `status: 'pr-open'` 也被判为未就位，在本该零写入
的幂等路径上产生一次写入。

`test_a_terminal_status_is_not_downgraded` 正是要挡住第一件事，但它只覆盖裸写形式，
挡不住引号形式。

## 影响范围

- `codex/runtime/aisoft_loop/documents.py` 的 `backfill_pr_url`：唯一的缺陷位置，
  推进 `status` 的那一行。
- 经它转发的 `backfill_pr_number`，以及 Controller 在 Loop 内建 PR 后的回填路径——
  两者都只是调用方，不需要各自改。
- `codex/runtime/tests/test_documents.py`：新增覆盖。

不影响模板、不影响历史文档、不影响 `check-change-documents` 的判据。

## 初步方案与建议

取值来源统一到 `resolve_summary` 已经解析好的 front matter（`contract._safe_scalar`
剥掉成对引号），与 #186 对同函数内 `pr_url` 的修法一致；写入位置仍由原始行 index 决定。
不新增第二套解析，也不新增报错。

## 风险

- 误伤既有的降级判定：约束是判定式本身不动，只把「当前 status 是什么」交给读侧那一套；
  裸写形式的行为必须逐字节不变，由既有用例钉死。
- 回滚为单 commit `git revert`，无迁移、无状态残留。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: backfill-pr-url 里 status 仍用原始行切分取值，引号包裹的终态被判成非 PR 承载态并降级重写成 pr-open；修法是把取值来源统一到 resolve_summary 已解析的 front matter，改动落在 aisoft_loop 治理运行时这一共享核心，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: restore`：修复的是既有缺陷，恢复 `status` 一栏本就声明的合同
  （终态不被回填降级），不新增也不改变任何外部行为。
- 但 `contract_effect` 只决定 small **候选**资格。触点是
  `codex/runtime/aisoft_loop/`——Loop、Controller 与全部治理 CLI 共用的运行时共享核心，
  且 `backfill_pr_url` 写的是判级/交付审计读取的 front matter，属 Agent 与平台治理变更，
  按 `AGENTS.md` 强制 complex 规则一律按 complex 处理。与 #186 同源同判。
- 缺陷可稳定复现：在 merged main `d73fee4` 上，`status: 'deployed'` + 已正确的 `pr_url`
  经一次 `backfill_pr_url` 后变成 `status: pr-open`、`changed=True`。

### 缺失的 acceptance criteria 或决策

- 无。Issue #189 正文已给出 AC-1..AC-4，范围外项也已写明。
