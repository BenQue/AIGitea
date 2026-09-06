---
issue: 271
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/271
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
depends_on:
  - 268
status: approved
branch: change/271-company-platform-baseline
created: 2026-09-06
updated: 2026-09-06
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 完整严格 inventory、状态与采用决定闭环，含 fixture/拒绝测试 | - | complete |
| T02 | 零写入固定探针、stdout envelope/checksum/离线验证及脱敏人工输入 | T01 | complete |
| T03 | 用户采集包、B2/B3 卡、验证与本地提交、最终 PR 待确认 | T02 | complete |

`blocked_by` 按表中 Blocked by 执行；所有工作属于 #271，一个最终 PR。已批准合同覆盖本拆分，不再重复启动确认。

## Expected touch points

- T01/T02：`codex/runtime/aisoft_company_baseline.py`、`company-delivery/baseline/`、`codex/runtime/tests/test_company_baseline.py`。
- T03：本 Issue 四份文档、`company-delivery/baseline/README.md` 和脱敏示例。独立目录避免与 #270 的现有 operator/runbook 变更冲突。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/AC-2 | unittest 注入固定探针 seam，检查 argv/HTTP/stat 白名单、无写入、无环境读取、重复执行与异常脱敏 |
| AC-3/AC-4 | unittest 真实 schema/validator/assess 入口；缺证据/历史/漂移/类型/重复键/未知键/敏感输入负向场景 |
| AC-5 | subprocess CLI end-to-end、schema 一致、checksum 篡改、runbook 块行数、B2/B3 卡核验 |
| AC-6 | 本机无主机采集；交付 blocked 示例及 `NOT RUN` 清单；fresh 公司证据需用户回流 |
| 全部本地 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_company_baseline.py'`；完整 runtime unittest；semantic checker；`git diff --check`；code-review |

## 数据库迁移

无，不执行数据库操作。

## 部署与回滚

无部署；只读代码本地普通 revert 即可。本任务不触碰公司现场状态，现场重复执行/恢复全部按实际证据记录，不以本地测试填 PASS。
