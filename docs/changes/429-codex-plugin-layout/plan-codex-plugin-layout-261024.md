---
issue: 429
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/429
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - external-contract
depends_on: []
branch: change/429-codex-plugin-layout
created: 2026-10-24
updated: 2026-10-24
---

# 实施计划

## 全局约束与接口

只写 spec.git_scope 和本票证据；仅当前会话是写者。保持平台 pin、用户配置、两侧插件不变。显式启用前提、严格元数据校验与未知状态失败由全部验证共同覆盖。现有 check-external-skill-versions.sh / --home 接口不变。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 新旧 Codex 插件布局的端到端版本诊断、失败语义及完整验证 | - | pending |

## T01：修复 Codex 官方新插件布局

- **交付/范围**：新增官方新布局解析，保留旧布局；对应 regression fixture 和本机核验。
- **blocked_by**：无。
- **AC**：AC-1、AC-2、AC-3、AC-4、AC-5。
- **接口/约束**：沿用顶层命令，源文件只限检查器和测试；不安装、不改配置，元数据读取失败不能降级求绿。
- **验证**：bash codex/tests/test-external-skill-versions.sh；bash -n codex/tests/test-external-skill-versions.sh；shellcheck codex/tests/test-external-skill-versions.sh；bash codex/tests/smoke.sh；bash codex/tools/check-external-skill-versions.sh（真实 HOME 只读）；文档、scope 与 fixed candidate 检查。
- **Expected**：fixture 旧代码 RED、修复后定向和完整 smoke exit 0；真实 HOME 输出 PIN_DRIFT installed=7.0.1 pinned=7.0.0，RESULT REVIEW_NEEDED / exit 1；无 HOME 写入和 pyc。真实结果不等于 fresh-session 测试。双轴及跨 provider 审查无未修复阻断项。
- **停止条件**：合同冲突、未知安装格式需扩大权威来源、范围扩张、凭据/外部阻塞、重复失败；最终 PR 前停止确认；不自动 merge。

## Expected touch points

T01：检查器 Python、现有 shell 回归和本票四份文档。

## 数据库迁移、部署与回滚

无迁移、无部署。修改可受控 revert；不变更真实 HOME，不需要运行安装器。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1–AC-4 | 顶层 fixture 回归及零写入断言 |
| AC-5 | RED/GREEN、bash -n、ShellCheck、smoke、实机只读和独立审查 |

## 执行证据


<!-- execution-evidence:start -->
T01 已开始；原始 ticket_base=3715f09b89b18291f0765f826ea88616bc2f8e0f。RED/GREEN、实机安装标记发现和本机核验见映射 verification；最终完整smoke及Codex两轴复审均PASS，graph因Claude独立审查尚未获外发授权而保持pending；不记完整交付通过。
<!-- execution-evidence:end -->
