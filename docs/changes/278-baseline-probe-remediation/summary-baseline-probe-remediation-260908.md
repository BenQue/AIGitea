---
issue: 278
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/278
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-platform-baseline/v2 的 closed schema 与现场只读诊断外部合同，并新增受约束的特权观察面，命中 schema、安全、外部合同与共享平台组件强制风险，固定走 manual。
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-baseline-probe-remediation-260908.md
  spec: spec-baseline-probe-remediation-260908.md
  plan: plan-baseline-probe-remediation-260908.md
  verification: verification-baseline-probe-remediation-260908.md
depends_on: []
status: pr-open
branch: change/278-baseline-probe-remediation
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/279
created: 2026-09-08
updated: 2026-09-08
---

## 问题/需求总结

NewEMaint #79 的真实公司 `scm-ci` 只读证据揭示两处 collector 表达缺口：Gitea 1.26.4 的实际小写版本前缀未被接受，PostgreSQL 的 `enabled-runtime` 状态无法进入 closed schema。同时，8888 无监听与非特权 UFW 不可见需要一个不泄露配置、日志、Secret、数据库或原始规则的第二阶段定点诊断包。

## 影响范围

修改 `codex/runtime/aisoft_company_baseline_v2.py` 及其 schema/测试语义，新增 source-only 的确定性诊断 collector、closed schema、bundle builder、说明与回归测试，并记录 Issue #278 的 summary/spec/plan/verification。v1 collector 保持字节不变；不修改公司主机、service、UFW、Runner、数据库、凭据或 NewEMaint 仓。

## 初步方案与建议

严格接受真实小写 Gitea 版本格式但继续拒绝畸形输出；把 `enabled-runtime` 作为可表达但不满足持久 `enabled` 的 GAP。新增由项目 profile 与交接卡固定 `company-scm-ci` / `scm-ci` 目标的诊断包：仅采集 selected systemd 状态、对 `app.ini` 的 `PROTOCOL` / `HTTP_ADDR` / `HTTP_PORT` 做布尔比较、将 UFW 输出归一化为 active/default-deny/rule-count，不回显原文。包固定 digest、host pin、原 baseline evidence UUID 与 fresh diagnostic UUID；执行和任何现场整改继续需要独立授权。

## 风险

- 把 `enabled-runtime` 错误提升为 `enabled` / PASS，掩盖重启后的持久性缺口。
- 诊断程序意外回显 `app.ini`、UFW 规则、stderr、环境或其他敏感内容。
- source 修复被误解为 installed/live 已更新，或旧 envelope 被追溯改写。
- 诊断授权被扩大为 service、UFW、Runner 或数据库 mutation。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 company-platform-baseline/v2 的 closed schema 与现场只读诊断外部合同，并新增受约束的特权观察面，命中 schema、安全、外部合同与共享平台组件强制风险，固定走 manual。
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue #278 由 NewEMaint #79 的真实只读回执衍生，正文固定了实际版本输出、`enabled-runtime` 和现场无监听/非特权边界。
- `codex/runtime/aisoft_company_baseline_v2.py` 的 Gitea regex 当前固定大写 `Gitea version`，`SERVICE` enum 仅允许 `enabled/disabled/static/masked/not-found`。
- 现有 collector 已把 stderr 丢弃、HTTP 限定两个固定 GET、UFW 归一化，说明本修复必须保持同等或更窄的敏感信息边界。
- AISoftPlatform 属于 `public-platform` 且 `routine_auto_merge_enabled=false`；平台/schema/安全变更必须 complex/manual。

### 缺失的 acceptance criteria 或决策

- 无；具体字段、失败语义与授权边界由映射 spec 固定。

## 合同/启动确认

2026-09-08 用户已批准 exact Issue #278 / `change/278-baseline-probe-remediation` 的映射 spec/plan 与 T01–T04 Development Loop。当前任务再次读取 Issue/comments 与语义文档，无合同冲突；typed broker 判级投影后回读 `approved / complexity/complex / type/platform`。授权包含本地实现、验证与原子提交；最终停在 `AWAITING_PR_CONFIRMATION`，不 push/create PR。

## Development Loop 本地交接

T01–T04 已完成 source/local 实现与验证，进入 `AWAITING_PR_CONFIRMATION` / `manual`。targeted 79 项连续两次、完整 runtime 813 项通过；完整 smoke 在 host `LC_ALL=C` 下通过，默认 locale 的既有 Bash 3.2 兼容失败独立记录于 verification。最终 exact head、bundle manifest digest 与分层证据绑定保存在 `/private/tmp/issue-278-validation/state/projects/aisoft-platform/issues/278.json`。未 push/create PR，未安装/部署/执行公司诊断或更新 NewEMaint #79 pin、PR #81。
