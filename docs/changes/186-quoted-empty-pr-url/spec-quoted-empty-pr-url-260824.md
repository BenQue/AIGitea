---
issue: 186
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/186
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
branch: change/186-quoted-empty-pr-url
created: 2026-08-24
updated: 2026-08-24
---

# Spec · backfill-pr-url 对引号空串的取值与报错

## 1. 目标与原因

`backfill_pr_url` 在 summary 的 `pr_url` 写成引号空串时报「summary already declares a
different pr_url」。这句话断言了一件没有发生的事——存在第二个 PR URL——于是把读者送上
一条空的排查路线（去查是不是别的会话建过 PR）。目标是让这条路径的说法与事实一致，
同时一个字节都不放松 #142 建立的 fail-closed 语义。

## 2. 为什么选「等价处理」而不是「新增一条报错」

Issue 的 AC-1 给了两条分支，由本 spec 择一。仓库证据指向第一条：

1. **读侧已有唯一权威的取值规则。** `contract._safe_scalar`（`contract.py:568`）剥掉
   成对引号，`parse_front_matter` 因此把引号空串解析成空字符串。所有读者——
   `change_audit._pr_url_problem`、`_pull_url_prefix`、Controller 的前置检查——看到的
   都是「空」。
2. **只有写侧不同意。** `backfill_pr_url` 用 `lines[index].split(":", 1)[1].strip()`
   自建第二套解析，引号原样留下。缺陷因此不是「用户写错了」，而是**一个仓库里两套
   「这个字段的值是什么」**。
3. **引号空串在本平台是合法拼写。** `templates/docs/changes/_template/summary.md` 自己
   就用 `override_reason: ''`。把它判成畸形值，等于宣布模板里两个空值键的写法一个合法
   一个非法，而这个区别对读侧根本不存在。

新增一条「空值写法不合模板」的报错会把上述分歧固化下来：写侧继续用自己的解析，只是把
错误的诊断换成另一句话。删掉分歧才是与本仓库既有结构一致的修法。

## 3. Acceptance criteria

- [ ] **AC-1** summary 的 `pr_url` 写成 `''` 或 `""` 时，`backfill_pr_url` 与裸空值
      完全等价：写入传入的 URL、按既有规则推进 `status`、返回 `changed=True`，不报错。
- [ ] **AC-2** summary 声明了一个与传入值不同的**真实**（非空）PR URL 时，仍然拒写、
      不落盘，且报错文本仍为 `summary already declares a different pr_url: <值>`。
      引号包裹的真实 URL 与裸写的真实 URL 判定一致。
- [ ] **AC-3** 幂等性不变：`pr_url` 已经等于传入值且 `status` 已是 PR 承载态时，
      `changed=False` 且文件字节完全不变。引号包裹的正确 URL 同样判为已就位。
- [ ] **AC-4** `bash codex/tests/smoke.sh` 全绿；`codex/runtime/tests/test_documents.py`
      覆盖 `''`、`""`、裸空值、真实不同 URL 四种输入。

## 4. 接口、数据与兼容性影响

- 无接口变化：`backfill_pr_url(repo, issue_number, pr_url)` 与
  `backfill_pr_number(...)` 的签名、返回值 `(Path, bool)` 与异常类型 `ContractError`
  都不变；CLI `backfill-pr-url` 的参数与退出码不变。
- 无 schema 变化：front matter 字段集合不变，模板不改。
- 行为变化只发生在一种输入上：`pr_url` 为引号空串时，从「拒写」变为「写入」。该输入
  此前必然以失败告终，因此没有依赖旧行为的成功路径可被打破。
- 历史文档不做任何批量改写；仓库内现存 summary 的 `pr_url` 保持原样。

## 5. 风险与回滚约束

- 主要风险是误伤 #142 的 fail-closed。约束：判定式保持「非空且不等于传入值 → 拒写」，
  只把「空」的定义交给读侧那一套；AC-2 用测试钉死报错文本，防止后续重构悄悄改写。
- 回滚：单文件、单函数内的局部改动，`git revert` 该 commit 即可，无迁移、无状态残留。

## 6. 非目标

- 不放宽 fail-closed，不允许覆盖已声明的另一个 PR URL。
- 不改 `templates/docs/changes/_template/summary.md`：裸 `pr_url:` 仍是规范写法，本次
  只是不再把等价拼写误判。
- 不做拼写归一化：已经正确的引号包裹 URL 不会被改写成裸形式（那会与 AC-3 冲突）。
- 不批量重写 `docs/changes/` 下的历史文档。
- **不修同函数内 `status` 的同类缺陷。** 该行同样用原始行切分取值，`status: 'pr-open'`
  会被判为非 PR 承载态并归一化重写。它有自己的可观察行为与自己的验收标准，按平台的
  衍生 Issue 判据应单独立项，不在本 PR 顺带。

## 7. 未决问题

- 无。
