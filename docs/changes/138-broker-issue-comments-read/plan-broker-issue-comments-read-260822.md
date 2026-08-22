---
issue: 138
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/138
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
status: pr-open
branch: change/138-broker-issue-comments-read
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/141
created: 2026-08-22
updated: 2026-08-22
---

# Plan · broker 补 gitea.issue.comments.read（#138）

```
T01 ──> T02 ──> T03 ──> T04 ──> T05
```

严格串行：T02 的 manifest 与 T01 的 `EXPECTED_OPERATIONS` 必须一致才载得起来；T03 的 helper 依赖前两者已声明该操作；T04 的三处枚举断言依赖 T02 的实际条目数；T05 的端到端验证依赖全部就位。

## T01 · contract.py 声明 typed 元组

`EXPECTED_OPERATIONS` 紧邻 `gitea.issue.comment` 之后新增 `("project-agent", False, ("number",))`，并写明命名依据与「刻意无 update/delete 对应物」的理由。

**验收**：`aisoft_host_access.cli validate` 通过；注释解释的是**为什么**（单复数承载语义、抹除讨论记录不可自动化），不是复述代码。

## T02 · 安装期 manifest 同步

`codex/config/host-access-broker.json` 的 operations 数组新增同名条目，`mutating: false`、`arguments: ["number"]`。

**验收**：`jq empty` 通过；`validate` 报 `operation_count` 为 27；manifest 与 `EXPECTED_OPERATIONS` 无漂移（运行时会交叉校验，不一致即 fail-closed）。

## T03 · broker.py 接线与 _issue_comments

三处：参数校验分支（`_positive_number`）、分派分支（提前 return 走 helper）、`_issue_comments` 本体（有界分页 + 逐条 schema 校验 + 四字段投影）。

**验收**：分页在 >50 条时确实翻页且顺序稳定；上游条目缺 `body` 时抛 `RESPONSE_SCHEMA_INVALID` 而非返回半个对象；返回对象恰好四个键，内嵌 user 的 `email`/`is_admin` 不出现在结果里；扫到第 100 页仍未结束时抛错而非静默截断。

## T04 · 三处枚举断言同步

`test_host_access.py` 的 typed 元组表补一行；`test-host-access-broker.sh` 的两处 `26` → `27`，并新增两条 jq 断言钉住新操作的 `arguments` 与 `mutating: false`。补 5 个 python 用例：投影+URL+仅 GET、分页、畸形条目、参数校验、无 update/delete 对应物。

**验收**：`test-host-access-broker.sh` 退出 0；python 单测全绿。**注意**这个 shell guard 失败时零输出（`jq -e` 静默 + `set -e`），定位要靠 `bash -x`。

## T05 · 对真实 Gitea 端到端验证

用本分支的 runtime 与本分支的 manifest（复刻已安装 wrapper 的调用方式）执行 `--project localwms --operation gitea.issue.comments.read --number 6`。

**验收**：返回 1 条评论，`author`/`created_at` 与 Gitea 页面一致，`body` 与人工核对的评论正文逐字一致，且这正是本 Issue 起因的那条评论——用它自己解决它自己。

## 交付前统一验证

`bash codex/tests/smoke.sh` 退出 0（含 462 个 python 单测）。全绿后一次性 push，再开 PR。
