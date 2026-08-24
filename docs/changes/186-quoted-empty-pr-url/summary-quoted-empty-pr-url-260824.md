---
issue: 186
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/186
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修好 backfill-pr-url 里第二套 front matter 取值方式：它绕开 contract._safe_scalar 直接切原始行，于是把引号空串读成非空值并报成「已有另一个 pr_url」；改动落在 aisoft_loop 治理运行时这一共享核心，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-quoted-empty-pr-url-260824.md
  spec: spec-quoted-empty-pr-url-260824.md
  plan: plan-quoted-empty-pr-url-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/186-quoted-empty-pr-url
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/187
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

summary front matter 把 `pr_url` 写成引号空串时，`aisoft-loop backfill-pr-url` 拒写并报
「summary already declares a different pr_url」。拒写方向本身没错，但这句话断言的事实
（存在另一个 PR URL）不存在，把读者推向「是不是别的会话已经建过 PR 并回填过」这条根本
没发生的排查路线。#175 会话在 PR #183 上实测到这一点。

## 影响范围

- `codex/runtime/aisoft_loop/documents.py` 的 `backfill_pr_url`：唯一的缺陷位置。
- 经它转发的 `backfill_pr_number`，以及 Controller 在 Loop 内建 PR 后的回填路径
  （`controller.py` 约 368–385 行）——两者都只是调用方，不需要各自改。
- `codex/runtime/tests/test_documents.py`：新增覆盖。

不影响模板、不影响历史文档、不影响 `check-change-documents` 的判据。

## 初步方案与建议

根因不是「引号空串是一种该被拒绝的写法」，而是**同一个仓库里存在两套「这个字段的值是
什么」**：

- 读侧唯一权威是 `contract._safe_scalar`（`contract.py:568`），它会剥掉成对引号，所以
  `parse_front_matter` 把引号空串解析成空字符串。`change_audit._pr_url_problem`、
  `_pull_url_prefix` 等所有读者看到的都是「空」。
- 写侧 `backfill_pr_url` 却用 `lines[index].split(":", 1)[1].strip()` 自己再解析一遍，
  引号原样留下，于是落进 `if current and current != pr_url` 这一支。

模板里 `override_reason: ''` 正是引号空串写法，说明这在本平台的 front matter 语法里
是合法拼写，不是畸形值——`pr_url` 上出现它是把同一份模板里的写法照抄过来。

因此按 AC-1 的第一条分支实现：**与裸空值等价处理并正常写入**，做法是删掉写侧那套弱
解析，改用函数已经持有的、`resolve_summary` 解析好的 front matter 取值；原始行只用来
定位「改哪一行」。这样修的是分歧本身，而不是在分歧上再加一条报错。

## 风险

- 放松空值判定会不会削弱 #142 的 fail-closed？不会：判定式仍是「非空且不等于传入值就
  拒写」，只有「什么算空」这一项跟读侧对齐。真实的另一个 PR URL 依旧非空、依旧拒写、
  报错字面不变（AC-2 用测试钉死）。
- 幂等性风险：引号包裹的**正确** URL 现在会被判为相等而不写。这正是 AC-3 要的行为
  （值已正确时一个字节都不写），不是回归。
- `status` 字段在同一函数里仍用原始行切分，带同一类缺陷。本次不动，见 spec 非目标。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修好 backfill-pr-url 里第二套 front matter 取值方式：它绕开 contract._safe_scalar 直接切原始行，于是把引号空串读成非空值并报成「已有另一个 pr_url」；改动落在 aisoft_loop 治理运行时这一共享核心，属平台治理变更，强制 complex
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

- 改动文件 `codex/runtime/aisoft_loop/documents.py` 属 `aisoft_loop` 治理运行时，是
  Controller 与交互会话共用的核心组件 → `platform-governance` 与 `shared-core`，两条
  都在 `FORCED_COMPLEX_RISKS` 里；`change_type: platform` 本身也在
  `FORCED_COMPLEX_TYPES` 里。complex 三重强制。
- `contract_effect: restore`：既有合同是「空则写、声明了另一个 PR URL 则拒写」，引号
  空串按本运行时自己的 scalar 规则就是空；写侧未能兑现该合同。恢复既有合同的意图，
  不新增也不改变合同面。
- `required_docs` 不含 `verification`：全部验收标准都能由 diff review 与 required CI
  （`codex/runtime/tests` 与 `codex/tests/smoke.sh`）复现，落在 `03` §3 判据表第一行。

### 缺失的 acceptance criteria 或决策

- 无。AC-1 的二选一由本次 spec 依仓库证据定为「等价处理并正常写入」，理由见 spec §2。
