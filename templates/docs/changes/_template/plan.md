---
issue: ISSUE_NUMBER
gitea_url: ISSUE_URL
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: complex
contract_effect: CONTRACT_EFFECT
confidence: CONFIDENCE
risk_flags: []
depends_on: []
branch: change/ISSUE_NUMBER-SHORT-SLUG
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Implementation plan template

## 全局约束与接口

- 写明所有 ticket 共用的接口、已批准决定和停止条件；没有额外约束时明确写“无”。
- Txx 是唯一任务身份。按路由选择一个执行入口；SP 的 Task N 仅为可再生视图，不另写一份人工计划。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 一个端到端可验证的垂直切片 | - | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID，图与正文的 blocked_by 必须一致。
每个 ticket 都须完整交接并可由所选 provider 独立执行和验证；仅依赖已完成且有证据的 frontier 可启动。
默认使用可独立验收的 vertical slice；只有无法逐片保持绿色的宽重构才按 expand → migrate batches → contract 建图。

## T01：一个端到端可验证的垂直切片

- **交付/范围**：写可验收结果、属于本票的改动与不包含的工作。
- **blocked_by**：无；或列出本图的完整 Txx ID，不能用模糊前缀。
- **AC**：AC-1；引用映射 spec 的验收标准。
- **接口/约束**：引用本计划全局约束，并写本票新增的已批准接口决定。
- **验证**：真实命令或明确的观察方法；这里只写计划，未运行不写 PASS。
- **Expected**：每条验证应观察到什么，以及它没有覆盖什么。
- **停止条件**：合同冲突、范围扩张及现有升级条件；治理步骤须独立 commit 后 STOP/fresh run。

## Expected touch points

- 按 ticket 列出预期文件或模块；这是范围提示，不授权扩大 spec。

## 数据库迁移

没有迁移时明确写“无”。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 待填写 |

## 执行证据

<!-- execution-evidence:start -->
尚未执行。实际记录 ticket_base、起始状态、provider/入口来源、验证结果、candidate_head、
审查范围与 findings；可引用本 Issue 映射 verification，不另建证据权威。
<!-- execution-evidence:end -->

语义摘要仅排除图中的 Status 单元、updated 与这段成对标识的执行证据；原始全文摘要另存审计。
标记不得嵌套、重复或包住任务图/正文/约束。正常状态推进、补证不改变任务语义；
AC/依赖/命令/Expected/约束变化必须报告，不能静默续跑。具体规则见平台 execution-adapter。

## 部署与回滚

没有部署影响时明确写“无”。有部署影响时必须计划映射的 `verification` 文档、两次重复执行和一次故意失败回滚。
