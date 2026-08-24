---
issue: 189
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/189
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/189-quoted-terminal-status
created: 2026-08-24
updated: 2026-08-24
---

# Spec · backfill-pr-url 推进 status 时的取值来源

## 1. 目标与原因

`backfill_pr_url` 决定要不要把 `status` 推进成 `pr-open` 时，用原始行切分取值：

```python
status = lines[status_index].split(":", 1)[1].strip()
if status not in PR_BEARING_STATUSES:
    lines[status_index] = _replaced(lines[status_index], "status", "pr-open")
```

引号原样留下，`'deployed'` 不在 `PR_BEARING_STATUSES` 里，于是一个终态被**降级**重写
成 `pr-open`。回填是幂等写者，把一份已经交付完成的 summary 改回「PR 刚打开」，会让判级
与交付审计读到一个与事实相反的生命周期状态。

目标是让这条路径按值而不是按拼写判断，恢复 `test_a_terminal_status_is_not_downgraded`
本就声明的合同。

## 2. 为什么是「统一取值来源」而不是别的修法

仓库证据只指向一条路：

1. **读侧已有唯一权威的取值规则。** `contract._safe_scalar`（`contract.py:568`）剥掉
   成对引号，`parse_front_matter` 因此把 `status: 'deployed'` 解析成 `deployed`。
   所有读者看到的都是终态。
2. **只有这一行不同意。** 同一个函数已经持有 `resolve_summary` 解析好的 front matter
   （局部变量 `summary`），却对 `status` 又切了一遍原始行——一个函数里两套「这个字段的
   值是什么」。
3. **#186 已经在同一个函数里把 `pr_url` 修成了第 1 条。** 那次修改在 spec 的非目标里
   显式声明「不修同函数内 `status` 的同类缺陷，应单独立项」。本 spec 就是那一项，修法
   必须与它一致，否则同函数内的分歧只是从两处减为一处又换了个位置。

新增一条「status 拼写不合模板」的报错会把分歧固化：写侧继续用自己的解析，只是换一句
话说错。归一化重写（把 `'deployed'` 改写成 `deployed`）则会把一次本该零写入的回填变成
一次改写，与 Issue 的范围外项冲突。

**与 `pr_url` 的差别**：`pr_url` 需要「值」也需要「写入位置」；`status` 只需要「值」，
写入位置仍由 `_front_matter_field` 给出的原始行 index 决定。因此本次只改取值来源一处，
`_front_matter_field` / `_replaced` 都不动。

## 3. Acceptance criteria

- [ ] **AC-1** summary 的 `status` 写成引号包裹的终态（`'deployed'`、`"completed"`）时
      不被降级：文件里该行保持原值，`changed` 不因它变 True。
- [ ] **AC-2** `status` 写成引号包裹的 `'pr-open'` 时视为已就位：不产生写入，
      `changed` 不因它变 True。
- [ ] **AC-3** 裸写形式行为完全不变：`status: approved` 仍被推进成 `status: pr-open`，
      既有用例 `test_a_terminal_status_is_not_downgraded`、
      `test_repeating_the_backfill_produces_no_diff`、
      `test_writes_pr_url_and_advances_status_together` 保持绿。
- [ ] **AC-4** `bash codex/tests/smoke.sh` 全绿；新增用例覆盖引号包裹的终态与引号包裹
      的 PR 承载态。

## 4. 接口、数据与兼容性影响

- 无接口变化：`backfill_pr_url(repo, issue_number, pr_url)` 与 `backfill_pr_number(...)`
  的签名、返回值 `(Path, bool)` 与异常类型 `ContractError` 都不变；CLI
  `backfill-pr-url` 的参数与退出码不变。
- 无 schema 变化：front matter 字段集合与 `PR_BEARING_STATUSES` 都不变，模板不改。
- 行为变化只发生在一类输入上：`status` 为引号包裹值时，从「按非承载态处理并重写」变为
  「按其剥引号后的值处理」。该输入此前必然以一次错误写入告终，没有依赖旧行为的正确
  路径可被打破。
- 历史文档不做任何批量改写。

## 5. 风险与回滚约束

- 主要风险是把降级判定本身改松。约束：判定式仍为「当前值不在 `PR_BEARING_STATUSES`
  里 → 重写为 `pr-open`」，只把「当前值」的来源换成读侧那一套；AC-3 用既有用例钉死
  裸写路径。
- 次要风险是解析结果类型不是字符串（front matter 的 list 值）。约束：取值处按 `pr_url`
  同样的方式做 `isinstance` 收窄，非字符串一律按「不是承载态」处理，维持现有的
  fail-forward 方向而不是新增报错。
- 回滚：单文件、单函数内的局部改动，`git revert` 该 commit 即可，无迁移、无状态残留。

## 6. 非目标

- 不做拼写归一化：已经正确的引号包裹值不改写成裸形式（那会与 AC-2 冲突）。
- 不改 `PR_BEARING_STATUSES` 的成员，不新增生命周期状态。
- 不改 `templates/docs/changes/_template/summary.md`：裸 `status:` 仍是规范写法。
- 不批量重写 `docs/changes/` 下的历史文档。
- 不动 `_front_matter_field` 与 `_replaced`：写入位置的确定方式不在本次范围内。

## 7. 未决问题

- 无。
