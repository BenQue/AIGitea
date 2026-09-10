---
issue: 280
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/280
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - deployment
depends_on: []
status: approved
branch: change/280-diagnostics-reason-codes
created: 2026-09-10
updated: 2026-09-10
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立 v2 collector/schema，原因码与协议状态闭环及最小 mock 用例 | - | complete-local |
| T02 | 独立 v2 builder/guide 与可复核离线包、compatibility guard | T01 | complete-local |
| T03 | 完整 run 层 mock/脱敏/兼容回归及 verification 收敛 | T02 | complete-local |

用户已明确批准本票实施，三个 Ticket 已完成本地实现与验证；没有继承下游 #79 的现场授权。

## Expected touch points

T01：
- 新增 codex/runtime/aisoft_company_baseline_diagnostics_v2.py。
- 新增 company-delivery/baseline/diagnostics-v2.schema.json。
- 新增 codex/runtime/tests/test_company_baseline_diagnostics_v2.py。
- v1 语义作为基线，新增闭合原因表达；run 的异常在发生处分类，collect 保留 reason；
  verify 独立重算 reason/value/status，未知字段/伪造 fail closed。

T02：
- 新增 company-delivery/baseline/prepare-diagnostics-v2-bundle.py。
- 新增 company-delivery/baseline/DIAGNOSTICS-V2.md。
- 新增对应 builder 测试；只在必要时更新 company-delivery/baseline/README.md 的 v2 入口链接。
- 新包六文件为 v2 collector、diagnostics-v2.schema.json、原 profile-v1.schema.json、
  DIAGNOSTICS-V2.md、消费方 canonical baseline-profile.json、manifest.json。
- profile 由合成 fixture 注入，不将公司实例值作为平台默认值。正式交付只用 merged exact commit，
  local candidate 包明确标为 source/local，不给现场执行命令。

T03：
- 完成两个新测试文件与本目录 verification；必要的 README 链接，除此不修改旧 runtime/schema/builder。
- 检查真实 run 控制流的 mock：Popen startup OSError、selector 超时、oversize、decode、nonzero、
  cleanup；测试不得执行主机二进制或读取真实配置。
- 哨兵放在未知字段、异常、stdout/stderr 模拟内容，断言所有输出无哨兵；保持 stderr 丢弃。
- v1 文件与 exact base 比较，运行旧 suite，版本与 receipt 污染负例覆盖。

## 数据库迁移

无；无数据库连接。

## 测试与验收映射

实际命令与结果见 verification；新测试统一位于 test_company_baseline_diagnostics_v2.py，包含 collector 与 builder 测试。

| AC | 验证 |
|---|---|
| AC-1/2/3 | 新 v2 unittest：protocol/command/parse 表驱动 fixture 与精确 reason 断言 |
| AC-4 | Git diff allowlist、v1 hash guard、两代 verifier version/pin/time/checksum 负例 |
| AC-5 | Popen/文件访问 mock trap、stdout/stderr/exception 哨兵、argv/timeout/limit guard |
| AC-6 | 新 targeted suite 连续两次、既有 diagnostics/baseline suite、semantic docs、diff check |
| AC-7 | 新目录 builder 两次、manifest/payload 相同；digest/mode/symlink/extra-file 故意失败 |

计划运行 PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests
-p 'test_company_baseline_diagnostics_v2.py'；builder 测试同样按单文件 discover。
实际同时运行 test_company_baseline_diagnostics_v1、test_company_baseline_v2 与 test_company_baseline，合计 104 个测试通过。
若改 shell wrapper 则按 AGENTS 运行 smoke、bash -n、ShellCheck；本合同不计划改 shell 或 CI。

## 部署与回滚

无现场部署；仅生成本地 candidate 并标注 provenance。最终人工 PR 合并后，下游 #79 独立 repin、
手工拷贝与复采。Git revert 为 source 回退；不删除或改写 v1/history，不执行数据库恢复。
