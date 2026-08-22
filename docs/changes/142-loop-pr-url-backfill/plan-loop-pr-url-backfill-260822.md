---
issue: 142
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/142
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/142-loop-pr-url-backfill
created: 2026-08-22
updated: 2026-08-22
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `contract.resolve_summary` 公开访问器 + `backfill_pr_url` 写入器与单测 | - | done |
| T02 | `change_audit` 巡检模块（两条判据）与单测 | - | done |
| T03 | `cli.py` 两个子命令 | T01, T02 | done |
| T04 | 模板去键 + `03` 与两份 SKILL.md 的书面合同同步 | T01 | done |
| T05 | `aisoft-project-check.sh` 与 `smoke.sh` 接入 | T02, T03 | done |
| T06 | 真实数据验证（平台仓自身 + `admin/LocalWMS`）与 verification | T03, T05 | done |

## T01 — 写入器

- `contract.py`：新增 `resolve_summary(repo, issue_number) -> tuple[Path, dict]`，薄封装既有 `_document_context`，让外部拿到 active summary 路径与已解析 front matter 而不必碰私有函数；
- `documents.py`：新增 `backfill_pr_url(repo, issue_number, pr_url) -> tuple[Path, bool]`，行为按 spec §4；
- front matter 行定位只在首尾 `---` 之间进行，正文里出现的 `pr_url:` 字样不受影响；
- 单测覆盖：空值写入、同值零 diff、异值 fail-closed 且不写、缺键报错、URL 不自洽报错、正文同名字符串不被误改。

## T02 — 巡检

- 新模块 `codex/runtime/aisoft_loop/change_audit.py`：`audit_change_documents(repo) -> AuditReport`；
- 目录枚举跳过 `_template` 与非目录项；目录名解析失败单独成一条 GAP（不是崩溃）；
- `resolve_documents` 抛 `ContractError` 时，GAP 文案带上变更号与原始错误串；`ContractError` 已包含文件名的场景直接透传，否则补上正在解析的目录；
- `change-pr-url` 判据只在 `status ∈ {pr-open, completed, deployed}` 时生效；
- 单测覆盖：全绿仓库、缺 front matter 的 spec、`pr-open` + 空 `pr_url`、未知目录名、`_template` 被跳过、legacy 数字目录仍可通过。

## T03 — CLI

- `backfill-pr-url N --repo <path> --pr-url <url>`：成功打印写入路径与 `changed`/`unchanged`，`ContractError` 走既有的 stderr + 退出码 2 约定；
- `check-change-documents --repo <path>`：打印 PASS/GAP 行与 `result:` 汇总，有 GAP 退 1。

## T04 — 书面合同

- 模板三份删 `pr_url:`；
- `03-Issue-Spec-Plan与单闸门开发流程.md:71` 把 `pr_url` 从「所有 change 文档共同字段」移入 summary 专属字段，并写明理由指针；
- `skill-for-claude/SKILL.md` 与 `skill-for-codex/SKILL.md` 的第 4 步改为调用 `backfill-pr-url`。

## T05 — 接入

- `aisoft-project-check.sh`：新增 `change-documents` 与 `change-pr-url` 两项，调用 T03 的子命令（`PYTHONPATH="$ROOT/codex/runtime"`），沿用既有 `pass`/`gap` 计数器；无 `docs/changes/` 时按 `skip` 处理；
- `smoke.sh`：对平台仓自身跑一次 `check-change-documents`。

## T06 — 验证

- 平台仓自身与 `admin/LocalWMS` 各跑一次，如实记录；
- 负向验证在临时副本上做，不污染任何真实 checkout；
- 记录模板改动会让哪些已接入仓转 GAP。

## 回滚

纯新增子命令与检查项 + 三份模板与三处文档的文本改动，`git revert` 单个 commit 即可完全回退；未安装任何东西，未改 broker，无需重装或重启。
